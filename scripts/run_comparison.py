"""Evaluate Day 7 retrieval on dev, freeze choice, then inspect held-out test."""
import json
from pathlib import Path

from src.day7 import Retriever, benchmark, cases, corpus, evidence_hit, load_chunks, settings
from src.day6.chunking import by_sentence

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "starter/results/day7"


def write(folder, summary, traces):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (folder / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_gold():
    url, model = settings()
    chunks = load_chunks(url, model)
    expected = {c.chunk_id: c for page in corpus() for c in by_sentence(page, 650)}
    if len(expected) != len(chunks) or any(
        c["id"] not in expected or
        (c["source_id"], c["source"], c["page"], c["text"], c["metadata"]) !=
        (expected[c["id"]].document_id, expected[c["id"]].source,
         expected[c["id"]].page, expected[c["id"]].text, expected[c["id"]].metadata)
        for c in chunks
    ):
        raise ValueError("pgvector rows differ from Day 6 chunk ID/source/page/text/metadata")
    for q in cases("dev") + cases("test"):
        if q["gold"] and not any(evidence_hit(c, q["gold"]) for c in chunks):
            raise ValueError(f"Gold evidence is not contained in a Day 6 chunk: {q['id']}")
    return len(chunks)


def main():
    chunk_count = validate_gold()
    configs = [
        ("dense", 3, 1800, "Day 6 dense baseline"),
        ("tfidf", 3, 1800, "Lexical method"),
        ("hybrid", 3, 1800, "RRF method"),
    ]
    retrievers = {method: Retriever(method) for method in {c[0] for c in configs}}
    dev = []
    for method, top_k, budget, hypothesis in configs:
        summary, traces = benchmark(method, "dev", top_k, budget, retrievers[method])
        key = f"{method}-k{top_k}-b{budget}"
        summary["hypothesis"] = hypothesis
        summary["key"] = key
        write(OUT / "dev" / key, summary, traces)
        dev.append(summary)
        print(key, summary["hit1"], summary["hit3"], summary["context_hit"], summary["median_ms"])
    # Published rule: context evidence, then top-3 evidence, then top-1,
    # then lower median latency. Baseline remains separately reported.
    chosen = max(dev, key=lambda s: (s["context_hit"], s["hit3"], s["hit1"], -s["median_ms"]))
    selection = {"criterion": "max context_hit, then hit3, then hit1, then min median_ms on dev",
                 "chosen": chosen["key"], "chunks": chunk_count, "dev": dev}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "selection.json").write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")
    for summary in (dev[0], chosen):
        method, top_k, budget = summary["method"], summary["top_k"], summary["budget_chars"]
        result, traces = benchmark(method, "test", top_k, budget, retrievers[method])
        write(OUT / "test" / summary["key"], result, traces)
        print("test", summary["key"], result["hit1"], result["hit3"], result["context_hit"])


if __name__ == "__main__":
    main()
