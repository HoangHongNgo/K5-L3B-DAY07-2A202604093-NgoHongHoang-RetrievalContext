"""Treat the already inspected Day 6 test as development data; hold out new Day 7 test."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ID = "taiwan-tourism-guide-2020"


def case(id, split, question, answer, page=None, evidence=None):
    return {"id": id, "split": split, "question": question,
            "expected_answer": answer,
            "gold": [] if page is None else [{"source_id": SOURCE_ID, "page": page, "evidence": evidence}]}


raw = json.loads((ROOT / "data/day6_questions.json").read_text(encoding="utf-8"))["questions"]
questions = []
for q in raw:
    gold = q.get("gold_evidence") or [{"source_id": q["gold_source_id"],
                                      "page": q["gold_page"], "evidence_quote": q["evidence_quote"]}]
    questions.append({"id": q["id"], "split": "dev", "question": q["question"],
                      "expected_answer": q["expected_answer"],
                      "gold": [{"source_id": g["source_id"], "page": g["page"],
                                "evidence": g["evidence_quote"]} for g in gold]})

questions += [
    case("dev_abs_1", "dev", "How many people attended the 2025 Taiwan Lantern Festival?",
         "Insufficient evidence in the 2020 guide."),
    case("dev_abs_2", "dev", "What was Orchid Island's hotel occupancy rate in 2024?",
         "Insufficient evidence in the 2020 guide."),
    case("test_1", "test", "What outbreak inspired the Yanshui Beehive Rockets Festival?",
         "A cholera outbreak.", 8, "The Yanshui Beehive Rockets Festival is the legacy of a cholera outbreak"),
    case("test_2", "test", "In which months does the Formosa Summer Festival run?",
         "June to September.", 11, "June to September"),
    case("test_3", "test", "Which indigenous people are associated with millet mochi?",
         "The Amis people.", 16, "Millet mochi is one of the best-known tra -\nditional snacks of the Amis indigenous people."),
    case("test_4", "test", "How many stages does Yunlong Waterfall descend in?",
         "Three stages.", 25, "The hanging\nvalley waterfall descends straight\nfrom the cliff in three stages"),
    case("test_5", "test", "What do goats symbolize in the Yami tribe?",
         "Property.", 35, "Goats, a symbol of property in the Yami tribe"),
    case("test_abs_1", "test", "What is the 2026 high-speed rail fare from Taipei to Kaohsiung?",
         "Insufficient evidence in the 2020 guide."),
    case("test_abs_2", "test", "Who won the Taipei International Marathon in 2025?",
         "Insufficient evidence in the 2020 guide."),
]

out = ROOT / "data/day7_questions.json"
out.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
cases = [{"id": q["id"], "split": q["split"], "answerable": bool(q["gold"])} for q in questions]
(ROOT / "data/day7_agent_cases.json").write_text(
    json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {len(questions)} questions to {out}")
