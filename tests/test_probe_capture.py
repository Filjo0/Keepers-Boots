import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from tools.captured_agent_server import save_response


class RawCaptureTests(unittest.TestCase):
    def test_raw_review_is_preserved_without_transport_metadata_or_overwrite(self):
        value = {"status": "insufficient_evidence", "rejected_claim_ids": [],
                 "reasons": ["No unsupported statements."]}
        response = SimpleNamespace(text=json.dumps(value), value=value,
                                   headers={"Authorization": "test-only-metadata"})
        with tempfile.TemporaryDirectory() as temporary:
            first = save_response(Path(temporary), "reviewer", response)
            original = first.read_bytes()
            second = save_response(Path(temporary), "reviewer", response)
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_bytes(), original)
            saved = json.loads(original)
            self.assertEqual(saved, {"role": "reviewer", "sequence": 1, "text": response.text, "value": value})
            self.assertNotIn("headers", saved)


if __name__ == "__main__":
    unittest.main()
