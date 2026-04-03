import pandas as pd

def get_feature_columns():
    df = pd.read_csv("data/processed/final_ml_dataset.csv")
    return df.drop(columns=['fraud_label']).columns.tolist()