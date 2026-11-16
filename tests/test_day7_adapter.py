"""Check the real-model HTTP adapter's protocol without reporting mock quality."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.day7_agent import ChatController


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class AdapterTests(unittest.TestCase):
    def test_search_tool_and_cited_answer(self):
        cid = "a" * 64
        replies = [
            {"choices": [{"message": {"tool_calls": [{"function": {
                "name": "search", "arguments": '{"query":"Yanshui cholera"}'}}]}}],
             "usage": {"total_tokens": 20}},
            {"choices": [{"message": {"content": f"Cholera [{cid} | page 8]"}}],
             "usage": {"total_tokens": 30}},
        ]
        requests = []

        def fake_open(request, timeout):
            requests.append(json.loads(request.data))
            return Response(json.dumps(replies[len(requests) - 1]).encode("utf-8"))

        controller = ChatController("model", "http://localhost:1234/v1", None)
        with patch("urllib.request.urlopen", side_effect=fake_open):
            search = controller.decide("What caused the festival?", [])
            answer = controller.decide("What caused the festival?", [{"context": f"[{cid}] cholera"}])
        self.assertEqual(search, {"action": "search", "query": "Yanshui cholera"})
        self.assertEqual(answer["citations"], [cid])
        self.assertEqual(answer["answer"], f"Cholera [{cid}]")
        self.assertEqual(requests[0]["tools"][0]["function"]["name"], "search")
        self.assertEqual(len(controller.calls), 2)


if __name__ == "__main__":
    unittest.main()
