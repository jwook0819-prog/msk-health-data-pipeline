import time
import logging
import datetime
from scripts.pipeline_ingest import ingest_raw_data
from scripts.pipeline_transform import transform_silver_to_gold
from scripts.train_model import train_pain_predictor

def run_total_pipeline():
    # ... 이전 단계 생략 ...
    try:
        ingest_raw_data()
        transform_silver_to_gold()
        
        # Step 3: ML 모델 학습 추가
        train_pain_predictor()
        
        print("✨ ML 포함 모든 파이프라인 성공!")
    except Exception as e:
        print(f"❌ 에러: {e}")

# 로깅 설정
logging.basicConfig(
    filename='pipeline.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)

def run_total_pipeline():
    start_time = time.time()
    logging.info("🚀 파이프라인 가동 시작")
    print("🚀 전체 데이터 파이프라인을 시작합니다...")

    try:
        # Step 1: Ingestion
        ingest_raw_data()
        
        # Step 2: Transformation
        transform_silver_to_gold()

        duration = round(time.time() - start_time, 2)
        logging.info(f"✨ 파이프라인 완료 (소요시간: {duration}s)")
        print(f"✨ 모든 작업이 성공적으로 완료되었습니다! ({duration}초)")

    except Exception as e:
        logging.error(f"❌ 에러 발생: {str(e)}")
        print(f"❌ 에러 발생: {str(e)}\n상세 내용은 pipeline.log를 확인하세요.")

if __name__ == "__main__":
    run_total_pipeline()