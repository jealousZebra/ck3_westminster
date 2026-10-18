#!/usr/bin/env python3
"""Character authoring checks; no CK3 installation or network required."""
import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import character_overrides as custom
from pdx_script import get, parse

MOD = Path(__file__).resolve().parents[2] / "westminster"


class CharacterOverrides(unittest.TestCase):
    def load(self, settings):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "characters.json"
            path.write_text(json.dumps({"characters": {"wm_test": settings}}))
            return custom.load_overrides(path)

    def test_missing_override_preserves_defaults(self):
        with patch.dict(custom.OVERRIDES, {}, clear=True):
            self.assertEqual(custom.ideology_for("wm_test", "liberal"), "liberal")
            self.assertEqual(
                custom.history_lines("wm_test", "wm_ideo_liberal"),
                ["\treligion = wm_ideo_liberal"],
            )

    def test_custom_fields_render_as_ck3_history(self):
        settings = self.load(
            {
                "skills": {"diplomacy": 16},
                "traits": ["diligent"],
                "ideology": "social_democrat",
                "dna": "wm_dna_custom",
            }
        )
        with patch.dict(custom.OVERRIDES, settings, clear=True):
            body = parse(
                "wm_test = {\n"
                + "\n".join(
                    custom.history_lines("wm_test", "wm_ideo_liberal", "wm_dna_old")
                )
                + "\n}"
            )
            character = get(body, "wm_test")
            self.assertEqual(get(character, "religion"), "wm_ideo_social_democrat")
            self.assertEqual(get(character, "dna"), "wm_dna_custom")
            self.assertEqual(get(character, "diplomacy"), "16")
            self.assertEqual(get(character, "trait"), "diligent")

    def test_typos_and_script_injection_fail_before_generation(self):
        for settings in [
            {"charisma": 12},
            {"skills": {"diplomacy": True}},
            {"skills": {"learning": -1}},
            {"traits": "diligent"},
            {"dna": "wm_dna_bad }"},
            {"ideology": "social_democratt"},
        ]:
            with self.subTest(settings=settings), self.assertRaises(ValueError):
                self.load(settings)

    def test_configured_ids_and_references_exist(self):
        history = "\n".join(
            p.read_text(encoding="utf-8-sig")
            for p in (MOD / "history/characters").glob("wm_*_mps.txt")
        )
        ids = set(re.findall(r"^(wm_\w+)\s*=\s*\{", history, re.M))
        dna = "\n".join(
            p.read_text(encoding="utf-8-sig")
            for p in (MOD / "common/dna_data").glob("*.txt")
        )
        dna_ids = set(re.findall(r"^(\w+)\s*=\s*\{", dna, re.M))
        for character, settings in custom.OVERRIDES.items():
            self.assertIn(
                character, ids, "Unknown character override; check the history ID"
            )
            if "dna" in settings:
                self.assertIn(settings["dna"], dna_ids)


if __name__ == "__main__":
    unittest.main()
