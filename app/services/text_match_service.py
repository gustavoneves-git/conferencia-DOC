import re
import unicodedata


QUOTE_TRANSLATION = str.maketrans({
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "´": "'",
    "`": "'",
    "–": "-",
    "—": "-",
    "−": "-",
})


def normalize_for_match(text: str) -> str:
    text = str(text or "").translate(QUOTE_TRANSLATION)
    text = strip_accents(text).lower()
    text = re.sub(r"[^a-z0-9§ºª]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def strip_accents(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", str(text or ""))
        if unicodedata.category(char) != "Mn"
    )


def candidate_phrases(text: str, min_words: int = 4) -> list[str]:
    clean = " ".join(str(text or "").translate(QUOTE_TRANSLATION).split())
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
    candidates.extend(_key_phrases(clean))
    return _unique([item for item in candidates if len(item) >= 8])


def text_contains(page_text: str, issue_text: str) -> bool:
    return locate_strategy(page_text, issue_text) != "NOT_FOUND"


def locate_strategy(page_text: str, issue_text: str) -> str:
    raw_page = " ".join(str(page_text or "").translate(QUOTE_TRANSLATION).split())
    raw_issue = " ".join(str(issue_text or "").translate(QUOTE_TRANSLATION).split())
    if not raw_page or not raw_issue:
        return "NOT_FOUND"
    if raw_issue in raw_page:
        return "EXACT"

    normalized_page = normalize_for_match(page_text)
    normalized_issue = normalize_for_match(issue_text)
    if normalized_issue and normalized_issue in normalized_page:
        return "NORMALIZED"

    for candidate in _substring_candidates(issue_text):
        if normalize_for_match(candidate) in normalized_page:
            return "SUBSTRING"

    for candidate in _key_phrases(issue_text):
        if normalize_for_match(candidate) in normalized_page:
            return "KEY_PHRASE"
    return "NOT_FOUND"


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        key = normalize_for_match(value)
        if key and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def _substring_candidates(text: str) -> list[str]:
    clean = " ".join(str(text or "").translate(QUOTE_TRANSLATION).split())
    words = clean.split()
    candidates = []
    if len(words) > 6:
        candidates.extend([" ".join(words[:12]), " ".join(words[-12:])])
    if len(words) > 14:
        mid = len(words) // 2
        candidates.append(" ".join(words[max(0, mid - 6) : mid + 6]))
    sentences = re.split(r"(?<=[.;:])\s+", clean)
    candidates.extend(sentence for sentence in sentences if 8 <= len(sentence) < len(clean))
    return _unique(candidates)


def _key_phrases(text: str) -> list[str]:
    clean = " ".join(str(text or "").translate(QUOTE_TRANSLATION).split())
    protected = [
        "art. 1.072,, § 3º",
        "mandado judicial",
        "Legislação vigente da época",
        "A sócia administradora declara",
        "O sócio administrador declara",
        "A sócia administradora, poderá",
        "O sócio administrador, poderá",
        "Faculta-se ao sócio administrador, constituir",
        "Faculta-se a sócia administradora, constituir",
        "residente e domiciliado",
        "casado no regime comunhão parcial de bens",
        "casada no regime comunhão parcial de bens",
        "pesa a cláusula restritiva",
        "foro da sede",
        "cláusula adjudicia e a extra",
        "contas-corrente",
        "ordenar títulos de créditos para protesto",
    ]
    result = [phrase for phrase in protected if normalize_for_match(phrase) in normalize_for_match(clean)]
    quoted = re.findall(r"[\"“”']([^\"“”']{8,80})[\"“”']", clean)
    result.extend(quoted)
    return _unique(result)
