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
        c1, c2 = st.columns(2)
        c1.markdown(f"**환자 번호:** `{sel_id}` | **현재 연령:** `{p_data['age']}세`")
        c2.markdown(f"**최근 측정일:** `{p_data['ingested_at'].strftime('%Y-%m-%d')}`")
        st.markdown("---")

        # AI 진단
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

# --- 레이더 차트 및 상세 카드 섹션 (완전 교체용) ---
        cv_l, cv_r = st.columns([1, 1])

        # 1. 관절별 임상 정상 기준치 정의 (각 관절의 100% 지점)
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
            st.write("#### 🎯 신체 밸런스 맵 (정상치 대비 달성도)")
            
            # 실제 각도는 소수점 1자리로 반올림하여 준비
            actual_vals = [round(float(p_data[f'{j}_rom']), 1) for j in joints]
            # 차트에 그릴 때는 '실제값 / 기준값' 비율(%)로 환산 (최대 110%로 제한)
            percent_vals = [min((v / joints_map[j]['limit']) * 100, 110) for v, j in zip(actual_vals, joints)]
            
            # 평균 달성률에 따라 색상 결정 (70% 미만 시 경고색)
            avg_score = sum(percent_vals) / len(percent_vals)
            theme_color = '#ef5350' if avg_score < 70 else '#007bff'
            fill_color = 'rgba(239, 83, 80, 0.3)' if avg_score < 70 else 'rgba(0, 123, 255, 0.3)'

            fig_r = go.Figure()

            # 가이드라인: 정상 기준 100% 라인 (점선)
            fig_r.add_trace(go.Scatterpolar(
                r=[100] * 6,
                theta=[info['name'] for info in joints_map.values()],
                fill='none',
                name='정상 기준 (100%)',
                line=dict(color='rgba(150, 150, 150, 0.5)', dash='dash', width=2),
                hoverinfo='skip'
            ))

            # 환자 데이터: 비율(%) 기준으로 시각화
            fig_r.add_trace(go.Scatterpolar(
                r=percent_vals,
                theta=[info['name'] for info in joints_map.values()],
                fill='toself',
                name='현재 달성도 (%)',
                fillcolor=fill_color,
                line=dict(color=theme_color, width=3),
                customdata=actual_vals, # 실제 각도 데이터를 숨겨둠
                hovertemplate='<b>%{theta}</b><br>달성도: %{r:.1f}%<br>실제각도: %{customdata}°<extra></extra>'
            ))

            fig_r.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True, 
                        range=[0, 115], # 시각적 안정감을 위해 115%까지 표시
                        tickvals=[0, 50, 100],
                        ticktext=['0%', '50%', '100%'],
                        gridcolor="#eee"
                    ),
                    bgcolor="white"
                ),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5),
                margin=dict(t=80, b=40, l=60, r=60),
                height=450
            )
            st.plotly_chart(fig_r, use_container_width=True)

        with cv_r:
            st.write("#### 📍 부위별 상세 상태")
            for j in joints:
                info = joints_map[j]
                val = round(float(p_data[f'{j}_rom']), 1) # 여기서 소수점 1자리 고정
                status = p_data.get(f'{j}_status', 'N/A')
                # 정상치 대비 현재 비율 계산
                percent = (val / info['limit']) * 100
                
                # 상태별 카드 색상 (비율이 70% 미만이면 빨간색)
                card_color = "#ef5350" if percent < 70 else "#66bb6a"
                
                st.markdown(f"""
                    <div style="background-color: {card_color}; padding: 12px 20px; border-radius: 8px; color: white; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: bold;">{info['name']}</span>
                        <span><b>{val}°</b> / {info['limit']}° ({status})</span>
                    </div>
                """, unsafe_allow_html=True)

        # 시계열 추세
        st.write("#### 📈 Recovery Roadmap")
        fig_t = go.Figure()
        fig_t.add_trace(go.Bar(x=history['ingested_at'], y=history['mobility_score'], name="가동성", marker_color='#E3F2FD'))
        fig_t.add_trace(go.Scatter(x=history['ingested_at'], y=history['avg_pain'], name="통증", yaxis="y2", line=dict(color='#ef5350', width=4)))
        fig_t.update_layout(yaxis=dict(title="Mobility"), yaxis2=dict(title="Pain", overlaying="y", side="right"), template="plotly_white")
        st.plotly_chart(fig_t, use_container_width=True)

