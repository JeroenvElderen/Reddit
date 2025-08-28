"""
Language detection helpers.
"""

EN_STOPWORDS = {
    "the","be","to","of","and","a","in","that","have","i","it","for","not",
    "on","with","he","as","you","do","at","this","but","his","by","from","we",
    "say","her","she","or","an","will","my","one","all","would","there","their"
}

def likely_english(text: str) -> bool:
    if not text:
        return True
    t = text.lower()
    letters = sum(ch.isalpha() for ch in t)
    ascii_letters = sum(('a' <= ch <= 'z') for ch in t)
    ratio = (ascii_letters / max(1, letters))
    sw_hits = sum(1 for w in EN_STOPWORDS if f" {w} " in f" {t} ")
    score = ratio + 0.05 * sw_hits
    return score >= 0.6
