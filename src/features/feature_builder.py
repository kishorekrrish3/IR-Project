"""
feature_builder.py
==================
Builds the features dataset from the processed final_dataset.csv.

Instead of storing 384 raw embedding dimensions (which drown out structured
features), we compute a single distilled `nlp_fraud_score` per row using the
NLP fraud scorer. This gives the model a clean, interpretable NLP signal.
"""

import sys
import os
import pandas as pd

# Allow importing from sibling directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from nlp_fraud_scorer import compute_nlp_fraud_score


def build_features():
    print("🚀 Building dual-channel features (structured + NLP score)...")

    df = pd.read_csv("data/processed/final_dataset.csv")

    print(f"   → Dataset: {len(df)} rows, fraud rate: {df['fraud_label'].mean():.1%}")
    print("   → Computing NLP fraud scores from claim text (this may take a minute)...")

    nlp_scores = []
    for i, text in enumerate(df['claim_text']):
        score = compute_nlp_fraud_score(str(text))
        nlp_scores.append(score)
        if (i + 1) % 100 == 0:
            print(f"      Processed {i + 1}/{len(df)} rows...")

    df['nlp_fraud_score'] = nlp_scores

    # Save enriched dataset
    df.to_csv("data/processed/features_dataset.csv", index=False)

    fraud_nlp   = df[df['fraud_label'] == 1]['nlp_fraud_score'].mean()
    legit_nlp   = df[df['fraud_label'] == 0]['nlp_fraud_score'].mean()
    print(f"\n✅ NLP scores computed!")
    print(f"   Avg NLP score  — FRAUD: {fraud_nlp:.3f}  |  LEGIT: {legit_nlp:.3f}")
    print("   Features dataset saved → data/processed/features_dataset.csv")


if __name__ == "__main__":
    build_features()