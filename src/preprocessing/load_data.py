import pandas as pd

def load_dataset(path):
    df = pd.read_csv(path)
    
    print("✅ Dataset Loaded Successfully")
    print("Shape:", df.shape)
    print("\nColumns:", df.columns.tolist())
    
    return df


if __name__ == "__main__":
    df = load_dataset("data/raw/insurance.csv")
    print(df.head())