# 🏥 MSK Health Data Pipeline & AI Dashboard

> **근골격계(MSK) 건강 데이터를 수집, 정제하고 AI로 통증을 예측하는 엔드투엔드 데이터 파이프라인 프로젝트입니다.**
>
> 배포 주소: https://msk-health-data-pipeline.streamlit.app/



MSK AI Analytics Dashboard
근골격계 검사 데이터 기반 AI 분석 및 맞춤형 재활 처방 시스템

<img width="1913" height="928" alt="image" src="https://github.com/user-attachments/assets/e1237c26-5d77-40e7-b86e-e550f0b020d6" />
<img width="1914" height="930" alt="image" src="https://github.com/user-attachments/assets/e36f9e57-2eee-4c78-a99c-761099ab3953" />
<img width="1585" height="366" alt="image" src="https://github.com/user-attachments/assets/2f4d9fa7-cef6-41df-af1f-54a55b4566b1" />
<img width="1599" height="544" alt="image" src="https://github.com/user-attachments/assets/d43df69f-cdad-41c1-b164-e5a8539d7336" />



🌟 프로젝트 개요
본 프로젝트는 환자의 6대 관절(경추, 어깨, 몸통, 고관절, 무릎, 발목) 가동 범위(ROM) 데이터를 수집하여 AI 기반의 통증 예측과 부위별 정밀 분석을 제공하는 헬스케어 대시보드입니다. 단순한 수치 나열이 아닌, 정상치 대비 달성도를 시각화하고 그에 따른 맞춤형 운동 가이드를 자동으로 생성합니다.

🛠 주요 기능 (Key Features)
1. AI 통증 예측 및 진단
머신러닝 기반 예측: 수집된 ROM 데이터를 바탕으로 환자의 예상 통증 지수(VAS)를 예측합니다.

상태 자동 분류: 각 관절의 가동 범위를 분석하여 Normal, Impaired, Severe 단계로 자동 판독합니다.

2. 정밀 시각화 리포트
비율 기반 레이더 차트: 관절마다 다른 가동 범위를 정상치 대비 비율(%)로 환산하여 신체 균형을 한눈에 파악합니다.

시계열 회복 로드맵: 과거 데이터를 바 차트와 라인 차트로 결합하여 환자의 회복 추이를 추적합니다.

3. AI 맞춤형 운동 처방
지능형 추천 시스템: 가동성이 정상치의 70% 미만으로 떨어진 부위를 자동으로 감지하여 '집중관리' 운동을 처방합니다.

콘텐츠 연동: 각 처방에는 해당 부위의 재활 운동 유튜브 가이드 링크가 포함되어 환자의 실천을 돕습니다.

4. 데이터 파이프라인 자동화
GitHub Actions: 매일 오전 10시(KST) 신규 데이터를 분석하고 모델을 업데이트하는 자동화 파이프라인을 운영합니다.

PDF 리포트 발행: 분석 결과와 레이더 차트가 포함된 전문적인 PDF 리포트를 원클릭으로 생성합니다.

💻 기술 스택 (Tech Stack)
Language: Python 3.10+

Framework: Streamlit (Dashboard UI)

Data: DuckDB (OLAP Database), Pandas

AI/ML: Scikit-learn, Joblib

Visualization: Plotly (Radar, Scatter, Bar charts)

Automation: GitHub Actions (CI/CD Pipeline)

Reporting: FPDF (Automated PDF generation)

📂 프로젝트 구조
Plaintext

project/
├── .github/workflows/   # GitHub Actions 자동화 설정
├── database/            # DuckDB 파이프라인 DB
├── models/              # 학습된 AI 모델 및 피처 이름
├── app.py               # Streamlit 메인 애플리케이션
├── main_pipeline.py     # 데이터 전처리 및 분석 스크립트
└── requirements.txt     # 의존성 패키지 목록
🚀 시작하기
Bash

# 저장소 복제
git clone https://github.com/jwook0819-prog/msk-health-data-pipeline.git

# 가상환경 구축 및 패키지 설치
pip install -r requirements.txt

# 대시보드 실행
streamlit run app.py
