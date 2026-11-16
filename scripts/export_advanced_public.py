"""Export advanced agent traces without redistributing PDF excerpts or credentials."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/advanced"
SOURCES = {
    "pilot_test": ROOT / ".local/advanced_pilot_test_traces.json",
    "dev": ROOT / "starter/results/advanced/dev/agent-k3-b10000/traces.json",
    "test": ROOT / "starter/results/advanced/test/agent-k3-b10000/traces.json",
}


def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def redact(trace):
    row = {k: v for k, v in trace.items() if k not in {"events", "model_calls"}}
    row["model_calls"] = [{k: v for k, v in call.items() if k != "tool_calls"}
                          for call in trace["model_calls"]]
    row["events"] = []
    for event in trace["events"]:
        clean = {k: v for k, v in event.items() if k not in {"results", "context", "attempted_answer"}}
        if "context" in event:
            clean["context_sha256"] = digest(event["context"])
            clean["context_length"] = len(event["context"])
        if "attempted_answer" in event:
            clean["attempted_answer_sha256"] = digest(event["attempted_answer"])
        if "results" in event:
            clean["results"] = []
            for hit in event["results"]:
                item = {k: v for k, v in hit.items() if k != "text"}
                item["text_sha256"] = digest(hit["text"])
                item["text_length"] = len(hit["text"])
                clean["results"].append(item)
        row["events"].append(clean)
    return row


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, source in SOURCES.items():
        traces = json.loads(source.read_text(encoding="utf-8"))
        (OUT / f"{name}_traces_public.json").write_text(
            json.dumps([redact(t) for t in traces], ensure_ascii=False, indent=2)+"\n",
            encoding="utf-8")
        print(name, len(traces))


if __name__ == "__main__":
    main()
