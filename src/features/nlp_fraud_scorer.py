"""
nlp_fraud_scorer.py
====================
Standalone NLP module that analyses unstructured claim text (emails, letters,
claim narratives) and returns a fraud score in [0, 1].

Signals used:
  1. Semantic similarity to a rich library of fraud-pattern sentences
  2. Fraud keyword density (urgency, vagueness, exaggeration)
  3. Vagueness / hedge word density
  4. Sentiment polarity (fraud texts tend toward neutral/robotic or overly negative)
  5. Text specificity penalty (real claims name people, times, places)
"""

import re
from sentence_transformers import SentenceTransformer, util

# ─────────────────────────────────────────────
# Model (loaded once at import time)
# ─────────────────────────────────────────────
_embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# ─────────────────────────────────────────────
# 1. Fraud pattern library (30+ patterns)
# ─────────────────────────────────────────────
FRAUD_PATTERNS = [
    # Vagueness / inability to recall
    "I cannot remember the exact details of the incident",
    "I am not sure exactly what happened or when it occurred",
    "the details are unclear to me at this time",
    "I do not recall exactly where the accident took place",
    "I was in shock and cannot remember specifics",

    # No witnesses
    "there were no witnesses present at the scene",
    "no one saw what happened",
    "it happened in an isolated area with nobody around",
    "nobody was around to witness the incident",

    # Urgency / pressure tactics
    "I need this claim processed urgently",
    "please approve the full claim amount as soon as possible",
    "I am in urgent financial need and cannot wait",
    "I urgently request immediate payment",
    "please process this immediately I am in distress",

    # Exaggerated or maximum claim requests
    "I want to claim the maximum policy amount",
    "the damage is much worse than it appears",
    "the car is completely destroyed beyond repair",
    "I need to be compensated for the full value",
    "the losses are enormous and I need full reimbursement",

    # Lack of documentation
    "I cannot provide documentation at this time",
    "I do not have receipts or photos available right now",
    "the police were not called to the scene",
    "I did not file a police report for the incident",
    "there is no official report for this incident",

    # Financial stress motivation language
    "I am in a very difficult financial situation",
    "I have urgent bills and cannot afford to wait",
    "I desperately need this money as soon as possible",
    "this is causing me significant financial hardship",

    # Other driver fled / no contact
    "the other driver fled the scene before police arrived",
    "the other party left without leaving contact details",
    "the at-fault vehicle drove away immediately",

    # Loyalty / entitlement pressure
    "I have been a loyal customer for many years",
    "after so many years of paying premiums I deserve this",
    "I expect this to be handled given my long history with you",
]

# Pre-encode fraud patterns once
_FRAUD_PATTERN_EMBEDDINGS = _embed_model.encode(FRAUD_PATTERNS, convert_to_tensor=True)

# ─────────────────────────────────────────────
# 2. Keyword lists
# ─────────────────────────────────────────────
# Fraud-specific keywords: urgency, exaggeration, pressure, missing evidence
# NOTE: Pure hedge/vague words are intentionally excluded here — they have their
# own dedicated channel (_hedge_density) to avoid double-counting.
FRAUD_KEYWORDS = {
    # urgency / pressure tactics
    "urgent", "urgently", "immediately", "asap", "right away", "emergency",
    "desperate", "desperately", "cannot wait",
    # exaggeration of damage / claim
    "totally destroyed", "completely destroyed", "maximum",
    "full amount", "full value", "much worse", "way more",
    # manipulation / entitlement
    "loyal customer", "deserve", "unfair", "distress",
    "financial difficulty", "financial hardship", "financial crisis",
    # missing evidence (explicit absence statements)
    "no witnesses", "no police", "no report", "no photos", "no documentation",
    "no evidence", "nobody saw", "no one saw",
}

# Vague / uncertain language — measured separately from fraud keywords
HEDGE_WORDS = {
    "approximately", "about", "around", "roughly", "maybe", "perhaps",
    "possibly", "probably", "i think", "i believe", "i guess", "i feel",
    "might", "could have", "not sure", "unclear", "somewhere", "sometime",
    "kind of", "sort of", "i don't know", "don't remember", "not exactly",
    "more or less", "i cannot recall", "cannot remember", "do not recall",
    "i forgot", "i don't remember", "not sure", "unsure",
}

SPECIFICITY_INDICATORS = {
    # Specific times / dates
    r'\b\d{1,2}:\d{2}\s*(am|pm)?\b',    # 9:10 AM
    r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
    r'\b\d{1,2}(st|nd|rd|th)\b',         # 14th
    r'\breport\s*(number|no\.?|#)\s*\w+',  # report number
    r'\bofficer\s+[A-Z][a-z]+\b',          # Officer Williams
    r'\bcase\s+number\b',
    r'\bpolice\s+report\b',
    r'\bwitness\b',
    r'\breceipt\b',
    r'\bphoto\b',
    r'\bhospital\b',
}


