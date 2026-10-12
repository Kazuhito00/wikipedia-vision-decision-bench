# -*- coding: utf-8 -*-
"""Tests for tools/scan_secrets.py. The fake keys are built at run time so that this file itself is clean.
    uv run python -m unittest discover -s tools -p "test_*.py"
"""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import scan_secrets as S  # noqa: E402

FAKE = "s" + "k-" + "proj-" + "A1b2C3d4E5f6G7h8I9j0K1l2"      # not a real key


class Scan(unittest.TestCase):
    def test_key_is_found_and_masked(self):
        """A key-shaped string is reported, and the report never contains the key itself."""
        hits = S.scan_text("x = '%s'\n" % FAKE, "a.py")
        self.assertEqual(len(hits), 1)
        self.assertNotIn(FAKE, repr(hits))
        self.assertEqual(hits[0][:2], ("a.py", 1))

    def test_empty_assignment_is_clean(self):
        """.env.example style lines (empty value, placeholders) pass."""
        text = "OPENAI_API_KEY=\nWIKIQA_CONTACT=\nOPENAI_API_KEY=<your key>\nTOKEN=${TOKEN}\n"
        self.assertEqual(S.scan_text(text, ".env.example"), [])

    def test_filled_assignment_is_found(self):
        """A key assignment with a real-looking value is reported."""
        self.assertEqual(len(S.scan_text("OPENAI_API_KEY=" + "q" * 30, "x")), 1)

    def test_env_files_are_not_read(self):
        """.env is skipped (never opened) but .env.example is scanned."""
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            (d / ".env").write_text("OPENAI_API_KEY=" + FAKE, encoding="utf-8")
            (d / ".env.example").write_text("OPENAI_API_KEY=" + FAKE, encoding="utf-8")
            hits = S.scan_files([d / ".env", d / ".env.example"])
            self.assertEqual({h[0] for h in hits}, {str(d / ".env.example")})


if __name__ == "__main__":
    unittest.main()
