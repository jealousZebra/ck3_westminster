#!/usr/bin/env python3
"""Modern icons for what the map shows (ROADMAP 0.4 item 5): map-mode buttons, holdings, capital markers and the
county markers, as flat newspaper badges in the style of the ideology and stat icons (build_ideology_icons.py,
build_stat_icons.py): an ink ring, a paper hairline, a coloured disc and a bold pictogram.

    .venv/bin/python westminster/tools/ui/build_map_icons.py [--fetch-only] [pictogram ...]   # names fetch only those

Pictograms are black-on-white silhouettes from fal.ai (FLUX dev), cached in westminster/art/fal/mapicon_<key>.jpg
(delete one to regenerate it; the API key comes from $FAL_KEY or ~/.config/fal/key, as for fal_images.py). The
capital star is drawn here. Offline once cached. Run after build_theme.py (it reads gui/shared/buttons.gui).

Meanings (vanilla -> Westminster):
  holdings     castle -> constituency office, city -> town hall, church -> community centre,
               temple citadel -> party HQ, tribal/herder/nomad -> a house; camp -> campaign office (megaphone),
               estates and manors (domiciles) -> a house
  capitals     county capital -> a ballot box (the constituency's seat), realm capital -> a gold star
  markers      building available -> a hard hat, low control -> a key on red, hired troops -> volunteers
  map modes    realms -> party map (rosette), de jure counties/duchies/kingdoms/empires/hegemonies ->
               constituencies (ballot box), regions (map pin), nations (flag), the UK (Elizabeth Tower), world (globe);
               faiths -> ideology (light bulb), cultures -> identity (ID card), houses -> party members (people),
               languages -> speech bubbles, landless -> activists (megaphone), and so on (MAP_MODES below)

Replaces, at vanilla's paths and sizes (uncompressed RGBA DDS, like vanilla), under westminster/westminster/:
  gfx/interface/icons/flat_icons/map_modes/<mode>.dds     every map mode (60/70/120/140 px, as vanilla)
  gfx/interface/icons/icon_holding_{castle,church,city,temple_citadel}.dds, text_icons/icon_holding.dds,
  map_icons/onmap_holding_icon.dds                         holding badges
  gfx/interface/icons/holding_types_tab/<holding>.dds      county-view tab glyphs: flat black silhouettes, because
                                                           the GUI tints them (additive) like vanilla's
  gfx/interface/icons/icon_capital.dds                     120x60 strip, 2 frames: county capital, realm capital
  gfx/interface/icons/map_icons/county_{building_available,low_control,hired_troops}.dds,
  map_icons/map_icon_{camp,estate,estate_church,chinese_manor,japanese_manor,yurt}.dds
And writes gui/wm_map_icons.gui: the type icon_button_mapmode, copied from the mod's gui/shared/buttons.gui
(build_theme.py's) without the additive tint vanilla puts on button icons (Master_Button_Modify_Texture), which
would wash out a coloured badge. Also writes westminster/tools/test_out/map_icons.png, a contact sheet (native
size, then 24 and 16 px on paper, on the night-edition charcoal and on a map green).
"""
import io
import re
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                                  # westminster/
MOD = ROOT / "westminster"
CACHE = ROOT / "art" / "fal"
SHEET = ROOT / "tools/test_out/map_icons.png"
GUI_OUT = MOD / "gui/wm_map_icons.gui"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT.parent / "common" / "tools"))
import fal_images                                          # noqa: E402  (api_key, request, SIZES)
from ck3paths import GAME                                  # noqa: E402

MODEL = "fal-ai/flux/dev"
STYLE = ("flat solid black silhouette pictogram, simple bold filled shapes, thick chunky forms, no thin lines, "
         "no outlines, centred with wide empty margins, pure white background, no text, no letters, no shading, "
         "no frame, no circle, vector icon")

INK = (40, 38, 36)
PAPER = (235, 229, 213)
EDGE, RING, HAIR = 0.02, 0.08, 0.022    # ring geometry (fractions of the icon), as the stat icons
REACH = 0.355                           # the pictogram stays within this radius (the disc is 0.398)

