import streamlit as st
import duckdb, pandas as pd, plotly.graph_objects as go, plotly.express as px
import joblib, os, io, tempfile
from fpdf import FPDF

# 1. 페이지 설정 (아이콘 및 타이틀)
st.set_page_config(page_title="MSK AI Analytics", page_icon="🏥", layout="wide")

# 2. 맞춤형 CSS (카드 디자인 및 글꼴 스타일)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="stExpander"] {
        border: none !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .status-card {
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def load_data():
    if not os.path.exists('database/pipeline.db'): return None
    conn = duckdb.connect('database/pipeline.db')
    df = conn.execute("SELECT * FROM gold_msk_analytics").df()
    conn.close()
    return df.sort_values(['patient_id', 'ingested_at'], ascending=[True, False])

# [PDF 함수 동일 유지]
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

# --- 사이드바: 데이터 소스 선택 로직 ---
st.sidebar.title("📁 데이터 소스 관리")

# 1. 샘플 엑셀 다운로드 (사용자 편의성)
def get_sample_excel():
    sample_cols = ['patient_id', 'age', 'avg_pain', 'mobility_score', 
                   'cervical_rom', 'shoulder_rom', 'trunk_rom', 
                   'hip_rom', 'knee_rom', 'ankle_rom', 'ingested_at']
    # 샘플 데이터 1건 생성
    sample_df = pd.DataFrame([['P_SAMPLE', 45, 3.5, 75.0, 45, 150, 60, 100, 130, 20, '2026-01-01']], columns=sample_cols)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False)
    return output.getvalue()

st.sidebar.download_button("📥 엑셀 양식 다운로드", get_sample_excel(), "msk_template.xlsx")

# 2. 파일 업로더
uploaded_file = st.sidebar.file_uploader("📂 환자 데이터 업로드 (Excel)", type=["xlsx"])

# 3. 데이터 로드 (DB vs Excel 선택)
df_db = load_data() # 기존 DB 로드 함수 호출

if uploaded_file:
    try:
        df_upload = pd.read_excel(uploaded_file)
        # 날짜 형식 변환 (시계열 그래프용)
        df_upload['ingested_at'] = pd.to_datetime(df_upload['ingested_at'])
        
        # 선택 라디오 버튼
        source = st.sidebar.radio("사용할 데이터 선택:", ["기존 데이터베이스", "업로드한 엑셀 파일"])
        
        if source == "업로드한 엑셀 파일":
            df = df_upload
            st.sidebar.success("✅ 업로드된 데이터를 사용 중입니다.")
        else:
            df = df_db
    except Exception as e:
        st.sidebar.error(f"❌ 파일 읽기 오류: {e}")
        df = df_db
else:
    df = df_db



# --- 사이드바 디자인 ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3774/3774293.png", width=80)

df = load_data()
if df is not None:
    p_list = sorted(df['patient_id'].unique())
    sel_id = st.sidebar.selectbox("👤 분석 대상 환자 선택", p_list)
    p_data = df[df['patient_id'] == sel_id].iloc[0]
    history = df[df['patient_id'] == sel_id].sort_values('ingested_at')

# --- 사이드바: 데이터 소스 선택 로직 ---
st.sidebar.title("📁 데이터 소스 관리")

# 1. 샘플 엑셀 다운로드 (사용자 편의성)
def get_sample_excel():
    sample_cols = ['patient_id', 'age', 'avg_pain', 'mobility_score', 
                   'cervical_rom', 'shoulder_rom', 'trunk_rom', 
                   'hip_rom', 'knee_rom', 'ankle_rom', 'ingested_at']
    # 샘플 데이터 1건 생성
    sample_df = pd.DataFrame([['P_SAMPLE', 45, 3.5, 75.0, 45, 150, 60, 100, 130, 20, '2026-01-01']], columns=sample_cols)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False)
    return output.getvalue()

st.sidebar.download_button("📥 엑셀 양식 다운로드", get_sample_excel(), "msk_template.xlsx")

# 2. 파일 업로더
uploaded_file = st.sidebar.file_uploader("📂 환자 데이터 업로드 (Excel)", type=["xlsx"])

# 3. 데이터 로드 (DB vs Excel 선택)
df_db = load_data() # 기존 DB 로드 함수 호출

if uploaded_file:
    try:
        df_upload = pd.read_excel(uploaded_file)
        # 날짜 형식 변환 (시계열 그래프용)
        df_upload['ingested_at'] = pd.to_datetime(df_upload['ingested_at'])
        
        # 선택 라디오 버튼
        source = st.sidebar.radio("사용할 데이터 선택:", ["기존 데이터베이스", "업로드한 엑셀 파일"])
        
        if source == "업로드한 엑셀 파일":
            df = df_upload
            st.sidebar.success("✅ 업로드된 데이터를 사용 중입니다.")
        else:
            df = df_db
    except Exception as e:
        st.sidebar.error(f"❌ 파일 읽기 오류: {e}")
        df = df_db
