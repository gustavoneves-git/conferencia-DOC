import re


class DocumentClassifierService:
    def classify(self, full_text: str) -> dict:
        text = full_text.lower()
        if "contrato social" in text:
            doc_type = "CONTRATO_SOCIAL_CONSTITUICAO_LTDA"
        elif "alteracao contratual" in text or "alteração contratual" in text:
            doc_type = "ALTERACAO_CONTRATUAL"
        elif "assembleia geral" in text or "ata" in text:
            doc_type = "ATA_AGE"
        elif "estatuto social" in text:
            doc_type = "ESTATUTO_SOCIAL"
        else:
            doc_type = "NAO_IDENTIFICADO"
        company = self._company(full_text, doc_type)
        return {"document_type": doc_type, "company_name": company}

    def _company(self, text: str, doc_type: str | None = None) -> str | None:
        lines = [self._clean_line(line) for line in (text or "").splitlines()]
        lines = [line for line in lines if line]

        for line in lines[:80]:
            candidate = self._company_from_line(line)
            if candidate:
                return candidate

        joined = " ".join(lines[:80])
        for match in self._company_pattern().finditer(joined):
            candidate = self._clean_company(match.group(0))
            if self._valid_company(candidate):
                return candidate
        return None

    def _company_from_line(self, line: str) -> str | None:
        match = self._company_pattern().search(line)
        if not match:
            return None
        candidate = self._clean_company(match.group(0))
        return candidate if self._valid_company(candidate) else None

    def _company_pattern(self):
        chars = r"A-ZÁÀÂÃÉÊÍÓÔÕÚÜÇ0-9&.,'’\-\s"
        return re.compile(rf"[{chars}]{{4,}}?\s(?:LTDA\.?|S/A\.?|S\.A\.|LIMITADA)\.?", re.IGNORECASE)

    def _valid_company(self, candidate: str) -> bool:
        if not candidate or len(candidate.split()) < 2:
            return False
        upper = candidate.upper()
        blocked = [
            "CONTRATO SOCIAL",
            "CONSTITUIÇÃO DE SOCIEDADE",
            "CONSTITUICAO DE SOCIEDADE",
            "ATA DA ASSEMBLEIA",
            "ATA DE ASSEMBLEIA",
            "ESTATUTO SOCIAL",
            "SOCIEDADE LIMITADA",
            "SOCIEDADE ANÔNIMA",
            "SOCIEDADE ANONIMA",
        ]
        if any(term in upper for term in blocked) and not re.search(r"\b(LTDA|S/A|S\.A\.)\.?$", upper):
            return False
        return bool(re.search(r"\b(LTDA|S/A|S\.A\.|LIMITADA)\.?$", upper))

    def _clean_line(self, line: str) -> str:
        return " ".join((line or "").replace("–", "-").split())

    def _clean_company(self, value: str) -> str:
        value = self._clean_line(value)
        value = re.sub(r"^(?:DENOMINAÇÃO|DENOMINACAO|EMPRESA|RAZÃO SOCIAL|RAZAO SOCIAL)\s*[:\-]\s*", "", value, flags=re.IGNORECASE)
        return value.strip(" :-")
