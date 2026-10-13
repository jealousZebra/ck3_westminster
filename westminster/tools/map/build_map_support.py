#!/usr/bin/env python3
"""Write the map-sized winter lookup and import CK3-generated map locators.

    .venv/bin/python westminster/tools/map/build_map_support.py
    .venv/bin/python westminster/tools/map/build_map_support.py --import-locators

Boot Westminster once after rebuilding the map, then import its generated
locators. Release checks require them, so subscribers don't have to generate
building, army and activity anchors on first launch.
"""
import io
import re
import struct
import sys
from pathlib import Path

from PIL import Image

MOD = Path(__file__).resolve().parents[2] / "westminster"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common/tools"))
from ck3paths import DOCS, GAME  # noqa: E402


def main():
    with Image.open(MOD / "map_data/provinces.png") as im:
        width, height = im.size
    rel = "gfx/map/terrain/snow_diffuse_for_combined_winter.dds"
    with Image.open(GAME / rel) as im:
        winter = im.convert("RGBA").resize((width // 64, height // 64), Image.Resampling.BILINEAR)
        # CK3 updates this lookup on the CPU and explicitly requires BGRA8,
        # unlike the ordinary map textures that accept DXT compression.
        buffer = io.BytesIO()
        winter.save(buffer, format="DDS")
        header = bytearray(buffer.getvalue()[:128])
        struct.pack_into("<III", header, 92, 0x00FF0000, 0x0000FF00, 0x000000FF)
        (MOD / rel).write_bytes(header + winter.tobytes("raw", "BGRA"))
    print("Winter lookup:", winter.size)
    if "--import-locators" not in sys.argv:
        return
    out = MOD / "gfx/map/map_object_data"
    out.mkdir(parents=True, exist_ok=True)
    definitions = {int(line.split(";")[0]) for line in
                   (MOD / "map_data/definition.csv").read_text().splitlines()
                   if line.split(";")[0].isdigit()}
    for kind in ("buildings", "activities", "combat", "siege", "special_building", "unit_stack_player_owned"):
        p = DOCS / "generated" / ("generated_map_object_locators_" + kind + ".txt")
        src = p.read_text(encoding="utf-8-sig")
        ids = [int(x) for x in re.findall(r"\bid=(\d+)", src)]
        positions = re.findall(r"position=\{\s*([\d.-]+)\s+[\d.-]+\s+([\d.-]+)", src)
        assert ids and len(ids) == len(set(ids)), "Missing or duplicate locator ids: " + kind
        assert set(ids) <= definitions, "Locators reference a different map: " + kind
        assert len(positions) == len(ids), "Missing locator positions: " + kind
        # CK3 offsets combat anchors a few pixels from the unit anchor, which
        # can put an edge sea-zone combat anchor just outside the image.
        assert all(-8 <= float(x) <= width + 8 and -8 <= float(z) <= height + 8 for x, z in positions), kind
        (out / ("wm_" + kind + "_locators.txt")).write_text(
            "# CK3-generated Westminster locators, imported by build_map_support.py.\n" + src,
            encoding="utf-8-sig")
        print(kind, len(ids), "locators")


if __name__ == "__main__":
    main()
