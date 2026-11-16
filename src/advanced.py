"""Build a page-linked index of WDR 2024 text and checked visual regions."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import pymupdf

from starter.baseline import TfidfIndex

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/world_development_report_2024.pdf"
NOTES = ROOT / "data/advanced_visual_notes.json"
INDEX = ROOT / ".local/advanced_chunks.json"
SOURCE = "World Bank, World Development Report 2024: The Middle-Income Trap"
SOURCE_ID = "wdr2024-middle-income-trap"
PDF_SHA256 = "dc69d858e364a1534a57c49fbb72237f69d88165a63933a98f01f3c20262aded"


def _chunk(page: int, start: int, text: str, kind: str, bbox=None, label=None):
    identity = f"{SOURCE_ID}\0{page}\0{kind}\0{start}\0{text}"
    return {"id": hashlib.sha256(identity.encode()).hexdigest(), "source_id": SOURCE_ID,
            "source": SOURCE, "page": page, "text": text,
            "metadata": {"kind": kind, "start_char": start, "bbox": bbox, "label": label}}


def build_index(pdf: Path = PDF, notes_path: Path = NOTES):
    actual_sha256 = hashlib.sha256(pdf.read_bytes()).hexdigest()
    if actual_sha256 != PDF_SHA256:
        raise ValueError(f"WDR PDF checksum mismatch: {actual_sha256}")
    notes = json.loads(notes_path.read_text(encoding="utf-8"))
    note_pages = {}
    for note in notes:
        note_pages.setdefault(note["page"], []).append(note)
    chunks = []
    pages = []
    with pymupdf.open(pdf) as doc:
        for number, page in enumerate(doc, 1):
            # PDF's native reading order preserves the report's two-column prose
            # and figure labels better than geometric sort on this document.
            text = page.get_text(sort=False).strip()
            pages.append({"page": number, "text_chars": len(text),
                          "images": len(page.get_images()), "drawings": len(page.get_drawings())})
            if text:
                # Sliding windows keep figure labels and nearby axes together.
                for start in range(0, len(text), 1300):
                    piece = text[max(0, start - 200):start + 1300].strip()
                    if piece:
                        chunks.append(_chunk(number, start, piece, "page_text",
                                             [0, 0, round(page.rect.width), round(page.rect.height)]))
            for note in note_pages.get(number, []):
                bbox = note["bbox"]
                if not (0 <= bbox[0] < bbox[2] <= page.rect.width and
                        0 <= bbox[1] < bbox[3] <= page.rect.height):
                    raise ValueError(f"Invalid crop on page {number}: {bbox}")
                chunks.append(_chunk(number, 0, f"{note['label']} ({note['kind']}): {note['description']}",
                                     note["kind"], bbox, note["label"]))
    manifest = {"source": SOURCE, "url": "https://openknowledge.worldbank.org/server/api/core/bitstreams/862729db-69a7-48a8-ba91-df8fe8d8745b/content",
                "sha256": actual_sha256, "physical_pages": len(pages),
                "chunks": len(chunks), "visual_notes": len(notes),
                "pages_without_text": [p["page"] for p in pages if not p["text_chars"]],
                "pages": pages}
    return chunks, manifest


def save_index():
    chunks, manifest = build_index()
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    (INDEX.parent / "advanced_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


class AdvancedRetriever:
    def __init__(self, chunks=None):
        if chunks is None:
            chunks = json.loads(INDEX.read_text(encoding="utf-8"))
        self.index = TfidfIndex(chunks)

    def search(self, query: str, *, filters=None, top_k=3):
        if filters:
            raise ValueError("Advanced retrieval has no benchmark-derived filters")
        if top_k < 1 or not query.strip():
            raise ValueError("query and top_k must be positive")
        labels = [re.sub(r"\s+", " ", match.group()).casefold() for match in
                  re.finditer(r"\b(?:Table|Figure|Map)\s+[A-Z]?\d+(?:\.\d+){0,2}", query, re.I)]
        candidates = self.index.search(query, len(self.index.chunks))
        for hit in candidates:
            haystack = re.sub(r"\s+", " ", hit["text"]).casefold()
            exact_labels = sum(label in haystack for label in labels)
            hit["score"] += 0.45 * exact_labels if hit["page"] >= 60 else 0
            if hit["page"] < 60:
                hit["score"] *= 0.65  # Front matter includes figure/table lists, not the actual evidence.
        candidates.sort(key=lambda h: (-h["score"], h["id"]))
        # Return distinct pages so a long table cannot crowd out a second source.
        results, seen_pages = [], set()
        for hit in candidates:
            if hit["page"] in seen_pages:
                continue
            seen_pages.add(hit["page"])
            results.append(hit)
            if len(results) >= top_k:
                break
        return results


if __name__ == "__main__":
    print(json.dumps(save_index(), indent=2))
