#!/usr/bin/env python3
"""The unlanded (adventurer) start in modern dress: the camp is a campaign office.

    .venv/bin/python westminster/tools/ui/build_campaign_office.py [--images-only | --no-images]

Run by build_ui.sh after build_theme.py and fal_images.py (it reads build_theme's palette when present).

1. Pictures (fal.ai FLUX dev, the house press-photo style of fal_images.py; cached in westminster/art/fal/co_*.jpg,
   prompts in art/fal/prompts_campaign_office.json; only a missing picture calls fal.ai, with the key from $FAL_KEY or
   ~/.config/fal/key), installed over vanilla's camp textures at their own paths and sizes:
     - the camp window's scene: every terrain backdrop (camp_terrain_*_bg) becomes one campaign office interior,
       darkened, and the foregrounds (camp_terrain_*_fg) a soft dark vignette;
     - each camp building's picture (laamp_building_*) becomes a photo pinned to the office wall (a white-bordered
       print with tape), with a click mask of the same shape; empty slots become an empty pinned card;
     - the camp's illustration (event_scenes/ep3_camp_arid_terrain, also the camp officers' backdrop): the office
       from the street;
     - the six camp purpose pictures (icons/laws/camp_purpose_*): one per political focus.
2. Localization (localization/english/replace/wm_campaign_office_l_english.yml): the camp, its purposes (political
   focuses), buildings, officers, supplies, temperament and the contract board in political words. Keys another
   mod localization file defines are skipped (build_terms.py, which runs before this, skips ours on its next run).
"""
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                                      # westminster/
MOD = ROOT / "westminster"
CACHE = ROOT / "art" / "fal"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT.parent / "common" / "tools"))
from ck3paths import GAME  # noqa: E402

WD = "gfx/interface/window_domiciles/"
NO_FACES = ", no people or only people seen from behind with no visible faces, no logos, no readable text"

# Pictures: name -> (fal size, prompt). The house STYLE is added by fal_images.generate.
PICTURES = {
    # the camp window's backdrop and the camp illustration
    "co_backdrop": ("co_wide",
                    "Wide interior of a constituency campaign office at night in a converted shop in a northern English "
                    "town, long room with desks, laptops, phones and stacks of leaflets, a large map of the constituency "
                    "on the far wall covered in coloured pins, whiteboards with rotas, empty office chairs, warm desk "
                    "lamps, dark moody light" + NO_FACES),
    "co_street": ("co_street",
                  "A campaign office in a converted shopfront on a northern English high street at dusk, warm light "
                  "spilling from the big windows, blank posters in the windows, wet pavement, terraced shops either "
                  "side" + NO_FACES),
    # the buildings, pinned to the wall as photographs
    "co_office_1": ("square", "A small rented room above a shop used as a volunteer campaign office, a folding table "
                    "with a laptop and a kettle, boxes of leaflets, a constituency map taped to the wall" + NO_FACES),
    "co_office_2": ("square", "A British high street shop unit converted into a campaign office, seen from the "
                    "pavement through the large window, desks and phones inside, lights on at dusk" + NO_FACES),
    "co_office_3": ("square", "A busy open-plan regional campaign headquarters, rows of desks with monitors and "
                    "phones, a big screen with charts on the wall, staff seen from behind" + NO_FACES),
    "co_print_room": ("square", "Cardboard boxes and neat stacks of plain folded A5 election leaflets beside a "
                      "large office printer in a campaign office storeroom, shelves of envelopes, no newspapers, no "
                      "photographs of people" + NO_FACES),
    "co_welfare": ("square", "A small staff rest room in an office, a worn sofa, a green first aid kit on the wall, "
                   "a water cooler, a pot plant, soft lamp light" + NO_FACES),
    "co_battle_bus": ("square", "A plain white minibus parked on a British town street with its side door open, "
                      "clipboards and boxes of leaflets on the seats, overcast day" + NO_FACES),
    "co_kitchen": ("square", "An office kitchenette in a campaign office late in the evening, a tea urn, mismatched "
                   "mugs, a stack of pizza boxes and a packet of biscuits on the counter" + NO_FACES),
    "co_meeting": ("square", "A circle of mismatched plastic chairs in a church hall set out for an evening campaign "
                   "team meeting, a flip chart, tea cups on the floor" + NO_FACES),
    "co_training": ("square", "A small training room with a whiteboard covered in a hand-drawn canvassing plan with "
                    "arrows, a flip chart, folding chairs and a projector screen" + NO_FACES),
    "co_front_desk": ("square", "The empty front desk of a small campaign office with nobody behind it, a reception "
                      "counter with an open visitors' book and a pen, a door entry intercom and a small security camera "
                      "on the wall" + NO_FACES),
    "co_fitting_out": ("square", "An empty shop unit being fitted out as an office, dust sheets, paint tins, a "
                       "stepladder and flat-packed desks in boxes, daylight" + NO_FACES),
    # the political focuses (camp purposes)
    "co_focus_activist": ("square", "Close-up of a plain white and grey rosette with no writing, a clipboard with a "
                          "canvassing sheet and a bundle of leaflets resting on a garden wall outside a terraced house" + NO_FACES),
    "co_focus_organiser": ("square", "Close-up of a hand pushing a leaflet through the letterbox of a terraced house "
                           "front door on a rainy evening, only the hand and sleeve visible" + NO_FACES),
    "co_focus_wonk": ("square", "Overhead view of a desk with a printed policy report, highlighter pens, a laptop "
                      "showing charts and a cup of coffee" + NO_FACES),
    "co_focus_pundit": ("square", "An empty guest chair in a television news studio with a microphone, bright studio "
                        "lights and cameras" + NO_FACES),
    "co_focus_consultant": ("square", "A laptop showing polling charts, a smartphone and a stack of business cards on "
                            "a table in a hotel bar, evening" + NO_FACES),
    "co_focus_fixer": ("square", "A dim Gothic stone corridor in the Palace of Westminster with two men in suits "
                       "talking quietly in silhouette, seen from behind" + NO_FACES),
}

