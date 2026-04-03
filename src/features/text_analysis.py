from sentence_transformers import SentenceTransformer, util
from textblob import TextBlob

model = SentenceTransformer('all-MiniLM-L6-v2')

# More realistic fraud patterns
fraud_patterns = [
    "there were no witnesses",
    "I cannot remember what happened",
    "it happened suddenly",
    "no one saw the incident",
    "details are unclear"
]

def analyze_text(text):
    # Sentiment
    sentiment = TextBlob(text).sentiment.polarity

    # Length
    length = len(text.split())

    # Semantic similarity
    text_emb = model.encode(text)

    similarities = []
    for pattern in fraud_patterns:
        pattern_emb = model.encode(pattern)
        score = util.cos_sim(text_emb, pattern_emb).item()
        similarities.append(score)

    max_similarity = max(similarities)

    return {
        "sentiment": sentiment,
        "text_length": length,
        "fraud_similarity": max_similarity
    }