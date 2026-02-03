# 🏥 MSK Health Data Pipeline & AI Dashboard

> **근골격계(MSK) 건강 데이터를 수집, 정제하고 AI로 통증을 예측하는 엔드투엔드 데이터 파이프라인 프로젝트입니다.**
>
> 배포 주소: https://msk-health-data-pipeline.streamlit.app/



## ✨ 주요 기능 (Key Features)
- **자동화된 ETL 파이프라인:** 가상 환자 데이터 생성부터 DuckDB 적재까지 전 과정 자동화
- **데이터 품질 검증:** 의료 표준 기반의 관절 가동 범위(ROM) 데이터 무결성 체크
- **AI 통증 예측:** RandomForest 알고리즘을 활용한 신체 지표 기반 잠재적 통증(VAS) 예측
- **인터랙티브 대시보드:** Streamlit을 활용한 실시간 환자별 리포트 및 그룹 인사이트 제공

## 🛠 기술 스택 (Tech Stack)
- **Language:** Python
- **Database:** DuckDB (OLAP 최적화)
- **ML Framework:** Scikit-learn (RandomForest)
- **Visualization:** Streamlit, Plotly
- **DevOps:** GitHub, Streamlit Cloud (Deployment)

## 🏗 시스템 아키텍처
1. **Raw Layer:** `generate_data.py`를 통해 원천 데이터 생성 및 저장
2. **Gold Layer:** 데이터 정제 및 관절별 상태(Normal/Mild/Severe) 분류 로직 적용
3. **ML Layer:** 신체 지표 데이터를 학습하여 통증 지수 예측 모델 생성
4. **App Layer:** Streamlit을 통한 시각화 및 모델 서빙

## 🚀 실행 방법
```bash
# 1. 라이브러리 설치
pip install -r requirements.txt

# 2. 파이프라인 가동 및 모델 학습
python main_pipeline.py

# 3. 대시보드 실행
streamlit run app.py
