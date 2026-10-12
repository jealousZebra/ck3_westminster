#!/usr/bin/env python3
"""Builds Westminster's map and its titles from open data (westminster/data/raw, see data/README.md).

    .venv/bin/python westminster/tools/map/build_map.py

Provinces:
  - every constituency is a county; it is split into baronies around its biggest towns (up to 3, GeoNames),
  - neighbouring land (Ireland, the Isle of Man, the Channel Islands, the French and Low Countries coast) is
    impassable scenery that belongs to no title,
  - the sea is split into named zones.
Titles: e_united_kingdom > k_<nation> > d_<ITL2 area> > c_<seat> > b_<town>.
Terrain: heights from the Copernicus DEM, terrain materials, colour map, paper map and water colour (terrain.py).

Writes into westminster/westminster/: map_data/, gfx/map/, common/landed_titles/, history/provinces/,
history/province_mapping/, map_data/geographical_regions/, localization/english/replace/, common/defines/.
"""
import random
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.spatial import cKDTree
from shapely.geometry import Point
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parent))
import geo             # noqa: E402
import heightmap_pack  # noqa: E402
import terrain         # noqa: E402

MOD = geo.ROOT / "westminster"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)
W, H = geo.WIDTH, geo.HEIGHT
SEA_ZONES = 60
TOWNS_PER_SEAT = 3
TOWN_SPACING = 2500            # metres: towns closer than this to a bigger one don't get their own barony
NATIONS = {"E": ("england", "England"), "S": ("scotland", "Scotland"), "W": ("wales", "Wales"),
           "N": ("northern_ireland", "Northern Ireland")}
CULTURE = {"E": "english", "S": "scottish", "W": "welsh", "N": "irish"}
# Named seas: the nearest one names a sea zone (lon, lat)
SEAS = [("North Sea", 2.5, 56.0), ("North Sea", 3.0, 53.5), ("North Sea", 0.0, 58.5), ("English Channel", -1.5, 50.2),
        ("English Channel", -4.0, 49.8), ("Strait of Dover", 1.4, 51.0), ("Thames Estuary", 1.2, 51.6),
        ("The Wash", 0.4, 52.95), ("Irish Sea", -5.0, 53.8), ("Irish Sea", -4.8, 54.4), ("Liverpool Bay", -3.6, 53.5),
        ("Celtic Sea", -7.0, 51.0), ("Bristol Channel", -4.2, 51.3), ("Cardigan Bay", -4.5, 52.4),
        ("North Channel", -5.5, 55.2), ("Firth of Clyde", -5.0, 55.6), ("Solway Firth", -3.6, 54.85),
        ("Atlantic Ocean", -10.5, 55.5), ("Atlantic Ocean", -9.0, 58.5), ("Atlantic Ocean", -9.5, 51.0),
        ("Sea of the Hebrides", -7.0, 57.0), ("The Minch", -6.0, 58.0), ("Moray Firth", -3.6, 57.8),
        ("Firth of Forth", -2.8, 56.1), ("Pentland Firth", -3.1, 58.75), ("Norwegian Sea", 0.5, 61.0),
        ("Fair Isle Channel", -1.8, 59.5), ("Bay of Biscay", -5.5, 48.8)]


def write(path, text, bom=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig" if bom else "utf-8")


def step(msg, t0=[time.time()]):
    print("[%5.1fs] %s" % (time.time() - t0[0], msg), flush=True)


def colors(n, seed=1):
    rng = random.Random(seed)
    used, out = {(0, 0, 0)}, []
    while len(out) < n:
        c = tuple(rng.randrange(1, 256) for _ in range(3))
        if c not in used:
            used.add(c)
            out.append(c)
    return out


def towns_for(seat, places, tree):
    """Up to TOWNS_PER_SEAT biggest places inside the seat, at least TOWN_SPACING apart."""
    inside = [places[i] for i in tree.query(seat["geom"]) if seat["geom"].contains(Point(places[i]["x"], places[i]["y"]))]
    inside.sort(key=lambda p: -p["pop"])
    chosen = []
    for p in inside:
        if all((p["x"] - q["x"]) ** 2 + (p["y"] - q["y"]) ** 2 >= TOWN_SPACING ** 2 for q in chosen):
            chosen.append(p)
        if len(chosen) == TOWNS_PER_SEAT:
            break
    return chosen


def fill_enclosed_water(grid):
    """Sea pixels not connected to the open sea are gaps between datasets (or lakes inside seats): give them
    to the nearest land."""
    sea = grid == 0
    lab, _ = ndimage.label(sea)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])).tolist()) - {0}
    enclosed = sea & ~np.isin(lab, list(border))
    if enclosed.any():
        _, (iy, ix) = ndimage.distance_transform_edt(sea, return_indices=True)
        grid[enclosed] = grid[iy[enclosed], ix[enclosed]]
    return int(enclosed.sum())


