from hashlib import sha256
from pathlib import Path, PurePosixPath
import tempfile
from types import SimpleNamespace
import unittest
from email.message import Message

from tools.export_dependency_notices import collect_notices


class NoticeTests(unittest.TestCase):
    def test_original_notices_and_pins_are_bound_without_including_other_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            relative = PurePosixPath("example-1.dist-info/licenses/LICENSE")
            (root / relative).parent.mkdir(parents=True)
            raw = b"Example original copyright and permission.  \r\nSecond line.\t\r\n"
            (root / relative).write_bytes(raw)
            metadata = Message()
            metadata["License-Expression"] = "MIT"
            dist = SimpleNamespace(version="1", metadata=metadata,
                                   files=[relative, PurePosixPath("example/private.txt")],
                                   locate_file=lambda path: root / path)
            text, manifest = collect_notices("example==1\n", lambda name: dist)
            self.assertIn("Example original copyright and permission.\nSecond line.\n", text)
            self.assertNotIn("\r", text)
            self.assertTrue(all(line == line.rstrip() for line in text.splitlines()))
            self.assertNotIn("private.txt", text)
            self.assertEqual(manifest["packages"][0]["notice_files"][0]["sha256"], sha256(raw).hexdigest())
            self.assertEqual(manifest["notices_sha256"], sha256(text.encode()).hexdigest())
            with self.assertRaisesRegex(ValueError, "version differs"):
                collect_notices("example==2", lambda name: dist)
            dist.files = []
            with self.assertRaisesRegex(ValueError, "No installed notice"):
                collect_notices("example==1", lambda name: dist)


if __name__ == "__main__":
    unittest.main()
