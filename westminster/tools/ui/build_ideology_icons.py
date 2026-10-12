#!/usr/bin/env python3
"""Icons for the ideologies (faiths) and political camps (religions): a flat newspaper badge per key, an ink ring
around a disc with a bold pictogram. Ideologies are a coloured disc with a paper (or ink) pictogram; camps and
"Not Stated" are a paper disc with a coloured (or ink) mark. Symbols are generic, never a party's logo.

    .venv/bin/python westminster/tools/ui/build_ideology_icons.py [key ...]

Each pictogram is a black-on-white silhouette from fal.ai (FLUX), cached in westminster/art/fal/ideo_<key>.jpg
(delete one to regenerate it; the API key comes from $FAL_KEY or ~/.config/fal/key, as for fal_images.py). Offline
once every image is cached.

CK3 has no separate icon for a religion: the game shows faith icons only (common/religion faith `icon = <key>`,
looked up in gfx/interface/icons/faith/). The camp icons sit in the same folder, for a faith or GUI to use by name.
Vanilla's faith icons are 100x100 uncompressed RGBA DDS (checked on catholic.dds, sunni.dds), matched here.

Writes:
  westminster/gfx/interface/icons/faith/<key>.dds      every wm_ideo_* and wm_camp_* key
  westminster/gfx/interface/icons/faith/wm_faith_not_stated.dds   a paper badge with a dash
  westminster/tools/test_out/ideology_icons.png         contact sheet at 100, 48 and 24 px
"""
import io
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
OUT = MOD / "gfx/interface/icons/faith"
SHEET = ROOT / "tools/test_out/ideology_icons.png"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT.parent / "common" / "tools"))
import fal_images                                          # noqa: E402  (api_key, request, SIZES)
from ck3paths import GAME                                  # noqa: E402

MODEL = "fal-ai/flux/dev"
STYLE = ("flat solid black silhouette pictogram, simple bold filled shapes, thick chunky forms, no thin lines, "
         "no outlines, centred with wide empty margins, pure white background, no text, no letters, no shading, "
         "no frame, no circle, vector icon")

INK = (40, 38, 36)          # as wm_faith_not_stated.dds
PAPER = (235, 229, 213)
REACH = 0.30               # the pictogram stays within this radius (fraction of the icon; the disc is 0.355)
FALLBACK_SIZE = 100         # if the game isn't installed: vanilla's faith icon size

# key: (pictogram subject, disc colour, pictogram colour, pictogram scale). Ideologies grouped by camp.
DESIGNS = {
    # Left: reds and green
    "wm_ideo_socialist": ("a raised clenched fist, front view, wrist at the bottom", (170, 28, 36), PAPER, 0.62),
    "wm_ideo_social_democrat": ("two open cupped hands held together holding a heart above them",
                                (222, 92, 72), PAPER, 0.64),
    "wm_ideo_green": ("a single broad leaf with a short stem, tilted diagonally", (44, 138, 72), PAPER, 0.62),
    # Centre: orange, violet, teal
    "wm_ideo_liberal": ("a feather quill pen standing diagonally, nib at the bottom left", (236, 132, 32), INK, 0.64),
    "wm_ideo_centrist": ("a balanced pair of scales of justice with two pans level, symmetrical",
                         (118, 82, 160), PAPER, 0.64),
    "wm_ideo_cross_community": ("a handshake of two clasped hands, side view, horizontal", (54, 136, 146), PAPER,
                                0.68),
    # Right: blues, gold
    "wm_ideo_one_nation": ("a single wide arched stone bridge, side view, one broad semicircular arch, thick deck",
                           (56, 104, 184), PAPER, 0.66),
    "wm_ideo_free_market": ("a bar chart of three rising vertical bars, short to tall from left to right",
                            (206, 160, 44), INK, 0.56),
    "wm_ideo_national_conservative": ("a heraldic lion walking to the left, side view, tail raised, one paw lifted",
                                      (24, 46, 100), PAPER, 0.68),
    "wm_ideo_populist_right": ("a megaphone loudspeaker pointing to the right, side view", (22, 166, 196), PAPER,
                               0.64),
    # Nationalist: yellow and greens
    "wm_ideo_scottish_nationalist": ("a single thistle flower with a spiky round head and two spiky leaves on a "
                                     "stem", (244, 206, 52), INK, 0.66),
    "wm_ideo_welsh_nationalist": ("a single large daffodil flower head with a bold trumpet and six broad petals, "
                                  "three quarter view, on a short thick stem with one broad leaf", (0, 102, 92), PAPER, 0.66),
    "wm_ideo_irish_republican": ("a Celtic harp, side view, ornate curved frame with strings", (0, 96, 48), PAPER,
                                 0.64),
    "wm_ideo_irish_nationalist": ("a shamrock with three round heart-shaped leaves and a short stem",
                                  (96, 168, 64), PAPER, 0.62),
    # Unionist
    "wm_ideo_unionist": ("two interlocking oval chain links, horizontal, joined in the middle", (30, 40, 96),
                         PAPER, 0.66),
    # Camps (religions): paper disc, coloured mark
    "wm_camp_left": ("a bold thick arrow pointing left", PAPER, (170, 28, 36), 0.58),
    "wm_camp_centre": ("a solid round dot inside a thick ring, bullseye target with two parts", PAPER,
                       (118, 82, 160), 0.52),
    "wm_camp_right": ("a bold thick arrow pointing right", PAPER, (40, 80, 160), 0.58),
    "wm_camp_nationalist": ("a four pointed compass rose star with long sharp points", PAPER, (0, 110, 70), 0.64),
    "wm_camp_unionist": ("two interlocking thick rings overlapping side by side", PAPER, (30, 40, 96), 0.64),
}
NOT_STATED = "wm_faith_not_stated"


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
    with urllib.request.urlopen(generate(DESIGNS[n][0], key), timeout=120) as r:
        im = Image.open(io.BytesIO(r.read())).convert("RGB")
    im.save(CACHE / ("ideo_%s.jpg" % n), quality=90, progressive=True)