# Vanilla building picture families (laamp_building_<family>[ _variant].dds) -> the photo pinned for them
BUILDING_PHOTOS = [
    (r"pavillion(_[a-z]+)?_level_01", "co_office_1"),
    (r"pavillion(_[a-z]+)?_level_02", "co_office_2"),
    (r"pavillion(_[a-z]+)?_level_03", "co_office_3"),
    (r"pavillion(_[a-z]+)?", "co_office_1"),
    (r"supply_tent", "co_print_room"),
    (r"barber", "co_welfare"),
    (r"baggage_train", "co_battle_bus"),
    (r"mess", "co_kitchen"),
    (r"roaring_campfire", "co_meeting"),
    (r"proving_grounds", "co_training"),
    (r"perimeter.*", "co_front_desk"),
    (r"under_construction.*", "co_fitting_out"),
    (r"empty_slot.*", None),                                  # an empty card
]

PURPOSE_PHOTOS = {
    "wanderers": "co_focus_activist", "explorers": "co_focus_organiser", "scholars": "co_focus_wonk",
    "brigands": "co_focus_pundit", "mercenaries": "co_focus_consultant", "legitimists": "co_focus_fixer",
}


# ------------------------------------------------------------------------------------------------ palette

def palette():
    """The UI palette: build_theme.py's night edition when it defines one, else the agreed dark defaults."""
    pal = {"panel": (0x1d, 0x1f, 0x22), "text": (0xec, 0xe7, 0xdc), "red": (0xc8, 0x10, 0x2e)}
    try:
        import build_theme  # noqa: E402
        for name, attr in (("panel", "PAPER"), ("text", "INK")):
            v = getattr(build_theme, attr, None)
            if v is not None and len(v) == 3:
                pal[name] = tuple(int(x) for x in v)
    except Exception:
        pass
    # a light "paper" panel would mean the light edition: keep the dark defaults for the office scene anyway
    if sum(pal["panel"]) > 3 * 128:
        pal["panel"], pal["text"] = (0x1d, 0x1f, 0x22), (0xec, 0xe7, 0xdc)
    return pal


