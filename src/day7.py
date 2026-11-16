"""Day 7 retrieval on sentence chunks, including OCR-only PDF pages."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import time
from pathlib import Path

import psycopg
from dotenv import load_dotenv

from src.day6.chunking import by_sentence
from src.day6.embeddings import MyEmbedder
from src.day6.ingestion import evidence_text, load_pdf
from src.day6.store import PgVectorStore
from starter.baseline import TfidfIndex, pack_context

ROOT = Path(__file__).resolve().parents[1]
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
STRATEGY = "B_OCR"  # Separate index: the published Day 6 B results remain intact.


def settings():
    load_dotenv(ROOT / "starter/.env")
    os.environ.setdefault("HF_HOME", str(ROOT / ".local/models/huggingface"))
    url = os.environ.get("DATABASE_URL")
    model = os.environ.get("EMBEDDING_MODEL", MODEL)
    if not url or model != MODEL:
        raise ValueError("Day 6 DATABASE_URL and all-MiniLM-L6-v2 are required")
    return url, model


def corpus():
    manifest = json.loads((ROOT / "data/day6_manifest.json").read_text(encoding="utf-8"))
    pages = []
    for doc in manifest["documents"]:
        path = ROOT / "data" / doc["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != doc["sha256"]:
            raise ValueError(f"PDF checksum differs: {path}")
        selected = set(doc["content_pages"])
        extracted = load_pdf(path, doc["document_id"], doc["source"], selected,
                             ROOT / ".local/ocr")
        if {p.page for p in extracted} != selected:
            raise ValueError("Missing content pages")
        sections = doc.get("section_ranges", [])
        for page in extracted:
            expected_chars = doc["page_character_counts"].get(str(page.page))
            if page.metadata["extraction_method"] != "ocr_overlay" and expected_chars is not None and len(page.text) != expected_chars:
                raise ValueError(f"Page {page.page} changed")
            page.metadata.update({k: doc[k] for k in ("category", "year", "language", "title", "license_or_permission") if k in doc})
            page.metadata["category"] = next((s["category"] for s in sections if s["start_page"] <= page.page <= s["end_page"]), doc["category"])
            pages.append(page)
    return pages


def ingest():
    url, model = settings()
    pages = corpus()
    chunks = [c for page in pages for c in by_sentence(page, 650)]
    embedder = MyEmbedder(model)
    if embedder.dimensions != 384:
        raise ValueError("Day 6 model should have 384 dimensions")
    store = PgVectorStore(url, 384, model)
    store.create_schema()
    store.upsert(STRATEGY, chunks, embedder.embed_documents([c.text for c in chunks]))
    return {"pages": len({p.page for p in pages}), "segments": len(pages),
            "chunks": len(chunks), "model": model, "dimensions": 384, "strategy": STRATEGY}


def load_chunks(url, model):
    with psycopg.connect(url) as db:
        rows = db.execute("""SELECT chunk_id, document_id, source, page, content, metadata
            FROM starter_chunks WHERE strategy = %s AND model_name = %s ORDER BY chunk_id""",
            (STRATEGY, model)).fetchall()
    if not rows:
        raise ValueError("No B_OCR chunks in pgvector; run ingest first")
    return [{"id": row[0], "source_id": row[1], "source": row[2], "page": row[3],
             "text": row[4], "metadata": row[5]} for row in rows]


class Retriever:
    def __init__(self, method: str):
        if method not in {"dense", "tfidf", "hybrid"}:
            raise ValueError("method must be dense, tfidf, or hybrid")
        self.method = method
        url, model = settings()
        self.store = PgVectorStore(url, 384, model)
        self.chunks = load_chunks(url, model)
        self.lexical = TfidfIndex(self.chunks)
        self.embedder = MyEmbedder(model) if method != "tfidf" else None

    def search(self, query: str, *, filters=None, top_k=3):
        if top_k < 1 or not query.strip():
            raise ValueError("top_k and query must be positive")
        filters = filters or {}
        def allowed(c):
            return all(str(c.get(k, c["metadata"].get(k))) == str(v) for k, v in filters.items())
        n = min(len(self.chunks), max(20, top_k * 4))
        dense = []
        lexical = []
        if self.method != "tfidf":
            dense = self.store.search(STRATEGY, self.embedder.embed_query(query), n, filters)
            dense = [{"id": h["chunk_id"], "source_id": h["document_id"],
                      **{k: h[k] for k in ("source", "page", "text", "metadata", "score")}} for h in dense]
        if self.method != "dense":
            lexical = [c for c in self.lexical.search(query, top_k=len(self.chunks)) if allowed(c)][:n]
        if self.method == "dense":
            return dense[:top_k]
        if self.method == "tfidf":
            return lexical[:top_k]
        # Reciprocal rank fusion keeps the two score scales separate.
        by_id = {c["id"]: c for c in dense + lexical}
        scores = {}
        for hits in (dense, lexical):
            for rank, hit in enumerate(hits, 1):
                scores[hit["id"]] = scores.get(hit["id"], 0.0) + 1 / (60 + rank)
        return [{**by_id[cid], "score": score} for cid, score in
                sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))[:top_k]]


def cases(split, questions_path=None):
    data = json.loads(Path(questions_path or ROOT / "data/day7_questions.json").read_text(encoding="utf-8"))
    return [q for q in data if q["split"] == split]


def evidence_hit(chunk, gold):
    return any(chunk["source_id"] == g["source_id"] and chunk["page"] == g["page"]
               and evidence_text(g["evidence"]) in evidence_text(chunk["text"]) for g in gold)


def benchmark(method, split, top_k=3, budget=1800, retriever=None, questions_path=None):
    retriever = retriever or Retriever(method)
    selected = cases(split, questions_path)
    traces = []
    for q in selected:
        started = time.perf_counter()
        results = retriever.search(q["question"], top_k=max(3, top_k))
        context, context_ids = pack_context(results[:top_k], budget)
        gold = q.get("gold", [])
        traces.append({"query_id": q["id"], "split": split, "method": method,
                       "group": q.get("group", "text"),
                       "config": {"top_k": top_k, "budget_chars": budget},
                       "query": q["question"], "filter": None,
                       "results": results, "context": context, "context_ids": context_ids,
                       "hit1": bool(gold and results and evidence_hit(results[0], gold)),
                       "hit3": bool(gold and any(evidence_hit(r, gold) for r in results[:3])),
                       "context_hit": bool(gold and any(evidence_hit(r, gold) for r in results if r["id"] in context_ids)),
                       "elapsed_ms": round((time.perf_counter()-started)*1000, 2)})
    answerable = [t for t, q in zip(traces, selected) if q.get("gold")]
    summary = {"method": method, "split": split, "top_k": top_k, "budget_chars": budget,
               "answerable": len(answerable), "unanswerable": len(traces)-len(answerable),
               "hit1": sum(t["hit1"] for t in answerable),
               "hit3": sum(t["hit3"] for t in answerable),
               "context_hit": sum(t["context_hit"] for t in answerable),
               "median_ms": statistics.median(t["elapsed_ms"] for t in traces),
               "service_cost_usd": 0}
    return summary, traces


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("ingest")
    e = sub.add_parser("benchmark")
    e.add_argument("--method", choices=("dense", "tfidf", "hybrid"), required=True)
    e.add_argument("--split", choices=("dev", "test"), required=True)
    e.add_argument("--top-k", type=int, default=3)
    e.add_argument("--budget", type=int, default=1800)
    e.add_argument("--output", type=Path, required=True)
    e.add_argument("--questions", type=Path, default=ROOT / "data/day7_questions.json")
    args = p.parse_args()
    if args.command == "ingest":
        print(json.dumps(ingest(), indent=2))
    else:
        summary, traces = benchmark(args.method, args.split, args.top_k, args.budget,
                                    questions_path=args.questions)
        args.output.mkdir(parents=True, exist_ok=True)
        for name, value in (("summary.json", summary), ("traces.json", traces)):
            (args.output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
