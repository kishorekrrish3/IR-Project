from load_data import load_dataset
from clean_data import clean_dataset
from generate_text import add_claim_text

def build_pipeline():
    df = load_dataset("data/raw/insurance.csv")
    
    df = clean_dataset(df)
    
    df = add_claim_text(df)
    
    df.to_csv("data/processed/final_dataset.csv", index=False)
    
    print("✅ Final dataset saved!")


if __name__ == "__main__":
    build_pipeline()