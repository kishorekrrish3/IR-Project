import pandas as pd

df = pd.read_csv("data/processed/final_ml_dataset.csv")
print(df['fraud_label'].value_counts())