# Colours (muted newspaper tones; each readable on paper, charcoal and the map)
RED, NAVY, BLUE, TEAL = (170, 28, 36), (30, 52, 96), (36, 116, 190), (0, 120, 120)
GREEN, LEAF, OLIVE = (44, 130, 72), (110, 154, 40), (120, 128, 52)
ORANGE, GOLD, AMBER = (214, 120, 36), (204, 158, 40), (226, 160, 40)
PURPLE, MAGENTA, BROWN, SLATE = (104, 72, 160), (170, 48, 110), (128, 84, 52), (78, 92, 108)
SILVER = (150, 156, 162)

# Pictograms from FLUX: key -> subject
PICTOS = {
    "ballot_box": "a ballot box seen from the front, a plain box with a slot in its lid and a folded ballot paper "
                  "half way into the slot",
    "office": "the front of a small high street office: a shop front with one big window on the left and a door "
              "on the right, a flat sign board above them and a flat roof",
    "town_hall": "a civic town hall building, front view, symmetrical, with a tall square clock tower in the "
                 "centre with a round clock face, and two wings with tall windows",
    "party_hq": "a tall modern office tower block with a grid of square windows and a flag flying from a short "
                "pole on its roof",
    "community": "a simple single storey community hall with a pitched roof and wide double doors, and a heart "
                 "shape on the gable above the doors",
    "megaphone": "a megaphone loudhailer pointing to the right, side view, a wide cone with a handle underneath",
    "house": "a detached house with a pitched roof, a chimney, a door and two windows, front view",
    "rosette": "an election rosette: a round pleated ribbon rosette with a plain round centre and two ribbon "
               "tails with notched ends hanging down below it",
    "map": "a folded paper map seen from the front: four solid black panels folded in a zigzag like an accordion, "
           "with a thick white winding road line cut out across them",
    "flag": "a rectangular flag on a tall flagpole, the flag waving to the right from the top of the pole",
    "tower": "the Elizabeth Tower clock tower in London (Big Ben), tall and narrow, a square tower with a big round "
             "clock face near the top and a tall pointed spire",
    "globe": "a simple solid black ball with thick white curved lines of latitude and longitude cut out of it, "
             "no continents, standing on a small thick curved stand",
    "bulb": "a light bulb standing upright, round glass bulb at the top and a ribbed screw base at the bottom",
    "id_card": "an identity card in landscape format with rounded corners, a head and shoulders portrait silhouette "
               "cut out on the left half and three thick lines cut out on the right half",
    "people": "three people standing side by side, head and shoulders, the middle one taller and in front",
    "bubbles": "two overlapping speech bubbles, a big rounded one at the front left with a tail at the bottom left, "
               "and a smaller one behind it at the top right",
    "person": "a single person, head and shoulders bust, front view",
    "handshake": "two hands shaking, a firm handshake, side view, horizontal",
    "envelope": "a closed envelope letter, front view, with the V of the flap cut out as a thick white line",
    "puzzle": "two jigsaw puzzle pieces fitting together side by side, classic shape with round knobs",
    "key": "a single door key lying diagonally, a big round bow with a hole at the top left and the bit at the "
           "bottom right",
    "hardhat": "a builder's hard hat safety helmet, side view, a rounded dome with a ridge along the top and a "
               "wide flat brim at the front",
    "skyline": "three office buildings side by side of different heights, the tallest in the middle, with "
               "rows of square windows cut out",
    "virus": "a virus particle: a round ball with short thick spikes ending in round knobs all around it",
    "sprout": "a seedling sprout with two big rounded leaves growing from a small mound of soil",
    "portico": "a classical government building front: a triangular pediment on four thick columns standing on "
               "wide steps",
    "placard": "a protest placard: a big solid black rectangular sign board on a thick solid black stick, held "
               "upright, all black",
    "pin": "a map location pin marker, a teardrop shape pointing down with a round hole near the top",
    "newspaper": "a folded newspaper, front page, three quarter view, with thick bars for headlines and a blank "
                 "rectangle for a photo",
    "suitcase": "a suitcase with a handle on top, front view, upright",
    "mountains": "two mountain peaks side by side, the left one bigger, with snow caps cut out",
    "mountain_tree": "a single mountain peak with a pine tree standing in front of it on the right",
    "warning": "a warning triangle road sign with rounded corners and an exclamation mark cut out of it",
    "arrows": "two thick arrows pointing towards each other, head to head, horizontal, one from the left and one "
              "from the right, nearly touching in the middle",
}

