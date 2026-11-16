"""Deterministic fixed-window and sentence-group chunking per source page."""
from hashlib import sha256
import re
from .models import Chunk, DocumentPage


def _make_chunk(page: DocumentPage, start: int, end: int) -> Chunk:
    text = page.text[start:end].strip()
    identity = f"{page.document_id}\0{page.page}\0{start}\0{text}"
    chunk_id = sha256(identity.encode("utf-8")).hexdigest()
    metadata = {**page.metadata, "start_char": start, "end_char": end}
    return Chunk(chunk_id, page.document_id, page.source, page.page, text, metadata)


def fixed_size(page: DocumentPage, size: int, overlap: int) -> list[Chunk]:
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("Require size > 0 and 0 <= overlap < size")
    chunks = []
    step = size - overlap
    for start in range(0, len(page.text), step):
        end = min(start + size, len(page.text))
        if not page.text[start:end].strip():
            continue
        chunks.append(_make_chunk(page, start, end))
        if start + size >= len(page.text):
            break
    return chunks


def by_sentence(page: DocumentPage, max_size: int) -> list[Chunk]:
    """Group complete sentences up to a size limit, splitting long units at spaces."""
    if max_size <= 0:
        raise ValueError("max_size must be positive")
    text = page.text
    if not text.strip():
        return []
    # PDF line breaks are mostly visual wrapping. Sentence punctuation is a
    # more reliable boundary for this corpus than a single extracted newline.
    boundaries = [0]
    boundaries.extend(match.end() for match in re.finditer(
        r'[.!?]["”’]?\s+(?=[A-Z])', text
    ))
    boundaries.append(len(text))
    chunks = []
    group_start = group_end = 0
    for start, end in zip(boundaries, boundaries[1:]):
        if end - start > max_size:
            if group_end > group_start:
                chunks.append(_make_chunk(page, group_start, group_end))
            group_start = group_end = 0
            while start < end:
                stop = min(start + max_size, end)
                if stop < end:
                    space = text.rfind(" ", start + max_size // 2, stop)
                    if space > start:
                        stop = space + 1
                if text[start:stop].strip():
                    chunks.append(_make_chunk(page, start, stop))
                start = stop
        elif group_end == group_start:
            group_start, group_end = start, end
        elif end - group_start <= max_size:
            group_end = end
        else:
            chunks.append(_make_chunk(page, group_start, group_end))
            group_start, group_end = start, end
    if group_end > group_start:
        chunks.append(_make_chunk(page, group_start, group_end))
    return chunks