def split_baronies(seats, grid, places, tree):
    """Split each seat's pixels between its towns (nearest town wins). Returns the province grid and baronies."""
    prov = np.zeros_like(grid)
    baronies, used_keys = [], {}
    ys, xs = np.nonzero((grid > 0) & (grid <= 650))
    order = np.argsort(grid[ys, xs], kind="stable")
    ys, xs = ys[order], xs[order]
    starts = np.searchsorted(grid[ys, xs], np.arange(1, 652))
    for i, s in enumerate(seats):
        py, px = ys[starts[i]:starts[i + 1]], xs[starts[i]:starts[i + 1]]
        towns = towns_for(s, places, tree)
        nearest = np.zeros(len(px), dtype=int)
        if len(towns) > 1:
            pts = np.stack([px, py], axis=1)
            seeds = np.array([geo.to_px([(t["x"], t["y"])])[0] for t in towns])
            _, nearest = cKDTree(seeds).query(pts)
            counts = np.bincount(nearest, minlength=len(towns))
            keep = [j for j in range(len(towns)) if counts[j] >= 40] or [int(counts.argmax())]
            if len(keep) < len(towns):          # drop towns whose share would be a speck, and split again
                towns = [towns[j] for j in keep]
                nearest = cKDTree(seeds[keep]).query(pts)[1] if len(keep) > 1 else np.zeros(len(px), dtype=int)
        names = [t["name"] for t in towns] or [s["name"]]
        s["baronies"] = []
        for j, name in enumerate(names):
            k = geo.key(name) or geo.key(s["name"])
            n = used_keys.get(k, 0) + 1
            used_keys[k] = n
            b = {"id": len(baronies) + 1, "key": k if n == 1 else "%s_%d" % (k, n), "name": name, "seat": s}
            baronies.append(b)
            s["baronies"].append(b)
            sel = nearest == j
            prov[py[sel], px[sel]] = b["id"]
    return prov, baronies


def sea_zones(prov, sea, first_id):
    """Split the sea into SEA_ZONES zones (Voronoi cells of evenly spread points), named after the nearest sea."""
    sy, sx = np.nonzero(sea[::32, ::32])
    pts = np.stack([sy * 32, sx * 32], axis=1)
    rng = np.random.default_rng(7)
    seeds = [pts[rng.integers(len(pts))]]
    dmin = np.full(len(pts), np.inf)
    for _ in range(SEA_ZONES - 1):
        dmin = np.minimum(dmin, ((pts - seeds[-1]) ** 2).sum(1))
        seeds.append(pts[int(dmin.argmax())])
    seeds = np.array(seeds)
    sy, sx = np.nonzero(sea)
    prov[sy, sx] = first_id + cKDTree(seeds).query(np.stack([sy, sx], axis=1))[1]
    sea_px = np.array([geo.to_px([geo.TO_BNG.transform(lon, lat)])[0][::-1] for _, lon, lat in SEAS])
    return [SEAS[i][0] for i in cKDTree(sea_px).query(seeds)[1]]


