import pandas as pd
import numpy as np
import os
import duckdb

def generate_msk_data(num_patients=100):
    np.random.seed(42)
    joints = ['cervical', 'shoulder', 'trunk', 'hip', 'knee', 'ankle']
    
    data = {
        'patient_id': range(1, num_patients + 1),
        'age': np.random.randint(20, 75, size=num_patients),
        'gender': np.random.choice(['M', 'F'], size=num_patients),
        'forward_head_angle': np.random.uniform(10, 45, size=num_patients),
        'pelvic_tilt': np.random.uniform(-10, 25, size=num_patients),
        'grip_strength': np.random.uniform(15, 55, size=num_patients),
        'recorded_at': pd.date_range(start='2026-01-01', periods=num_patients, freq='D')
    }

    for joint in joints:
        rom = np.random.randint(30, 160, size=num_patients)
        data[f'{joint}_rom'] = rom
        # 가동범위와 통증의 상관관계 시뮬레이션
        data[f'{joint}_vas'] = (160 - rom) // 16 + np.random.randint(0, 3, size=num_patients)
        data[f'{joint}_vas'] = np.clip(data[f'{joint}_vas'], 0, 10)

    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    os.makedirs('database', exist_ok=True)
    df = generate_msk_data(100)
    print(f"✅ {len(df)}명의 샘플 데이터 생성 완료!")