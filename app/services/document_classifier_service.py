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
        company = self._company(full_text)
        return {"document_type": doc_type, "company_name": company}

    def _company(self, text: str) -> str | None:
        match = re.search(r"([A-Z0-9&.,\s]{4,}\s(?:LTDA|S\.A\.|S/A|LIMITADA))", text)
        return " ".join(match.group(1).split()) if match else None
