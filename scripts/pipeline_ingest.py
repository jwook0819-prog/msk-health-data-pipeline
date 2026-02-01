import os
import sys
import datetime
import pandas as pd
import duckdb

# 경로 설정: scripts 폴더 내의 파일을 찾을 수 있도록 함
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    from generate_data import generate_msk_data
except ImportError:
    from scripts.generate_data import generate_msk_data

def ingest_raw_data():
    # 1. 데이터 수집
    df = generate_msk_data(100)
    
    # 2. 메타데이터 추가
    df['ingested_at'] = datetime.datetime.now()
    
    # 3. Raw 레이어 저장
    os.makedirs('database', exist_ok=True)
    conn = duckdb.connect('database/pipeline.db')
    
    # [수정된 부분] 
    # 기존 테이블이 있으면 지우고 새로 만들거나, 최신 데이터로 덮어씁니다.
    # 이렇게 하면 UNIQUE 제약 조건 에러 없이 항상 최신 100건이 유지됩니다.
    conn.execute("CREATE OR REPLACE TABLE raw_msk_data AS SELECT * FROM df")
    
    print(f"[{datetime.datetime.now()}] 📥 1단계: Raw 데이터 수집 및 적재 완료")
    conn.close()

if __name__ == "__main__":
    ingest_raw_data()