def main():
    Image.MAX_IMAGE_PIXELS = None
    seats = geo.load_seats()
    areas = geo.load_itl2()
    geo.assign_areas(seats, areas)
    places = geo.load_places()
    scenery = geo.load_scenery()
    step("loaded %d seats, %d ITL2 areas, %d places, %d scenery shapes" % (len(seats), len(areas), len(places), len(scenery)))

    # Labels: seats 1..650, scenery 1001..; seats win where they overlap
    seat_grid = geo.rasterize([(i + 1, s["geom"]) for i, s in enumerate(seats)])
    present = set(np.unique(seat_grid).tolist())
    for i, s in enumerate(seats):                     # seats too small to survive rasterizing: stamp one pixel
        if i + 1 not in present:
            x, y = geo.to_px([s["geom"].representative_point().coords[0]])[0]
            seat_grid[int(y), int(x)] = i + 1
    scen_names = sorted({n for n, _ in scenery})
    scen_grid = geo.rasterize([(1001 + scen_names.index(n), g) for n, g in scenery])
    grid = np.where(seat_grid > 0, seat_grid, scen_grid)
    del seat_grid, scen_grid
    filled = fill_enclosed_water(grid)
    step("rasterized; %d enclosed water pixels given to the nearest land" % filled)

    tree = STRtree([Point(p["x"], p["y"]) for p in places])
    prov, baronies = split_baronies(seats, grid, places, tree)
    n_bar = len(baronies)
    step("%d baronies in %d seats" % (n_bar, len(seats)))

    scen_ids = {}
    for j, n in enumerate(scen_names):
        m = grid == 1001 + j
        if m.any():
            scen_ids[n] = n_bar + len(scen_ids) + 1
            prov[m] = scen_ids[n]
    n_land = n_bar + len(scen_ids)
    sea = grid == 0
    sea_names = sea_zones(prov, sea, n_land + 1)
    n_prov = n_land + SEA_ZONES
    land = (prov > 0) & (prov <= n_land)
    step("%d scenery provinces, %d sea zones" % (len(scen_ids), SEA_ZONES))

    # map_data
    md = MOD / "map_data"
    md.mkdir(parents=True, exist_ok=True)
    cols = colors(n_prov)
    palette = np.zeros((n_prov + 1, 3), dtype=np.uint8)
    palette[1:] = cols
    Image.fromarray(palette[prov]).save(md / "provinces.png")
    lines = ["0;0;0;0;x;x;"]
    for b in baronies:
        lines.append("%d;%d;%d;%d;%s;x;" % ((b["id"],) + cols[b["id"] - 1] + (b["key"],)))
    for n, pid in scen_ids.items():
        lines.append("%d;%d;%d;%d;%s;x;" % ((pid,) + cols[pid - 1] + (geo.key(n),)))
    for z in range(SEA_ZONES):
        pid = n_land + 1 + z
        lines.append("%d;%d;%d;%d;sea_%s_%d;x;" % ((pid,) + cols[pid - 1] + (geo.key(sea_names[z]), z + 1)))
    write(md / "definition.csv", "\n".join(lines) + "\n", bom=False)
    write(md / "default.map", """definitions = "definition.csv"
provinces = "provinces.png"
rivers = "rivers.png"
topology = "heightmap.heightmap"
continent = "continent.txt"
adjacencies = "adjacencies.csv"
island_region = "island_region.txt"
seasons = "seasons.txt"

sea_zones = RANGE { %d %d }
# Neighbouring land: scenery, owned by no one and not crossable
impassable_mountains = LIST { %s }
""" % (n_land + 1, n_prov, " ".join(str(v) for v in scen_ids.values())), bom=False)
    # The game reads adjacencies until the "-1" line; without it, it loops forever on "Initializing Game"
    write(md / "adjacencies.csv", "From;To;Type;Through;start_x;start_y;stop_x;stop_y;Comment\n-1;-1;;-1;-1;-1;-1;-1;\n", bom=False)
    for f in ("island_region.txt", "climate.txt", "continent.txt"):
        write(md / f, "# Generated by build_map.py\n")
    write(md / "seasons.txt", (GAME / "map_data" / "seasons.txt").read_text(encoding="utf-8-sig"))
    vr = Image.open(GAME / "map_data" / "rivers.png")
    rivers = Image.fromarray(np.where(land, 255, 254).astype(np.uint8), "P")
    rivers.putpalette(vr.getpalette())
    rivers.save(md / "rivers.png")
    step("provinces.png, definition.csv, default.map, rivers.png")

    elev = terrain.elevation(W, H)
    elev[~land] = 0
    step("elevation sampled (highest %.0f m)" % elev.max())
    heightmap_pack.write(terrain.heightmap(elev, land), md)
    step("heightmap packed")
    gt = MOD / "gfx" / "map" / "terrain"
    (gt / "flat_maps").mkdir(parents=True, exist_ok=True)
    index, inten = terrain.materials(elev, land)
    Image.fromarray(index, "RGBA").save(gt / "detail_index.tga")
    Image.fromarray(inten, "RGBA").save(gt / "detail_intensity.tga")
    del index, inten
    step("terrain materials")
    cm = terrain.colormap(elev, land)
    Image.fromarray(np.dstack([cm, np.full(cm.shape[:2], 255, np.uint8)]), "RGBA").save(gt / "colormap.dds", pixel_format="DXT5")
    del cm
    edges = (np.diff(prov, axis=0, prepend=prov[:1]) != 0) | (np.diff(prov, axis=1, prepend=prov[:, :1]) != 0)
    Image.fromarray(terrain.flatmap(elev, land, edges)).save(gt / "flat_maps" / "flatmap.dds", pixel_format="DXT1")
    del edges
    wdir = MOD / "gfx" / "map" / "water"
    wdir.mkdir(parents=True, exist_ok=True)
    Image.fromarray(terrain.watercolor(land, W, H), "RGBA").save(wdir / "watercolor_rgb_waterspec_a.dds", pixel_format="DXT5")
    step("colour map, paper map, water colour")

    # Titles
    for s in seats:
        s["key"] = geo.key(s["name"])
        s["nation"] = s["code"][0]
    assert len({s["key"] for s in seats}) == 650
    out = ["# Generated by westminster/tools/map/build_map.py - edit there.\n"]
    loc = ["l_english:"]
    london = next(s for s in seats if s["name"] == "Cities of London and Westminster")
    # definite_form: shown as "United Kingdom", not "Empire of United Kingdom"
    out.append("e_united_kingdom = {\n\tcolor = { 30 50 110 }\n\tcapital = c_%s\n\tdefinite_form = yes\n" % london["key"])
    loc.append(' e_united_kingdom: "United Kingdom"')
    nation_colors = {"E": (205, 40, 50), "S": (40, 90, 190), "W": (40, 150, 70), "N": (230, 150, 40)}
    duchy_keys = []
    for nk in sorted({s["nation"] for s in seats}):
        nkey, nlabel = NATIONS[nk]
        nseats = [s for s in seats if s["nation"] == nk]
        ncap = london if nk == "E" else max(nseats, key=lambda s: s["baronies"][0]["name"] in ("Edinburgh", "Cardiff", "Belfast"))
        out.append("\tk_%s = {\n\t\tcolor = { %d %d %d }\n\t\tcapital = c_%s\n\t\tdefinite_form = yes\n" % ((nkey,) + nation_colors[nk] + (ncap["key"],)))
        loc.append(' k_%s: "%s"' % (nkey, nlabel))
        for acode in sorted({s["area"]["code"] for s in nseats}):
            aseats = [s for s in nseats if s["area"]["code"] == acode]
            aname = aseats[0]["area"]["name"]
            akey = geo.key(aname)
            duchy_keys.append(akey)
            capital = max(aseats, key=lambda s: max([t["pop"] for t in towns_for(s, places, tree)] or [0]))
            r, g, b = cols[aseats[0]["baronies"][0]["id"] - 1]
            out.append("\t\td_%s = {\n\t\t\tcolor = { %d %d %d }\n\t\t\tcapital = c_%s\n\t\t\tdefinite_form = yes\n" % (akey, r, g, b, capital["key"]))
            loc.append(' d_%s: "%s"' % (akey, aname.replace(" - ", ": ")))
            for s in aseats:
                r, g, b = cols[s["baronies"][0]["id"] - 1]
                out.append("\t\t\tc_%s = {\n\t\t\t\tcolor = { %d %d %d }\n\t\t\t\tdefinite_form = yes\n" % (s["key"], r, g, b))
                for bar in s["baronies"]:
                    r, g, b = cols[bar["id"] - 1]
                    out.append("\t\t\t\tb_%s = {\n\t\t\t\t\tprovince = %d\n\t\t\t\t\tcolor = { %d %d %d }\n\t\t\t\t}\n" % (bar["key"], bar["id"], r, g, b))
                    loc.append(' b_%s: "%s"' % (bar["key"], bar["name"].replace('"', "'")))
                out.append("\t\t\t}\n")
                loc.append(' c_%s: "%s"' % (s["key"], s["name"].replace('"', "'")))
            out.append("\t\t}\n")
        out.append("\t}\n")
    out.append("}\n")
    write(MOD / "common" / "landed_titles" / "00_westminster_titles.txt", "".join(out))
    for z in range(SEA_ZONES):
        loc.append(' sea_%s_%d: "%s"' % (geo.key(sea_names[z]), z + 1, sea_names[z]))
    for n in scen_ids:
        loc.append(' %s: "%s"' % (geo.key(n), n))
    write(MOD / "localization" / "english" / "replace" / "wm_titles_l_english.yml", "\n".join(loc) + "\n")

    # Every land province needs a visual ("graphical") region, or the game crashes reading province history
    gr = md / "geographical_regions"
    gr.mkdir(exist_ok=True)
    write(gr / "geographical_region.txt", "# Generated by westminster/tools/map/build_map.py - edit there.\n"
          "graphical_western = {\n\tgraphical = yes\n\tcolor = { 255 0 0 }\n\tduchies = {\n%s\n\t}\n}\n"
          % "\n".join("\t\td_" + k for k in duchy_keys))

    # Province history, one file per kingdom: the seat's main town holds the castle, other baronies are empty
    for f in (MOD / "history" / "provinces").glob("*.txt"):
        f.unlink()
    hist_by = {}
    # faith: the seat's ideology, the party that won it in 2024 (data/ge2024_results.csv, column winner_ideology,
    # written by tools/data/build_2024.py, which also sets it here when it runs); "Not Stated" until then
    seat_faith = {}
    results = geo.ROOT / "data" / "ge2024_results.csv"
    if results.exists():
        import csv
        with open(results, encoding="utf-8") as f:
            seat_faith = {r["title"][2:]: r.get("winner_ideology") or "wm_faith_not_stated" for r in csv.DictReader(f)}
    for s in seats:
        h = hist_by.setdefault(s["nation"], ["# Generated by westminster/tools/map/build_map.py - edit there.\n"])
        for j, bar in enumerate(s["baronies"]):
            h.append("%d = {\t# %s, %s\n\tculture = %s\n\tfaith = %s\n\tholding = %s\n}\n"
                     % (bar["id"], bar["name"], s["name"], CULTURE[s["nation"]], seat_faith.get(s["key"], "wm_faith_not_stated"),
                        "castle_holding" if j == 0 else "none"))
    for nk, h in hist_by.items():
        write(MOD / "history" / "provinces" / ("k_%s.txt" % NATIONS[nk][0]), "".join(h))
    # CK3 1.20 crashes reading province history if there are no province mappings at all (it reads the first
    # entry of the empty list), so map one sea zone onto another: sea zones have no history to copy
    write(MOD / "history" / "province_mapping" / "00_westminster.txt",
          "# Generated by build_map.py. Needed: the game crashes when this list is empty.\n%d = %d\n" % (n_prov, n_prov - 1))

    lpx = geo.to_px([london["geom"].representative_point().coords[0]])[0]
    write(MOD / "common" / "defines" / "wm_map_defines.txt", """NJominiMap = {
	WORLD_EXTENTS_X = %d
	WORLD_EXTENTS_Y = %d
	WORLD_EXTENTS_Z = %d
	WATERLEVEL = %s
}
NGame = {
	END_DATE = "2200.1.1"
}
""" % (W - 1, terrain.WORLD_Y, H - 1, terrain.WATERLEVEL))
    write(MOD / "common" / "defines" / "graphic" / "wm_graphics.txt", """NCamera = {
	START_LOOK_AT = { %.1f 0 %.1f }
	PANNING_WIDTH = %d
	PANNING_HEIGHT = %d
}
""" % (lpx[0], H - lpx[1], W, H))
    sizes = np.bincount(prov[(prov > 0) & (prov <= n_bar)].ravel(), minlength=n_bar + 1)[1:]
    step("done. %d provinces: %d baronies (smallest %d px: %s), %d scenery, %d sea"
         % (n_prov, n_bar, sizes.min(), baronies[int(sizes.argmin())]["name"], len(scen_ids), SEA_ZONES))


if __name__ == "__main__":
    main()
