import pandas as pd
import numpy as np
import os

def generate_msk_data(num_patients=100):
    np.random.seed(42)
    joints = ['cervical', 'shoulder', 'trunk', 'hip', 'knee', 'ankle']
    
    # 1. 기본 인적 사항 생성
    age = np.random.randint(20, 80, size=num_patients)
    gender = np.random.choice(['M', 'F'], size=num_patients)
    
    data = {
        'patient_id': range(1, num_patients + 1),
        'age': age,
        'gender': gender,
        'forward_head_angle': np.random.uniform(10, 45, size=num_patients),
        'pelvic_tilt': np.random.uniform(-10, 25, size=num_patients),
        'grip_strength': np.random.uniform(15, 55, size=num_patients),
        'recorded_at': pd.date_range(start='2026-01-01', periods=num_patients, freq='D')
    }

    # 2. 연령에 따른 가동범위 저하 모델 적용 (노화 시뮬레이션)
    for joint in joints:
        # 연령이 높을수록 기본 가동범위 기대값이 낮아짐 (Age Penalty)
        # 20대 평균 140도 -> 70대 평균 80도 식으로 시뮬레이션
        age_penalty = (age - 20) * 0.8 
        base_rom = np.random.randint(110, 160, size=num_patients) - age_penalty
        
        # 최소/최대 가동범위 제한 (현실적인 수치)
        rom = np.clip(base_rom, 30, 170).astype(int)
        data[f'{joint}_rom'] = rom
        
        # 통증 지수(VAS): 가동범위가 낮을수록, 연령이 높을수록 증가
        # 가동범위가 10도 줄어들 때마다 통증 1단계 상승 + 무작위성 추가
        vas = (170 - rom) // 15 + np.random.randint(0, 3, size=num_patients)
        data[f'{joint}_vas'] = np.clip(vas, 0, 10).astype(int)

    return pd.DataFrame(data)

if __name__ == "__main__":
    df = generate_msk_data(100)
    print("✅ 현실적인 근골격계 시뮬레이션 데이터 생성 완료")