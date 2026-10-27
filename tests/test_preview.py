from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from tools.build_preview import build_preview, checked_member


class PreviewTests(unittest.TestCase):
    def test_preview_is_reproducible_labelled_and_rejects_private_or_binary_members(self):
        for name in ("../secret", "C:/private.txt", "local-artifacts/raw.json", ".env", "model.gguf", "tool.exe", "book.pdf"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                checked_member(name)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("Fictional football.\n", encoding="utf-8")
            first, second = root / "one.zip", root / "two.zip"
            manifest = build_preview(root, ["README.md"], first)
            build_preview(root, ["README.md"], second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(manifest["publication_status"], "unpublished_local_preview")
            with ZipFile(first) as archive:
                self.assertIn(b"NOT CLEARED FOR PUBLICATION", archive.read("PREVIEW_STATUS.txt"))
                self.assertEqual(archive.read("README.md"), (root / "README.md").read_bytes())
                self.assertEqual(set(archive.namelist()), {"README.md", "PREVIEW_STATUS.txt", "preview-manifest.json"})


if __name__ == "__main__":
    unittest.main()