def silhouette(raw):
    """Black-on-white pictogram -> alpha mask cropped to the ink (white areas outside the shape are dropped)."""
    g = np.array(Image.open(raw).convert("L")).astype(np.float32) / 255
    a = np.clip((0.75 - g) / 0.45, 0, 1)
    ys, xs = np.nonzero(a > 0.3)
    if not len(ys):
        raise ValueError("no ink in %s" % raw)
    return Image.fromarray((a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] * 255).astype(np.uint8))


def reach(mask):
    """How far the ink reaches from the middle of its box (pixels): the radius that must fit inside the disc."""
    a = np.array(mask) > 76
    ys, xs = np.nonzero(a)
    return float(np.sqrt((ys - (a.shape[0] - 1) / 2) ** 2 + (xs - (a.shape[1] - 1) / 2) ** 2).max())


def badge(size, disc, mark=None, mark_colour=None, scale=0.62, dash=False):
    """The badge drawn at 8x and scaled down: ink ring, a paper hairline, the disc, the pictogram centred."""
    s = size * 8
    r = s / 2
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    edge = s * 0.03
    d.ellipse((edge, edge, s - edge, s - edge), fill=INK + (255,))
    ring = s * 0.115
    d.ellipse((ring, ring, s - ring, s - ring), fill=PAPER + (255,))
    if disc != PAPER:
        inner = ring + s * 0.03
        d.ellipse((inner, inner, s - inner, s - inner), fill=disc + (255,))
    if dash:
        d.rectangle((r - s * 0.2, r - s * 0.045, r + s * 0.2, r + s * 0.045), fill=INK + (255,))
    if mark is not None:
        m = mark.copy()
        f = min(s * scale / max(m.size), s * REACH / reach(m))     # diagonal shapes must not touch the ring
        m = m.resize((max(1, round(m.width * f)), max(1, round(m.height * f))), Image.LANCZOS)
        layer = Image.new("RGBA", m.size, mark_colour + (255,))
        layer.putalpha(m)
        im.alpha_composite(layer, (int(r - m.width / 2), int(r - m.height / 2)))
    return im.resize((size, size), Image.LANCZOS)


def save_dds(im, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path)                     # Pillow writes uncompressed 32-bit RGBA DDS, as vanilla's faith icons


def contact_sheet(icons):
    cell, pad = 190, 12
    cols = 5
    rows = (len(icons) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * cell), (250, 247, 240))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
    except OSError:
        font = ImageFont.load_default()
    for i, (k, im) in enumerate(icons):
        x, y = (i % cols) * cell, (i // cols) * cell
        sheet.paste(im, (x + pad, y + pad), im)
        sheet.paste(im.resize((48, 48), Image.LANCZOS), (x + pad + 110, y + pad), im.resize((48, 48), Image.LANCZOS))
        sm = im.resize((24, 24), Image.LANCZOS)
        sheet.paste(sm, (x + pad + 110, y + pad + 60), sm)
        dark = Image.new("RGB", (40, 40), (52, 48, 44))
        dark.paste(sm, (8, 8), sm)
        sheet.paste(dark, (x + pad + 140, y + pad + 52))
        d.text((x + pad, y + pad + 112), k.replace("wm_", ""), fill=(30, 30, 30), font=font)
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(SHEET)
    return SHEET


def main():
    names = sys.argv[1:] or list(DESIGNS)
    vanilla = GAME / "gfx/interface/icons/faith/catholic.dds"
    size = Image.open(vanilla).size[0] if vanilla.exists() else FALLBACK_SIZE
    CACHE.mkdir(parents=True, exist_ok=True)
    key = None
    for n in names:
        raw = CACHE / ("ideo_%s.jpg" % n)
        if not raw.exists():
            key = key or fal_images.api_key()
            fetch(n, key)
            print("generated", raw.name)
        _, disc, colour, scale = DESIGNS[n]
        save_dds(badge(size, disc, silhouette(raw), colour, scale), OUT / ("%s.dds" % n))
        print("icon", (OUT / ("%s.dds" % n)).relative_to(ROOT.parent))
    ns = OUT / ("%s.dds" % NOT_STATED)
    if True:                           # a matching paper badge with a dash (rebuilt every run: gfx/interface is gitignored)
        save_dds(badge(size, PAPER, dash=True), ns)
        print("icon", ns.relative_to(ROOT.parent))
    icons = [(NOT_STATED, Image.open(ns).convert("RGBA"))]
    icons += [(k, Image.open(OUT / ("%s.dds" % k)).convert("RGBA")) for k in DESIGNS if (OUT / ("%s.dds" % k)).exists()]
    print("contact sheet", contact_sheet(icons).relative_to(ROOT.parent))


if __name__ == "__main__":
    main()
