"""Aggregate human-reviewed labels for the frozen replacement test."""
import hashlib
import json
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "data/advanced_questions.json"
TRACES = ROOT / "starter/results/advanced/test/agent-k3-b10000/traces.json"
SELECTION = ROOT / "artifacts/advanced/selection.json"
OUT = ROOT / "artifacts/advanced"
REVIEWS = ROOT / "report/individual/advanced_test_reviews.json"

# Each outcome was checked against the cited physical PDF page and region.
REASONS = [
    "Table P1.1, low-income population cell is 8.9%; cited table region on PDF page 63.",
    "Table P1.1, lower-middle-income extreme-poverty cell is 55.4%; citation supports the unit.",
    "Table P1.1, upper-middle-income global-GDP cell is 30.3%; cited table region.",
    "Table P1.1, high-income population cell is 15.7%; cited table region.",
    "Table 2.1 shows the blue/lower-priority innovation dial for lower-middle-income economies.",
    "Table 4.1 consumer-welfare cons cell says fewer players ease cartel formation.",
    "Figure 2.2 horizontal axis is proximity to the frontier; citation points to the diagram.",
    "Figure P2.1 left arrangement has the smallest circle for destruction.",
    "Map 6.2 legend identifies the red marks as power transmission lines; cited map page.",
    "Map 6.1 legend uses orange for upper-middle-income economies; cited map region.",
    "Figure 7.2 top box reads disciplining incumbency; cited diagram region.",
    "Figure 3.5a UMIC bar is 9.0 exajoules per trillion US dollars.",
    "Figure 3.5b LMIC bar is 0.098 GtCO2 equivalent per exajoule.",
    "Figure 3.4 2028 endpoints are 9.7% of revenue and 2.6% of GDP; comparison and citation correct.",
    "Figure 8.6 and accompanying paragraph show subsidies' negative price signal.",
    "Figure 9.12 stacked areas label coal, oil, and natural gas as the dominant fossil fuels.",
    "Table P1.1 gives 8.3 + 30.3 = 38.6%; Figure 1.2 supports the stagnant relative-income trend; both pages cited.",
    "Table 4.1 supports weaker innovation incentives; Figure 7.1 supports fewer patents among market leaders; both regions cited.",
    "Map 6.2 shows grid constraints and Figure 3.6 shows higher solar WACC; both PDF pages cited.",
    "The answer includes an unfinished US savings sentence and cites pages 169/254/255 but not Figure 6.1 on page 171; fails complete answer and figure citation.",
    "Part 1 says approximately three-fourths of the world's population; cited page 63 supports this.",
    "Chapter 3 states over 300 million people still lack electricity; cited page 107.",
    "Page 171 states the IEA revised the 2023-24 renewable-capacity forecast upward by 38%.",
    "Page 223 states Korea devoted nearly 80% of its 1950s education budget to primary education.",
    "Explicitly refuses a 2034 observed population share; no unsupported claim.",
    "Explicitly says 2029 observed low-carbon job count is unavailable; the cited 2022 comparison is supported.",
    "Explicitly refuses a post-publication 2028 prize winner; no unsupported claim.",
    "Explicitly says 2032 observed CO2 share is unavailable; cited 2022 value is correct.",
    "Explicitly refuses an observed 2035 solar-electricity share; no unsupported claim.",
    "Explicitly refuses a 2030 cross-country fossil-fuel-jobs ranking; supplementary claims are supported by cited pages.",
]


def main():
    selection = json.loads(SELECTION.read_text(encoding="utf-8"))
    assert selection["benchmark_sha256"] == hashlib.sha256(QUESTIONS.read_bytes()).hexdigest()
    questions = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8")) if q["split"] == "test"}
    traces = json.loads(TRACES.read_text(encoding="utf-8"))
    assert len(questions) == len(traces) == len(REASONS) == 30
    reviews = []
    for number, (trace, reason) in enumerate(zip(traces, REASONS), 1):
        q = questions[trace["query_id"]]
        assert trace["query_id"] == f"adv_test_{number:02d}"
        hit_by_id = {h["id"]: h for e in trace["events"] if e["event"] == "search" for h in e["results"]}
        cited_pages = sorted({hit_by_id[c]["page"] for c in trace["citations"]})
        required_pages = sorted({g["page"] for g in q["gold"]})
        passed = number != 20
        if q["gold"] and passed:
            assert trace["status"] == "answered" and set(required_pages) <= set(cited_pages), q["id"]
        if not q["gold"] and passed:
            assert "không đủ" in trace["answer"].casefold() or any(
                phrase in trace["answer"].casefold() for phrase in ("does not contain", "insufficient", "not provided", "cannot determine"))
        reviews.append({"query_id": q["id"], "group": q["group"], "passed": passed,
                        "reason": reason, "required_pdf_pages": required_pages,
                        "cited_pdf_pages": cited_pages, "status": trace["status"]})
    by_group = defaultdict(lambda: {"passed": 0, "total": 0})
    for r in reviews:
        by_group[r["group"]]["total"] += 1
        by_group[r["group"]]["passed"] += r["passed"]
    costs = [sum((c.get("usage") or {}).get("cost") or 0 for c in t["model_calls"]) for t in traces]
    summary = {"test_questions": 30, "passed": sum(r["passed"] for r in reviews),
               "pass_rate": sum(r["passed"] for r in reviews)/30,
               "by_group": dict(by_group), "errors": sum(t["status"] == "error" for t in traces),
               "median_elapsed_ms": statistics.median(t["elapsed_ms"] for t in traces),
               "total_cost_usd": round(sum(costs), 8),
               "search_calls": sum(e["event"] == "search" for t in traces for e in t["events"]),
               "model_calls": sum(len(t["model_calls"]) for t in traces),
               "selection_sha256": hashlib.sha256(SELECTION.read_bytes()).hexdigest(),
               "note": "Human review; status=answered can still be a semantic refusal."}
    REVIEWS.write_text(json.dumps(reviews, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "test_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
