"""
main.py — Dual-Channel Fraud Detection API
==========================================
Two independent fraud signals blended into a final score:
  - Channel A: XGBoost on structured form data (scaled, as trained)
  - Channel B: NLP fraud scorer on free-text claim narrative
  - Final: 50% A + 50% B  (equal weight to both channels)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../features'))

import joblib
import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from nlp_fraud_scorer import compute_nlp_fraud_score, get_nlp_breakdown

# ─────────────────────────────────────────────
# Load model artifacts
# ─────────────────────────────────────────────
model     = joblib.load("models/xgboost/xgb_model.pkl")
scaler    = joblib.load("models/xgboost/scaler.pkl")
threshold = joblib.load("models/xgboost/threshold.pkl")

# Load feature column order from training
_feature_df   = pd.read_csv("data/processed/final_ml_dataset.csv")
FEATURE_COLS  = _feature_df.drop(columns=['fraud_label']).columns.tolist()

# ─────────────────────────────────────────────
# App
# ─────────────────────────────────────────────
app = FastAPI(title="Dual-Channel Insurance Fraud Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Input schema
# ─────────────────────────────────────────────
class ClaimInput(BaseModel):
    # Structured form fields
    age: int
    months_as_customer: int
    policy_annual_premium: float
    umbrella_limit: float
    incident_hour_of_the_day: int
    number_of_vehicles_involved: int
    bodily_injuries: int
    witnesses: int
    total_claim_amount: float
    injury_claim: float
    property_claim: float
    vehicle_claim: float
    # Categorical (optional, default to unknown)
    incident_type: str = "Single Vehicle Collision"
    incident_severity: str = "Minor Damage"
    policy_state: str = "NY"
    insured_sex: str = "MALE"
    collision_type: str = "Front Collision"
    # Unstructured text
    claim_text: str


# ─────────────────────────────────────────────
# Feature engineering (mirrors training pipeline)
# ─────────────────────────────────────────────
CATEGORICAL_MAP = {
    'incident_type': {
        'Single Vehicle Collision': 0, 'Multi-vehicle Collision': 1,
        'Parked Car': 2, 'Vehicle Theft': 3,
    },
    'incident_severity': {
        'Minor Damage': 0, 'Major Damage': 1,
        'Total Loss': 2, 'Trivial Damage': 3,
    },
    'policy_state': {'IL': 0, 'IN': 1, 'OH': 2, 'NY': 3, 'PA': 4},
    'insured_sex': {'MALE': 0, 'FEMALE': 1},
    'collision_type': {
        'Front Collision': 0, 'Rear Collision': 1,
        'Side Collision': 2, '?': 3,
    },
}


def _encode_cat(col: str, val: str) -> int:
    mapping = CATEGORICAL_MAP.get(col, {})
    return mapping.get(val, 0)


def create_structured_features(data: ClaimInput) -> pd.DataFrame:
    d = data.dict()

    # Ratios
    d['claim_ratio']           = d['total_claim_amount'] / (d['policy_annual_premium'] + 1)
    d['avg_claim_per_vehicle'] = d['total_claim_amount'] / (d['number_of_vehicles_involved'] + 1)
    d['injury_ratio']          = d['injury_claim'] / (d['total_claim_amount'] + 1)
    d['property_ratio']        = d['property_claim'] / (d['total_claim_amount'] + 1)
    d['vehicle_ratio']         = d['vehicle_claim'] / (d['total_claim_amount'] + 1)

    # Flags
    d['high_claim_flag']        = int(d['claim_ratio'] > 5)
    d['no_witness_high_claim']  = int(d['witnesses'] == 0 and d['claim_ratio'] > 3)

    # Encode categoricals
    for col in ['incident_type', 'incident_severity', 'policy_state', 'insured_sex', 'collision_type']:
        d[col] = _encode_cat(col, d[col])

    # NLP score — placeholder (will be set after text analysis)
    d['nlp_fraud_score'] = 0.0

    # Remove raw text
    d.pop('claim_text', None)

    # Build DataFrame with correct column order
    df = pd.DataFrame([d])

    # Align to training columns
    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0
    df = df[FEATURE_COLS]

    return df


# ─────────────────────────────────────────────
# SHAP risk factors
# ─────────────────────────────────────────────
def get_risk_factors(df_scaled: pd.DataFrame) -> list:
    try:
        import shap
        explainer   = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(df_scaled)
        values      = shap_values[0]
        impact      = sorted(zip(FEATURE_COLS, values), key=lambda x: abs(x[1]), reverse=True)
        return [{"feature": str(f), "impact": round(float(v), 4)} for f, v in impact[:6]]
    except Exception as e:
        print("SHAP warning:", e)
        return []


# ─────────────────────────────────────────────
# Main endpoint
# ─────────────────────────────────────────────
@app.post("/analyze-claim")
def analyze_claim(input_data: ClaimInput):
    try:
        # ── Channel B: NLP Analysis ──────────────────
        nlp_score    = compute_nlp_fraud_score(input_data.claim_text)
        nlp_breakdown = get_nlp_breakdown(input_data.claim_text)

        # ── Channel A: Structured XGBoost ────────────
        df = create_structured_features(input_data)

        # Inject NLP score into the structured feature row
        if 'nlp_fraud_score' in df.columns:
            df['nlp_fraud_score'] = nlp_score

        df_scaled   = scaler.transform(df)
        df_scaled   = pd.DataFrame(df_scaled, columns=FEATURE_COLS)

        struct_prob = float(model.predict_proba(df_scaled)[0][1])

        # ── Blend: equal weight both channels ────────
        final_prob   = 0.50 * struct_prob + 0.50 * nlp_score
        final_score  = round(final_prob * 100, 2)
        struct_score = round(struct_prob * 100, 2)
        nlp_score_pct = round(nlp_score * 100, 2)

        # ── Risk label ───────────────────────────────
        if final_score < 30:
            risk_level = "LOW"
        elif final_score < 60:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # ── SHAP risk factors ────────────────────────
        risk_factors = get_risk_factors(df_scaled)

        return {
            # Combined
            "final_score":         final_score,
            "fraud_probability":   round(final_prob, 4),
            "risk_level":          risk_level,

            # Channel A
            "structured_score":    struct_score,
            "structured_prob":     round(struct_prob, 4),

            # Channel B
            "nlp_score":           nlp_score_pct,
            "nlp_breakdown":       nlp_breakdown,

            # Explainability
            "risk_factors":        risk_factors,
        }

    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
def health():
    return {"status": "ok", "model": "XGBoost + NLP Dual-Channel"}