# Grey levels (0-255) read as ink in a cached pictogram, for pictograms FLUX drew holes in as grey
INK_BAND = {"rosette": (0, 110)}

# badge name: (pictogram, disc colour, pictogram colour, pictogram scale)
BADGES = {
    # holdings and markers
    "office": ("office", RED, PAPER, 0.70),
    "town_hall": ("town_hall", TEAL, PAPER, 0.72),
    "party_hq": ("party_hq", INK, PAPER, 0.72),
    "community": ("community", GREEN, PAPER, 0.70),
    "home": ("house", BROWN, PAPER, 0.68),
    "campaign": ("megaphone", MAGENTA, PAPER, 0.72),
    "seat": ("ballot_box", PAPER, INK, 0.68),
    "capital": ("star", RED, PAPER, 0.74),
    "build": ("hardhat", ORANGE, INK, 0.74),
    "low_control": ("key", RED, PAPER, 0.70),
    "volunteers": ("people", NAVY, PAPER, 0.74),
    # map modes
    "mm_realms": ("rosette", RED, PAPER, 0.74),
    "mm_counties": ("ballot_box", PAPER, INK, 0.68),
    "mm_duchies": ("pin", BLUE, PAPER, 0.66),
    "mm_kingdoms": ("flag", NAVY, PAPER, 0.72),
    "mm_empires": ("tower", INK, PAPER, 0.76),
    "mm_hegemonies": ("globe", SLATE, PAPER, 0.72),
    "mm_religions": ("bulb", GOLD, INK, 0.72),
    "mm_cultures": ("id_card", TEAL, PAPER, 0.74),
    "mm_houses": ("people", PURPLE, PAPER, 0.74),
    "mm_languages": ("bubbles", ORANGE, PAPER, 0.72),
    "mm_landless": ("megaphone", MAGENTA, PAPER, 0.72),
    "mm_players": ("person", GREEN, PAPER, 0.68),
    "mm_diplomacy": ("handshake", BLUE, PAPER, 0.76),
    "mm_relations": ("envelope", BROWN, PAPER, 0.70),
    "mm_confederations": ("puzzle", OLIVE, PAPER, 0.68),
    "mm_control": ("key", SLATE, PAPER, 0.70),
    "mm_development": ("hardhat", ORANGE, INK, 0.74),
    "mm_economy": ("skyline", GREEN, PAPER, 0.72),
    "mm_epidemics": ("virus", (176, 60, 40), PAPER, 0.70),
    "mm_fertility": ("sprout", LEAF, PAPER, 0.70),
    "mm_government": ("portico", NAVY, PAPER, 0.72),
    "mm_holy_orders": ("placard", MAGENTA, PAPER, 0.70),
    "mm_clerical": ("map", RED, PAPER, 0.72),
    "mm_legends": ("newspaper", INK, PAPER, 0.74),
    "mm_migration": ("suitcase", BROWN, PAPER, 0.66),
    "mm_simple_terrain": ("mountains", OLIVE, PAPER, 0.74),
    "mm_terrain": ("mountain_tree", GREEN, PAPER, 0.74),
    "mm_situation": ("warning", AMBER, INK, 0.72),
    "mm_struggle": ("arrows", SLATE, PAPER, 0.76),
}

MAP_MODES = {
    "realms": "mm_realms", "dejure_counties": "mm_counties", "dejure_duchies": "mm_duchies",
    "dejure_kingdoms": "mm_kingdoms", "dejure_empires": "mm_empires", "dejure_hegemonies": "mm_hegemonies",
    "religions": "mm_religions", "cultures": "mm_cultures", "houses": "mm_houses",
    "court_languages": "mm_languages", "landless_rulers": "mm_landless", "players": "mm_players",
    "diplomacy": "mm_diplomacy", "diplomatic_relations": "mm_relations", "confederations": "mm_confederations",
    "county_control": "mm_control", "county_development": "mm_development", "economy_buildings": "mm_economy",
    "epidemics": "mm_epidemics", "fertility": "mm_fertility", "government": "mm_government",
    "holy_orders": "mm_holy_orders", "clerical_regions": "mm_clerical", "legends": "mm_legends",
    "migration_counties": "mm_migration", "simple_terrain": "mm_simple_terrain", "terrain": "mm_terrain",
    "situation": "mm_situation", "struggle": "mm_struggle",
}


