import os      # <--- 이 줄이 반드시 있어야 합니다!
import sys
import datetime
import pandas as pd
import numpy as np
import duckdb

# [수정 포인트] 현재 파일의 부모 폴더(프로젝트 루트)를 경로에 강제로 추가
current_file_path = os.path.abspath(__file__) # 현재 파일의 절대 경로
project_root = os.path.dirname(os.path.dirname(current_file_path)) # scripts의 상위 폴더

if project_root not in sys.path:
    sys.path.append(project_root)

# 이제 'scripts'를 인식할 수 있게 됩니다.
try:
    from scripts.generate_data import generate_msk_data
except ImportError:
    # 만약 scripts 폴더 내부에서 직접 실행할 경우를 대비
    from generate_data import generate_msk_data

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