"""Include small frontend behaviour checks in discovery when Node is available."""
from pathlib import Path
import shutil
import subprocess
import unittest


class FrontendTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is needed for frontend behaviour checks")
    def test_browser_independent_behaviour(self):
        result = subprocess.run([shutil.which("node"), "--test", "tests/test_web.mjs"],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True,
                                text=True, encoding="utf-8", timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
