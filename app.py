import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import joblib

# 1. 페이지 설정
st.set_page_config(page_title="근골격계 분석 대시보드", layout="wide")

# 2. AI 예측 함수 정의 (상단 배치)
def predict_pain(patient_row):
    try:
        model = joblib.load('models/pain_predictor.pkl')
        features = joblib.load('models/feature_names.pkl')
        
        # 환자 데이터에서 필요한 특징만 추출
        input_data = pd.DataFrame([patient_row[features]])
        prediction = model.predict(input_data)[0]
        return round(prediction, 1)
    except:
        return None

# 3. 데이터 로드 함수
@st.cache_data
def load_data():
    try:
        conn = duckdb.connect('database/pipeline.db')
        df = conn.execute("SELECT * FROM gold_msk_analytics").df()
        conn.close()
        return df
    except Exception as e:
        return None

df = load_data()

# 데이터 로드 실패 시 중단
if df is None or df.empty:
    st.warning("⚠️ 'database/pipeline.db' 파일이나 테이블이 없습니다. 'python main_pipeline.py'를 먼저 실행해 주세요.")
    st.stop()

# 4. 사이드바: 환자 선택
st.sidebar.title("👤 환자 관리 시스템")
patient_list = df['patient_id'].tolist()
selected_id = st.sidebar.selectbox("환자 ID를 선택하세요", patient_list)
p_data = df[df['patient_id'] == selected_id].iloc[0]

# 5. 메인 화면 헤더
st.title("🦴 근골격계 데이터 분석 리포트")
st.markdown(f"**데이터 업데이트 시간:** `{p_data['ingested_at']}`")
st.divider()

# 6. 탭 구성 (중요: 여기서 tab1, tab2 변수가 생성됨)
tab1, tab2 = st.tabs(["📊 그룹 인사이트 분석", "🔍 개별 정밀 리포트"])

# --- Tab 1: 그룹 인사이트 ---
with tab1:
    st.subheader("📈 전체 데이터 인사이트")
    col1, col2, col3 = st.columns(3)
    col1.metric("평균 가동성 점수", f"{df['mobility_score'].mean():.1f} / 100")
    col2.metric("평균 통증 지수(VAS)", f"{df['avg_pain'].mean():.1f} / 10")
    col3.metric("총 분석 환자 수", f"{len(df)} 명")

    st.markdown("---")
    c_left, c_right = st.columns(2)
    
    with c_left:
        df['age_group'] = (df['age'] // 10 * 10).astype(str) + "대"
        fig_box = px.box(df, x="age_group", y="mobility_score", points="all", 
                         title="연령대별 종합 가동성 분포", color="age_group")
        st.plotly_chart(fig_box, use_container_width=True)

    with c_right:
        try:
            fig_scatter = px.scatter(df, x="mobility_score", y="avg_pain", trendline="ols",
                                     title="가동성 점수와 통증의 상관관계 (Trendline)")
            st.plotly_chart(fig_scatter, use_container_width=True)
        except:
            st.info("추세선을 보려면 'pip install statsmodels'가 필요합니다.")

# --- Tab 2: 개별 정밀 리포트 ---
with tab2:
    # 1. 환자 기본 헤더
    st.subheader(f"🔍 ID {selected_id} 환자 정밀 분석 리포트")

    # 2. 🤖 AI 예측 섹션 (최상단 배치)
    # p_data는 위에서 이미 선택된 환자의 데이터입니다.
    predicted_vas = predict_pain(p_data)
    
    if predicted_vas is not None:
        actual_vas = p_data['avg_pain']
        diff = round(predicted_vas - actual_vas, 1)

        # 강조 박스 시작
        st.info("### 🤖 AI 통합 진단 결과")
        
        c_pred1, c_pred2, c_pred3 = st.columns(3)
        c_pred1.metric("AI 예측 통증 지수", f"{predicted_vas} / 10", delta=f"{diff} (예측치 차이)")
        c_pred2.metric("실제 기록 통증 (VAS)", f"{actual_vas} / 10")
        c_pred3.metric("분석 모델", "RandomForest v1")

        # 예측 결과에 따른 자동 코멘트
        if diff > 1.2:
            st.error(f"⚠️ **잠재적 위험군**: 현재 느끼는 통증({actual_vas})보다 신체 지표 기반 예측치({predicted_vas})가 높습니다. 근육 피로도가 누적된 상태이므로 휴식을 권장합니다.")
        elif diff < -1.2:
            st.success(f"✅ **회복 우수군**: 신체 지표에 비해 통증을 적게 느끼고 있습니다. 현재의 재활 운동 강도가 적절합니다.")
        else:
            st.warning(f"🔔 **관리 필요**: AI 예측치가 실제 통증 수치와 일치합니다. 현재의 신체 불균형 상태가 통증에 직접적인 영향을 주고 있습니다.")
    else:
        # 모델 파일이 없거나 에러가 났을 때 메시지
        st.error("❌ AI 모델을 로드할 수 없습니다. 'python main_pipeline.py'를 실행하여 모델을 먼저 학습시켜 주세요.")

    st.divider()

    # 3. 기본 신체 지표 (기존 내용)
    col_metrics = st.columns(3)
    col_metrics[0].metric("종합 가동성 점수", f"{p_data['mobility_score']} 점")
    col_metrics[1].metric("거북목 각도", f"{p_data['forward_head_angle']:.1f} °")
    col_metrics[2].metric("악력(전신근력)", f"{p_data['grip_strength']:.1f} kg")

    st.markdown("---")
    
    # 4. 관절 상태 및 레이더 차트
    l_col, r_col = st.columns([1, 1.2])
    
    with l_col:
        st.markdown("#### **📍 부위별 가동 범위(ROM)**")
        joints = ['cervical', 'shoulder', 'trunk', 'hip', 'knee', 'ankle']
        for j in joints:
            status = p_data[f'{j}_status']
            color = "red" if status == "Severe" else "orange" if status == "Mild" else "green"
            st.write(f"**{j.capitalize()}**: :{color}[{status}] (ROM: {p_data[f'{j}_rom']}°)")

    with r_col:
        categories = [j.capitalize() for j in joints]
        values = [p_data[f'{j}_rom'] for j in joints]
        fig_radar = go.Figure(go.Scatterpolar(r=values, theta=categories, fill='toself'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 180])),
                                title="신체 밸런스 맵", showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)