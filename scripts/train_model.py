import duckdb
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import os

def train_pain_predictor():
    conn = duckdb.connect('database/pipeline.db')
    df = conn.execute("SELECT * FROM gold_msk_analytics").df()
    conn.close()

    # 1. 특징(Feature)과 타겟(Target) 설정
    # 나이, 거북목 각도, 각 관절의 ROM을 기반으로 평균 통증(avg_pain)을 예측
    features = ['age', 'forward_head_angle', 'grip_strength'] + [col for col in df.columns if '_rom' in col]
    X = df[features]
    y = df['avg_pain']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 2. 모델 학습 (Random Forest)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 3. 모델 저장
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/pain_predictor.pkl')
    
    # 특징 목록도 함께 저장 (나중에 예측 시 순서 보장을 위해)
    joblib.dump(features, 'models/feature_names.pkl')
    
    print(f"✅ ML 모델 학습 완료 (Test Score: {model.score(X_test, y_test):.2f})")

if __name__ == "__main__":
    train_pain_predictor()