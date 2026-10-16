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
import build_stability as stability

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common/tools"))
from ck3_checks import static  # noqa: E402


class StartupRegressionTests(unittest.TestCase):
    def test_frontend_cache_is_retained_with_bookmark_database_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            game, mod = Path(folder) / "game", Path(folder) / "mod"
            source = game / "common/bookmark_portraits/default.txt"
            source.parent.mkdir(parents=True)
            original = "default_menu_character = { type = male id = 42 genes = { } }\n"
            source.write_text(original, encoding="utf-8-sig")
            custom = mod / "common/bookmark_portraits/wm_custom.txt"
            custom.parent.mkdir(parents=True)
            custom.write_text("custom = { type = female id = 43 }", encoding="utf-8-sig")
            stability.retain_frontend_portraits(game, mod)
            output = mod / stability.FRONTEND_PORTRAITS
            self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))
            self.assertIn(original, output.read_text(encoding="utf-8-sig"))
            self.assertIn("custom =", custom.read_text(encoding="utf-8-sig"))
            # Regeneration must replace the cache, rather than append duplicates.
            stability.retain_frontend_portraits(game, mod)
            self.assertEqual(output.read_text(encoding="utf-8-sig").count(original), 1)

    @unittest.skipUnless(stability.GAME.is_dir(), "CK3 installation unavailable")
    def test_shipped_frontend_cache_covers_installed_portraits(self):
        cache = (stability.MOD / stability.FRONTEND_PORTRAITS).read_text(encoding="utf-8-sig")
        for source in (stability.GAME / "common/bookmark_portraits").glob("*.txt"):
            self.assertIn(source.read_text(encoding="utf-8-sig"), cache, source.name)

    def test_history_is_shadowed_without_replace_path(self):
        with tempfile.TemporaryDirectory() as folder:
            game, mod = Path(folder) / "game", Path(folder) / "mod"
            for rel in ("history/situations/dlc/example.txt", "history/struggles/example.txt"):
                source = game / rel
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text("1.1.1 = { effect = { start_situation = { type = old_map } } }")
            stability.disable_vanilla_history(game, mod)
            for source in game.rglob("*.txt"):
                override = mod / source.relative_to(game)
                self.assertTrue(override.is_file())
                self.assertTrue(override.read_bytes().startswith(b"\xef\xbb\xbf"))
                code = "\n".join(line.split("#", 1)[0] for line in override.read_text(encoding="utf-8-sig").splitlines())
                self.assertFalse(code.strip())

    @unittest.skipUnless(stability.GAME.is_dir(), "CK3 installation unavailable")
    def test_shipped_overrides_cover_installed_vanilla_history(self):
        for tree in stability.HISTORY_TREES:
            sources = list((stability.GAME / tree).rglob("*.txt"))
            self.assertTrue(sources, tree)
            for source in sources:
                override = stability.MOD / source.relative_to(stability.GAME)
                self.assertTrue(override.is_file(), str(override))
                code = "\n".join(line.split("#", 1)[0] for line in override.read_text(encoding="utf-8-sig").splitlines())
                self.assertFalse(code.strip(), str(override))

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