# --- 운동 처방 섹션 ---
        st.divider()
        st.subheader("🧘 AI 맞춤형 운동 처방")
        
        guide_db = {
            'cervical': {'name': '목 스트레칭', 'limit': 45, 'desc': '목 정렬 및 거북목 개선'},
            'shoulder': {'name': '어깨 스트레칭', 'limit': 150, 'desc': '굽은 어깨 및 가동성 확보'},
            'trunk': {'name': '몸통 스트레칭', 'limit': 60, 'desc': '척추 기립근 강화'},
            'hip': {'name': '골반 스트레칭', 'limit': 100, 'desc': '하체 유연성 증대'},
            'knee': {'name': '무릎 스트레칭', 'limit': 130, 'desc': '무릎 관절 안정화'},
            'ankle': {'name': '발목 스트레칭', 'limit': 20, 'desc': '보행 균형 개선'}
        }

        # 1. 관리 필요 부위 확인 (소수점 첫째자리 정밀도 반영)
        low_parts = [p for p, info in guide_db.items() if round(float(p_data.get(f'{p}_rom', 180)), 1) < info['limit']]

        # 2. UI 최상단 메시지 결정 (중복 방지를 위해 if-else로 분리)
        if low_parts:
            st.warning("⚠️ 현재 가동 범위가 부족한 부위 위주로 편성된 **맞춤 프로그램**입니다.")
            display_parts = low_parts # 부족한 부위만 표시
        else:
            st.success("✨ 모든 수치가 정상입니다! 예방 차원의 **전신 관리 프로그램**을 추천합니다.")
            display_parts = list(guide_db.keys()) # 전체 부위 표시

        # 3. 카드 레이아웃 출력
        rows = [display_parts[i:i + 3] for i in range(0, len(display_parts), 3)]
        
        for row in rows:
            cols = st.columns(3)
            for idx, part in enumerate(row):
                info = guide_db[part]
                val = round(float(p_data.get(f'{part}_rom', 0)), 1)
                
                with cols[idx]:
                    if part in low_parts:
                        st.error(f"**{part.upper()} 집중관리**")
                        status_msg = f"현재: {val}° (기준 미달)"
                    else:
                        st.info(f"**{part.upper()} 유지관리**")
                        status_msg = f"현재: {val}° (정상)"
                        
                    st.markdown(f"📍 **{info['name']}**")
                    st.caption(f"{info['desc']}\n\n{status_msg}")
                    search_url = f"https://www.youtube.com/results?search_query={info['name']}+방법"
                    st.link_button("🎥 가이드 보기", search_url, use_container_width=True)

    # [2순위: PDF 발행] - 환자 선택 블록(if df) 안에 위치
    st.sidebar.divider()
    st.sidebar.subheader("📄 결과물 내보내기")
    radar_bytes = fig_r.to_image(format="png")
    final_pdf = create_pdf(sel_id, p_data['age'], pred, "Care Needed" if (isinstance(pred, float) and pred > 5) else "Good", radar_bytes)
    st.sidebar.download_button("📂 PDF 리포트 발행", data=bytes(final_pdf), file_name=f"MSK_Report_{sel_id}.pdf", use_container_width=True)

# --- 5. 사이드바 최하단 (업로드 섹션) ---
for _ in range(10): st.sidebar.write("") # 간격 조절
st.sidebar.divider()
st.sidebar.subheader("환자 데이터 업로드")
uploaded_file = st.sidebar.file_uploader("📂 파일 업로드", type=["xlsx"])
st.sidebar.download_button("📥 양식 다운로드", get_sample_excel(), "msk_template.xlsx", use_container_width=True)

if uploaded_file:
    st.sidebar.success("파일 감지됨! 파이프라인 설정을 확인하세요.")

if df is None:
    st.error("데이터베이스 파일이 없습니다. 파이프라인을 먼저 실행하세요.")