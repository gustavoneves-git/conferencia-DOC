from pathlib import Path

import fitz
from docx import Document as DocxDocument


class TextExtractionService:
    def extract_pages(self, path: str) -> list[dict]:
        suffix = Path(path).suffix.lower()
        if suffix == ".pdf":
            return self._extract_pdf(path)
        if suffix == ".docx":
            return self._extract_docx(path)
        raise ValueError("Formato nao suportado para extracao.")

    def _extract_pdf(self, path: str) -> list[dict]:
        pages = []
        with fitz.open(path) as doc:
            for idx, page in enumerate(doc, start=1):
                text = page.get_text("text") or ""
                pages.append({"page_number": idx, "text": self.normalize(text)})
        return pages or [{"page_number": 1, "text": ""}]

    def _extract_docx(self, path: str) -> list[dict]:
        doc = DocxDocument(path)
        text = "\n".join(p.text for p in doc.paragraphs)
        return [{"page_number": 1, "text": self.normalize(text)}]

    def normalize(self, text: str) -> str:
        lines = [" ".join(line.split()) for line in (text or "").splitlines()]
        return "\n".join(line for line in lines if line)
