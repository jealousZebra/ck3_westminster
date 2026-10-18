#!/usr/bin/env python3
"""The new-game (bookmark) screen: a newspaper election map instead of vanilla's painted map, the featured
characters standing by their constituencies, and the screen's chrome in the look's paper and rules (build_theme.THEME:
dark paper and light hairlines in the night edition; the party colours stay).

    .venv/bin/python westminster/tools/ui/build_bookmark_screen.py            # everything below
    .venv/bin/python westminster/tools/ui/build_bookmark_screen.py --preview  # also tools/test_out/bookmark/preview.png
    .venv/bin/python westminster/tools/ui/build_bookmark_screen.py --import-dump   # new portrait dumps (see below)

- gfx/interface/bookmarks/bm_2024_starmer.dds: the bookmark's background (1920 x 1080, as vanilla's). The UK's 650
  seats coloured by their 4 July 2024 winner (data/ge2024_results.csv; party colours as build_polls_panel.py),
  drawn from the ONS boundaries the game map is built from (tools/map/geo.py), with London and Shetland insets, a
  legend, and a ringed seat and callout line for each featured character.
- gfx/interface/bookmarks/bm_2024_starmer_<character>.dds: the "location image" the game lays over the background
  (pulsing) when a character is selected or hovered: their party's seats stand out and their own seat is ringed.
- layout(): where each featured character stands on the screen (the bookmark's `position`). build_2024.py's
  bookmark writer calls it, so the map and the positions come from the same projection.
- gui/frontend_bookmarks.gui (build_theme.py's glow-free copy of vanilla's, patched again here): the dark
  scroll-patterned bars, the medieval arches and the dark "play as anyone" box become paper with ink rules.
- gfx/interface/bookmarks/any_ruler_*.dds, top_bar_panel.dds, start_buttons/, icons/banners/banner_blue_left*.dds
  (the characters' name banners), icons/bookmark_buttons/: paper and ink instead of dark stone, cloth and gilding.
- localization/english/replace/wm_bookmark_screen_l_english.yml: "Play as any MP".
- common/bookmark_portraits/<character>.txt: the featured characters' portraits (build_portraits()).

Runs after fal_images.py and build_theme.py (build_ui.sh), whose outputs it overwrites.
"""
import csv
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "map"))
sys.path.insert(0, str(HERE.parent / "data"))
from build_theme import DARK, GAME, MOD, ROOT, THEME, gui_color, grain, save_dds   # noqa: E402

W, H = 1920, 1080              # vanilla's bookmark backgrounds; the GUI shows them in a 1920 x 1080 frame
CHAR_DY = 60                   # characters sit in the 1920 x 1200 widget around it: position y = image y + 60
SS = 2                         # drawn at twice the size, then reduced (anti-aliasing)
ERA = next((int(arg[2:]) for arg in sys.argv if arg in ("--1945", "--1997", "--2010", "--2016")), None)
HISTORIC = "--1979" in sys.argv or ERA is not None
YEAR = ERA or (1979 if HISTORIC else 2024)
if ERA:
    from era_definitions import ERAS
    BOOKMARK = "bm_%s_%s" % (YEAR, ERAS[YEAR]["slug"])
else:
    BOOKMARK = "bm_1979_thatcher" if HISTORIC else "bm_2024_starmer"
OUT = MOD / "gfx" / "interface" / "bookmarks"
FONTS = ROOT / "data" / "raw" / "fonts"
TEST_OUT = ROOT / "tools" / "test_out" / "bookmark"

# Projection: British National Grid metres -> image pixels. Scilly to Orkney fills the height between the top and
# bottom bars; Shetland goes in an inset.
K = 0.00088                    # pixels per metre (0.88 px/km)
E0, N1 = 0, 1036000            # BNG of the image point (OX, OY)
OX, OY = 560, 92
SHETLAND_N = 1080000           # seat parts north of this are drawn in the Shetland inset
SHETLAND_SHIFT = (175000, -265000)      # metres the Shetland inset moves them (east, north)
LONDON_BOX = (503000, 155500, 562500, 201500)   # BNG (west, south, east, north) of the London inset
LONDON_AT = (345, 520)         # the inset's top-left in the image (over the Atlantic, south-west of Ireland)
LONDON_K = 0.0040              # its scale (4 px/km)

# Screen areas the characters must keep out of (image pixels): the date list (left) and the right-hand panel
# (bookmark text, then the selected character's sheet), the top and bottom bars
SAFE = (335, 95, 1470, 1000)
LAND_COST = 600                # how far (px) a character would rather stand from its seat than cover land
CHAR_W, CHAR_H = 265, 225      # a character's portrait, banner and two lines of text, from its position (measured
                               # in game: the position is the top-left of the portrait)
BANNER = (0, 127, 262, 175)    # the name banner within it (the callout line ends there)
PORTRAIT = (55, 0, 210, 127)   # the portrait itself (the rest above the banner is transparent)