# ---------------------------------------------------------------- pictograms

def generate(subject, key):
    job = fal_images.request("https://queue.fal.run/" + MODEL, key,
                             {"prompt": subject + ", " + STYLE, "image_size": fal_images.SIZES["square"],
                              "num_inference_steps": 32, "num_images": 1, "enable_safety_checker": True})
    for _ in range(120):
        if fal_images.request(job["status_url"], key).get("status") == "COMPLETED":
            break
        time.sleep(2)
    else:
        raise TimeoutError("fal job did not finish")
    return fal_images.request(job["response_url"], key)["images"][0]["url"]


def fetch(n, key):
    """Download a generation and cache it as JPEG (quality 90, progressive, like the other art)."""
    with urllib.request.urlopen(generate(PICTOS[n], key), timeout=120) as r:
        im = Image.open(io.BytesIO(r.read())).convert("RGB")
    im.save(CACHE / ("mapicon_%s.jpg" % n), quality=90, progressive=True)


def crop_mask(a):
    ys, xs = np.nonzero(a > 0.3)
    if not len(ys):
        raise ValueError("empty pictogram")
    return Image.fromarray((a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] * 255).astype(np.uint8))


def silhouette(raw, band=None):
    """Black-on-white pictogram -> alpha mask cropped to the ink (only grey levels within band, if given). Specks
    away from the main shape (FLUX's stray dots) are dropped."""
    g = np.array(Image.open(raw).convert("L")).astype(np.float32)
    if band is None:
        a = np.clip((191 - g) / 115, 0, 1)
    else:
        lo, hi = band
        a = np.clip((hi - g) / 16 + 0.5, 0, 1) * (np.clip((g - lo) / 16 + 0.5, 0, 1) if lo > 0 else 1)
    a[:8], a[-8:], a[:, :8], a[:, -8:] = 0, 0, 0, 0          # JPEG edge noise
    return crop_mask(drop_specks(a))


def drop_specks(a, keep=0.004):
    """Zero connected blobs smaller than keep x the image (a cheap flood fill on a 4x downsampled grid)."""
    small = a[::4, ::4] > 0.3
    h, w = small.shape
    label = np.zeros((h, w), np.int32)
    sizes = [0]
    for y in range(h):
        for x in range(w):
            if small[y, x] and not label[y, x]:
                n = len(sizes)
                stack, count = [(y, x)], 0
                label[y, x] = n
                while stack:
                    cy, cx = stack.pop()
                    count += 1
                    for ny, nx in ((cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)):
                        if 0 <= ny < h and 0 <= nx < w and small[ny, nx] and not label[ny, nx]:
                            label[ny, nx] = n
                            stack.append((ny, nx))
                sizes.append(count)
    small_ids = [i for i, c in enumerate(sizes) if i and c < keep * h * w]
    if small_ids:
        bad = np.isin(label, small_ids)
        big = np.kron(bad, np.ones((4, 4), bool))[:a.shape[0], :a.shape[1]]
        a = a.copy()
        a[big] = 0
    return a


def star_mask():
    """A bold five-pointed star (the cartographer's capital)."""
    s = 1000
    im = Image.new("L", (s, s), 0)
    pts = []
    for i in range(10):
        r = s * (0.48 if i % 2 == 0 else 0.2)
        ang = np.radians(-90 + i * 36)
        pts.append((s / 2 + r * np.cos(ang), s / 2 + r * np.sin(ang)))
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return crop_mask(np.array(im).astype(np.float32) / 255)


_MASKS = {}


def mask(picto):
    if picto not in _MASKS:
        _MASKS[picto] = star_mask() if picto == "star" else silhouette(CACHE / ("mapicon_%s.jpg" % picto),
                                                                       INK_BAND.get(picto))
    return _MASKS[picto]


def reach(m):
    a = np.array(m) > 76
    ys, xs = np.nonzero(a)
    return float(np.sqrt((ys - (a.shape[0] - 1) / 2) ** 2 + (xs - (a.shape[1] - 1) / 2) ** 2).max())


# ---------------------------------------------------------------- drawing (at 8x, scaled down)

