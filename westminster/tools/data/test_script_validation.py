"""Source validation must handle CK3 strings/comments without an installed game."""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common/tools"))
from ck3_checks import script_braces_balanced, static


class ScriptValidation(unittest.TestCase):
    def test_comment_quotes_and_escaped_format_strings(self):
        text = '# an unmatched " in a comment\nformat = { text = "quote: \\" and { colour }" }\n'
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "format.gui").write_text(text, encoding="utf-8-sig")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(static(folder))

    def test_real_missing_brace_is_not_hidden_by_strings(self):
        self.assertFalse(script_braces_balanced('event = { text = "}" # }\n'))

    def test_closing_before_opening_is_invalid(self):
        self.assertFalse(script_braces_balanced("} {"))


if __name__ == "__main__":
    unittest.main()
