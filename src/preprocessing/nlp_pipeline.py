from clean_text import clean_text
from lemmatize import lemmatize_text
from sentence_split import split_sentences
from ner import extract_entities


def process_text(text):
    return {
        "clean_tokens": clean_text(text),
        "lemmas": lemmatize_text(text),
        "sentences": split_sentences(text),
        "entities": extract_entities(text)
    }