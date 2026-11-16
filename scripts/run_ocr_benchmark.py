"""Evaluate image-only-page OCR retrieval separately from the published Day 7 run."""
import json
from pathlib import Path

from src.day6.chunking import by_sentence
from src.day7 import benchmark, cases, corpus, evidence_hit
from starter.baseline import TfidfIndex

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "data/day7_ocr_questions.json"
OUT = ROOT / "starter/results/day7/ocr"


class LocalRetriever:
    def __init__(self, chunks):
        self.index = TfidfIndex(chunks)

    def search(self, query, *, filters=None, top_k=3):
        if filters:
            raise ValueError("This diagnostic does not support filters")
        return self.index.search(query, top_k)


def main():
    pages = corpus()
    chunks = [{"id": c.chunk_id, "source_id": c.document_id, "source": c.source,
               "page": c.page, "text": c.text, "metadata": c.metadata}
              for page in pages for c in by_sentence(page, 650)]
    questions = cases("dev", QUESTIONS) + cases("test", QUESTIONS)
    for q in questions:
        if q["gold"] and not any(evidence_hit(c, q["gold"]) and
                                 c["metadata"]["extraction_method"] in {"ocr", "ocr_overlay"}
                                 for c in chunks):
            raise ValueError(f"Gold evidence is absent from the OCR corpus: {q['id']}")
    # Same full-page corpus in both runs; only the OCR chunks are withheld from baseline.
    configs = {
        "text_only": [c for c in chunks if c["metadata"]["extraction_method"] == "pdf_text"],
        "with_ocr": chunks,
    }
    for name, selected in configs.items():
        retriever = LocalRetriever(selected)
        for split in ("dev", "test"):
            summary, traces = benchmark(name, split, top_k=3, budget=3000,
                                        retriever=retriever, questions_path=QUESTIONS)
            summary["corpus_chunks"] = len(selected)
            summary["question_set"] = str(QUESTIONS.relative_to(ROOT))
            summary["by_group"] = {}
            for group in ("ocr_text", "ocr_mixed_text"):
                group_traces = [t for t in traces if t["group"] == group]
                summary["by_group"][group] = {
                    "answerable": len(group_traces),
                    "hit1": sum(t["hit1"] for t in group_traces),
                    "hit3": sum(t["hit3"] for t in group_traces),
                    "context_hit": sum(t["context_hit"] for t in group_traces),
                }
            folder = OUT / name / split
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (folder / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(name, split, f"Hit@1 {summary['hit1']}/{summary['answerable']}",
                  f"Hit@3 {summary['hit3']}/{summary['answerable']}",
                  f"context {summary['context_hit']}/{summary['answerable']}")


if __name__ == "__main__":
    main()