PAPER_RGB = THEME["paper"]
SEA = THEME["sea"]
SCENERY_RGB = THEME["land"]
INK = THEME["ink"]                 # lettering and the callouts
LINE = THEME["line"]               # frames and rules
MUTED = THEME["muted"]             # leader lines, the legend's subtitle
RED = THEME["red"]

# Winner codes in ge2024_results.csv -> build_polls_panel.py party codes
CODE = {"Lab": "lab", "Con": "con", "LD": "ld", "RUK": "ruk", "Green": "grn", "SNP": "snp", "PC": "pc", "SF": "sf",
        "DUP": "dup", "SDLP": "sdlp", "APNI": "apni", "UUP": "uup", "TUV": "tuv", "Ind": "ind", "Spk": "spk"}


def party_colours():
    from build_polls_panel import CHART
    cols = {c: tuple(int(round(v * 255)) for v in rgb) for c, _, _, rgb in CHART}
    names = {c: n for c, _, n, _ in CHART}
    cols["spk"], names["spk"] = (140, 138, 132) if DARK else (70, 70, 70), "The Speaker"
    return cols, names


# ------------------------------------------------------------------------------------------------ geometry

_SEATS = None


def seats():
    """Every seat: code, title key, name, region, winner code and its geometry in image pixels (main map and,
    for London seats, the inset)."""
    global _SEATS
    if _SEATS is not None:
        return _SEATS
    import geo
    from shapely.affinity import affine_transform
    from shapely.geometry import box
    rows = {r["ons_code"]: r for r in csv.DictReader(open(ROOT / "data" / "ge2024_results.csv", encoding="utf-8"))}
    main_t = [K, 0, 0, -K, OX - E0 * K, OY + N1 * K]
    w, s, e, n = LONDON_BOX
    lon_t = [LONDON_K, 0, 0, -LONDON_K, LONDON_AT[0] - w * LONDON_K, LONDON_AT[1] + n * LONDON_K]
    north = box(-1e6, SHETLAND_N, 2e6, 2e6)
    out = []
    for st in geo.load_seats():
        r = rows[st["code"]]
        g = st["geom"]
        main = g.difference(north)
        shet = g.intersection(north)
        if not shet.is_empty:
            from shapely.affinity import translate
            main = main.union(translate(shet, *SHETLAND_SHIFT))
        rec = {"code": st["code"], "title": r["title"], "seat": r["title"][2:], "name": st["name"],
               "region": r["region"], "winner": CODE.get(r["winner_party"], "ind"),
               "px": affine_transform(main.buffer(0), main_t), "geom": g}
        rec["inset"] = affine_transform(g, lon_t) if r["region"] == "London" else None
        # The ringed point: a point well inside the seat (its largest part's pole of inaccessibility)
        rec["point"] = point_in(rec["px"])
        rec["inset_point"] = point_in(rec["inset"]) if rec["inset"] is not None else None
        out.append(rec)
    _SEATS = out
    return out


def by_name(seat):
    return next(r for r in seats() if r["seat"] == seat)


def point_in(g):
    from shapely.ops import polylabel
    from shapely.geometry import Polygon
    parts = [g] if isinstance(g, Polygon) else list(getattr(g, "geoms", []))
    big = max(parts, key=lambda p: p.area)
    p = polylabel(big, tolerance=0.5)
    return (p.x, p.y)


def scenery_px():
    import geo
    from shapely.affinity import affine_transform
    t = [K, 0, 0, -K, OX - E0 * K, OY + N1 * K]
    return [affine_transform(g, t) for _, g in geo.load_scenery()]


# ------------------------------------------------------------------------------------------------ layout

def featured():
    """(seat key, bookmark name) of each featured character."""
    if HISTORIC:
        import json
        from build_1979 import norm
        if ERA:
            historical_featured = [(name,) for name in ERAS[YEAR]["featured"]]
        else:
            from build_1979 import FEATURED as historical_featured
        snap = json.loads((ROOT / ("data/snapshots/%s.json" % YEAR)).read_text())
        by_person = {m["name"]: m["seat"] for m in snap["members"]}
        return [(by_person[f[0]], "bookmark_%s_" % YEAR + norm(f[0])) for f in historical_featured]
    from build_2024 import FEATURED, key
    return [(f[0], "bookmark_2024_" + key(f[1])) for f in FEATURED]


def apply_bookmark_winners():
    """Use the selected bookmark's election winners on the shared 2024 constituency geometry."""
    if not HISTORIC:
        return
    import json
    party = {"conservative": "con", "labour": "lab", "lib_dem": "ld", "snp": "snp", "plaid": "pc",
             "uup": "uup", "dup": "dup", "sdlp": "sdlp", "sinn_fein": "sf", "alliance": "apni", "green": "grn", None: "ind"}
    snap = json.loads((ROOT / ("data/snapshots/%s.json" % YEAR)).read_text())
    winners = {m["seat"]: party[m["party"]] for m in snap["members"] if m["seat"]}
    for seat in seats():
        seat["winner"] = winners[seat["seat"]]


