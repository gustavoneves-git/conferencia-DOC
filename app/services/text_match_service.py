import re
import unicodedata


def normalize_for_match(text: str) -> str:
    text = strip_accents(text).lower()
    text = re.sub(r"[^a-z0-9§ºª]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_accents(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", str(text or ""))
        if unicodedata.category(char) != "Mn"
    )


def candidate_phrases(text: str, min_words: int = 4) -> list[str]:
    clean = " ".join(str(text or "").split())
    if not clean:
        return []
    words = clean.split()
    candidates = [clean]
    if len(words) > min_words:
        candidates.append(" ".join(words[: min(len(words), 14)]))
        candidates.append(" ".join(words[-min(len(words), 14) :]))
    if len(words) > 10:
        mid = len(words) // 2
        candidates.append(" ".join(words[max(0, mid - 5) : mid + 7]))
    return _unique([item for item in candidates if len(item) >= 8])


def text_contains(page_text: str, issue_text: str) -> bool:
    normalized_page = normalize_for_match(page_text)
    for candidate in candidate_phrases(issue_text):
        if normalize_for_match(candidate) in normalized_page:
            return True
    return False


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        key = normalize_for_match(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result
