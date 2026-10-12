#!/usr/bin/env python3
"""Parties instead of families in the UI: a character's house is their party (tools/data/build_2024.py), so

  1. names never show the house: every name format in vanilla's character_l_english.yml loses $HOUSE$, $DYNASTY$ and
     $PATRONYM$ (characters carry their whole name as their first name, "Keir Starmer"; a format that showed only the
     house, such as "$TIER$ $HOUSE$", shows the name instead);
  2. the character window's Family tab becomes "Colleagues": it lists the character's fellow party members (the
     living members of their house) instead of relatives, and its count is the party's size;
  3. the House and Dynasty concepts read "Party".

    .venv/bin/python westminster/tools/ui/build_colleagues.py        (run by build_ui.sh, after build_theme.py)

Writes:
  westminster/gui/window_character.gui      vanilla's, patched (whole-file override; re-run after a game update)
  westminster/localization/english/replace/wm_colleagues_l_english.yml

Keys that another mod localization file already defines are skipped (build_terms.py does the same in reverse).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent          # westminster/
MOD = ROOT / "westminster"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME, game_version  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)
GUI = "gui/window_character.gui"
LOC_OUT = MOD / "localization/english/replace/wm_colleagues_l_english.yml"
VERSION_TAG = ("# Westminster: Crusader Kings III's own gui/window_character.gui (Paradox Interactive), changed by "
               "westminster/tools/ui/build_colleagues.py - edit there. Game version ")
DARK_GLOW = re.compile(r"glow_color:\{ ?0(\.[0-9]+)?, ?0(\.[0-9]+)?, ?0(\.[0-9]+)?, ?[01](\.[0-9]+)? ?\}")   # as build_theme.py

LABELS = {
    "CV_TAB_FAMILY": "Colleagues",
    "WM_COLLEAGUES_HEADING": "Colleagues in the [Character.GetHouse.GetBaseNameNoTooltip] ([GetDataModelSize( Character.GetHouse.GetAliveMembers )|0])",
    "WM_COLLEAGUES_NONE": "No party, no colleagues",
    "DYNASTY": "Party",
    "DYNASTY_HOUSE": "Party",
    "game_concept_house": "Party",
    "game_concept_houses": "Parties",
    "game_concept_house_head": "Party Leader",
    "game_concept_dynasty": "Party",
    "game_concept_dynasties": "Parties",
    "game_concept_dynast": "Party Leader",
    "game_concept_house_desc": "A $game_concept_house$ is a political party. Every member of a party belongs to it, and its emblem is their shield.\n\nYou can cross the floor to another party, or found your own, with a [decision|E].",
    "game_concept_dynasty_desc": "A $game_concept_dynasty$ is a political party: its members are colleagues, not relatives. Each party has one [house|E], led by the party's leader.",
    "game_concept_house_head_desc": "The $game_concept_house_head$ heads a [house|E]: the party's members answer to them.",
    "game_concept_dynast_desc": "The $game_concept_dynast$ heads a [dynasty|E]: in Westminster, the party's leader.",
}

# The family tab's views, hidden: the colleagues list takes their place
FAMILY_VIEWS = ["family_main_view", "family_siblings_expanded", "family_children_expanded", "family_concubines_expanded"]

COLLEAGUES = '''
				### WESTMINSTER: COLLEAGUES (build_colleagues.py): fellow members of the character's party, which is their house.
				### At most 42 portraits; the party's shield opens the full list.
				scrollbox = {
					name = "wm_colleagues"
					visible = "[Character.GetHouse.IsValid]"
					size = { 100% 100% }

					blockoverride "scrollbox_replace_vbox" {
						vbox_character_row_item = {
							name = "wm_colleagues_row"
							margin_top = 10
							spacing = 5

							blockoverride "portrait_datamodel" {
								datamodel = "[DataModelFirst( Character.GetHouse.GetAliveMembers, '(int32)42' )]"
							}

							blockoverride "header_text"
							{
								text = "WM_COLLEAGUES_HEADING"
							}

							blockoverride "expand_button" {}

							blockoverride "gridbox_slots" {}
						}
					}
				}

				text_single = {
					name = "wm_colleagues_none"
					visible = "[Not( Character.GetHouse.IsValid )]"
					parentanchor = center
					text = "WM_COLLEAGUES_NONE"
					default_format = "#low"
				}
'''


def parse_yml(path):
    out = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r'^ ([A-Za-z0-9_.\-]+):\d* "(.*)"\s*$', line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def mod_keys():
    keys = {}
    for p in sorted((MOD / "localization").rglob("*.yml")):
        if p == LOC_OUT:
            continue
        for k, _ in parse_yml(p):
            keys.setdefault(k, p.relative_to(MOD).as_posix())
    return keys


TOKENS = re.compile(r"\$(HOUSE|DYNASTY|PATRONYM)\$")


def name_formats():
    """Vanilla's name formats without the house, dynasty or patronym."""
    out = {}
    for k, v in parse_yml(GAME / "localization/english/character_l_english.yml"):
        if not TOKENS.search(v):
            continue
        rest = TOKENS.sub("", v)
        if not re.search(r"\$[A-Z_]+\$", rest):
            continue                                    # a format for the token itself (FORMAT_CHARACTER_HOUSE)
        if "$NAME$" not in rest:
            new = TOKENS.sub("$NAME$", v, count=1)      # "$TIER$ $HOUSE$" names the character instead
            new = TOKENS.sub("", new)
        else:
            new = rest
        new = re.sub(r" {2,}", " ", new).strip()
        new = new.replace("#high #!", "")
        out[k] = new
    return out