def anchor(seat):
    """Where a featured character's seat is ringed: in the London inset for London seats."""
    rec = next(r for r in seats() if r["seat"] == seat)
    return rec["inset_point"] or rec["point"]


def _rect(x, y, m=0):
    return (x - m, y - m, x + CHAR_W + m, y + CHAR_H + m)


def _overlap(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0, w) * max(0, h)


def _banner_point(x, y, p):
    """The point of a character's banner nearest to p (image pixels, character at x, y)."""
    bx0, by0, bx1, by1 = x + BANNER[0], y + BANNER[1], x + BANNER[2], y + BANNER[3]
    return (min(max(p[0], bx0), bx1), min(max(p[1], by0), by1))


def layout():
    """Each featured character's screen position {bookmark name: (x, y)} in the bookmark's coordinates (the 1920 x
    1200 widget: image y + CHAR_DY). Placed one by one (in build_2024's order, the Prime Minister first) at the
    spot nearest its seat that keeps clear of the other characters, every ringed seat, the London inset, the
    screen's panels and as much of the land as it can."""
    mask = Image.new("L", (W, H), 0)
    dm = ImageDraw.Draw(mask)
    for r in seats():
        for p in polys(r["px"]):
            dm.polygon(list(p.exterior.coords), fill=1)
    sat = np.pad(np.asarray(mask, np.float64).cumsum(0).cumsum(1), ((1, 0), (1, 0)))   # summed-area table of land

    def area(x0, y0, x1, y1):
        x0, y0, x1, y1 = (int(v) for v in (x0, y0, x1, y1))
        return sat[y1, x1] - sat[y0, x1] - sat[y1, x0] + sat[y0, x0]

    def land(x, y):
        """The share of the character's visible footprint (portrait, banner and text) that covers seats."""
        a = area(x + PORTRAIT[0], y + PORTRAIT[1], x + PORTRAIT[2], y + PORTRAIT[3]) + area(x, y + BANNER[1], x + CHAR_W, y + CHAR_H)
        return a / ((PORTRAIT[2] - PORTRAIT[0]) * (PORTRAIT[3] - PORTRAIT[1]) + CHAR_W * (CHAR_H - BANNER[1]))
    inset = london_frame()
    rings = [anchor(s) for s, _ in featured()]
    placed, out = [], {}
    for seat, name in featured():
        p = anchor(seat)
        best = None
        for y in range(SAFE[1], SAFE[3] - CHAR_H + 1, 5):
            for x in range(SAFE[0], SAFE[2] - CHAR_W + 1, 5):
                r = _rect(x, y)
                if any(_overlap(_rect(*q, 12), r) for q in placed):
                    continue
                if any(r[0] - 14 < q[0] < r[2] + 14 and r[1] - 14 < q[1] < r[3] + 14 for q in rings):
                    continue
                if _overlap(r, (inset[0] - 12, inset[1] - 40, inset[2] + 12, inset[3] + 12)):    # and its label
                    continue
                bp = _banner_point(x, y, p)
                dist = ((bp[0] - p[0]) ** 2 + (bp[1] - p[1]) ** 2) ** 0.5
                cost = dist + LAND_COST * land(x, y)
                if best is None or cost < best[0]:
                    best = (cost, x, y)
        _, x, y = best
        placed.append((x, y))
        out[name] = (x, y + CHAR_DY)
    return out


def london_frame():
    w, s, e, n = LONDON_BOX
    return (LONDON_AT[0], LONDON_AT[1], LONDON_AT[0] + (e - w) * LONDON_K, LONDON_AT[1] + (n - s) * LONDON_K)


# ------------------------------------------------------------------------------------------------ drawing

def font(name, size, weight=None):
    path = {"playfair": FONTS / "PlayfairDisplay[wght].ttf",
            "serif": FONTS / "sourceserif" / "source-serif-4.005_Desktop" / "TTF" / "SourceSerif4-Regular.ttf",
            "serif_bold": FONTS / "sourceserif" / "source-serif-4.005_Desktop" / "TTF" / "SourceSerif4-Semibold.ttf"}[name]
    f = ImageFont.truetype(str(path), size * SS)
    if weight:
        f.set_variation_by_axes([weight])
    return f


def polys(g):
    from shapely.geometry import Polygon
    if g is None or g.is_empty:
        return []
    return [g] if isinstance(g, Polygon) else [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]


def fill(d, g, colour, outline=None, width=1):
    for p in polys(g):
        d.polygon([(x * SS, y * SS) for x, y in p.exterior.coords], fill=colour)
        for hole in p.interiors:
            d.polygon([(x * SS, y * SS) for x, y in hole.coords], fill=SEA)
    if outline:
        for p in polys(g):
            for ring in [p.exterior] + list(p.interiors):
                d.line([(x * SS, y * SS) for x, y in ring.coords], fill=outline, width=width, joint="curve")


