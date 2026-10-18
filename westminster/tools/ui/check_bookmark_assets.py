#!/usr/bin/env python3
"""Release-only check: every featured character needs generated bookmark art.

Source checkouts omit these DDS files. Run after build_ui.sh, before packaging.
"""
import re
import sys
from pathlib import Path

MOD = Path(__file__).resolve().parents[2] / "westminster"


def missing_assets(mod=MOD):
    missing = []
    for source in sorted((mod / "common/bookmarks/bookmarks").glob("*.txt")):
        text = source.read_text(encoding="utf-8-sig")
        bookmark = re.search(r"^(bm_\w+)\s*=\s*\{", text, re.M)
        if not bookmark:
            continue
        names = re.findall(r'\bname\s*=\s*"(bookmark_\w+)"', text)
        for name in [bookmark[1], *(f"{bookmark[1]}_{name}" for name in names)]:
            relative = f"gfx/interface/bookmarks/{name}.dds"
            if not (mod / relative).is_file():
                missing.append(relative)
    return missing


if __name__ == "__main__":
    missing = missing_assets()
    print(
        "\n".join("missing: " + path for path in missing)
        if missing
        else "ok: bookmark art"
    )
    sys.exit(bool(missing))
