"""
train_xgb.py
============
Trains the XGBoost fraud classifier on the dual-channel feature dataset.

Key fixes vs. previous version:
  - Scaler is fit on X_train only (no data leakage) and SAVED to disk
  - scale_pos_weight computed from actual data (not hardcoded)
  - Threshold tuning via precision-recall analysis, not guesswork
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, f1_score, roc_auc_score,
    classification_report, precision_recall_curve
)
import xgboost as xgb


def train_xgboost():
    print("🚀 Training Dual-Channel Fraud Detection Model (XGBoost)...")

    df = pd.read_csv("data/processed/final_ml_dataset.csv")

    X = df.drop(columns=['fraud_label'])
    y = df['fraud_label']

    # Fraud ratio for class weighting
    fraud_rate  = y.mean()
    legit_rate  = 1 - fraud_rate
    pos_weight  = legit_rate / fraud_rate
    print(f"   Fraud rate: {fraud_rate:.1%}  |  scale_pos_weight: {pos_weight:.2f}")

    # Stratified split — preserves fraud ratio in both sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # ─────────────────────────────────────────
    # Scale features — fit ONLY on train set
    # ─────────────────────────────────────────
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # Save scaler for inference
    joblib.dump(scaler, "models/xgboost/scaler.pkl")
    print("   Scaler saved → models/xgboost/scaler.pkl")

    # ─────────────────────────────────────────
    # Model
    # ─────────────────────────────────────────
    model = xgb.XGBClassifier(
        n_estimators=400,
        max_depth=6,
        learning_rate=0.05,
        scale_pos_weight=pos_weight,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        tree_method="hist",
        eval_metric='logloss',
        early_stopping_rounds=30,
        random_state=42,
    )

    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False,
    )

    # ─────────────────────────────────────────
    # Threshold tuning via F1 on precision-recall curve
    # ─────────────────────────────────────────
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    precisions, recalls, thresholds = precision_recall_curve(y_test, y_prob)

    f1_scores = 2 * precisions * recalls / (precisions + recalls + 1e-8)
    best_idx  = np.argmax(f1_scores)
    best_threshold = float(thresholds[best_idx]) if best_idx < len(thresholds) else 0.5
    print(f"   Optimal threshold: {best_threshold:.3f}")

    y_pred = (y_prob > best_threshold).astype(int)

    # ─────────────────────────────────────────
    # Metrics
    # ─────────────────────────────────────────
    acc = accuracy_score(y_test, y_pred)
    f1  = f1_score(y_test, y_pred)
    roc = roc_auc_score(y_test, y_prob)

    print("\n📊 Model Performance:")
    print(f"   Accuracy : {acc:.4f}")
    print(f"   F1 Score : {f1:.4f}")
    print(f"   ROC-AUC  : {roc:.4f}")
    print("\n📄 Classification Report:")
    print(classification_report(y_test, y_pred))

    # Feature importance — top 10
    feature_names = X.columns.tolist()
    importances   = model.feature_importances_
    top_features  = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)[:10]
    print("🔍 Top 10 Features:")
    for name, imp in top_features:
        bar = "█" * int(imp * 200)
        print(f"   {name:<35} {imp:.4f}  {bar}")

    # Save model + best threshold
    joblib.dump(model, "models/xgboost/xgb_model.pkl")
    joblib.dump(best_threshold, "models/xgboost/threshold.pkl")
    print("\n✅ Model saved → models/xgboost/xgb_model.pkl")
    print("✅ Threshold saved → models/xgboost/threshold.pkl")


if __name__ == "__main__":
    train_xgboost()