def soften(rgb, k=None):
    """Party colours printed on paper: a little of the paper in them (THEME["soften"])."""
    k = THEME["soften"] if k is None else k
    return tuple(int(round(c * (1 - k) + p * k)) for c, p in zip(rgb, PAPER_RGB))


def draw_seats(d, key, colours):
    rs = [r for r in seats() if r[key] is not None]
    for r in rs:
        fill(d, r[key], soften(colours[r["winner"]]))
    border = THEME["seam"]
    for r in rs:
        for p in polys(r[key]):
            d.line([(x * SS, y * SS) for x, y in p.exterior.coords], fill=border, width=1 if key == "px" else 2)


def background(colours, names, positions):
    w, h = W * SS, H * SS
    img = Image.new("RGB", (w, h), SEA)
    d = ImageDraw.Draw(img)
    # Neighbouring land (Ireland, the Isle of Man, France ...)
    for g in scenery_px():
        fill(d, g, SCENERY_RGB, outline=THEME["land_line"], width=SS)
    draw_seats(d, "px", colours)
    # Coast of the UK
    from shapely.ops import unary_union
    uk = unary_union([r["px"] for r in seats()])
    for p in polys(uk.simplify(0.3)):
        d.line([(x * SS, y * SS) for x, y in p.exterior.coords], fill=THEME["coast"], width=SS)

    # Shetland inset frame
    import geo
    from shapely.geometry import box as sbox
    shet = [st["geom"] for st in geo.load_seats() if st["code"] == by_name("orkney_and_shetland")["code"]][0]
    sb = shet.intersection(sbox(-1e6, SHETLAND_N, 2e6, 2e6)).bounds          # Shetland, moved into its inset
    bx0, by1 = OX + (sb[0] + SHETLAND_SHIFT[0] - E0) * K, OY + (N1 - sb[1] - SHETLAND_SHIFT[1]) * K
    bx1, by0 = OX + (sb[2] + SHETLAND_SHIFT[0] - E0) * K, OY + (N1 - sb[3] - SHETLAND_SHIFT[1]) * K
    d.rectangle([(bx0 - 10) * SS, (by0 - 8) * SS, (bx1 + 10) * SS, (by1 + 8) * SS], outline=LINE, width=SS)

    # London: a box on the main map and the inset
    w_, s_, e_, n_ = LONDON_BOX
    x0, y0 = OX + (w_ - E0) * K, OY + (N1 - n_) * K
    x1, y1 = OX + (e_ - E0) * K, OY + (N1 - s_) * K
    d.rectangle([x0 * SS, y0 * SS, x1 * SS, y1 * SS], outline=LINE, width=SS)
    fx0, fy0, fx1, fy1 = london_frame()
    pad = 8
    d.rectangle([(fx0 - pad) * SS, (fy0 - pad) * SS, (fx1 + pad) * SS, (fy1 + pad) * SS], fill=SEA, outline=LINE, width=SS * 2)
    draw_seats(d, "inset", colours)
    # Leader lines from the small box to the inset, in grey (they cross England)
    grey = MUTED
    d.line([x0 * SS, y0 * SS, (fx1 + pad) * SS, (fy0 - pad) * SS], fill=grey, width=SS)
    d.line([x0 * SS, y1 * SS, (fx1 + pad) * SS, (fy1 + pad) * SS], fill=grey, width=SS)
    lab = font("playfair", 17, 700)
    d.text(((fx0 - pad) * SS, (fy0 - pad - 24) * SS), "LONDON", font=lab, fill=INK)

    # Legend
    legend(d, colours, names)

    # Featured seats: a ring, and a callout line to the character's banner
    for seat, name in featured():
        p = anchor(seat)
        x, y = positions[name]
        y -= CHAR_DY
        bp = _banner_point(x, y, p)
        d.line([p[0] * SS, p[1] * SS, bp[0] * SS, bp[1] * SS], fill=INK, width=int(1.5 * SS))
        r = 6
        d.ellipse([(p[0] - r) * SS, (p[1] - r) * SS, (p[0] + r) * SS, (p[1] + r) * SS], outline=INK, width=SS * 2,
                  fill=None)
        d.ellipse([(p[0] - 2) * SS, (p[1] - 2) * SS, (p[0] + 2) * SS, (p[1] + 2) * SS], fill=INK)

    img = img.resize((W, H), Image.LANCZOS)
    arr = np.asarray(img).astype(np.float32)
    arr = np.clip(arr + grain(H, W, YEAR) * 0.7, 0, 255).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


