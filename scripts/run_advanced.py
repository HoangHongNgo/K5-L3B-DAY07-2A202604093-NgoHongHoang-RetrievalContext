"""Run the frozen 276-page WDR benchmark without passing gold to retrieval or model."""
import argparse
import hashlib
import json
import statistics
import time
from pathlib import Path

from dotenv import load_dotenv

from src.advanced import AdvancedRetriever, INDEX, ROOT

QUESTIONS = ROOT / "data/advanced_questions.json"
OUT = ROOT / "starter/results/advanced"


def retrieval(split: str, top_k: int):
    questions = [q for q in json.loads(QUESTIONS.read_text(encoding="utf-8")) if q["split"] == split]
    retriever = AdvancedRetriever()
    traces = []
    for q in questions:
        start = time.perf_counter()
        hits = retriever.search(q["question"], top_k=top_k)
        pages = {h["page"] for h in hits}
        required = {g["page"] for g in q["gold"]}
        traces.append({"query_id": q["id"], "group": q["group"], "query": q["question"],
                       "hits": [{"id": h["id"], "page": h["page"], "kind": h["metadata"]["kind"],
                                 "label": h["metadata"].get("label"), "score": h["score"]} for h in hits],
                       "gold_pages": sorted(required), "page_recall": bool(required and required <= pages),
                       "elapsed_ms": round((time.perf_counter() - start) * 1000, 2)})
    answerable = [t for t in traces if t["gold_pages"]]
    summary = {"split": split, "top_k": top_k, "answerable": len(answerable),
               "unanswerable": len(traces)-len(answerable),
               "page_recall": sum(t["page_recall"] for t in answerable),
               "median_ms": statistics.median(t["elapsed_ms"] for t in traces),
               "index_chunks": len(retriever.index.chunks)}
    folder = OUT / split / f"retrieval-k{top_k}"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (folder / "summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    return summary


def agent(split: str, top_k: int, budget: int, max_searches: int):
    import os
    from starter.agentic import run_agent
    from src.day7_agent import ChatController

    if split == "test":
        selection = json.loads((ROOT / "artifacts/advanced/selection.json").read_text(encoding="utf-8"))
        chosen = selection["chosen_after_dev"]
        if selection["status"] != "frozen_before_replacement_test" or any((
            selection["benchmark_sha256"] != hashlib.sha256(QUESTIONS.read_bytes()).hexdigest(),
            selection["index_sha256"] != hashlib.sha256(INDEX.read_bytes()).hexdigest(),
            (top_k, budget, max_searches) != (chosen["top_k"], chosen["context_budget_chars"], chosen["max_searches"]),
        )):
            raise ValueError("Test requires the frozen benchmark, index, and dev-selected configuration")

    load_dotenv(ROOT / "starter/.env")
    model = os.environ.get("OPENAI_MODEL")
    base_url = os.environ.get("OPENAI_BASE_URL")
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not (model and base_url and key):
        raise ValueError("Set OPENAI_MODEL, OPENAI_BASE_URL, and API key in starter/.env")
    questions = [q for q in json.loads(QUESTIONS.read_text(encoding="utf-8")) if q["split"] == split]
    retriever = AdvancedRetriever()
    folder = OUT / split / f"agent-k{top_k}-b{budget}"
    folder.mkdir(parents=True, exist_ok=True)
    traces = []
    for q in questions:
        controller = ChatController(model, base_url, key, max_searches, False, 600)
        start = time.perf_counter()
        try:
            result = run_agent(q["question"], controller, retriever, max_searches=max_searches,
                               top_k=top_k, budget=budget)
        except Exception as exc:
            result = {"status": "error", "answer": "", "citations": [], "events": [],
                      "error": f"{type(exc).__name__}: {exc}"}
        row = {"query_id": q["id"], "group": q["group"], "question": q["question"],
               **result, "model": model, "config": {"top_k": top_k, "budget": budget,
               "max_searches": max_searches, "max_tokens": 600}, "model_calls": controller.calls,
               "elapsed_ms": round((time.perf_counter()-start)*1000, 2)}
        traces.append(row)
        (folder / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        cost = sum((c.get("usage") or {}).get("cost") or 0 for c in controller.calls)
        print(f"{q['id']}: {result['status']}; calls={len(controller.calls)}; USD={cost:.6f}", flush=True)
        if result["status"] == "error" and any(f"HTTP {code}" in result.get("error", "") for code in (401,402,403)):
            raise RuntimeError("Stopped on provider authentication, credit, or permission error")
    return folder


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--split", choices=("dev","test"), required=True)
    p.add_argument("--mode", choices=("retrieval","agent"), required=True)
    p.add_argument("--top-k", type=int, default=3)
    p.add_argument("--budget", type=int, default=6000)
    p.add_argument("--max-searches", type=int, default=3)
    a=p.parse_args()
    if not INDEX.exists():
        raise SystemExit("Run python -m src.advanced first")
    result = retrieval(a.split,a.top_k) if a.mode=="retrieval" else agent(a.split,a.top_k,a.budget,a.max_searches)
    print(result)


if __name__=="__main__": main()
