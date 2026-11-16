"""Locate citations needing manual source review; exact gold match is only a triage aid."""
import json
from pathlib import Path

from src.day7 import evidence_hit

ROOT = Path(__file__).resolve().parents[1]
questions = {q["id"]: q for q in json.loads((ROOT / "data/day7_questions.json").read_text(encoding="utf-8"))}
traces = json.loads((ROOT / "starter/results/day7/agent-dev-tfidf-v4.json").read_text(encoding="utf-8"))
for trace in traces:
    q = questions[trace["query_id"]]
    if not q["gold"]:
        continue
    hits = {hit["id"]: hit for event in trace["events"] if event["event"] == "search" for hit in event["results"]}
    missing = [cid for cid in trace["citations"] if not evidence_hit(hits[cid], q["gold"])]
    if missing:
        print(trace["query_id"], "citations without whole gold quote:", [cid[:8] for cid in missing])
