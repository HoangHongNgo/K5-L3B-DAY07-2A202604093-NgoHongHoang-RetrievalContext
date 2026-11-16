"""Publish Day 7 metrics and trace metadata without redistributing PDF excerpts."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "starter/results/day7"
DEST = ROOT / "artifacts/day7"
selection = json.loads((SOURCE / "selection.json").read_text(encoding="utf-8"))
reported = {summary["key"] for summary in selection["dev"]}

for folder in [SOURCE / "dev", SOURCE / "test"]:
    for run in folder.iterdir():
        if not run.is_dir() or run.name not in reported:
            continue
        target = DEST / folder.name / run.name
        target.mkdir(parents=True, exist_ok=True)
        summary = json.loads((run / "summary.json").read_text(encoding="utf-8"))
        traces = json.loads((run / "traces.json").read_text(encoding="utf-8"))
        public = []
        for trace in traces:
            row = {k: v for k, v in trace.items() if k not in {"results", "context"}}
            row["results"] = []
            for hit in trace["results"]:
                item = {k: v for k, v in hit.items() if k != "text"}
                item["text_sha256"] = hashlib.sha256(hit["text"].encode("utf-8")).hexdigest()
                item["text_length"] = len(hit["text"])
                row["results"].append(item)
            row["context_length"] = len(trace["context"])
            public.append(row)
        (target / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
        (target / "traces_public.json").write_text(json.dumps(public, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

DEST.mkdir(parents=True, exist_ok=True)
(DEST / "selection.json").write_text((SOURCE / "selection.json").read_text(encoding="utf-8"), encoding="utf-8")
print(f"Published redacted traces in {DEST}")
