from transformers import pipeline

# Keep your existing model
nli_pipeline = pipeline("text-classification", model="roberta-large-mnli")

def detect_contradiction(claim_text, reference_text):
    # Combine both sentences properly
    input_text = f"{claim_text} </s> {reference_text}"
    
    result = nli_pipeline(input_text)
    
    return result