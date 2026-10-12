#!/usr/bin/env python3
"""Event window backdrops: every vanilla event background (throne rooms, taverns, battlefields...) shows a modern
scene instead (photos from fal_images.py).

    .venv/bin/python westminster/tools/ui/build_event_backgrounds.py

Writes common/event_backgrounds/01_event_backgrounds.txt and activity_backgrounds.txt with vanilla's background
names, so events and themes that name them keep working. Each name gets one scene, chosen by keywords in the name;
the portrait lighting (environment) of vanilla's first variant is kept.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MOD = ROOT / "westminster"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)
SRC = GAME / "common" / "event_backgrounds"

WM = "gfx/interface/illustrations/wm/"
SK = "gfx/interface/skinned/illustrations/"
# (keyword regex, scene), first match wins
SCENES = [
    (r"dungeon|prison|catacomb|gallows", SK + "dungeon.dds"),
    (r"temple|church|cathedral|holy_site|mosque|hagia|papal|pyre|funeral|runestone", WM + "church.dds"),
    (r"tavern|inn|wine_cellar|kitchen|feast|festival|bonfire|campfire", WM + "pub.dds"),
    (r"physician|nursery|bedchamber|bath|black_death|bedroom", WM + "hospital.dds"),
    (r"battlefield|army|military|siege|riot|raid|burning|harrying|camp|contest|pivotal|tournament|chariot|"
     r"hippodrome|duel|melee|joust|archery|wrestling|hunt", WM + "protest.dds"),
    (r"throne|council|investiture|coronation|ecumenical", SK + "councilchamber_bg.dds"),
    (r"study|university|examination|steward", WM + "office.dds"),
    (r"sitting_room|relaxing|estate|wedding|playdate|tent_interior", WM + "home.dds"),
    (r"ocean|docks|coast|beached|riverside|river|sea\b|village_sea", WM + "seaside.dds"),
    (r"wilderness|forest|plains|hills|mountain|terrain|steppe|drylands|wetlands|jungle|desert|farm|garden|village|"
     r"travel|winter|rice|cave|oasis|spring|bridge|survey|journey|crossroad|ruin|kennel|mews", WM + "countryside.dds"),
    (r"market|alley|courtyard|city|gate|street|settlement|constantinople|tour|corridor|armory|location", WM + "street.dds"),
]
DEFAULT = WM + "street.dds"


def blocks(text):
    """Top-level 'name = { ... }' blocks: [(name, body)]."""
    out, i = [], 0
    for m in re.finditer(r"^([a-z0-9_]+) = \{", text, re.M):
        if m.start() < i:
            continue
        depth, j = 0, m.end() - 1
        while True:
            c = text[j]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    break
            j += 1
        out.append((m.group(1), text[m.end():j]))
        i = j
    return out


def scene_for(name):
    for pat, scene in SCENES:
        if re.search(pat, name):
            return scene
    return DEFAULT


def main():
    total = 0
    for fname in ("01_event_backgrounds.txt", "activity_backgrounds.txt"):
        src = re.sub(r"#[^\n]*", "", (SRC / fname).read_text(encoding="utf-8-sig"))
        out = ["# Westminster: the backgrounds of Crusader Kings III's own common/event_backgrounds/%s (Paradox "
               "Interactive), with modern scenes, by westminster/tools/ui/build_event_backgrounds.py - edit there.\n" % fname]
        for name, body in blocks(src):
            env = re.search(r'environment = "([^"]+)"', body)
            out.append('%s = {\n\tbackground = {\n\t\treference = "%s"\n%s\t}\n}\n'
                       % (name, scene_for(name), '\t\tenvironment = "%s"\n' % env.group(1) if env else ""))
            total += 1
        dest = MOD / "common" / "event_backgrounds" / fname
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(out), encoding="utf-8-sig")
    print("event backgrounds replaced:", total)


if __name__ == "__main__":
    main()
