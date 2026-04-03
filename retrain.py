"""
retrain.py
==========
Master script to rebuild the dataset and retrain the dual-channel fraud model.

Run from project root:
    python retrain.py

Steps:
  1. build_dataset  — load raw CSV, clean, generate fraud-aware text
  2. feature_builder— compute NLP fraud scores per row
  3. final_features — engineer structured features + combine
  4. train_xgboost  — train model, save model + scaler + threshold
"""

import sys
import os

# Ensure all sub-packages can import each other
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(root_dir, "src/preprocessing"))
sys.path.insert(0, os.path.join(root_dir, "src/features"))
sys.path.insert(0, os.path.join(root_dir, "src/models"))

print("=" * 60)
print("  DUAL-CHANNEL FRAUD DETECTOR — FULL RETRAIN PIPELINE")
print("=" * 60)

# ── Step 1: Build dataset ──────────────────────────────────────
print("\n[1/4] Building dataset with fraud-aware text...")
from build_dataset import build_pipeline
build_pipeline()

# ── Step 2: Compute NLP features ──────────────────────────────
print("\n[2/4] Computing NLP fraud scores per row...")
from feature_builder import build_features
build_features()

# ── Step 3: Prepare final ML dataset ──────────────────────────
print("\n[3/4] Engineering final feature set...")
from final_features import prepare_features
prepare_features()

# ── Step 4: Train XGBoost ─────────────────────────────────────
print("\n[4/4] Training XGBoost model...")
from train_xgb import train_xgboost
train_xgboost()

print("\n" + "=" * 60)
print("  ✅ RETRAIN COMPLETE")
print("  Now start the API: uvicorn src.api.main:app --reload")
print("  Then the UI:       streamlit run app/streamlit_app.py")
print("=" * 60)
