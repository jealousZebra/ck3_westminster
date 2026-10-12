#!/usr/bin/env python3
"""The faith window as an ideology view (PLAN.md, "Ideology replaces religion"): vanilla's gui/window_faith.gui with
its medieval parts hidden. Westminster's ideologies each have one rite, no head of faith, no holy orders and no
sins or virtues, and players can't found or reform one (tools/data/build_ideology.py switches rite creation and
editing off in the scripted rules; the buttons are hidden here too).

    .venv/bin/python westminster/tools/ui/build_faith_view.py       (run by build_ui.sh, after build_theme.py)

Hidden:
  - the rite status under the name ("Mainline Rite"), the "No Branched Rites" line, the head-of-faith doctrine icon
    and the challenger (antipope) button; the strip they sit in shows only for another ideology (how far apart we
    are) and no longer for your own ("Spiritual Fulfillment" and personal beliefs, driven by sins and virtues);
  - the tab row: Holy Orders, and Holy Sites (Heartlands; Westminster has none), leaving only Beliefs;
  - the Movement Leader (head of faith) slot when there is none, which in Westminster is always;
  - the Sins / Virtues strip;
  - the Modify / Reform Rite and Create Rite buttons;
  - in Ideology Details: the Saints tab, the "1 Rite" count, the "Mainline Rite" line of each rite, and the Causes
    tab's "Unknown" group: vanilla's 97 medieval tenets, which no ideology holds (a tenet's visible = no doesn't
    keep them out of that list). Other ideologies' causes show there once known.
The picture behind the leaders is the scene list religion_interior (tools/ui/build_illustrations.py); the words are
tools/ui/build_terms.py's.

Writes westminster/gui/window_faith.gui (whole-file override of vanilla's, with build_theme.py's glow pass applied
too; re-run after a game update).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent          # westminster/
MOD = ROOT / "westminster"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME, game_version  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)
GUI = "gui/window_faith.gui"
VERSION_TAG = ("# Westminster: Crusader Kings III's own gui/window_faith.gui (Paradox Interactive), with its dark text "
               "glows made transparent and its medieval parts hidden, by westminster/tools/ui/build_faith_view.py - "
               "edit there. Game version ")
DARK_GLOW = re.compile(r"glow_color:\{ ?0(\.[0-9]+)?, ?0(\.[0-9]+)?, ?0(\.[0-9]+)?, ?[01](\.[0-9]+)? ?\}")   # as build_theme.py
NOTE = "\t# Westminster (build_faith_view.py)"

# (what, pattern, replacement): each pattern must match exactly once in vanilla's file
PATCHES = [
    ("'Adopt This Ideology' (vanilla conversion skips the party wing and party fit): the Change Your Politics decision instead",
     r'visible = "\[FaithWindow\.ConvertButtonIsShown\]"',
     r'visible = no' + NOTE),
    ("rite status line: hidden children take no space",
     r'(\n(\t+)hbox = \{\n\t+layoutpolicy_horizontal = expanding\n\t+spacing = 8\n\t+margin_left = 1\n)',
     r'\1\2\tignoreinvisible = yes\n'),
    ("rite status ('Mainline Rite') under the name",
     r'using = Visible_Rite_Not_Heresy(\n\t+max_width = 180\n\t+text = "FAITH_VIEW_RITE_STATUS")',
     r'visible = no' + NOTE + r'\1'),
    ("divider before 'Your Ideology'",
     r'(visible = "\[IsPlayerRite\]"\n\t+spacing = 8\n\n(\t+)divider_light = \{\n)',
     r'\1\2\tvisible = no' + NOTE + r'\n'),
    ("window body: hidden parts take no space",
     r'(### Top Section \(Above Tabs\)\n(\t+)vbox = \{\n)', r'\1\2\tignoreinvisible = yes\n'),
    ("tab row (Beliefs, Holy Orders, Holy Sites): only Beliefs has anything to show",
     r'(\n(\t+)name = "tabs"\n)', r'\1\2visible = no' + NOTE + r': no holy orders or heartlands\n'),
    ("Holy Orders tab",
     r'shortcut = "tab_2"(\n\t+onclick = "\[FaithWindow\.SetActiveTab\( \'tab_holy_orders\' \)\]")',
     r'visible = no' + NOTE + r': no holy orders\1'),
    ("Holy Sites (Heartlands) tab's shortcut",
     r'shortcut = "tab_3"(\n\t+onclick = "\[FaithWindow\.SetActiveTab\( \'tab_holy_sites\' \)\]")',
     r'visible = no' + NOTE + r': no heartlands\1'),
    ("beliefs tab: hidden parts take no space",
     r'(\n(\t+)name = "tab_beliefs"\n)', r'\1\2ignoreinvisible = yes\n'),
    ("backdrop area: hidden parts take no space",
     r'(\n(\t+)datacontext = "\[GetIllustration\( \'religion_interior\' \)\]"\n)', r'\1\2ignoreinvisible = yes\n'),
    ("strip of divergence and opinion: another ideology only",
     r'(### Divergence and opinion\n(\t+)hbox = \{\n)',
     r'\1\2\tvisible = "[Not( ObjectsEqual( GetPlayer.GetFaith, Faith.Self ) )]"' + NOTE
     + r': how far apart we are; nothing for your own\n'),
    ("'No Branched Rites' and the challenger button",
     r'(# Main Rite\n\t+hbox = \{\n\t+)visible = "\[Rite\.IsMain\]"', r'\1visible = no' + NOTE),
    ("head of faith doctrine icon",
     r'(### Head of Faith Doctrine\n(\t+)flowcontainer = \{\n)', r'\1\2\tvisible = no' + NOTE + r'\n'),
    ("leaders row: hidden slots take no space",
     r'(\n(\t+)hbox = \{\n\t+spacing = 20\n\t+# HoF\n)', r'\1\2\tignoreinvisible = yes\n'),
    ("Movement Leader slot only when there is one (never, in Westminster)",
     r'visible = "\[(Or\( Rite\.IsMain, EqualTo_int32\( PdxGuiWidget\.AccessParent\.AccessParent\.FindChild\(\'items\'\)'
     r'\.CountVisibleChildren, \'\(int32\)0\'\) \))\]"',
     r'visible = "[And( Character.IsValid, \1 )]"' + NOTE + r': no empty Movement Leader slot'),
    ("Sins / Virtues strip",
     r'(### Sins & Virtues\n\t+)widget_sins_virtues = \{\}', r'\1widget_sins_virtues = { visible = no }' + NOTE),
    ("action buttons: hidden ones take no space",
     r'(\n(\t+)name = "actions"\n)', r'\1\2ignoreinvisible = yes\n'),
    ("Modify / Reform Rite button",
     r'(name = "edit_rite"\n\t+)visible = "\[FaithWindow\.CanEditRite\]"', r'\1visible = no' + NOTE),
    ("Create Rite button",
     r'(name = "create_rite"\n\t+)visible = "[^"\n]*"', r'\1visible = no' + NOTE),
    ("Create Rite button (puppet)",
     r'(name = "create_rite_puppet"\n\t+)visible = "[^"\n]*"', r'\1visible = no' + NOTE),
    ("Ideology Details: Saints tab",
     r'\n(\t+)oncreate = "\[PdxGuiTabs\.AddTab\( \'saints\' \)\]"', r'\n\1# no Saints tab' + NOTE),
    ("Ideology Details, Causes: no 'Unknown' group (vanilla's medieval tenets, which no ideology holds)",
     r'(\n(\t+)datamodel = "\[FaithWindow\.GetTenetGroupItems\]"\n\t+item = \{\n\t+)vbox_tenet_group_foldout = \{\}',
     r'\2ignoreinvisible = yes\1vbox_tenet_group_foldout = {\n\2\t\tvisible = "[Not( EqualTo_string( TenetGroupItem.GetGroupTitle, '
     "Localize( 'TENET_GROUP_ITEM_UNKNOWN' ) ) )]\"" + NOTE + r'\n\2\t}'),
    ("Ideology Details: '1 Rite' count",
     r'(\n(\t+)text = "FAITH_VIEW_RITE_LIST_NUMBER_OF_RITES")', r'\n\2visible = no' + NOTE + r'\1'),
    ("Ideology Details: 'Mainline Rite' line",
     r'(# Main rite\n\t+text_single = \{\n\t+)visible = "\[Rite\.IsMain\]"', r'\1visible = no' + NOTE),
]


def patch(src):
    for what, pat, rep in PATCHES:
        src, n = re.subn(pat, rep, src)
        if n != 1:
            sys.exit("window_faith.gui: %s: pattern matched %d times (game update?)" % (what, n))
    return src


def main():
    src = (GAME / GUI).read_text(encoding="utf-8-sig")
    src = patch(DARK_GLOW.sub("glow_color:{0,0,0,0}", src))
    dest = MOD / GUI
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(VERSION_TAG + game_version() + "\n" + src, encoding="utf-8-sig")
    print("wrote", dest.relative_to(ROOT.parent), "(%d changes)" % len(PATCHES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
