"""Check the advanced split contract and source-aware retrieval behavior."""
import json
import unittest
from collections import Counter
from pathlib import Path

from src.advanced import AdvancedRetriever

ROOT = Path(__file__).resolve().parents[1]


class AdvancedTests(unittest.TestCase):
    def test_frozen_benchmark_has_required_held_out_groups(self):
        rows = json.loads((ROOT / "data/advanced_questions.json").read_text(encoding="utf-8"))
        self.assertEqual(len(rows), len({r["id"] for r in rows}))
        for split, answerable, absent in (("dev", 15, 3), ("test", 24, 6)):
            selected = [r for r in rows if r["split"] == split]
            self.assertEqual(sum(bool(r["gold"]) for r in selected), answerable)
            self.assertEqual(sum(not r["gold"] for r in selected), absent)
        groups = Counter(r["group"] for r in rows if r["split"] == "test")
        self.assertEqual(groups, {"table": 6, "image_diagram": 5, "chart": 5,
                                  "multi_hop": 4, "text": 4, "no_evidence": 6})
        for row in rows:
            if row["group"] == "multi_hop":
                self.assertGreaterEqual(len({g["page"] for g in row["gold"]}), 2)

    def test_named_figure_uses_content_page_and_distinct_pages(self):
        chunks = [
            {"id": "toc", "source_id": "doc", "source": "doc.pdf", "page": 10,
             "text": "Figure 2.2 economic progress", "metadata": {}},
            {"id": "figure", "source_id": "doc", "source": "doc.pdf", "page": 88,
             "text": "Figure 2.2 investment infusion innovation", "metadata": {}},
            {"id": "same-page", "source_id": "doc", "source": "doc.pdf", "page": 88,
             "text": "Figure 2.2 investment infusion", "metadata": {}},
        ]
        hits = AdvancedRetriever(chunks).search("What does Figure 2.2 show?", top_k=3)
        self.assertEqual(hits[0]["page"], 88)
        self.assertEqual(len({h["page"] for h in hits}), len(hits))


if __name__ == "__main__":
    unittest.main()
