from pathlib import Path
import re

import fitz
from docx import Document

from app.models.feedback import IngestOutput


def _clean_text(text: str) -> str:
    cleaned = re.sub(r"\r\n?", "\n", text)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def _extract_sections(text: str) -> list[str]:
    sections: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.isupper() and len(s.split()) <= 8:
            sections.append(s.title())
        elif re.match(r"^\d+(\.\d+)*\s+[A-Za-z]", s):
            sections.append(s)
    return sections[:20]


def parse_file(file_path: str, file_type: str) -> IngestOutput:
    path = Path(file_path)
    ext = file_type.lower()
    raw_text = ""

    if ext == "txt":
        raw_text = path.read_text(encoding="utf-8", errors="ignore")
    elif ext == "pdf":
        with fitz.open(path) as doc:
            raw_text = "\n".join(page.get_text() for page in doc)
    elif ext == "docx":
        doc = Document(path)
        raw_text = "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    cleaned = _clean_text(raw_text)
    paragraphs = [p for p in cleaned.split("\n\n") if p.strip()]
    words = re.findall(r"\b[\w'-]+\b", cleaned)

    return IngestOutput(
        raw_text=cleaned,
        word_count=len(words),
        paragraph_count=len(paragraphs),
        detected_sections=_extract_sections(cleaned),
        language="en",
    )