def legend(d, colours, names):
    counts = {}
    for r in seats():
        counts[r["winner"]] = counts.get(r["winner"], 0) + 1
    order = sorted(counts, key=lambda c: (-counts[c], names[c]))
    x, y = 60, 470
    title = font("playfair", 22, 700)
    small = font("serif", 15)
    bold = font("serif_bold", 15)
    d.line([x * SS, y * SS, (x + 250) * SS, y * SS], fill=INK, width=SS * 3)
    d.text((x * SS, (y + 8) * SS), "General election", font=title, fill=INK)
    election_date = ("%s Parliament (modern map)" % YEAR) if ERA else ("Seats won, 3 May 1979" if HISTORIC else "Seats won, 4 July 2024")
    d.text((x * SS, (y + 38) * SS), election_date, font=small, fill=THEME["coast"] if DARK else (70, 70, 66))
    y += 70
    for c in order:
        d.rectangle([x * SS, (y + 3) * SS, (x + 14) * SS, (y + 17) * SS], fill=soften(colours[c]))
        d.text(((x + 24) * SS, y * SS), names[c], font=small, fill=INK)
        n = str(counts[c])
        tw = d.textlength(n, font=bold)
        d.text(((x + 250) * SS - tw, y * SS), n, font=bold, fill=INK)
        y += 22
    d.line([x * SS, (y + 6) * SS, (x + 250) * SS, (y + 6) * SS], fill=LINE, width=SS)


def location_image(seat, party):
    """The overlay for one character: other parties' seats washed towards paper, their own seat ringed in red."""
    w, h = W * SS, H * SS
    wash = Image.new("L", (w, h), 0)
    dw = ImageDraw.Draw(wash)
    for r in seats():
        if party and r["winner"] == party:
            continue
        for key in ("px", "inset"):
            for p in polys(r[key]):
                dw.polygon([(x * SS, y * SS) for x, y in p.exterior.coords], fill=150)
    ring = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(ring)
    rec = next(r for r in seats() if r["seat"] == seat)
    for key in ("px", "inset"):
        for p in polys(rec[key]):
            dr.line([(x * SS, y * SS) for x, y in p.exterior.coords], fill=255, width=3 * SS, joint="curve")
    p = rec["inset_point"] or rec["point"]
    rr = 15
    dr.ellipse([(p[0] - rr) * SS, (p[1] - rr) * SS, (p[0] + rr) * SS, (p[1] + rr) * SS], outline=255, width=3 * SS)
    wash = np.asarray(wash.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    ring = np.asarray(ring.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    rgb = np.empty((H, W, 3), np.float32)
    rgb[:] = PAPER_RGB
    rgb = rgb * (1 - ring[..., None]) + np.array(RED, np.float32) * ring[..., None]
    a = np.maximum(wash, ring)
    return Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), "RGBA")


# ------------------------------------------------------------------------------------------------ chrome

GUI = Path("gui/frontend_bookmarks.gui")
PAPER_TINT = gui_color("paper")


def build_gui():
    """Edits build_theme.py's glow-free copy of vanilla's frontend_bookmarks.gui (rebuilt from vanilla first, so
    this pass can run again)."""
    dest = MOD / GUI
    src = dest.read_text(encoding="utf-8-sig")
    first, _, body = src.partition("\n")
    if "build_bookmark_screen.py" in first:          # already patched: start again from vanilla with build_theme's glows
        from build_theme import DARK_GLOW
        body = DARK_GLOW.sub("glow_color:{0,0,0,0}", (GAME / GUI).read_text(encoding="utf-8-sig"))
    n = {}
    # The top and bottom bars: a dark band with a scrollwork pattern -> plain paper
    body, n["pattern bars"] = re.subn(
        r'texture = "gfx/interface/component_masks/patterns/mask_pattern_01\.dds"(\s*)spriteType = corneredtiled(\s*)'
        r'color = \{ 0\.1 0\.1 0\.12 1 \}',
        r'texture = "gfx/interface/colors/white.dds"\1spriteType = corneredtiled\2color = { %s }' % PAPER_TINT, body)
    # The ornaments on the bottom bar's top edge (a centre boss and two arches)
    body, n["ornaments"] = re.subn(
        r'\n(\t+)icon = \{\n\t+parentanchor = (?:top\|hcenter|top\|right|top\|left)\n\t+position = \{ -?\d+ -\d+ \}\n'
        r'(?:\t+size = \{ 40 40 \}\n)?\t+texture = "gfx/interface/component_decoration/decoration_(?:frame_top_center|arch)\.dds"\n'
        r'(?:\t+(?:texture_density = 2|mirror = horizontal)\n)?\1\}', "", body)
    # The screen's backdrop (dark map colour with fades) -> the map's sea, so a screen taller than 16:9 shows sea
    # above and below the map instead of black
    body, n["backdrop"] = re.subn(
        r'(\t#Background\n\ticon = \{\n\t\tsize = \{ 100% 100%\}\n\t\tparentanchor = center\n)'
        r'\t\ttexture = "gfx/interface/colors/map_color\.dds"\n.*?\n\t\}\n',
        lambda m: m.group(1) + '\t\ttexture = "gfx/interface/colors/white.dds"\n\t\tcolor = { %s 1 }\n\t}\n'
        % " ".join("%.3f" % (c / 255) for c in SEA), body, count=1, flags=re.S)
    # Colour-dodge glows and shimmers (the bookmark tab, the Start button, "play as anyone"): on paper they burn
    # to white. Their textures become black, which colour dodge leaves unchanged.
    dodged = []

    def no_dodge(m):
        blk = m.group(0)
        if "blend_mode = colordodge" not in blk:
            return blk
        dodged.append(1)
        return re.sub(r'texture = "[^"]+"', 'texture = "gfx/interface/colors/black.dds"', blk, count=1)
    body = re.sub(r'modify_texture = \{[^{}]*\}', no_dodge, body)
    n["glows"] = len(dodged)
    # The black smudge behind the word Start
    body, n["start smudge"] = re.subn(
        r'(text = "START"\n(?:\t+[a-z_]+ = [^\n]+\n)+?)\t+background = \{\n\t+texture ="gfx/interface/colors/black\.dds"\n'
        r'(?:\t+[a-z_]+ = [^\n]+\n)+\t+modify_texture = \{[^{}]*\}\n\t+\}\n', r"\1", body)
    # The dark halo behind the year on the year tab
    body, n["year halo"] = re.subn(
        r'(texture = "gfx/interface/component_masks/mask_fade_circle\.dds"\n\t+color = \{ 0\.1 0\.1 0\.1 )1( \})', r"\g<1>0\2", body)
    # The map's torn top and bottom edges: a clean rectangle
    body, n["torn edges"] = re.subn(
        r'\n\t+modify_texture = \{\n\t+name = "mask"\n\t+texture = "gfx/interface/component_masks/'
        r'mask_seamless_torn_edge_horizontal\.dds"\n(?:\t+[A-Za-z_]+ = [^\n]+\n)+?\t+\}', "", body)
    head = ("# Westminster: Crusader Kings III's own gui/frontend_bookmarks.gui (Paradox Interactive), with its dark text "
            "glows made transparent, its dark patterned bars, ornaments and glows made paper and the map's backdrop sea, by "
            "westminster/tools/ui/build_bookmark_screen.py - edit there.\n")
    dest.write_text(head + body, encoding="utf-8-sig")
    return n


