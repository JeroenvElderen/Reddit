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
