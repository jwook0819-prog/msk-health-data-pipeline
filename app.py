import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import joblib
import os
import subprocess
import sys
import io
import tempfile
from fpdf import FPDF

# 1. 페이지 설정 (최상단)
st.set_page_config(page_title="근골격계 분석 대시보드", layout="wide")

# --- PDF 생성 함수 (이미지 삽입 로직 통합) ---
def create_pdf(patient_id, age, prediction, status, radar_img_bytes):
    pdf = FPDF()
    pdf.add_page()
    
    # 폰트 설정
    font_path = "NanumGothic-Regular.ttf"
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 16)
    else:
        pdf.set_font('Arial', 'B', 16)

    # 헤더
    pdf.cell(200, 10, txt="[근골격계 건강 분석 리포트]", ln=True, align='C')
    pdf.ln(10)
    
    # 이미지 삽입 (레이더 차트)
    if radar_img_bytes:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            tmpfile.write(radar_img_bytes)
            tmp_path = tmpfile.name
        pdf.image(tmp_path, x=45, y=30, w=120)
        os.unlink(tmp_path) # 임시파일 삭제
        pdf.ln(110) # 이미지 공간 확보

    # 환자 정보 및 AI 분석 결과
    if 'Nanum' in pdf.fonts: pdf.set_font('Nanum', '', 12)
    pdf.cell(200, 10, txt=f"환자 ID: {patient_id}  |  연령: {age}세", ln=True)
    pdf.cell(200, 10, txt=f"AI 예측 통증 지수 (VAS): {prediction} / 10", ln=True)
    pdf.cell(200, 10, txt=f"종합 분석 소견: {status}", ln=True)
    
    return pdf.output()

# --- 자동 데이터 파이프라인 (서버용) ---
current_dir = os.path.dirname(os.path.abspath(__file__))
db_dir = os.path.join(current_dir, 'database')
db_path = os.path.join(db_dir, 'pipeline.db')

if not os.path.exists(db_path):
    if not os.path.exists(db_dir): os.makedirs(db_dir)
    st.info("🌐 서버 데이터가 감지되지 않아 파이프라인을 자동 가동합니다...")
    try:
        pipeline_script = os.path.join(current_dir, "main_pipeline.py")
        subprocess.run([sys.executable, pipeline_script], check=True)
        st.success("✅ 데이터 생성 완료!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 가동 실패: {e}")
        st.stop()

# --- 모델 및 데이터 로드 ---
@st.cache_resource
def load_trained_model():
    try:
        model = joblib.load('models/pain_predictor.pkl')
        features = joblib.load('models/feature_names.pkl')
        return model, features
    except: return None, None

@st.cache_data
def load_data():
    try:
        conn = duckdb.connect('database/pipeline.db')
        df = conn.execute("SELECT * FROM gold_msk_analytics").df()
        conn.close()
        return df
    except: return None

df = load_data()
model, features = load_trained_model()

# --- 사이드바 및 엑셀 업로드 ---
st.sidebar.title("환자 관리 시스템")

def get_sample_excel():
    sample_cols = ['patient_id', 'age', 'gender', 'height', 'weight', 'forward_head_angle', 'grip_strength', 'pelvic_tilt', 'cervical_rom', 'shoulder_rom', 'trunk_rom', 'hip_rom', 'knee_rom', 'ankle_rom', 'avg_pain']
    sample_df = pd.DataFrame([['SAMPLE_01', 45, 'M', 175.5, 72.0, 15.5, 38.2, 12.0, 45, 150, 60, 100, 130, 20, 3.5]], columns=sample_cols)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False)
    return output.getvalue()

st.sidebar.download_button("📥 샘플 양식 다운로드", get_sample_excel(), "sample.xlsx")
uploaded_file = st.sidebar.file_uploader("엑셀 업로드", type=["xlsx", "csv"])

if uploaded_file:
    try:
        ext_df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
        mode = st.sidebar.radio("데이터 소스", ["기본 DB", "업로드 파일"])
        if mode == "업로드 파일": df = ext_df
    except Exception as e: st.sidebar.error(f"오류: {e}")

selected_id = st.sidebar.selectbox("환자 ID 선택", df['patient_id'].tolist())
p_data = df[df['patient_id'] == selected_id].iloc[0]

# --- 메인 화면 구성 ---
st.title("🦴 근골격계 데이터 분석 리포트")
tab1, tab2 = st.tabs(["📊 그룹 인사이트", "🔍 개별 정밀 리포트"])

with tab1:
    st.subheader("📈 전체 데이터 인사이트")
    col1, col2, col3 = st.columns(3)
    col1.metric("평균 가동성", f"{df['mobility_score'].mean():.1f}")
    col2.metric("평균 통증(VAS)", f"{df['avg_pain'].mean():.1f}")
    col3.metric("총 환자 수", f"{len(df)}명")
    
    fig_box = px.box(df, x="age", y="mobility_score", title="연령별 가동성")
    st.plotly_chart(fig_box, use_container_width=True)

with tab2:
    st.subheader(f"🔍환자{selected_id}  분석")
    
    # AI 예측
    predicted_vas = None
    if model and features:
        input_data = pd.DataFrame([p_data[features]])
        predicted_vas = round(model.predict(input_data)[0], 1)
        st.info(f"AI 예측 통증 지수: {predicted_vas} / 10 (실제: {p_data['avg_pain']})")

    # 레이더 차트 생성 및 이미지 캡처
    joints = ['cervical', 'shoulder', 'trunk', 'hip', 'knee', 'ankle']
    categories = [j.capitalize() for j in joints]
    values = [p_data[f'{j}_rom'] for j in joints]
    
    fig_radar = go.Figure(go.Scatterpolar(r=values, theta=categories, fill='toself'))
    fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 180])), title="신체 밸런스 맵")
    
    # 🖼️ 이미지를 바이트로 변환 (PDF용)
    radar_img_bytes = fig_radar.to_image(format="png", engine="kaleido")
    
    c1, c2 = st.columns(2)
    with c1:
        for j in joints:
            st.write(f"**{j.capitalize()}**: {p_data[f'{j}_rom']}°")
    with c2:
        st.plotly_chart(fig_radar, use_container_width=True)

    # PDF 출력 버튼
    st.divider()
    raw_age = p_data['age']
    clean_age = raw_age.values[0] if hasattr(raw_age, 'values') else raw_age
    status_text = "관리가 필요한 상태입니다." if (predicted_vas and predicted_vas > 4) else "양호한 상태입니다."
    
    pdf_output = create_pdf(selected_id, clean_age, predicted_vas, status_text, radar_img_bytes)
    st.download_button("결과지 PDF 다운로드", data=bytes(pdf_output), file_name=f"Report_{selected_id}.pdf", mime="application/pdf")