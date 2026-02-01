import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="MSK Healthcare Analytics", layout="wide")

@st.cache_data
def load_data():
    try:
        conn = duckdb.connect('database/pipeline.db')
        df = conn.execute("SELECT * FROM gold_msk_analytics").df()
        conn.close()
        return df
    except:
        return None

df = load_data()

if df is None:
    st.error("❌ 데이터를 찾을 수 없습니다. main_pipeline.py를 먼저 실행해 주세요!")
    st.stop()

# --- 사이드바 ---
st.sidebar.title("🏥 설정")
st.sidebar.info("데이터 파이프라인을 통해 가공된 근골격계 분석 리포트입니다.")

# --- 메인 타이틀 ---
st.title("🦴 근골격계 통합 분석 대시보드 v1.0")
st.markdown("---")

tab1, tab2 = st.tabs(["📊 그룹 인사이트 분석", "🔍 환자 개별 리포트"])

# --- Tab 1: 그룹 인사이트 (내용 강화) ---
with tab1:
    # 1. 상단 핵심 지표 (KPI)
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("평균 가동성 점수", f"{df['mobility_score'].mean():.1f}")
    with kpi2:
        # 가장 상태가 안 좋은(Severe) 부위 찾기
        status_cols = [c for c in df.columns if 'status' in c]
        severe_counts = (df[status_cols] == 'Severe').sum().sort_values(ascending=False)
        worst_joint = severe_counts.index[0].replace('_status', '').upper()
        st.metric("가장 취약한 부위", worst_joint, delta="Severe 빈도 최고", delta_color="inverse")
    with kpi3:
        st.metric("평균 통증 지수(VAS)", f"{df['avg_pain'].mean():.1f}")
    with kpi4:
        st.metric("총 분석 인원", f"{len(df)}명")

    st.markdown("### 📈 데이터 트렌드 분석")
    col_a, col_b = st.columns(2)
    
    with col_a:
        # 연령대별 가동성 점수 (Box Plot)
        df['age_group'] = (df['age'] // 10 * 10).astype(str) + "대"
        fig_age = px.box(df, x="age_group", y="mobility_score", points="all",
                         title="연령대별 가동성 점수 분포", color="age_group")
        st.plotly_chart(fig_age, use_container_width=True)
        
    with col_b:
        # 부위별 위험군 비율 (Bar Chart)
        severe_rates = (df[status_cols] == 'Severe').mean() * 100
        severe_df = pd.DataFrame({'Joint': [s.replace('_status', '').capitalize() for s in severe_rates.index],
                                  'Severe Rate (%)': severe_rates.values})
        fig_bar = px.bar(severe_df, x='Joint', y='Severe Rate (%)', color='Severe Rate (%)',
                         color_continuous_scale='Reds', title="부위별 고위험군(Severe) 비율")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- Tab 2: 개별 리포트 (시각화 강화) ---
with tab2:
    pid = st.selectbox("조회할 환자 ID 선택", df['patient_id'].sort_values())
    p = df[df['patient_id'] == pid].iloc[0]
    
    st.markdown(f"### 👤 Patient ID: {pid} 상세 분석")
    
    c1, c2, c3 = st.columns([1, 1, 2])
    
    with c1:
        st.markdown("#### **기본 정보**")
        st.write(f"**연령:** {p['age']}세")
        st.write(f"**성별:** {p['gender']}")
        st.write(f"**수집일:** {p['ingested_at'].strftime('%Y-%m-%d %H:%M')}")
        
    with c2:
        st.markdown("#### **체형 분석**")
        st.write(f"**거북목 각도:** {p['forward_head_angle']:.1f}°")
        st.write(f"**골반 기울기:** {p['pelvic_tilt']:.1f}°")
        st.write(f"**악력:** {p['grip_strength']:.1f} kg")

    with c3:
        # 레이더 차트
        categories = ['Cervical', 'Shoulder', 'Trunk', 'Hip', 'Knee', 'Ankle']
        values = [p[f'{j.lower()}_rom'] for j in categories]
        fig_radar = go.Figure(go.Scatterpolar(r=values, theta=categories, fill='toself', name='현재 ROM'))
        fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 180])), 
                                title="관절 가동 범위(ROM) 균형", showlegend=False)
        st.plotly_chart(fig_radar, use_container_width=True)

    st.markdown("#### **🩺 부위별 정밀 진단 내역**")
    diag_cols = st.columns(6)
    for i, j in enumerate(['cervical', 'shoulder', 'trunk', 'hip', 'knee', 'ankle']):
        with diag_cols[i]:
            status = p[f'{j}_status']
            color = "red" if status == "Severe" else "orange" if status == "Mild" else "green"
            st.markdown(f"**{j.capitalize()}**")
            st.markdown(f":{color}[{status}]")
            st.caption(f"ROM: {p[f'{j}_rom']}°")