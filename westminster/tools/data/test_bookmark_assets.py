"""Keep generated-art requirements in release checks, not source-checkout tests."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ui"))
from check_bookmark_assets import missing_assets


class BookmarkAssets(unittest.TestCase):
    def make_bookmark(self, folder):
        mod = Path(folder)
        source = mod / "common/bookmarks/bookmarks/example.txt"
        source.parent.mkdir(parents=True)
        source.write_text('bm_test = { character = { name = "bookmark_test_mp" } }')
        return mod

    def test_release_rejects_missing_map_and_character_highlight(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(
                missing_assets(self.make_bookmark(folder)),
                [
                    "gfx/interface/bookmarks/bm_test.dds",
                    "gfx/interface/bookmarks/bm_test_bookmark_test_mp.dds",
                ],
            )

    def test_release_requires_each_featured_highlight(self):
        with tempfile.TemporaryDirectory() as folder:
            mod = self.make_bookmark(folder)
            art = mod / "gfx/interface/bookmarks"
            art.mkdir(parents=True)
            (art / "bm_test.dds").touch()
            self.assertEqual(
                missing_assets(mod),
                ["gfx/interface/bookmarks/bm_test_bookmark_test_mp.dds"],
            )
            (art / "bm_test_bookmark_test_mp.dds").touch()
            self.assertEqual(missing_assets(mod), [])


if __name__ == "__main__":
    unittest.main()
