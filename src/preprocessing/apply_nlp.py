import pandas as pd
from nlp_pipeline import process_text

def apply_nlp():
    df = pd.read_csv("data/processed/final_dataset.csv")
    
    df['nlp_features'] = df['claim_text'].apply(process_text)
    
    df.to_csv("data/processed/nlp_processed.csv", index=False)
    
    print("✅ NLP processing completed!")

if __name__ == "__main__":
    apply_nlp()