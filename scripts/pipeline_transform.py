import duckdb
import pandas as pd
import datetime

def check_quality(df):
    """품질 검사: 가동범위가 정상 범위를 초과하는지 확인"""
    if (df['shoulder_rom'] < 0).any() or (df['shoulder_rom'] > 200).any():
        return False, "⚠️ 품질 오류: 비정상적인 ROM 수치 발견"
    return True, "✅ 품질 검사 통과"

def transform_silver_to_gold():
    conn = duckdb.connect('database/pipeline.db')
    
    # 1. Raw 데이터 읽기
    raw_df = conn.execute("SELECT * FROM raw_msk_data").df()
    
    # 2. 품질 검사
    is_valid, msg = check_quality(raw_df)
    if not is_valid:
        conn.close()
        raise ValueError(msg)
    
    # 3. 분석 지표 계산 (종합 가동성 점수)
    standards = {'cervical': 45, 'shoulder': 150, 'trunk': 40, 'hip': 100, 'knee': 130, 'ankle': 20}
    joints = list(standards.keys())
    
    for j in joints:
        threshold = standards[j]
        raw_df[f'{j}_status'] = raw_df[f'{j}_rom'].apply(
            lambda x: 'Normal' if x >= threshold else ('Mild' if x >= threshold*0.7 else 'Severe')
        )
    
    # 가동성 점수 (Mobility Score)
    rom_cols = [f'{j}_rom' for j in joints]
    std_vals = [standards[j] for j in joints]
    raw_df['mobility_score'] = (raw_df[rom_cols] / std_vals).mean(axis=1) * 100
    raw_df['mobility_score'] = raw_df['mobility_score'].clip(upper=100).round(1)
    raw_df['avg_pain'] = raw_df[[f'{j}_vas' for j in joints]].mean(axis=1).round(1)

    # 4. Gold 테이블 저장
    conn.execute("CREATE OR REPLACE TABLE gold_msk_analytics AS SELECT * FROM raw_df")
    
    print(f"[{datetime.datetime.now()}] 🔄 2단계: 품질 검사 통과 및 Gold 테이블 갱신 완료")
    conn.close()

if __name__ == "__main__":
    transform_silver_to_gold()