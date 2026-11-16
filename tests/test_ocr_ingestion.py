"""Mixed PDF-text/image pages must retain OCR-only evidence."""
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from src.day6.ingestion import load_pdf, novel_ocr_text


class FakePage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class OcrIngestionTests(unittest.TestCase):
    def test_mixed_page_keeps_only_novel_ocr_lines(self):
        reader = SimpleNamespace(pages=[FakePage("Hotel National is in Taichung.")])
        with patch("src.day6.ingestion.PdfReader", return_value=reader), patch(
            "src.day6.ingestion.ocr_page",
            return_value="Hotel National is in Taichung.\nIt has 178 deluxe guest rooms.",
        ):
            pages = load_pdf(Path("unused.pdf"), "doc", "source")
        self.assertEqual([p.metadata["extraction_method"] for p in pages],
                         ["pdf_text", "ocr_overlay"])
        self.assertEqual(pages[1].text, "It has 178 deluxe guest rooms.")
        self.assertEqual([p.page for p in pages], [1, 1])

    def test_image_only_page_keeps_ocr_as_primary_text(self):
        reader = SimpleNamespace(pages=[FakePage("")])
        with patch("src.day6.ingestion.PdfReader", return_value=reader), patch(
            "src.day6.ingestion.ocr_page", return_value="Emperor Hotel",
        ):
            pages = load_pdf(Path("unused.pdf"), "doc", "source")
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0].metadata["extraction_method"], "ocr")
        self.assertEqual(novel_ocr_text("Hotel National", "Hotel National"), "")


if __name__ == "__main__":
    unittest.main()
