import os, datetime
import pandas as pd
import numpy as np
import duckdb
from scripts.generate_data import generate_msk_data

def ingest_raw_data():
    base_df = generate_msk_data(100)
    all_visits = []
    start_date = datetime.datetime(2025, 1, 1)
    
    for _, row in base_df.iterrows():
        for visit in range(3): # 환자당 3회 방문 생성
            new_row = row.copy()
            new_row['ingested_at'] = start_date + datetime.timedelta(days=visit * 14)
            # 방문할수록 상태 호전되는 트렌드
            noise = np.random.normal(0, 1)
            new_row['avg_pain'] = max(0, row['avg_pain'] - (visit * 1.5) + noise)
            new_row['mobility_score'] = min(100, row['mobility_score'] + (visit * 8) + noise)
            for col in [c for c in new_row.index if '_rom' in c]:
                new_row[col] = min(180, new_row[col] + (visit * 5) + noise)
            all_visits.append(new_row)
            
    time_series_df = pd.DataFrame(all_visits)
    os.makedirs('database', exist_ok=True)
    conn = duckdb.connect('database/pipeline.db')
    conn.execute("CREATE OR REPLACE TABLE raw_msk_data AS SELECT * FROM time_series_df")
    conn.close()
    print("✅ 1단계: 시계열 Raw 데이터 적재 완료")