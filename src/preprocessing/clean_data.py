import pandas as pd

def clean_dataset(df):
    # Drop duplicates
    df = df.drop_duplicates()
    
    # Handle missing values - newer pandas uses .ffill() / .bfill()
    df = df.ffill().bfill()
    
    # Convert fraud label to numeric
    if 'fraud_reported' in df.columns:
        df['fraud_label'] = df['fraud_reported'].map({'Y': 1, 'N': 0})
    
    return df