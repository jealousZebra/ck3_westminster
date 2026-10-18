#!/usr/bin/env python3
"""Cross-file audits for playable starts, dated governments, identities and portrait caches."""
import json, re, unittest
from pathlib import Path
from era_definitions import ERAS
from build_1979 import norm

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "westminster"


class Eras(unittest.TestCase):
    def test_new_localization_scope_access(self):
        for name in ["movement", "press", "governing"]:
            text = (MOD / f"localization/english/wm_{name}_l_english.yml").read_text(
                encoding="utf-8-sig"
            )
            self.assertNotIn("ROOT.Char.Var(", text)

    def test_event_identifiers(self):
        for stem in ["wm_governing", "wm_movement"]:
            text = (MOD / f"events/{stem}_events.txt").read_text(encoding="utf-8-sig")
            self.assertNotRegex(text, r"(?m)^['\"]wm_")

    def test_map_and_government(self):
        county = set(
            re.findall(
                r"^c_\w+(?= = \{)",
                (MOD / "history/titles/wm_2024_seats.txt").read_text(
                    encoding="utf-8-sig"
                ),
                re.M,
            )
        )
        history = (MOD / "history/titles/wm_2024_seats.txt").read_text(
            encoding="utf-8-sig"
        )
        for year, cfg in ERAS.items():
            with self.subTest(year=year):
                a = json.loads((ROOT / f"data/snapshots/{year}.json").read_text())[
                    "members"
                ]
                landed = [m for m in a if m["seat"]]
                self.assertEqual(len(landed), 650)
                self.assertEqual({"c_" + m["seat"] for m in landed}, county)
                self.assertEqual(len({m["id"] for m in a}), len(a))
                pm = next(m for m in a if m["name"] == cfg["pm"])
                self.assertTrue(pm["seat"])
                self.assertEqual(pm["party"], cfg["party"])
                self.assertTrue(
                    f'{cfg["date"]} = {{\n\t\tholder = {pm["id"]}' in history,
                    f"Missing {year} PM history",
                )
                for m in a:
                    self.assertLess(int(m["birth"].split(".")[0]), year - 17)

    def test_every_history_dna_exists(self):
        dna = set(
            re.findall(
                r"^(wm_dna_\w+) =",
                (MOD / "common/dna_data/wm_likenesses_dna.txt").read_text(
                    encoding="utf-8-sig"
                ),
                re.M,
            )
        )
        for year in ERAS:
            text = (MOD / f"history/characters/wm_{year}_mps.txt").read_text(
                encoding="utf-8-sig"
            )
            self.assertFalse(set(re.findall(r"dna = (wm_dna_\w+)", text)) - dna)

    def test_every_featured_character_has_cache(self):
        for year, cfg in ERAS.items():
            for name in cfg["featured"]:
                key = f"bookmark_{year}_" + norm(name)
                self.assertTrue(
                    (MOD / f"common/bookmark_portraits/{key}.txt").exists(), key
                )
                self.assertTrue(
                    (
                        MOD
                        / f'gfx/interface/bookmarks/bm_{year}_{cfg["slug"]}_{key}.dds'
                    ).exists(),
                    key,
                )

    def test_portrait_caches_include_engine_rendering_data(self):
        for path in (MOD / "common/bookmark_portraits").glob("bookmark_*.txt"):
            with self.subTest(portrait=path.name):
                text = path.read_text(encoding="utf-8-sig")
                self.assertRegex(text, r"entity\s*=\s*\{")
                self.assertRegex(text, r"tags\s*=\s*\{")
                for gene in ["hairstyles", "beards"]:
                    match = re.search(gene + r'=\{\s*"([^"]+)"', text)
                    if match:
                        self.assertFalse(
                            match[1].startswith(
                                ("male_hair_", "female_hair_", "male_beard_")
                            ),
                            match[1],
                        )

    def test_dated_sources(self):
        records = json.loads((ROOT / "data/members_1945_affiliations.json").read_text())
        self.assertEqual(len(records["members"]), 640)
        self.assertTrue(records["source"].startswith("https://"))

    def test_each_start_has_lean_effect(self):
        for year in ERAS:
            text = (
                MOD / f"common/scripted_effects/wm_{year}_seat_leans.txt"
            ).read_text(encoding="utf-8-sig")
            self.assertEqual(len(re.findall(r"title:c_", text)), 650)


if __name__ == "__main__":
    unittest.main()