else:
    df = df_db


# --- 메인 대시보드 ---
st.title("🏥 근골격계 AI 정밀 분석 시스템")
st.caption(f"최종 업데이트: {p_data['ingested_at'] if df is not None else 'N/A'}")

tab1, tab2 = st.tabs(["📊 그룹 통계 분석", "🔍 환자별 정밀 리포트"])

with tab1:
    st.subheader("🌐 전체 환자군 인사이트")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("평균 가동성", f"{df['mobility_score'].mean():.1f}", "↑ 1.2%")
    m2.metric("평균 통증 지수", f"{df['avg_pain'].mean():.1f}", "↓ 0.5%")
    m3.metric("누적 분석 건수", f"{len(df)}건")
    m4.metric("고위험군 비율", "12%", "🚩 관리필요")
    
    st.plotly_chart(px.scatter(df, x="mobility_score", y="avg_pain", color="pain_status", 
                               title="가동성 점수와 통증 지수의 상관관계", template="plotly_white"), use_container_width=True)

with tab2:
    # 환자 기본 정보 카드
    c_info1, c_info2, c_info3 = st.columns([1, 1, 2])
    with c_info1:
        st.markdown(f"**환자 번호:** `{sel_id}`")
        st.markdown(f"**현재 연령:** `{p_data['age']}세`")
    with c_info2:
        st.markdown(f"**측정 일시:** `{p_data['ingested_at'].strftime('%Y-%m-%d')}`")
    
    # AI 통합 진단 섹션
    st.markdown("---")
    try:
        model = joblib.load('models/pain_predictor.pkl')
        feats = joblib.load('models/feature_names.pkl')
        pred = round(model.predict(pd.DataFrame([p_data[feats]]))[0], 1)
        
        col_pred, col_msg = st.columns([1, 2])
        col_pred.metric("🤖 AI 예측 VAS", f"{pred} / 10")
        
        with col_msg:
            diff = pred - p_data['avg_pain']
            if diff > 1.2:
                st.warning(f"**[AI 판정] 잠재적 통증 위험** : 신체 지표 대비 예측 통증이 {round(diff,1)} 높습니다. 신경학적 정밀 검사를 권장합니다.")
            else:
                st.success("**[AI 판정] 상태 안정** : 현재 신체 가동성과 통증 지수가 균형 있게 관리되고 있습니다.")
    except: pred = "N/A"

    # 시각화 레이아웃 (카드형 레이아웃)
    col_vis_l, col_vis_r = st.columns([1, 1])
    
    with col_vis_l:
        st.write("#### 🎯 신체 밸런스 맵")
        joints = ['cervical', 'shoulder', 'trunk', 'hip', 'knee', 'ankle']
        fig_r = go.Figure(go.Scatterpolar(r=[p_data[f'{j}_rom'] for j in joints], 
                                          theta=[j.capitalize() for j in joints], fill='toself',
                                          fillcolor='rgba(0, 123, 255, 0.3)', line=dict(color='#007bff')))
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 180])), showlegend=False, margin=dict(t=30, b=30))
        st.plotly_chart(fig_r, use_container_width=True)

    with col_vis_r:
        st.write("#### 📍 부위별 상세 상태")
        for j in joints:
            status = p_data[f'{j}_status']
            color = "#ef5350" if status == "Severe" else "#66bb6a"
            st.markdown(f"""
                <div style="background-color: {color}; padding: 8px 15px; border-radius: 5px; color: white; margin-bottom: 8px; font-weight: bold;">
                    {j.capitalize()} : {status} ({p_data[f'{j}_rom']}°)
                </div>
                """, unsafe_allow_html=True)

    # 하단 추세 차트 디자인
    st.write("#### 📈 Recovery Roadmap (시계열 분석)")
    fig_t = go.Figure()
    fig_t.add_trace(go.Bar(x=history['ingested_at'], y=history['mobility_score'], name="Mobility", marker_color='#E3F2FD'))
    fig_t.add_trace(go.Scatter(x=history['ingested_at'], y=history['avg_pain'], name="Pain (VAS)", yaxis="y2", line=dict(color='#ef5350', width=4)))
    fig_t.update_layout(yaxis=dict(title="Mobility Score"), yaxis2=dict(title="Pain Index", overlaying="y", side="right"),
                      template="plotly_white", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_t, use_container_width=True)

    # 리포트 다운로드 버튼 (색상 강조)
    radar_bytes = fig_r.to_image(format="png", engine="kaleido")
    final_pdf = create_pdf(sel_id, p_data['age'], pred, "Care Needed" if str(pred) != "N/A" and pred > 5 else "Good", radar_bytes)
    st.sidebar.divider()
    st.sidebar.download_button("📂 PDF 리포트 발행", data=bytes(final_pdf), file_name=f"MSK_Report_{sel_id}.pdf", use_container_width=True)