# ------------------------------------------------------------------------------------------------ pictures

def fetch(names):
    """Generate any missing picture with fal.ai and cache it as JPEG (quality 90, progressive)."""
    missing = [n for n in names if not (CACHE / (n + ".jpg")).exists()]
    CACHE.mkdir(parents=True, exist_ok=True)
    import fal_images                                          # noqa: E402  (generate, api_key, STYLE)
    (CACHE / "prompts_campaign_office.json").write_text(json.dumps(
        {n: PICTURES[n][1] + ". " + fal_images.STYLE for n in PICTURES}, indent=1) + "\n")
    if not missing:
        return
    key = fal_images.api_key()
    fal_images.SIZES.update({"co_wide": {"width": 1920, "height": 880}, "co_street": {"width": 1600, "height": 848}})
    for n in missing:
        size, prompt = PICTURES[n]
        url = fal_images.generate(prompt, size, key)
        with urllib.request.urlopen(url, timeout=120) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGB")
        im.save(CACHE / (n + ".jpg"), quality=90, progressive=True, optimize=True)
        print("fetched", n, im.size)


def photo(name):
    return Image.open(CACHE / (name + ".jpg")).convert("RGB")


def cover(im, w, h):
    s = max(w / im.width, h / im.height)
    im = im.resize((max(w, round(im.width * s)), max(h, round(im.height * s))), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


def save_dds(im, rel):
    out = MOD / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    im = im.convert("RGBA")
    fmt = "DXT5" if im.width % 4 == 0 and im.height % 4 == 0 else None
    if fmt:
        im.save(out, pixel_format=fmt)
    else:
        im.save(out)


def save_png(im, rel):
    out = MOD / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)


def vsize(rel):
    return Image.open(GAME / rel).size


def backdrop(pal):
    """The scene behind the buildings: the office interior, darkened towards the panel colour, a little blurred so
    the pinned photos stand out."""
    w, h = vsize(WD + "camp_terrain_green_bg.dds")
    im = cover(photo("co_backdrop"), w, h).filter(ImageFilter.GaussianBlur(2.5))
    a = np.asarray(im).astype(np.float32)
    panel = np.array(pal["panel"], np.float32)
    a = a * 0.55 + panel * 0.45 * 0.6
    bg = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    # foreground: a soft dark vignette at the edges (the window's frame sits on it)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.maximum(np.abs(xx / w - 0.5) * 2, np.abs(yy / h - 0.5) * 2)
    alpha = np.clip((d - 0.78) / 0.22, 0, 1) ** 1.6 * 200
    fg = np.zeros((h, w, 4), np.uint8)
    fg[..., :3] = pal["panel"]
    fg[..., 3] = alpha.astype(np.uint8)
    fg = Image.fromarray(fg, "RGBA")
    n = 0
    for f in sorted((GAME / WD).glob("camp_terrain_*_bg.dds")):
        save_dds(bg, WD + f.name)
        save_dds(fg, WD + f.name.replace("_bg.dds", "_fg.dds"))
        n += 1
    return n


