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

# 3. 데이터 로드 및 PDF 함수
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
    sample_cols = ['patient_id', 'age', 'avg_pain', 'mobility_score', 
                   'cervical_rom', 'shoulder_rom', 'trunk_rom', 
                   'hip_rom', 'knee_rom', 'ankle_rom', 'ingested_at',
                   'cervical_status', 'shoulder_status', 'trunk_status', 'hip_status', 'knee_status', 'ankle_status', 'pain_status']
    sample_df = pd.DataFrame([['P_SAMPLE', 45, 3.5, 75.0, 45, 150, 60, 100, 130, 20, '2026-01-01', 'Normal', 'Normal', 'Normal', 'Normal', 'Normal', 'Normal', 'Normal']], columns=sample_cols)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False)
    return output.getvalue()

# --- 4. 사이드바: 데이터 소스 및 환자 선택 ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774293.png", width=80)
st.sidebar.title("📁 데이터 관리 시스템")

# 엑셀 업로드 및 샘플 다운로드
st.sidebar.download_button("📥 엑셀 양식 다운로드", get_sample_excel(), "msk_template.xlsx")
uploaded_file = st.sidebar.file_uploader("📂 환자 데이터 업로드 (Excel)", type=["xlsx"])

# 데이터 결정 로직
df_db = load_db_data()
df = None

if uploaded_file:
    try:
        df_upload = pd.read_excel(uploaded_file)
        df_upload['ingested_at'] = pd.to_datetime(df_upload['ingested_at'])
        source = st.sidebar.radio("데이터 소스 선택:", ["기본 데이터베이스", "업로드 파일"])
        df = df_upload if source == "업로드 파일" else df_db
    except Exception as e:
        st.sidebar.error(f"파일 에러: {e}")
        df = df_db
else:
    df = df_db

# 환자 선택
if df is not None and not df.empty:
    df = df.sort_values(['patient_id', 'ingested_at'], ascending=[True, False])
    p_list = sorted(df['patient_id'].unique())
    sel_id = st.sidebar.selectbox("👤 분석 대상 환자 선택", p_list)
    
    # 선택된 환자 데이터 추출
    p_data = df[df['patient_id'] == sel_id].iloc[0]
    history = df[df['patient_id'] == sel_id].sort_values('ingested_at')

    # --- 5. 메인 대시보드 ---
    st.title("🏥 근골격계 AI 정밀 분석 시스템")
    st.caption(f"최종 업데이트: {p_data['ingested_at'].strftime('%Y-%m-%d') if pd.notnull(p_data['ingested_at']) else 'N/A'}")

    tab1, tab2 = st.tabs(["📊 그룹 통계 분석", "🔍 환자별 정밀 리포트"])

    with tab1:
        st.subheader("🌐 전체 환자군 인사이트")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("평균 가동성", f"{df['mobility_score'].mean():.1f}", "상태 지표")
        m2.metric("평균 통증 지수", f"{df['avg_pain'].mean():.1f}", "VAS 기준")
        m3.metric("총 분석 데이터", f"{len(df)}건")
        m4.metric("분석 환자 수", f"{len(p_list)}명")
        
        st.plotly_chart(px.scatter(df, x="mobility_score", y="avg_pain", color="pain_status" if 'pain_status' in df.columns else None, 
                                   title="가동성 점수와 통증 지수의 상관관계", template="plotly_white"), use_container_width=True)

    with tab2:
        # 환자 기본 정보
        c_info1, c_info2 = st.columns(2)
        c_info1.markdown(f"**환자 번호:** `{sel_id}` | **현재 연령:** `{p_data['age']}세`")
        c_info2.markdown(f"**최근 측정일:** `{p_data['ingested_at'].strftime('%Y-%m-%d')}`")
        
        # AI 진단
        st.markdown("---")
        try:
            model = joblib.load('models/pain_predictor.pkl')
            feats = joblib.load('models/feature_names.pkl')
            pred = round(model.predict(pd.DataFrame([p_data[feats]]))[0], 1)
            
            cp1, cp2 = st.columns([1, 2])
            cp1.metric("🤖 AI 예측 VAS", f"{pred} / 10")
            with cp2:
                diff = pred - p_data['avg_pain']
                if diff > 1.2: st.warning(f"**[AI 판정] 위험군** : 예측치({pred})가 실제 통증보다 높습니다. 잠재적 통증 악화에 주의하세요.")
                else: st.success("**[AI 판정] 안정** : 신체 지표와 통증 수준이 적절히 유지되고 있습니다.")
        except: pred = "N/A"; st.info("AI 모델을 불러올 수 없어 기본 분석만 제공합니다.")

        # 시각화
        cv_l, cv_r = st.columns([1, 1])
        joints = ['cervical', 'shoulder', 'trunk', 'hip', 'knee', 'ankle']
        
        with cv_l:
            st.write("#### 🎯 신체 밸런스 맵")
            fig_r = go.Figure(go.Scatterpolar(r=[p_data[f'{j}_rom'] for j in joints], 
                                              theta=[j.capitalize() for j in joints], fill='toself',
                                              fillcolor='rgba(0, 123, 255, 0.3)', line=dict(color='#007bff')))
            fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 180])), showlegend=False)
            st.plotly_chart(fig_r, use_container_width=True)

        with cv_r:
            st.write("#### 📍 부위별 상세 상태")
            for j in joints:
                status = p_data.get(f'{j}_status', 'N/A')
                color = "#ef5350" if status == "Severe" else "#66bb6a"
                st.markdown(f'<div class="status-card" style="background-color: {color};">{j.capitalize()} : {status} ({p_data[f"{j}_rom"]}°)</div>', unsafe_allow_html=True)

        # 회복 로드맵
        st.write("#### 📈 Recovery Roadmap (시계열 분석)")
        fig_t = go.Figure()
        fig_t.add_trace(go.Bar(x=history['ingested_at'], y=history['mobility_score'], name="Mobility", marker_color='#E3F2FD'))
        fig_t.add_trace(go.Scatter(x=history['ingested_at'], y=history['avg_pain'], name="Pain (VAS)", yaxis="y2", line=dict(color='#ef5350', width=4)))
        fig_t.update_layout(yaxis=dict(title="Mobility"), yaxis2=dict(title="Pain", overlaying="y", side="right"), template="plotly_white")
        st.plotly_chart(fig_t, use_container_width=True)

        # 리포트 발행
        radar_bytes = fig_r.to_image(format="png")
        final_pdf = create_pdf(sel_id, p_data['age'], pred, "Care Needed" if pred != "N/A" and pred > 5 else "Good", radar_bytes)
        st.sidebar.divider()
        st.sidebar.download_button("📂 PDF 리포트 발행", data=bytes(final_pdf), file_name=f"MSK_Report_{sel_id}.pdf", use_container_width=True)

else:
    st.title("🏥 MSK AI Analytics")
    st.error("표시할 데이터가 없습니다. 파이프라인을 실행하여 DB를 생성하거나 엑셀 파일을 업로드해 주세요.")