# ─────────────────────────────────────────────
# Core functions
# ─────────────────────────────────────────────

def _semantic_fraud_score(text: str) -> float:
    """Returns max cosine similarity to any fraud pattern (0–1)."""
    text_emb = _embed_model.encode(text, convert_to_tensor=True)
    scores = util.cos_sim(text_emb, _FRAUD_PATTERN_EMBEDDINGS)[0]
    return float(scores.max().item())


def _keyword_density(text: str) -> float:
    """Fraction of words that are fraud-indicating keywords (0–1, capped at 1)."""
    words = re.findall(r'\b\w+\b', text.lower())
    if not words:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for kw in FRAUD_KEYWORDS if kw in text_lower)
    return min(hits / max(len(words) / 10, 1), 1.0)


def _hedge_density(text: str) -> float:
    """Fraction of hedge/vague words present (0–1)."""
    text_lower = text.lower()
    hits = sum(1 for hw in HEDGE_WORDS if hw in text_lower)
    return min(hits / 5.0, 1.0)  # cap at 5 hedge phrases = score 1.0


def _specificity_score(text: str) -> float:
    """Returns 0–1: higher means MORE specific (less suspicious)."""
    text_lower = text.lower()
    matches = sum(
        1 for pattern in SPECIFICITY_INDICATORS
        if re.search(pattern, text_lower)
    )
    return min(matches / 4.0, 1.0)  # 4+ specificity signals = fully legit


def _sentiment_suspicion(text: str) -> float:
    """
    Purely lexical sentiment estimation (no external deps).
    Fraud texts tend to be very neutral (robotic) or extremely negative.
    Returns a suspicion score 0–1.
    """
    positive_words = {"thank", "appreciate", "grateful", "pleased", "cooperative",
                      "happy", "satisfied", "glad", "fortunately"}
    negative_urgent = {"distress", "desperate", "crisis", "hardship", "frustrated",
                       "angry", "unfair", "demand", "force", "must"}
    words = set(re.findall(r'\b\w+\b', text.lower()))
    pos_hits = len(words & positive_words)
    neg_hits = len(words & negative_urgent)
    if pos_hits == 0 and neg_hits == 0:
        return 0.4   # neutral / robotic → mildly suspicious
    if neg_hits > pos_hits:
        return min(0.5 + neg_hits * 0.1, 1.0)
    return 0.1   # positive, cooperative tone → low suspicion


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def compute_nlp_fraud_score(text: str) -> float:
    """
    Compute a single NLP-based fraud score in [0, 1].

    Four independent fraud signals are combined:
      - Semantic similarity to fraud patterns  (45%) — strongest signal
      - Fraud keyword density                  (35%) — urgency/pressure/exaggeration only
      - Vagueness / hedge word density         (10%) — uncertainty language
      - Sentiment suspicion                    (10%) — tone analysis
      - Specificity bonus                      (−20%) — named people/dates/reports reduce score

    Tier targets after blending with XGBoost (50/50):
      LOW    : final_score < 30
      MEDIUM : 30 ≤ final_score < 60
      HIGH   : final_score ≥ 60
    """
    if not text or not text.strip():
        return 0.3   # no text → mild neutral suspicion

    sem    = _semantic_fraud_score(text)    # 0‒1 (higher = more fraud-like)
    kwd    = _keyword_density(text)         # 0‒1 (higher = more fraud-like)
    hedge  = _hedge_density(text)           # 0‒1 (higher = more fraud-like)
    spec   = _specificity_score(text)       # 0‒1 (higher = more legit → reduces score)
    sent   = _sentiment_suspicion(text)     # 0‒1 (higher = more suspicious)

    score = (
        0.45 * sem
        + 0.35 * kwd
        + 0.10 * hedge
        + 0.10 * sent
        - 0.20 * spec
    )

    # Clamp to [0, 1]
    return float(max(0.0, min(1.0, score)))


def get_nlp_breakdown(text: str) -> dict:
    """Returns individual sub-scores for explainability / UI display."""
    sem   = _semantic_fraud_score(text)
    kwd   = _keyword_density(text)
    hedge = _hedge_density(text)
    spec  = _specificity_score(text)
    sent  = _sentiment_suspicion(text)

    return {
        "semantic_similarity": round(sem, 4),
        "keyword_density":     round(kwd, 4),
        "vagueness_score":     round(hedge, 4),
        "sentiment_suspicion": round(sent, 4),
        "specificity_score":   round(spec, 4),
        "nlp_fraud_score":     round(compute_nlp_fraud_score(text), 4),
    }
