import pandas as pd
import spacy

print("Pandas version:", pd.__version__)

nlp = spacy.load("en_core_web_sm")
doc = nlp("This is a test sentence.")

print("Tokens:", [token.text for token in doc])