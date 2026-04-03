from sentence_transformers import util
from embedding import get_embedding

# Example fraud reference texts
fraud_patterns = [
    # "The accident happened suddenly with no witnesses",
    "Vehicle was stolen without any evidence",
    "Claim amount is unusually high for minor damage"
]

def compute_similarity(claim_text):
    claim_emb = get_embedding(claim_text)
    
    scores = []
    
    for pattern in fraud_patterns:
        pattern_emb = get_embedding(pattern)
        score = util.cos_sim(claim_emb, pattern_emb).item()
        scores.append(score)
    
    return max(scores)  # highest similarity

