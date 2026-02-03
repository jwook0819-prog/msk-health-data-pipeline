from scripts.pipeline_ingest import ingest_raw_data
from scripts.pipeline_transform import transform_silver_to_gold
from scripts.train_model import train_pain_predictor

def run_total_pipeline():
    try:
        ingest_raw_data()
        transform_silver_to_gold()
        train_pain_predictor()
        print("🚀 모든 파이프라인이 성공적으로 가동되었습니다!")
    except Exception as e:
        print(f"❌ 파이프라인 에러: {e}")

if __name__ == "__main__":
    run_total_pipeline()