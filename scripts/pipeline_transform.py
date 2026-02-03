import duckdb
import pandas as pd
import datetime

def check_quality(df):
    """품질 검사: 가동범위가 물리적 한계(0~200도)를 벗어나는지 확인"""
    if (df.filter(like='_rom') < 0).any().any() or (df.filter(like='_rom') > 200).any().any():
        return False, "⚠️ 품질 오류: 비정상적인 ROM 수치가 발견되었습니다."
    return True, "✅ 품질 검사 통과"

def transform_silver_to_gold():
    # 1. DB 연결 및 데이터 로드 (이 부분이 빠지면 NameError 발생)
    conn = duckdb.connect('database/pipeline.db')
    
    # Raw 데이터를 가져와 raw_df 변수에 할당
    raw_df = conn.execute("SELECT * FROM raw_msk_data").df()
    
    # 2. 품질 검증
    is_valid, msg = check_quality(raw_df)
    if not is_valid:
        conn.close()
        raise ValueError(msg)

    # 3. 다채로운 분석을 위한 의료 표준 가동 범위 설정
    standards = {
        'cervical': 45, 'shoulder': 160, 'trunk': 45, 
        'hip': 120, 'knee': 140, 'ankle': 25
    }
    joints = list(standards.keys())
    
    # 4. 분석 지표 계산 (가동성 점수 및 상태 분류)
    weighted_scores = []
    for j in joints:
        # 가동 비율 계산 (표준 대비 현재 가동 범위)
        ratio = (raw_df[f'{j}_rom'] / standards[j]).clip(upper=1.0)
        weighted_scores.append(ratio)
        
        # 등급 분류 (Normal, Mild, Severe)
        raw_df[f'{j}_status'] = ratio.apply(
            lambda x: 'Normal' if x >= 0.9 else ('Mild' if x >= 0.7 else 'Severe')
        )
    
    # 종합 가동성 점수 (0~100) 및 평균 통증(VAS)
    raw_df['mobility_score'] = (sum(weighted_scores) / len(joints) * 100).round(1)
    raw_df['avg_pain'] = raw_df[[f'{j}_vas' for j in joints]].mean(axis=1).round(1)

    # 5. 최종 분석 데이터(Gold Layer) 저장
    conn.execute("CREATE OR REPLACE TABLE gold_msk_analytics AS SELECT * FROM raw_df")
    
    print(f"[{datetime.datetime.now()}] 🔄 2단계: 분석 지표 변환 및 Gold 테이블 업데이트 완료")
    conn.close()

if __name__ == "__main__":
    transform_silver_to_gold()