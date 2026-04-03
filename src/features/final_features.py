"""
final_features.py
=================
Prepares the final ML-ready dataset for XGBoost training.

Feature set:
  - Structured numerical/engineered features (15)
  - Encoded categorical features (5)
  - NLP fraud score (1 distilled text signal)
  = ~21 clean, discriminative features

No raw embeddings — they add noise, not signal.
"""

import pandas as pd
from sklearn.preprocessing import LabelEncoder


def prepare_features():
    print("📊 Preparing final dual-channel ML dataset...")

    df = pd.read_csv("data/processed/features_dataset.csv")

    # ─────────────────────────────────────────
    # 1. Numerical Feature Engineering
    # ─────────────────────────────────────────
    df['claim_ratio']          = df['total_claim_amount'] / (df['policy_annual_premium'] + 1)
    df['avg_claim_per_vehicle'] = df['total_claim_amount'] / (df['number_of_vehicles_involved'] + 1)
    df['injury_ratio']         = df['injury_claim'] / (df['total_claim_amount'] + 1)
    df['property_ratio']       = df['property_claim'] / (df['total_claim_amount'] + 1)
    df['vehicle_ratio']        = df['vehicle_claim'] / (df['total_claim_amount'] + 1)

    # High-amount flag: claim is more than 5× the annual premium
    df['high_claim_flag'] = (df['claim_ratio'] > 5).astype(int)

    # Suspicion flag: high claim + no witnesses
    if 'witnesses' in df.columns:
        df['no_witness_high_claim'] = (
            (df['witnesses'] == 0) & (df['claim_ratio'] > 3)
        ).astype(int)

    # ─────────────────────────────────────────
    # 2. Encode Categorical Columns
    # ─────────────────────────────────────────
    categorical_cols = [
        'policy_state',
        'insured_sex',
        'incident_type',
        'collision_type',
        'incident_severity',
    ]

    le = LabelEncoder()
    for col in categorical_cols:
        if col in df.columns:
            df[col] = le.fit_transform(df[col].astype(str))

    # ─────────────────────────────────────────
    # 3. Final Feature Selection
    # ─────────────────────────────────────────
    structured_features = [
        # Demographics
        'age', 'months_as_customer',
        # Policy
        'policy_annual_premium', 'umbrella_limit',
        # Incident context
        'incident_hour_of_the_day', 'number_of_vehicles_involved',
        'bodily_injuries', 'witnesses',
        # Claim amounts
        'total_claim_amount', 'injury_claim', 'property_claim', 'vehicle_claim',
        # Engineered ratios
        'claim_ratio', 'avg_claim_per_vehicle', 'injury_ratio',
        'property_ratio', 'vehicle_ratio',
        # Flags
        'high_claim_flag', 'no_witness_high_claim',
        # Categorical (encoded)
        'incident_type', 'incident_severity',
    ]

    # Add optional columns if they exist
    optional = ['policy_state', 'insured_sex', 'collision_type']
    for col in optional:
        if col in df.columns:
            structured_features.append(col)

    # NLP signal
    nlp_features = ['nlp_fraud_score']

    final_features = structured_features + nlp_features + ['fraud_label']

    # Keep only columns that exist
    final_features = [col for col in final_features if col in df.columns]

    df_final = df[final_features]

    df_final.to_csv("data/processed/final_ml_dataset.csv", index=False)

    fraud_rate  = df_final['fraud_label'].mean()
    print(f"✅ Final ML dataset ready!")
    print(f"   Features: {len(final_features) - 1} | Rows: {len(df_final)} | Fraud rate: {fraud_rate:.1%}")
    print("   Saved → data/processed/final_ml_dataset.csv")


if __name__ == "__main__":
    prepare_features()