def paste_mark(im, m, colour, scale, centre, reach_frac=REACH):
    s = im.width
    f = min(s * scale / max(m.size), s * reach_frac / reach(m))
    m = m.resize((max(1, round(m.width * f)), max(1, round(m.height * f))), Image.LANCZOS)
    layer = Image.new("RGBA", m.size, colour + (255,))
    layer.putalpha(m)
    im.alpha_composite(layer, (int(centre[0] - m.width / 2), int(centre[1] - m.height / 2)))


def badge(name, w, h=None, ring=INK, pad=1.0):
    """One badge at w x h (centred, square): ring, paper hairline, disc, pictogram. pad < 1 leaves a margin."""
    h = h or w
    size = max(1, round(min(w, h) * pad))
    s = size * 8
    picto, disc, colour, scale = BADGES[name]
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    edge = s * EDGE
    d.ellipse((edge, edge, s - edge, s - edge), fill=ring + (255,))
    ring_w = s * RING
    d.ellipse((ring_w, ring_w, s - ring_w, s - ring_w), fill=PAPER + (255,))
    if disc != PAPER:
        inner = ring_w + s * HAIR
        d.ellipse((inner, inner, s - inner, s - inner), fill=disc + (255,))
    paste_mark(im, mask(picto), colour, scale, (s / 2, s / 2))
    im = im.resize((size, size), Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(im, ((w - size) // 2, (h - size) // 2))
    return out


def flat(picto, w, h=None, fill=0.86):
    """The bare pictogram in black, for textures the GUI tints itself (the county view's holding tabs)."""
    h = h or w
    s = min(w, h) * 8
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    paste_mark(im, mask(picto), (0, 0, 0), fill, (s / 2, s / 2), reach_frac=0.48)
    im = im.resize((min(w, h),) * 2, Image.LANCZOS)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(im, ((w - im.width) // 2, (h - im.height) // 2))
    return out


def strip(w, h, frames):
    """Frames side by side at vanilla's frame boundaries (frame i covers round(i*w/n) .. round((i+1)*w/n))."""
    n = len(frames)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    for i, make in enumerate(frames):
        x0, x1 = round(i * w / n), round((i + 1) * w / n)
        out.alpha_composite(make(x1 - x0, h), (x0, 0))
    return out


def plain(name, **kw):
    return lambda w, h=None: badge(name, w, h, **kw)


def tab(picto):
    return lambda w, h=None: flat(picto, w, h)


# ---------------------------------------------------------------- targets

I = "gfx/interface/icons/"


def targets():
    """vanilla path -> function(w, h) -> image (or a list of frame functions for a strip)."""
    t = {}
    for mode, name in MAP_MODES.items():
        t[I + "flat_icons/map_modes/%s.dds" % mode] = plain(name)
    # holdings
    t[I + "icon_holding_castle.dds"] = plain("office")
    t[I + "icon_holding_city.dds"] = plain("town_hall")
    t[I + "icon_holding_church.dds"] = plain("community")
    t[I + "icon_holding_temple_citadel.dds"] = plain("party_hq")
    t[I + "text_icons/icon_holding.dds"] = plain("office")
    t[I + "map_icons/onmap_holding_icon.dds"] = plain("office")
    for holding, picto in (("castle_holding", "office"), ("city_holding", "town_hall"),
                           ("church_holding", "community"), ("temple_citadel_holding", "party_hq"),
                           ("tribal_holding", "house"), ("herder_holding", "house"), ("nomad_holding", "house")):
        t[I + "holding_types_tab/%s.dds" % holding] = tab(picto)
    # capitals: frame 1 county capital (the constituency's seat), frame 2 realm capital
    t[I + "icon_capital.dds"] = [plain("seat", ring=SILVER), plain("capital", ring=GOLD)]
    # county markers on the map
    t[I + "map_icons/county_building_available.dds"] = plain("build")
    t[I + "map_icons/county_low_control.dds"] = plain("low_control")
    t[I + "map_icons/county_hired_troops.dds"] = plain("volunteers")
    # domiciles (the unlanded start's camp, estates)
    t[I + "map_icons/map_icon_camp.dds"] = plain("campaign")
    for name in ("estate", "estate_church", "chinese_manor", "japanese_manor", "yurt"):
        t[I + "map_icons/map_icon_%s.dds" % name] = plain("home")
    return t


def render(path, make):
    w, h = Image.open(GAME / path).size
    if isinstance(make, list):
        return strip(w, h, make)
    return make(w, h)


# ---------------------------------------------------------------- GUI: map-mode buttons without the tint

def write_gui():
    """Copy type icon_button_mapmode from the mod's buttons.gui (or vanilla's) and switch off the additive tint
    on its icon, so the coloured badges show as drawn. The button's own frame still shows hover and selection."""
    src = MOD / "gui/shared/buttons.gui"
    if not src.exists():
        src = GAME / "gui/shared/buttons.gui"
    text = src.read_text(encoding="utf-8-sig")
    m = re.search(r"\n(\ttype icon_button_mapmode = widget \{.*?\n\t\})\n", text, re.S)
    if not m:
        sys.exit("type icon_button_mapmode not found in " + str(src))
    block = m.group(1)
    new, n = re.subn(r"(\n(\t+)button_icon = \{\n)", r'\1\2\tblockoverride "button_icon_modify_texture" {}\n',
                     block, count=1)
    if n != 1:
        sys.exit("button_icon not found in icon_button_mapmode")
    GUI_OUT.write_text("﻿# Westminster: the map-mode button type from gui/shared/buttons.gui (Crusader Kings III, "
                       "Paradox Interactive), with no tint on its icon, so the map-mode badges keep their colours. "
                       "Written by westminster/tools/ui/build_map_icons.py - edit there.\n\ntypes WmMapIcons\n{\n"
                       + new + "\n}\n", encoding="utf-8")


# ---------------------------------------------------------------- contact sheet

def contact_sheet(rows, cols=4):
    """rows: (label, image), laid out in a grid. Each cell: the label, the texture at native size on the map's
    green, then 24 and 16 px (by height) on paper, the night edition's charcoal and the map's green."""
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    except OSError:
        font = ImageFont.load_default()
    pad = 10
    bgs = ((235, 229, 213), (29, 31, 34), (128, 140, 84))

    def small(im, px):
        return im.resize((max(1, round(im.width * px / im.height)), px), Image.LANCZOS)
    native_w = max(im.width for _, im in rows)
    cell_w = max(380, native_w + 2 * pad + 6 * 40)
    cell_h = max(im.height for _, im in rows) + 3 * pad + 14
    nrows = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, nrows * cell_h), (250, 247, 240))
    d = ImageDraw.Draw(sheet)
    for i, (label, im) in enumerate(rows):
        x0, y0 = (i % cols) * cell_w + pad, (i // cols) * cell_h + pad
        d.text((x0, y0), label, fill=(30, 30, 30), font=font)
        y = y0 + 18
        native = Image.new("RGB", im.size, bgs[2])
        native.paste(im, (0, 0), im)
        sheet.paste(native, (x0, y))
        x = x0 + im.width + 12
        for bg in bgs:
            for px in (24, 16):
                sm = small(im, px)
                box = Image.new("RGB", (sm.width + 8, sm.height + 8), bg)
                box.paste(sm, (4, 4), sm)
                sheet.paste(box, (x, y))
                x += box.width + 2
            x += 6
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(SHEET)
    return SHEET


def main():
    args = sys.argv[1:]
    fetch_only = "--fetch-only" in args
    args = [a for a in args if a != "--fetch-only"]
    CACHE.mkdir(parents=True, exist_ok=True)
    key = None
    for n in [a for a in args if a in PICTOS] or list(PICTOS):
        raw = CACHE / ("mapicon_%s.jpg" % n)
        if not raw.exists():
            key = key or fal_images.api_key()
            fetch(n, key)
            print("generated", raw.relative_to(ROOT.parent))
    if fetch_only:
        return
    rows = []
    for path, make in targets().items():
        if not (GAME / path).exists():
            print("skip (no vanilla file)", path)
            continue
        im = render(path, make)
        out = MOD / path
        out.parent.mkdir(parents=True, exist_ok=True)
        im.save(out)                  # Pillow writes uncompressed 32-bit RGBA DDS, as vanilla's icons
        rows.append((path[len(I):], im))
    print("wrote %d textures" % len(rows))
    write_gui()
    print("wrote", GUI_OUT.relative_to(ROOT.parent))
    print("contact sheet", contact_sheet(rows).relative_to(ROOT.parent))


if __name__ == "__main__":
    main()
