import pandas as pd
import numpy as np

def generate_msk_data(n=100):
    np.random.seed(42)
    data = {
        'patient_id': [f"P_{i:03d}" for i in range(n)],
        'age': np.random.randint(20, 80, n),
        'gender': np.random.choice(['M', 'F'], n),
        'height': np.random.normal(170, 10, n),
        'weight': np.random.normal(70, 15, n),
        'forward_head_angle': np.random.normal(15, 5, n),
        'grip_strength': np.random.normal(35, 10, n),
        'avg_pain': np.random.uniform(2, 8, n),
        'mobility_score': np.random.uniform(50, 80, n),
        'cervical_rom': np.random.normal(40, 10, n),
        'shoulder_rom': np.random.normal(140, 20, n),
        'trunk_rom': np.random.normal(50, 15, n),
        'hip_rom': np.random.normal(90, 20, n),
        'knee_rom': np.random.normal(120, 15, n),
        'ankle_rom': np.random.normal(15, 5, n)
    }
    return pd.DataFrame(data)