def patch_gui():
    dest = MOD / GUI
    src = (GAME / GUI).read_text(encoding="utf-8-sig")
    src = DARK_GLOW.sub("glow_color:{0,0,0,0}", src)    # as build_theme.py's glow pass would, if it copies this file
    for view in FAMILY_VIEWS:
        pat = re.compile(r'(name = "%s"\s*\n\s*)visible = "[^"\n]*"' % view)
        src, n = pat.subn(r"\1visible = no\t# Westminster: replaced by the colleagues list", src)
        assert n == 1, (view, n)
    pat = re.compile(r'(\n(\t+)widget = \{\n\t+name = "family"\n(?:[^\n]*\n){1,6}?\t+using = Animation_Tab_Switch\n)')
    src, n = pat.subn(lambda m: m.group(1) + COLLEAGUES, src, count=1)
    assert n == 1, "family widget not found"
    old = "text = \"[CharacterWindow.GetTabItemsCount('family')]\""
    assert src.count(old) == 1, "family tab count not found"
    src = src.replace(old, "visible = \"[Character.GetHouse.IsValid]\"\n\t\t\t\t\t\ttext = \"[GetDataModelSize( Character.GetHouse.GetAliveMembers )]\"")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(VERSION_TAG + game_version() + "\n" + src, encoding="utf-8-sig")
    return dest


def main():
    taken = mod_keys()
    lines = ["l_english:", " # Generated by westminster/tools/ui/build_colleagues.py - edit there.",
             " # Name formats without the house (a character's house is their party; names are whole names)"]
    skipped = []
    for group in (name_formats(), LABELS):
        for k, v in group.items():
            if k in taken:
                skipped.append("%s (%s)" % (k, taken[k]))
                continue
            lines.append(' %s: "%s"' % (k, v.replace("\n", "\\n")))
        lines.append(" # The Family tab is Colleagues; houses and dynasties are parties")
    lines.pop()
    LOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    LOC_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8-sig")
    print("wrote", LOC_OUT.relative_to(ROOT.parent), "(%d keys)" % (len(lines) - 3))
    if skipped:
        print("skipped (defined elsewhere in the mod):", ", ".join(skipped))
    print("wrote", patch_gui().relative_to(ROOT.parent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
