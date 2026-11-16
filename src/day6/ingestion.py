"""Extract PDF pages while retaining physical page numbers."""
from pathlib import Path
import hashlib
import json
from difflib import SequenceMatcher
import re
import unicodedata

from pypdf import PdfReader
from .models import DocumentPage


def ocr_page(path: Path, number: int, cache_dir: Path | None = None) -> str:
    """OCR a rendered page, including images on pages with embedded PDF text."""
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    cache = (cache_dir or path.parent / ".ocr_cache") / f"{digest}-p{number}-rapidocr-1.4.4.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))["text"]
    from rapidocr_onnxruntime import RapidOCR
    import pymupdf
    with pymupdf.open(path) as document:
        pix = document[number - 1].get_pixmap(matrix=pymupdf.Matrix(2, 2), alpha=False)
        result, _ = RapidOCR()(pix.tobytes("png"))
    if not result:
        return ""
    # Keep the two-page-spread columns together instead of interleaving their lines.
    middle = pix.width / 2
    columns = [[], []]
    for box, line, confidence in result:
        if confidence < 0.60 or not line.strip():
            continue
        center_x = sum(point[0] for point in box) / len(box)
        top_y = min(point[1] for point in box)
        columns[int(center_x >= middle)].append((top_y, line.strip()))
    text = "\n".join(line for column in columns for _, line in sorted(column))
    if not text.strip():
        return ""
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps({"page": number, "engine": "rapidocr-onnxruntime 1.4.4",
                                 "text": text}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return text


def _compact(text: str) -> str:
    return "".join(ch for ch in text.casefold() if ch.isalnum())


def novel_ocr_text(ocr_text: str, pdf_text: str) -> str:
    """Keep OCR lines that do not already appear in the PDF text layer."""
    pdf_lines = [_compact(line) for line in pdf_text.splitlines()]
    pdf_joined = _compact(pdf_text)
    kept = []
    for line in ocr_text.splitlines():
        compact = _compact(line)
        if len(compact) < 4 or compact in pdf_joined:
            continue
        if any(SequenceMatcher(None, compact, native, autojunk=False).ratio() >= 0.90
               for native in pdf_lines if native):
            continue
        kept.append(line)
    return "\n".join(kept)


def load_pdf(path: Path, document_id: str, source: str,
             selected_pages: set[int] | None = None,
             ocr_cache_dir: Path | None = None) -> list[DocumentPage]:
    """Extract embedded text and novel OCR text from every physical page."""
    reader = PdfReader(path)
    pages = []
    for number, page in enumerate(reader.pages, start=1):
        if selected_pages is not None and number not in selected_pages:
            continue
        text = normalize_text(page.extract_text() or "")
        ocr_text = normalize_text(ocr_page(path, number, ocr_cache_dir))
        if text:
            pages.append(DocumentPage(document_id, source, number, text,
                                      {"extraction_method": "pdf_text"}))
            overlay = novel_ocr_text(ocr_text, text)
            if overlay:
                pages.append(DocumentPage(document_id, source, number, overlay,
                                          {"extraction_method": "ocr_overlay"}))
        else:
            if not ocr_text:
                raise ValueError(f"No PDF text or OCR text: {path}, page {number}")
            pages.append(DocumentPage(document_id, source, number, ocr_text,
                                      {"extraction_method": "ocr"}))
    return pages


def normalize_text(text: str) -> str:
    """Normalize Unicode and spaces while preserving paragraph boundaries."""
    text = unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[\t\f\v ]+", " ", line).strip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def evidence_text(text: str) -> str:
    """Collapse whitespace for matching quotes across PDF line breaks."""
    return " ".join(normalize_text(text).casefold().split())
