import streamlit as st
import duckdb, pandas as pd, plotly.graph_objects as go, plotly.express as px
import joblib, os, io, tempfile
from fpdf import FPDF

# 1. 페이지 설정
st.set_page_config(page_title="MSK AI Analytics", page_icon="🏥", layout="wide")

# 2. 맞춤형 CSS (디자인 요소)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .status-card { padding: 10px 15px; border-radius: 5px; color: white; margin-bottom: 8px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 도움 함수
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

# --- 데이터 준비 ---
df = load_db_data()

# --- 4. 사이드바 UI 구성 ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774293.png", width=60)
st.sidebar.title("데이터 관리")

if df is not None:
    # [1순위: 환자 선택]
    p_list = sorted(df['patient_id'].unique())
    sel_id = st.sidebar.selectbox("👤 환자 선택 (최우선)", p_list)
    p_data = df[df['patient_id'] == sel_id].iloc[0]
    history = df[df['patient_id'] == sel_id].sort_values('ingested_at')

    # --- 메인 대시보드 로직 ---
    st.title("관절검사 데이터 AI 분석 시스템")
    st.caption(f"최근 측정일: {p_data['ingested_at'].strftime('%Y-%m-%d')}")

    tab1, tab2 = st.tabs(["📊 그룹 통계 분석", "🔍 환자별 정밀 리포트"])

    with tab1:
        st.subheader("🌐 전체 환자군 인사이트")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("평균 가동성", f"{df['mobility_score'].mean():.1f}")
        m2.metric("평균 통증 지수", f"{df['avg_pain'].mean():.1f}")
        m3.metric("총 분석 데이터", f"{len(df)}건")
        m4.metric("분석 환자 수", f"{len(p_list)}명")
        st.plotly_chart(px.scatter(df, x="mobility_score", y="avg_pain", color="pain_status" if 'pain_status' in df.columns else None, template="plotly_white"), use_container_width=True)

    with tab2:
        c1, c2 = st.columns(2)
        c1.markdown(f"**환자 번호:** `{sel_id}` | **현재 연령:** `{p_data['age']}세`")
        c2.markdown(f"**최근 측정일:** `{p_data['ingested_at'].strftime('%Y-%m-%d')}`")
        st.markdown("---")

        # AI 진단 로직
        try:
            model = joblib.load('models/pain_predictor.pkl')
            feats = joblib.load('models/feature_names.pkl')
            pred = round(model.predict(pd.DataFrame([p_data[feats]]))[0], 1)
            cp1, cp2 = st.columns([1, 2])
            cp1.metric("🤖 AI 예측 VAS", f"{pred} / 10")
            with cp2:
                diff = pred - p_data['avg_pain']
                if diff > 1.2: st.warning("⚠️ 예측치가 실제보다 높습니다. 관리 주의.")
                else: st.success("✅ 지표가 안정적으로 유지되고 있습니다.")
        except: pred = "N/A"

        # 시각화 (레이더 차트)
        cv_l, cv_r = st.columns([1, 1])
        joints = ['cervical', 'shoulder', 'trunk', 'hip', 'knee', 'ankle']
        fig_r = go.Figure(go.Scatterpolar(r=[p_data[f'{j}_rom'] for j in joints], theta=[j.capitalize() for j in joints], fill='toself'))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 180])), showlegend=False)
        with cv_l: st.plotly_chart(fig_r, use_container_width=True)
        with cv_r:
            st.write("#### 📍 부위별 상세 상태")
            for j in joints:
                status = p_data.get(f'{j}_status', 'N/A')
                color = "#ef5350" if status == "Severe" else "#66bb6a"
                st.markdown(f'<div class="status-card" style="background-color: {color};">{j.capitalize()} : {status} ({p_data[f"{j}_rom"]}°)</div>', unsafe_allow_html=True)

        # 시계열 추세
        st.write("#### 📈 Recovery Roadmap (시계열 분석)")
        fig_t = go.Figure()
        fig_t.add_trace(go.Bar(x=history['ingested_at'], y=history['mobility_score'], name="가동성", marker_color='#E3F2FD'))
        fig_t.add_trace(go.Scatter(x=history['ingested_at'], y=history['avg_pain'], name="통증", yaxis="y2", line=dict(color='#ef5350', width=4)))
        fig_t.update_layout(yaxis=dict(title="Mobility"), yaxis2=dict(title="Pain", overlaying="y", side="right"), template="plotly_white")
        st.plotly_chart(fig_t, use_container_width=True)

        # [2순위: PDF 발행 버튼 - 환자 선택 바로 아래에 배치하기 위해 위치 조정]
        st.sidebar.divider()
        st.sidebar.subheader("📄 결과물 내보내기")
        radar_bytes = fig_r.to_image(format="png")
        final_pdf = create_pdf(sel_id, p_data['age'], pred, "Care Needed" if (isinstance(pred, float) and pred > 5) else "Good", radar_bytes)
        st.sidebar.download_button("📂 PDF 리포트 발행", data=bytes(final_pdf), file_name=f"MSK_Report_{sel_id}.pdf", use_container_width=True)

# --- 5. 사이드바 하단 (엑셀 업로드 섹션) ---
# 빈 공간을 여러 개 넣어 아래로 밀어냅니다.
    st.sidebar.write("") 

st.sidebar.divider()
st.sidebar.subheader("환자 업로드")
uploaded_file = st.sidebar.file_uploader("📂 파일 업로드 (Excel)", type=["xlsx"])
st.sidebar.download_button("📥 업로드 양식 받기", get_sample_excel(), "msk_template.xlsx", use_container_width=True)

if uploaded_file:
    st.sidebar.success("파일이 감지되었습니다. 파이프라인 반영은 서버 설정을 확인하세요.")

if df is None:
    st.error("데이터가 없습니다. 파이프라인을 먼저 실행하세요.")