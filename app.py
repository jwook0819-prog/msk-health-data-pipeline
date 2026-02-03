import streamlit as st
import duckdb, pandas as pd, plotly.graph_objects as go, plotly.express as px
import joblib, os, io, tempfile
from fpdf import FPDF

# 1. 페이지 설정
st.set_page_config(page_title="MSK AI Analytics", page_icon="🏥", layout="wide")

# 2. 맞춤형 CSS
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-card {
        padding: 10px 15px;
        border-radius: 5px;
        color: white;
        margin-bottom: 8px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [기초 데이터 및 함수 정의] ---
@st.cache_data
def load_db_data():
    if not os.path.exists('database/pipeline.db'): return None
    conn = duckdb.connect('database/pipeline.db')
    df = conn.execute("SELECT * FROM gold_msk_analytics").df()
    conn.close()
    return df

def create_pdf(p_id, age, pred, status, radar_bytes):
    pdf = FPDF()
    pdf.add_page()
    font_path = "NanumGothic-Regular.ttf"
    if os.path.exists(font_path):
        pdf.add_font('Nanum', '', font_path)
        pdf.set_font('Nanum', '', 16)
    else: pdf.set_font('Arial', 'B', 16)
    pdf.cell(200, 10, txt=f"[ {p_id} Patient Report ]", ln=True, align='C')
    if radar_bytes:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(radar_bytes); pdf.image(tmp.name, x=45, y=35, w=120)
        pdf.ln(110)
    if 'Nanum' in pdf.fonts: pdf.set_font('Nanum', '', 12)
    pdf.cell(200, 10, txt=f"Age: {age} / AI Pred VAS: {pred} / Result: {status}", ln=True)
    return pdf.output()

def get_sample_excel():
    sample_cols = ['patient_id', 'age', 'avg_pain', 'mobility_score', 'cervical_rom', 'shoulder_rom', 'trunk_rom', 'hip_rom', 'knee_rom', 'ankle_rom', 'ingested_at']
    sample_df = pd.DataFrame([['P_SAMPLE', 45, 3.5, 75.0, 45, 150, 60, 100, 130, 20, '2026-01-01']], columns=sample_cols)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False)
    return output.getvalue()

# --- [데이터 로드 로직: UI 표시 전 실행] ---
df_db = load_db_data()
df_final = df_db # 기본값

# --- 3. 사이드바 UI 구성 (요청하신 순서 적용) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774293.png", width=80)
st.sidebar.title("데이터 관리 시스템")

# [순서 1: 환자 선택]
if df_db is not None:
    # 엑셀 업로드 파일이 있는지 먼저 확인 (데이터 소스 스위칭용)
    uploaded_file = st.sidebar.file_uploader("📂 데이터 업로드 (Excel)", type=["xlsx"])
    
    if uploaded_file:
        try:
            df_upload = pd.read_excel(uploaded_file)
            df_upload['ingested_at'] = pd.to_datetime(df_upload['ingested_at'])
            source = st.sidebar.radio("데이터 소스 선택:", ["기본 DB", "업로드 파일"], horizontal=True)
            df_final = df_upload if source == "업로드 파일" else df_db
        except:
            st.sidebar.error("파일 읽기 실패")
            df_final = df_db

    df_final = df_final.sort_values(['patient_id', 'ingested_at'], ascending=[True, False])
    p_list = sorted(df_final['patient_id'].unique())
    sel_id = st.sidebar.selectbox("👤 환자 선택 (가장 많이 사용)", p_list)
    
    p_data = df_final[df_final['patient_id'] == sel_id].iloc[0]
    history = df_final[df_final['patient_id'] == sel_id].sort_values('ingested_at')

    # [순서 2: PDF 다운로드]
    st.sidebar.divider()
    st.sidebar.subheader("📄 결과물 내보내기")
    # PDF 생성을 위한 더미 이미지와 값들 (나중에 하단에서 실데이터로 업데이트)
    # 실제 PDF 버튼은 메인 로직 하단에서 이미지 생성 후 배치하거나, 여기서 함수화하여 호출

    # [순서 3: 엑셀 양식 다운로드]
    st.sidebar.divider()
    st.sidebar.subheader("⚙️ 시스템 관리")
    st.sidebar.download_button("📥 엑셀 업로드 양식 받기", get_sample_excel(), "msk_template.xlsx", use_container_width=True)

# --- 4. 메인 대시보드 표시 ---
if df_final is not None:
    st.title("관절검사 데이터 AI 분석 시스템")
    st.caption(f"최종 측정일: {p_data['ingested_at'].strftime('%Y-%m-%d')}")

    tab1, tab2 = st.tabs(["📊 그룹 통계 분석", "🔍 환자별 정밀 리포트"])

    # [Tab 1 & Tab 2 내용은 이전과 동일하게 유지...]
    with tab2:
        # (중략: AI 진단, 레이더 차트, 상세 상태 카드, 시계열 그래프 코드)
        # ... (이전 코드의 tab2 내용 삽입) ...
        
        # --- 레이더 차트 이미지 생성 ---
        joints = ['cervical', 'shoulder', 'trunk', 'hip', 'knee', 'ankle']
        fig_r = go.Figure(go.Scatterpolar(r=[p_data[f'{j}_rom'] for j in joints], theta=[j.capitalize() for j in joints], fill='toself'))
        # (차트 레이아웃 설정)
        st.plotly_chart(fig_r)
        
        # --- [순서 2의 실질적 구현: PDF 버튼] ---
        # Plotly 차트가 생성된 후 이미지를 뜰 수 있으므로, 
        # 버튼을 사이드바에 위치시키고 싶다면 이 위치에서 생성하여 사이드바 섹션에 할당
        radar_bytes = fig_r.to_image(format="png")
        # AI 예측값 pred가 계산되었다고 가정
        pred = 5.0 # 예시
        final_pdf = create_pdf(sel_id, p_data['age'], pred, "Care Needed", radar_bytes)
        
        # 사이드바의 특정 위치에 버튼 다시 배치
        st.sidebar.download_button(
            label="📥 PDF 리포트 다운로드",
            data=bytes(final_pdf),
            file_name=f"Report_{sel_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )