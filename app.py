import streamlit as st
import duckdb
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import joblib
import os
import subprocess
import streamlit as st
import os
import subprocess
import streamlit as st
import sys
from fpdf import FPDF

def create_pdf(patient_id, age, prediction, status):
    # 'latin-1' 에러를 방지하기 위해 유니코드 사용 설정
    pdf = FPDF()
    pdf.add_page()
    
    # 폰트 파일 경로 확인 (나눔고딕 파일이 app.py와 같은 위치에 있어야 함)
    font_path = "NanumGothic.ttf"
    
    if os.path.exists(font_path):
        try:
            # 폰트 등록 및 설정
            pdf.add_font('Nanum', '', font_path)
            pdf.set_font('Nanum', '', 16)
        except Exception as e:
            st.error(f"폰트 등록 오류: {e}")
            pdf.set_font('Arial', 'B', 16)
    else:
        st.error("⚠️ NanumGothic.ttf 파일을 찾을 수 없습니다. GitHub에 업로드했는지 확인하세요.")
        pdf.set_font('Arial', 'B', 16)

    # 텍스트 출력 시 유니코드 에러 방지
    pdf.cell(200, 10, txt="[근골격계 건강 분석 리포트]", ln=True, align='C')
    pdf.ln(10)
    
    # 폰트가 정상적으로 등록되었다면 한글 출력
    pdf.set_font('Nanum', '', 12)
    pdf.cell(200, 10, txt=f"환자 번호: {patient_id}", ln=True)
    pdf.cell(200, 10, txt=f"연령: {age}세", ln=True)
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"AI 예측 통증 지수 (VAS): {prediction}", ln=True)
    pdf.cell(200, 10, txt=f"종합 소견: {status}", ln=True)
    
    # latin-1 대신 유니코드 바이트로 반환
    return pdf.output()

# 서버 환경에서 실행 경로를 고정
current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, 'database', 'pipeline.db')

if not os.path.exists(db_path):
    st.info("🌐 서버 데이터가 감지되지 않아 파이프라인을 자동 가동합니다...")
    try:
        # 현재 실행 중인 파이프라인의 전체 경로 확보
        pipeline_script = os.path.join(current_dir, "main_pipeline.py")
        # 서버의 python 실행기를 사용하여 실행
        subprocess.run([sys.executable, pipeline_script], check=True)
        st.success("✅ 데이터 생성 완료! 페이지를 새로고침합니다.")
        st.rerun()
    except Exception as e:
        st.error(f"❌ 파이프라인 가동 실패: {e}")
        st.stop()

# 서버에 DB 파일이 없으면 자동으로 파이프라인 실행
if not os.path.exists('database/pipeline.db'):
    st.info("🌐 서버에 데이터가 없습니다. 파이프라인을 가동하여 데이터를 생성합니다...")
    # 파이프라인 실행 스크립트 호출
    subprocess.run(["python", "main_pipeline.py"])
    st.success("✅ 데이터 생성 및 모델 학습 완료!")

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

import io

# --- 샘플 양식 생성 함수 ---
def get_sample_excel():
    # 실제 학습에 사용되는 주요 컬럼들 정의
    sample_cols = [
        'patient_id', 'age', 'gender', 'height', 'weight',
        'forward_head_angle', 'grip_strength', 'pelvic_tilt',
        'cervical_rom', 'shoulder_rom', 'trunk_rom', 
        'hip_rom', 'knee_rom', 'ankle_rom', 'avg_pain'
    ]
    # 예시 데이터 1줄 생성
    sample_data = [[
        'SAMPLE_01', 45, 'M', 175.5, 72.0, 
        15.5, 38.2, 12.0, 
        45, 150, 60, 100, 130, 20, 3.5
    ]]
    sample_df = pd.DataFrame(sample_data, columns=sample_cols)
    
    # 메모리 상에서 엑셀 파일 생성
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        sample_df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

# --- 사이드바: 파일 업로드 섹션 ---
st.sidebar.divider()
st.sidebar.subheader("📂 환자 데이터 업로드")

# 1. 양식 다운로드 버튼 (미리 만들어둔 함수 호출)
st.sidebar.download_button(
    label="📥 샘플 엑셀 양식 다운로드",
    data=get_sample_excel(),
    file_name="msk_sample_form.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# 2. 파일 업로드 위젯
uploaded_file = st.sidebar.file_uploader("환자 엑셀 파일을 선택하세요", type=["xlsx", "csv"])

# 3. 파일 처리 로직 (이 부분이 핵심입니다)
if uploaded_file is not None:
    try:
        # 파일 확장자에 따라 데이터 읽기
        if uploaded_file.name.endswith('xlsx'):
            ext_df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            ext_df = pd.read_csv(uploaded_file)
            
        st.sidebar.success("✅ 파일 로드 성공!")

        # 데이터 소스 선택 (업로드 시에만 나타남)
        mode = st.sidebar.radio("분석 데이터 소스 선택", ["기본 DB", "업로드 파일"])
        
        if mode == "업로드 파일":
            df = ext_df  # 메인 데이터프레임을 업로드된 데이터로 교체
            st.sidebar.warning("⚠️ 현재 업로드된 데이터를 분석 중입니다.")
            
    except Exception as e:
        st.sidebar.error(f"❌ 파일 읽기 오류: {e}")
else:
    # 파일을 올리지 않았을 때는 기본적으로 DB 데이터를 사용하도록 설정
    # (이미 위쪽에서 df = conn.execute(...).df() 처리가 되어 있어야 함)
    pass

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
    st.subheader("📄 분석 리포트 내보내기")
    
    # 에러 방지용: age 값이 시리즈인 경우와 숫자인 경우 모두 대응
    raw_age = p_data['age']
    clean_age = raw_age.values[0] if hasattr(raw_age, 'values') else raw_age
    
    # PDF 생성 데이터 준비
    pdf_data = create_pdf(
        selected_id, 
        clean_age, # 안전하게 변환된 나이 값 전달
        predicted_vas, 
        "관리가 필요한 상태입니다." if predicted_vas > 4 else "양호한 상태입니다."
    )
    
    st.download_button(
        label="📥 PDF 리포트 다운로드",
        data=bytes(pdf_data),
        file_name=f"Report_{selected_id}.pdf",
        mime="application/pdf"
    )

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

@st.cache_resource  # 1. @는 맨 앞에 붙어야 함
def load_trained_model():
    # 2. 함수 안의 내용은 무조건 4칸(또는 Tab 1번) 들여쓰기
    model = joblib.load('models/pain_predictor.pkl')
    features = joblib.load('models/feature_names.pkl')
    return model, features