def card(name, size, seed, empty=False):
    """A photograph pinned to the office wall: white border, a strip of tape, a slight tilt and a shadow, on a
    transparent canvas of the vanilla sprite's size. Returns (sprite, mask)."""
    w, h = size
    rng = np.random.default_rng(seed)
    cw, ch = int(w * 0.80), int(h * 0.66)
    border = max(6, cw // 28)
    c = Image.new("RGBA", (cw, ch + border * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    if empty:
        # an empty card: dashed outline on a dark translucent panel
        d.rectangle([0, 0, c.width - 1, c.height - 1], fill=(29, 31, 34, 150))
        dash = max(8, cw // 20)
        for x in range(0, c.width, dash * 2):
            d.line([(x, 2), (min(x + dash, c.width), 2)], fill=(236, 231, 220, 200), width=3)
            d.line([(x, c.height - 3), (min(x + dash, c.width), c.height - 3)], fill=(236, 231, 220, 200), width=3)
        for y in range(0, c.height, dash * 2):
            d.line([(2, y), (2, min(y + dash, c.height))], fill=(236, 231, 220, 200), width=3)
            d.line([(c.width - 3, y), (c.width - 3, min(y + dash, c.height))], fill=(236, 231, 220, 200), width=3)
    else:
        d.rectangle([0, 0, c.width - 1, c.height - 1], fill=(240, 236, 228, 255))
        pic = cover(photo(name), cw - 2 * border, ch - border)
        c.paste(pic, (border, border))
    angle = float(rng.uniform(-4, 4))
    c = c.rotate(angle, resample=Image.BICUBIC, expand=True)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x, y = (w - c.width) // 2, int(h * 0.30) + (int(h * 0.66) - c.height) // 2
    y = max(0, min(h - c.height, y))
    # shadow
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sa = Image.new("L", (w, h), 0)
    sa.paste(c.getchannel("A").point(lambda v: int(v * 0.6)), (x + 8, y + 10))
    sh.putalpha(sa.filter(ImageFilter.GaussianBlur(9)))
    canvas = Image.alpha_composite(canvas, sh)
    canvas.alpha_composite(c, (x, y))
    if not empty:
        # tape across the top edge
        tw, th = cw // 3, max(12, ch // 10)
        tape = Image.new("RGBA", (tw, th), (228, 222, 200, 170))
        tape = tape.rotate(float(rng.uniform(-6, 6)), resample=Image.BICUBIC, expand=True)
        canvas.alpha_composite(tape, ((w - tape.width) // 2, max(0, y - tape.height // 2)))
    mask = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    m = canvas.getchannel("A").point(lambda v: 255 if v > 100 else 0)
    mask.putalpha(m)
    mask = Image.composite(Image.new("RGBA", (w, h), (255, 255, 255, 255)), mask, m)
    return canvas, mask


def buildings():
    n = 0
    files = sorted(p.name for p in (GAME / WD).glob("laamp_building_*.dds"))
    for i, fname in enumerate(files):
        stem = fname[len("laamp_building_"):-len(".dds")]
        for pattern, pic in BUILDING_PHOTOS:
            if re.fullmatch(pattern, stem.replace("_asian", "")) or re.fullmatch(pattern, stem):
                break
        else:
            print("  no picture for", fname)
            continue
        size = vsize(WD + fname)
        sprite, mask = card(pic, size, seed=i, empty=pic is None)
        save_dds(sprite, WD + fname)
        mfile = GAME / WD / fname.replace(".dds", "_mask.png")
        if mfile.exists():
            ms = Image.open(mfile).size
            save_png(mask.resize(ms, Image.NEAREST) if ms != size else mask, WD + mfile.name)
        n += 1
    return n


def illustration():
    rel = "gfx/interface/illustrations/event_scenes/ep3_camp_arid_terrain.dds"
    w, h = vsize(rel)
    save_dds(cover(photo("co_street"), w, h).convert("RGBA"), rel)


def purposes():
    for law, pic in PURPOSE_PHOTOS.items():
        rel = "gfx/interface/icons/laws/camp_purpose_%s.dds" % law
        w, h = vsize(rel)
        im = cover(photo(pic), w, h).convert("RGBA")
        # rounded corners and a soft edge, like vanilla's painted vignettes
        m = Image.new("L", (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle([6, 6, w - 7, h - 7], radius=w // 10, fill=255)
        im.putalpha(m.filter(ImageFilter.GaussianBlur(3)))
        save_dds(im, rel)


def chrome(pal):
    """The camp window's parchment and heraldry in the night edition: dark panels with light rules and the red accent,
    flat badges instead of pennants. Same files, sizes and alpha layout as vanilla (also the _asia variants)."""
    panel, text, red = (np.array(pal[k], np.float32) for k in ("panel", "text", "red"))
    rule = panel * 0.45 + text * 0.55
    out = []

    def load(name):
        return np.asarray(Image.open(GAME / WD / name).convert("RGBA")).astype(np.float32)

    def put(arr, name):
        save_dds(Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA"), WD + name)
        out.append(name)

    def flat(a, colour, lift=0.0):
        h = a.shape[0]
        grad = (1 + lift * (0.5 - np.arange(h, dtype=np.float32)[:, None] / h))[..., None]
        b = a.copy()
        b[..., :3] = colour[None, None, :] * grad
        return b

    for base in ("domicile_header_background", "domicile_banner", "domicile_progress_bar_bg"):
        for name in (base + ".dds", base + "_asia.dds"):
            if not (GAME / WD / name).exists():
                continue
            a = load(name)
            h, w = a.shape[:2]
            b = np.zeros_like(a)
            b[..., :3] = panel
            b[..., 3] = 235
            m = max(2, h // 30)
            b[:m, :, :3] = rule
            b[h - 2 * m:, :, :3] = red
            put(b, name)
    for name in ("domicile_window_control_background.dds", "domicile_window_control_background_asia.dds"):
        if (GAME / WD / name).exists():
            a = load(name)
            b = flat(a, panel * 1.15, 0.1)
            b[..., 3] = np.where(a[..., 3] > 8, 235, 0)
            ys, xs = np.nonzero(b[..., 3])
            if len(ys):
                y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
                for sl in (np.s_[y0:y0 + 2, x0:x1 + 1], np.s_[y1 - 1:y1 + 1, x0:x1 + 1],
                           np.s_[y0:y1 + 1, x0:x0 + 2], np.s_[y0:y1 + 1, x1 - 1:x1 + 1]):
                    b[sl][..., :3] = rule
            put(b, name)
    for name in ("domicile_frame.dds", "domicile_frame_asia.dds"):
        if (GAME / WD / name).exists():
            put(flat(load(name), rule), name)
    # the letter (paper) behind the window's text: dark paper, no shadow, a neutral overlay
    a = load("tile_letter_flat.dds")
    b = flat(a, panel * 1.12)
    b[..., 3] = 255
    put(b, "tile_letter_flat.dds")
    a = load("tile_letter_shadow.dds")
    a[..., 3] = 0
    put(a, "tile_letter_shadow.dds")
    a = load("overlay_letter_texture.dds")
    a[..., :3] = 128
    put(a, "overlay_letter_texture.dds")
    # team morale badges (three frames side by side: low, neutral, high): flat, rounded, muted
    tones = [np.array(c, np.float32) for c in ((150, 46, 52), (78, 84, 92), (52, 112, 84))]
    for name, fw in (("camp_follower_opinion_banner_bg.dds", None), ("camp_follower_opinion_bg.dds", None)):
        a = load(name)
        h, w = a.shape[:2]
        n = 3
        fw = w // n
        b = np.zeros_like(a)
        # vanilla's frame order: work it out from each frame's mean hue (red, green, blue -> low, high, neutral)
        for i in range(n):
            fr = a[:, i * fw:(i + 1) * fw]
            msk = fr[..., 3] > 30
            mean = fr[..., :3][msk].mean(axis=0) if msk.any() else np.array([100, 100, 100])
            tone = tones[0] if mean[0] > mean[1] and mean[0] > mean[2] else (
                tones[2] if mean[1] >= mean[2] else tones[1])
            m = Image.new("L", (fw, h), 0)
            pad = max(2, h // 14)
            ImageDraw.Draw(m).rounded_rectangle([pad, pad, fw - pad - 1, h - pad - 1], radius=max(4, h // 8), fill=230)
            b[:, i * fw:(i + 1) * fw, :3] = tone
            b[:, i * fw:(i + 1) * fw, 3] = np.asarray(m, np.float32)
        put(b, name)
    return out


def build_pictures():
    fetch(list(PICTURES))
    pal = palette()
    print("backdrops:", backdrop(pal))
    print("building pictures:", buildings())
    illustration()
    purposes()
    print("window chrome:", len(chrome(pal)))
    print("illustration and %d focus pictures installed" % len(PURPOSE_PHOTOS))


def main():
    args = sys.argv[1:]
    Image.MAX_IMAGE_PIXELS = None
    if "--no-images" not in args:
        build_pictures()
    if "--images-only" not in args:
        import build_campaign_office_loc  # noqa: E402
        build_campaign_office_loc.main()


if __name__ == "__main__":
    main()
