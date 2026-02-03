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
st.sidebar.title("진료 매니저")

if df is not None:
    # [1순위: 환자 선택]
    p_list = sorted(df['patient_id'].unique())
    st.sidebar.subheader("👤 환자 선택") 
    sel_id = st.sidebar.selectbox("", options=p_list, key="patient_selector")
    
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
    # 1. 상단 요약 바 (AI 진단 결과)
    st.markdown("#### 🩺 AI 종합 판독 결과")
    try:
        model = joblib.load('models/pain_predictor.pkl')
        feats = joblib.load('models/feature_names.pkl')
        pred = round(float(model.predict(pd.DataFrame([p_data[feats]]))[0]), 1)
        
        c_m1, c_m2 = st.columns([1, 2])
        c_m1.metric("예상 통증 지수 (VAS)", f"{pred} / 10")
        with c_m2:
            if pred > 6.0: st.error("🚨 중증도 통증 위험이 감지되었습니다. 즉각적인 가동성 개선이 필요합니다.")
            elif pred > 3.0: st.warning("⚠️ 경미한 통증이 예상됩니다. 무리한 운동은 피하고 스트레칭을 늘리세요.")
            else: st.success("✅ 통증 지수가 낮습니다. 현재의 가동성 밸런스를 잘 유지하고 계십니다.")
    except:
        st.info("ℹ️ AI 모델 로딩 중이거나 데이터가 부족하여 예측치를 표시할 수 없습니다.")

    st.divider()

    # 2. 중간 시각화 영역 (레이더 차트 & 상세 카드)
    cv_l, cv_r = st.columns([1, 1])
    
    joints_map = {
        'cervical': {'name': 'Cervical', 'limit': 45},
        'shoulder': {'name': 'Shoulder', 'limit': 150},
        'trunk': {'name': 'Trunk', 'limit': 60},
        'hip': {'name': 'Hip', 'limit': 100},
        'knee': {'name': 'Knee', 'limit': 130},
        'ankle': {'name': 'Ankle', 'limit': 20}
    }
    joints = list(joints_map.keys())

    with cv_l:
        st.write("#### 🎯 신체 가동성 밸런스 맵")
        actual_vals = [round(float(p_data[f'{j}_rom']), 1) for j in joints]
        percent_vals = [round(min((v / joints_map[j]['limit']) * 100, 110), 1) for v, j in zip(actual_vals, joints)]
        
        avg_score = sum(percent_vals) / len(percent_vals)
        theme_color = '#ef5350' if avg_score < 70 else '#007bff'
        fill_color = 'rgba(239, 83, 80, 0.3)' if avg_score < 70 else 'rgba(0, 123, 255, 0.3)'

        fig_r = go.Figure()
        fig_r.add_trace(go.Scatterpolar(r=[100]*6, theta=[info['name'] for info in joints_map.values()], fill='none', name='정상 기준(100%)', line=dict(color='rgba(150,150,150,0.5)', dash='dash')))
        fig_r.add_trace(go.Scatterpolar(r=percent_vals, theta=[info['name'] for info in joints_map.values()], fill='toself', name='환자 달성도(%)', fillcolor=fill_color, line=dict(color=theme_color, width=3), customdata=actual_vals, hovertemplate='<b>%{theta}</b><br>달성도: %{r:.1f}%<br>실제: %{customdata}°<extra></extra>'))
        
        fig_r.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 115], tickvals=[0, 50, 100], ticktext=['0%', '50%', '100%'])), showlegend=True, margin=dict(t=50, b=50))
        st.plotly_chart(fig_r, use_container_width=True)

    with cv_r:
        st.write("#### 📍 부위별 상세 상태")
        for j in joints:
            info = joints_map[j]
            val = round(float(p_data[f'{j}_rom']), 1)
            percent = (val / info['limit']) * 100
            card_color = "#ef5350" if percent < 70 else "#66bb6a"
            
            st.markdown(f"""
                <div style="background-color: {card_color}; padding: 12px 20px; border-radius: 8px; color: white; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: bold;">{info['name']}</span>
                    <span><b>{val:.1f}°</b> / {info['limit']}° ({percent:.1f}%)</span>
                </div>
            """, unsafe_allow_html=True)

    st.divider()

    # 3. 하단 운동 처방 영역
    st.subheader("🧘 AI 맞춤형 운동 처방")
    low_parts = [p for p, info in joints_map.items() if (float(p_data.get(f'{p}_rom', 0)) / info['limit']) < 0.7]

    if low_parts:
        st.warning(f"⚠️ 현재 가동 범위 달성도가 낮은 **{len(low_parts)}개 부위** 운동영상 링크입니다.")
        display_parts = low_parts
    else:
        st.success("✨ 모든 관절이 양호한 상태입니다! 예방 차원의 전신 관리 프로그램을 추천합니다.")
        display_parts = list(joints_map.keys())

    rows = [display_parts[i:i + 3] for i in range(0, len(display_parts), 3)]
    for row in rows:
        cols = st.columns(3)
        for idx, part in enumerate(row):
            info = joints_map[part]
            val = round(float(p_data.get(f'{part}_rom', 0)), 1)
            with cols[idx]:
                card_style = st.error if (val / joints_map[part]['limit']) < 0.7 else st.info
                card_style(f"**{part.upper()} {'집중' if (val / joints_map[part]['limit']) < 0.7 else '유지'}관리**")
                st.markdown(f"📍 **{part.capitalize()} 스트레칭**")
                st.caption(f"측정값: {val:.1f}° (기준: {joints_map[part]['limit']}°)")
                st.link_button("🎥 가이드 보기", f"https://www.youtube.com/results?search_query={part}+mobility+exercise", use_container_width=True)

    # [2순위: PDF 발행] - 환자 선택 블록(if df) 안에 위치
    st.sidebar.divider()
    st.sidebar.subheader("📄 결과물 내보내기")
    radar_bytes = fig_r.to_image(format="png")
    final_pdf = create_pdf(sel_id, p_data['age'], pred, "Care Needed" if (isinstance(pred, float) and pred > 5) else "Good", radar_bytes)
    st.sidebar.download_button("📂 PDF 리포트 발행", data=bytes(final_pdf), file_name=f"MSK_Report_{sel_id}.pdf", use_container_width=True)

# --- 5. 사이드바 최하단 (업로드 섹션) ---
st.sidebar.divider()
st.sidebar.subheader("환자 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("📂 파일 업로드", type=["xlsx"])
st.sidebar.download_button("📥 양식 다운로드", get_sample_excel(), "msk_template.xlsx", use_container_width=True)

if uploaded_file:
    st.sidebar.success("파일 감지됨! 파이프라인 설정을 확인하세요.")

if df is None:
    st.error("데이터베이스 파일이 없습니다. 파이프라인을 먼저 실행하세요.")