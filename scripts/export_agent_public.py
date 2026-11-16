"""Redact source excerpts and answer text while retaining auditable agent metadata."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "starter/results/day7"
DEST = ROOT / "artifacts/day7/agent_traces_public"
RUNS = (
    "agent-dev-dense-v3.json",
    "agent-dev-tfidf-v3.json",
    "agent-dev-tfidf-v4.json",
    "agent-test-dense-v3.json",
    "agent-test-tfidf-v4.json",
)


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


for name in RUNS:
    traces = json.loads((SOURCE / name).read_text(encoding="utf-8"))
    public = []
    for trace in traces:
        row = {k: v for k, v in trace.items() if k not in {"answer", "events", "model_calls"}}
        row["answer_sha256"] = digest(trace["answer"])
        row["answer_length"] = len(trace["answer"])
        row["model_calls"] = [
            {k: v for k, v in call.items() if k != "tool_calls"} for call in trace["model_calls"]
        ]
        row["events"] = []
        for event in trace["events"]:
            clean = {k: v for k, v in event.items() if k not in {"results", "context", "attempted_answer"}}
            if "context" in event:
                clean["context_sha256"] = digest(event["context"])
                clean["context_length"] = len(event["context"])
            if "attempted_answer" in event:
                clean["attempted_answer_sha256"] = digest(event["attempted_answer"])
                clean["attempted_answer_length"] = len(event["attempted_answer"])
            if "results" in event:
                clean["results"] = []
                for hit in event["results"]:
                    item = {k: v for k, v in hit.items() if k != "text"}
                    item["text_sha256"] = digest(hit["text"])
                    item["text_length"] = len(hit["text"])
                    clean["results"].append(item)
            row["events"].append(clean)
        public.append(row)
    DEST.mkdir(parents=True, exist_ok=True)
    (DEST / name).write_text(json.dumps(public, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(f"Exported {len(RUNS)} redacted agent runs to {DEST}")
