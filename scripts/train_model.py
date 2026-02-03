import pandas as pd
import duckdb, joblib, os
from sklearn.ensemble import RandomForestRegressor

def train_pain_predictor():
    conn = duckdb.connect('database/pipeline.db')
    df = conn.execute("SELECT * FROM gold_msk_analytics").df()
    conn.close()

    features = ['age', 'forward_head_angle', 'grip_strength', 'cervical_rom', 'shoulder_rom', 'trunk_rom', 'hip_rom', 'knee_rom', 'ankle_rom']
    X = df[features]
    y = df['avg_pain']

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)

    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/pain_predictor.pkl')
    joblib.dump(features, 'models/feature_names.pkl')
    print("✅ 3단계: AI 모델 학습 완료")