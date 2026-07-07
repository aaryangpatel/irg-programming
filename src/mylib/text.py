import string
from mylib.stopwords import STOPWORDS

def tokenize(text: str, remove_stopwords: bool = False) -> list[str]:
    """Break text into normalized lowercase words without punctuation."""
    table = str.maketrans("", "", string.punctuation)
    cleaned = text.translate(table).lower()
    words = cleaned.split()
    if remove_stopwords:
        words = [w for w in words if w not in STOPWORDS]
    return words