def inked(rgba, fill=PAPER_RGB, width=3, edge_only=False):
    """A texture's shape (its alpha) as paper with an ink rule along its edge, or the rule alone."""
    from scipy import ndimage
    solid = rgba[..., 3] > 128
    edge = solid & ~ndimage.binary_erosion(solid, iterations=width)
    h, w = solid.shape
    rgb = np.clip(np.array(fill, np.float32) + grain(h, w, w * 7 + h), 0, 255)
    rgb[edge] = LINE
    a = (edge if edge_only else solid).astype(np.uint8) * 255
    return np.dstack([rgb, a]).astype(np.uint8)


def bookmark_button(w, h):
    """The date list's button (shown at half size, its left part off screen): the year in ink beside a small
    election map, on paper."""
    full = Image.open(OUT / (BOOKMARK + ".dds")).convert("RGB")
    crop = full.crop((540, 60, 1180, 1010))           # the main map
    crop.thumbnail((w, h - 16), Image.LANCZOS)
    im = Image.new("RGBA", (w, h), PAPER_RGB + (255,))
    im.paste(crop, (w - crop.width - 70, (h - crop.height) // 2))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(FONTS / "PlayfairDisplay[wght].ttf"), 92)
    f.set_variation_by_axes([700])
    d.text((150, h // 2), str(YEAR), font=f, fill=INK, anchor="lm")
    return im


def build_chrome_textures(colours):
    """The bookmark screen's own textures: dark stone and gilding -> paper and ink; the bookmark's buttons."""
    bm = GAME / "gfx" / "interface" / "bookmarks"
    out = []
    for name in ("top_bar_panel.dds", "any_ruler_button.dds"):
        save_dds(inked(np.array(Image.open(bm / name).convert("RGBA"))), OUT / name)
        out.append(name)
    for name in ("any_ruler_frame.dds",):
        save_dds(inked(np.array(Image.open(bm / name).convert("RGBA")), width=2, edge_only=True), OUT / name)
        out.append(name)
    for name in ("any_ruler_shine.dds", "custom_ruler_backdrop.dds"):     # a shine; build_theme's empty paper box
        van = Image.open(bm / name)
        save_dds(np.zeros((van.height, van.width, 4), np.uint8), OUT / name)
        out.append(name)
    # The Start button (GameSetup.GetSelectedBookmark.GetStartButton: start_buttons/<bookmark>.dds) and its frame:
    # the shape of vanilla's, as paper with an ink rule
    shape = np.array(Image.open(bm / "start_buttons" / "bm_1066_hastings.dds").convert("RGBA"))
    save_dds(inked(shape, fill=THEME["paper_raised"] if DARK else (236, 231, 220), width=4),
             OUT / "start_buttons" / (BOOKMARK + ".dds"))
    save_dds(inked(np.array(Image.open(bm / "start_buttons" / "start_frame.dds").convert("RGBA")), width=3,
                   edge_only=True), OUT / "start_buttons" / "start_frame.dds")
    out += ["start_buttons/" + BOOKMARK + ".dds", "start_buttons/start_frame.dds"]
    # The bookmark's buttons in the date list and the info panel: the election map on paper, ruled
    icons = GAME / "gfx" / "interface" / "icons"
    van = np.array(Image.open(icons / "bookmark_buttons" / "bm_1066_hastings.dds").convert("RGBA"))
    h, w = van.shape[:2]
    arr = np.array(bookmark_button(w, h))
    arr[..., 3] = van[..., 3]
    from scipy import ndimage
    solid = van[..., 3] > 128
    arr[solid & ~ndimage.binary_erosion(solid, iterations=3), :3] = LINE
    save_dds(arr, MOD / "gfx" / "interface" / "icons" / "bookmark_buttons" / (BOOKMARK + ".dds"))
    # The year tab along the top (one per bookmark group): dark stone glass -> paper
    yt = icons / "bookmark_buttons" / "year_tab.dds"
    save_dds(inked(np.array(Image.open(yt).convert("RGBA")), width=2), MOD / "gfx" / "interface" / "icons" / "bookmark_buttons" / "year_tab.dds")
    out.append("icons/bookmark_buttons/year_tab.dds")
    # The characters' name banners (blue cloth with a ribbon tail, used only on this screen): a ruled paper
    # nameplate; the hover and selection glow around it becomes a red rule
    ban = GAME / "gfx" / "interface" / "icons" / "banners"
    h, w = Image.open(ban / "banner_blue_left.dds").size[::-1]
    x0, y0, x1, y1 = 40, 16, 712, 126              # vanilla's cloth, without the tail
    plate = np.zeros((h, w, 4), np.uint8)
    plate[y0:y1, x0:x1, :3] = np.clip(np.array(PAPER_RGB, np.float32) + grain(y1 - y0, x1 - x0, 77), 0, 255)
    plate[y0:y1, x0:x1, 3] = 255
    for t, c in ((5, LINE),):
        plate[y0:y0 + t, x0:x1, :3] = plate[y1 - t:y1, x0:x1, :3] = c
        plate[y0:y1, x0:x0 + t, :3] = plate[y0:y1, x1 - t:x1, :3] = c
    plate[y1 - 14:y1 - 11, x0 + 14:x1 - 14, :3] = LINE                # a thin second rule along the bottom
    save_dds(plate, MOD / "gfx" / "interface" / "icons" / "banners" / "banner_blue_left.dds")
    glow = np.zeros((h, w, 4), np.uint8)
    glow[..., :3] = RED
    t = 6
    for sl in (np.s_[y0 - t:y0, x0 - t:x1 + t], np.s_[y1:y1 + t, x0 - t:x1 + t], np.s_[y0 - t:y1 + t, x0 - t:x0],
               np.s_[y0 - t:y1 + t, x1:x1 + t]):
        glow[sl + (3,)] = 255
    save_dds(glow, MOD / "gfx" / "interface" / "icons" / "banners" / "banner_blue_left_glow.dds")
    out += ["icons/banners/banner_blue_left.dds", "icons/banners/banner_blue_left_glow.dds"]
    # The big one is laid faintly behind the bookmark text and the Start button: left empty (it read as a stain)
    van = Image.open(icons / "bookmark_big" / "bm_1066_hastings.dds")
    save_dds(np.zeros((van.height, van.width, 4), np.uint8), MOD / "gfx" / "interface" / "icons" / "bookmark_big" / (BOOKMARK + ".dds"))
    out += ["icons/bookmark_buttons/" + BOOKMARK + ".dds", "icons/bookmark_big/" + BOOKMARK + ".dds"]
    return out


LOC = """l_english:
 PICK_ANY_CHARACTER: "Play as any #bold MP#! in #bold [GameSetup.GetSelectedBookmark.GetDate.GetYear]#!, or #bold create your own!#!"
"""


def build_loc():
    p = MOD / "localization" / "english" / "replace" / "wm_bookmark_screen_l_english.yml"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# Generated by westminster/tools/ui/build_bookmark_screen.py - edit there.\n" + LOC, encoding="utf-8-sig")


# ------------------------------------------------------------------------------------------------ portraits

DUMPS = ROOT / "art" / "bookmark_portraits"
USER_DUMPS = Path("~/Documents/Paradox Interactive/Crusader Kings III/common/bookmark_portraits").expanduser()
# The game has no modern clothes: each featured character wears the plainest set (no furs, crowns or armour).
CLOTHES = ("fp4_western_bedchamber_clothes", 40)   # a plain linen shirt: the nearest to modern dress


def import_dumps():
    """Copies the game's dump (console command dump_bookmark_portraits, written to the user folder) into the cache."""
    DUMPS.mkdir(parents=True, exist_ok=True)
    n = 0
    for _, name in featured():
        f = USER_DUMPS / (name + ".txt")
        if f.exists():
            text = f.read_text(encoding="utf-8-sig")
            text = "\n".join(re.sub(r"^ +(?=\t)", "", line).rstrip() for line in text.splitlines()).rstrip() + "\n"
            (DUMPS / f.name).write_text(text, encoding="utf-8")
            n += 1
    return n


def build_portraits():
    """common/bookmark_portraits/<bookmark character>.txt: the portraits the bookmark screen shows (without one, a
    grey silhouette). The game writes them itself from the characters' likenesses (DNA and portrait modifiers) with
    the console command dump_bookmark_portraits in a game on the bookmark's date; the dumps are kept in
    art/bookmark_portraits/ (refresh: start a 2024 game in debug mode, run the command in the console, then this
    script with --import-dump). Here only their clothes change (CLOTHES), and headgear and cloaks are removed."""
    out_dir = MOD / "common" / "bookmark_portraits"
    out_dir.mkdir(parents=True, exist_ok=True)
    done = []
    for _, name in featured():
        dump = DUMPS / (name + ".txt")
        if not dump.exists():
            raise FileNotFoundError("Export this bookmark from CK3 with dump_bookmark_portraits, then run --import-dump: " + name)
        src = dump.read_text(encoding="utf-8-sig")
        body = src.split("\n", 2)[2] if src.startswith("# Auto generated") else src
        body, k = re.subn(r'clothes=\{ "[a-z0-9_]+" \d+', 'clothes={ "%s" %d' % CLOTHES, body)
        assert k == 1, name
        body = re.sub(r'headgear=\{ "[a-z0-9_]+"', 'headgear={ "no_headgear"', body)
        body = re.sub(r'cloaks=\{ "[a-z0-9_]+"', 'cloaks={ "no_cloak"', body)
        body = "\n".join(re.sub(r"^ +(?=\t)", "", line).rstrip() for line in body.splitlines()).rstrip() + "\n"
        head = ("# Generated by westminster/tools/ui/build_bookmark_screen.py - edit there. From the game's own dump\n"
                "# (console command dump_bookmark_portraits, art/bookmark_portraits/%s.txt), with plain clothes.\n" % name)
        (out_dir / (name + ".txt")).write_text(head + body, encoding="utf-8-sig")
        done.append(name)
    return done


# ------------------------------------------------------------------------------------------------ main

def main():
    apply_bookmark_winners()
    colours, names = party_colours()
    positions = layout()
    if ERA:
        bookmark_path = MOD / ("common/bookmarks/bookmarks/wm_%s_bookmark.txt" % YEAR)
        bookmark_text = bookmark_path.read_text(encoding="utf-8-sig")
        for name, (x, y) in positions.items():
            pattern = r'(name = "' + re.escape(name) + r'".*?position = \{ )\d+ \d+( \})'
            bookmark_text = re.sub(pattern, lambda m: m[1] + "%d %d" % (x, y) + m[2], bookmark_text, flags=re.S)
        bookmark_path.write_text(bookmark_text, encoding="utf-8-sig")
    bg = background(colours, names, positions)
    OUT.mkdir(parents=True, exist_ok=True)
    bg.convert("RGBA").save(OUT / (BOOKMARK + ".dds"), pixel_format="DXT1")
    print("background:", OUT / (BOOKMARK + ".dds"))
    if ERA:
        FEATURED = [(name,) for name in ERAS[YEAR]["featured"]]
    elif HISTORIC:
        from build_1979 import FEATURED
    else:
        from build_2024 import FEATURED
    by_seat = {r["seat"]: r for r in seats()}
    for (seat, name), f in zip(featured(), FEATURED):
        party = by_seat[seat]["winner"] if ERA else (by_seat[seat]["winner"] if (f[0] in ("Margaret Thatcher", "James Callaghan", "David Steel") if HISTORIC else f[4]) else None)
        im = location_image(seat, party)
        im.save(OUT / ("%s_%s.dds" % (BOOKMARK, name)), pixel_format="DXT5")
        print("location image:", name, positions[name])
    print("gui:", build_gui())
    print("chrome textures:", build_chrome_textures(colours))
    build_loc()
    if "--import-dump" in sys.argv:
        print("portrait dumps imported:", import_dumps())
    print("bookmark portraits:", build_portraits())
    if "--preview" in sys.argv:
        TEST_OUT.mkdir(parents=True, exist_ok=True)
        pv = bg.copy()
        d = ImageDraw.Draw(pv)
        for name, (x, y) in positions.items():
            y -= CHAR_DY
            d.rectangle([x, y, x + CHAR_W, y + CHAR_H], outline=(200, 0, 0))
            d.rectangle([x + BANNER[0], y + BANNER[1], x + BANNER[2], y + BANNER[3]], outline=(0, 0, 200))
            d.text((x + 70, y + 160), name.replace("bookmark_2024_", "").replace("bookmark_1979_", ""), fill=(0, 0, 0))
        d.rectangle(SAFE, outline=(0, 160, 0))
        pv.save(TEST_OUT / "preview.png")
        print("preview:", TEST_OUT / "preview.png")


if __name__ == "__main__":
    main()
