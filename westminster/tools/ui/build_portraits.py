#!/usr/bin/env python3
"""Takes the medieval crowns, hats, helmets and cloaks off every portrait.

    .venv/bin/python westminster/tools/ui/build_portraits.py

Each vanilla headgear and cloak portrait-modifier group (gfx/portraits/portrait_modifiers/*headgear*, *cloak*) is
replaced by a group of the same name whose only choice is no headgear / no cloak. Clothes are left alone for now:
the game has no modern clothes.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MOD = ROOT / "westminster"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)
PM = GAME / "gfx" / "portraits" / "portrait_modifiers"


def main():
    n = 0
    for f in sorted(PM.glob("*.txt")):
        kind = "headgear" if "headgear" in f.name else "cloak" if "cloak" in f.name else None
        if not kind:
            continue
        src = f.read_text(encoding="utf-8-sig")
        groups = re.findall(r"^([a-z0-9_]+) = \{", src, re.M)
        usage = dict(re.findall(r"^([a-z0-9_]+) = \{[^{]*?usage = (\w+)", src, re.M | re.S))
        gene, template = ("headgear", "no_headgear") if kind == "headgear" else ("cloaks", "no_cloak")
        out = ["# Westminster: the groups of Crusader Kings III's own gfx/portraits/portrait_modifiers/%s (Paradox "
               "Interactive), each giving no %s, by westminster/tools/ui/build_portraits.py - edit there.\n" % (f.name, kind)]
        for g in groups:
            out.append("""%s = {
	usage = %s
	selection_behavior = weighted_random
	priority = 1
	wm_no_%s = {
		dna_modifiers = {
			accessory = {
				mode = add
				gene = %s
				template = %s
				range = { 0 1 }
			}
		}
		weight = { base = 100 }
	}
}
""" % (g, usage.get(g, "game"), kind, gene, template))
            n += 1
        dest = MOD / "gfx" / "portraits" / "portrait_modifiers" / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("".join(out), encoding="utf-8-sig")
    print("headgear and cloak groups replaced:", n)


if __name__ == "__main__":
    main()
