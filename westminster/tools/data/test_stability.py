"""Regression checks for startup failures found in the October stability audit.

    .venv/bin/python westminster/tools/data/test_stability.py
"""
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import build_game_start as startup

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common/tools"))
from ck3_checks import static  # noqa: E402


class StartupRegressionTests(unittest.TestCase):
    def test_old_map_provinces_are_removed_even_when_ids_overlap(self):
        src = "province:1 = { set_variable = { name = old_temple value = yes } }\nset_global_variable = { name = keep value = yes }\n"
        result = startup.clean(src, set(), [0])
        self.assertNotIn("old_temple", result)
        self.assertIn("name = keep", result)

    def test_unavailable_named_characters_and_region_loops_are_removed(self):
        src = "character:missing_medieval_king = { add_character_flag = old }\nevery_county_in_region = { region = world_steppe add_county_modifier = old }\ncharacter:wm_test = { add_character_flag = keep }\n"
        result = startup.clean(src, {"wm_test"}, [0])
        self.assertNotIn("missing_medieval_king", result)
        self.assertNotIn("world_steppe", result)
        self.assertIn("add_character_flag = keep", result)

    def check_localization(self, text):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "localization/english/example_l_english.yml"
            p.parent.mkdir(parents=True)
            p.write_text(text, encoding="utf-8-sig")
            with contextlib.redirect_stdout(io.StringIO()):
                return static(folder)

    def test_duplicate_keys_in_one_file_fail_release_checks(self):
        self.assertFalse(self.check_localization('l_english:\n same: "One"\n same: "Two"\n'))

    def test_physical_newlines_fail_but_escaped_newlines_pass(self):
        self.assertFalse(self.check_localization('l_english:\n desc: "First\nSecond"\n'))
        self.assertTrue(self.check_localization('l_english:\n desc: "First\\nSecond"\n'))


if __name__ == "__main__":
    unittest.main()
