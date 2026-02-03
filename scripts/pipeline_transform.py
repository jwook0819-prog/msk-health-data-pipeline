import duckdb

def transform_silver_to_gold():
    conn = duckdb.connect('database/pipeline.db')
    query = """
    CREATE OR REPLACE TABLE gold_msk_analytics AS
    SELECT *,
        -- 통증 점수별 상태
        CASE WHEN avg_pain >= 7 THEN 'Severe' WHEN avg_pain >= 4 THEN 'Moderate' ELSE 'Normal' END as pain_status,
        -- 가동성 점수별 등급
        CASE WHEN mobility_score >= 80 THEN 'Good' WHEN mobility_score >= 60 THEN 'Fair' ELSE 'Poor' END as mobility_grade,
        -- [중요] 각 부위별 ROM 상태 판정 (대시보드 텍스트 출력용)
        CASE WHEN cervical_rom < 35 THEN 'Severe' ELSE 'Normal' END as cervical_status,
        CASE WHEN shoulder_rom < 130 THEN 'Severe' ELSE 'Normal' END as shoulder_status,
        CASE WHEN trunk_rom < 45 THEN 'Severe' ELSE 'Normal' END as trunk_status,
        CASE WHEN hip_rom < 85 THEN 'Severe' ELSE 'Normal' END as hip_status,
        CASE WHEN knee_rom < 115 THEN 'Severe' ELSE 'Normal' END as knee_status,
        CASE WHEN ankle_rom < 12 THEN 'Severe' ELSE 'Normal' END as ankle_status
    FROM raw_msk_data
    """
    conn.execute(query)
    conn.close()
    print("✅ 2단계: 상세 상태 판정 완료")