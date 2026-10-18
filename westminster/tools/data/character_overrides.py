"""Small, explicit character edits shared by all six generated starts.

Edit data/character_overrides.json; see docs/modding.md. Missing settings keep the
builder's defaults. CK3 still calculates modifiers and can change ideology in play.
"""

import json
import re
from pathlib import Path

from build_ideology import IDEO_KEYS, NOT_STATED, faith_key

SOURCE = Path(__file__).resolve().parents[2] / "data/character_overrides.json"
SKILLS = ("diplomacy", "stewardship", "martial", "intrigue", "learning", "prowess")
IDENTIFIER = re.compile(r"[a-z][a-z0-9_]*\Z")


def load_overrides(path=SOURCE):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(data) != {"characters"} or not isinstance(data["characters"], dict):
        raise ValueError(f"{path}: expected a 'characters' object")
    for character, settings in data["characters"].items():
        if not IDENTIFIER.fullmatch(character) or not isinstance(settings, dict):
            raise ValueError(f"{path}: invalid character entry {character!r}")
        unknown = set(settings) - {"skills", "traits", "ideology", "dna", "notes"}
        if unknown:
            raise ValueError(f"{character}: unknown fields {sorted(unknown)}")
        if "ideology" in settings and settings["ideology"] not in [
            *IDEO_KEYS,
            NOT_STATED,
        ]:
            raise ValueError(f"{character}: unknown ideology {settings['ideology']!r}")
        skills = settings.get("skills", {})
        if not isinstance(skills, dict):
            raise ValueError(f"{character}: skills must be an object")
        for skill, value in skills.items():
            if skill not in SKILLS or type(value) is not int or not 0 <= value <= 100:
                raise ValueError(
                    f"{character}: {skill} must be a CK3 skill from 0 to 100"
                )
        traits = settings.get("traits", [])
        if not isinstance(traits, list) or any(
            not isinstance(trait, str) or not IDENTIFIER.fullmatch(trait)
            for trait in traits
        ):
            raise ValueError(f"{character}: traits must be a list of CK3 identifiers")
        if "dna" in settings and (
            not isinstance(settings["dna"], str)
            or not IDENTIFIER.fullmatch(settings["dna"])
        ):
            raise ValueError(f"{character}: dna must name a DNA entry")
    return data["characters"]


OVERRIDES = load_overrides()


def ideology_for(character, default):
    return OVERRIDES.get(character, {}).get("ideology", default)


def faith_for(character, default):
    settings = OVERRIDES.get(character, {})
    return faith_key(settings["ideology"]) if "ideology" in settings else default


def dna_for(character, default=None):
    return OVERRIDES.get(character, {}).get("dna", default)


def extra_history_lines(character):
    settings = OVERRIDES.get(character, {})
    lines = [
        f"\t{skill} = {value}" for skill, value in settings.get("skills", {}).items()
    ]
    lines.extend(f"\ttrait = {trait}" for trait in settings.get("traits", []))
    return lines


def history_lines(character, default_faith, default_dna=None):
    """Return top-level CK3 character-history fields; traits are additive."""
    lines = [f"\treligion = {faith_for(character, default_faith)}"]
    dna = dna_for(character, default_dna)
    if dna:
        lines.append(f"\tdna = {dna}")
    return lines + extra_history_lines(character)
