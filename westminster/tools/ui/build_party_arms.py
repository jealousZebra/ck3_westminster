#!/usr/bin/env python3
"""Coats of arms for the parties: each party's house (and its dynasty and party title) carries an emblem inspired by
the party's real logo, simplified (a rose, an oak, a bird...), never a copy of the trademark. Parties founded in play
get one of six made-up emblems, one per founding slot (k_party_new_<n>, tools/data/build_2024.py).

    .venv/bin/python westminster/tools/ui/build_party_arms.py [party ...]

Each emblem is a black-on-white pictogram from fal.ai (FLUX), cached in westminster/art/fal/arms_<party>.jpg (delete
one to regenerate it; the API key comes from $FAL_KEY or ~/.config/fal/key, as for fal_images.py). It becomes a
CK3 colored emblem: gfx/coat_of_arms/colored_emblems/ce_wm_party_<party>.dds, 512x512 DXT5, in vanilla's channel
layout (checked on ce_martlet.dds and ce_flower.dds):

    alpha  the emblem's shape
    red    where color2 replaces color1 (0 here: one-colour emblems)
    green  where color3 replaces color1 (0 here)
    blue   shading: 128 is flat, lower is darker (vanilla draws outlines at about 96)

Writes:
  westminster/gfx/coat_of_arms/colored_emblems/ce_wm_party_<party>.dds
  westminster/gfx/coat_of_arms/colored_emblems/wm_party_emblems.txt    (so the CoA designer lists them)
  westminster/common/coat_of_arms/coat_of_arms/wm_party_arms.txt       house, dynasty and party title arms
"""
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                                  # westminster/
MOD = ROOT / "westminster"
CACHE = ROOT / "art" / "fal"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tools" / "data"))
import fal_images                                          # noqa: E402  (api_key, request)
import build_2024                                          # noqa: E402  (PARTIES, NEW_PARTIES, INDEPENDENT_HOUSE)

MODEL = "fal-ai/flux/dev"
STYLE = ("flat solid black silhouette pictogram, simple bold filled shapes, no outlines, centred with empty margins, "
         "pure white background, no text, no letters, no shading, no frame, vector emblem")
SIZE = 512
WHITE = (255, 255, 255)
FLAG_FIT = 0.80        # coats of arms show as 3:2 flags (build_coa_frames.py): keep emblems inside the middle band

# key: (pictogram subject, field pattern, pattern colours, emblem colour, emblem scale, extra emblems below it)
# Colours are RGB. "Inspired by" the parties' logos: simplified emblems in their colours.
DESIGNS = {
    "labour": ("a single rose flower with a short stem and two leaves, front view", "pattern_solid.dds", [WHITE],
               (228, 0, 59), 0.80, []),
    "conservative": ("a broad oak tree with a round leafy crown and a short trunk", "pattern_solid.dds", [WHITE],
                     (0, 87, 184), 0.82, []),
    "lib_dem": ("a bird flying with its wings spread wide, stylised dove in flight, side view", "pattern_solid.dds",
                [(250, 166, 26)], (255, 221, 51), 0.82, []),
    "snp": ("an abstract swirl emblem made of two interlocking curved loops", "pattern_solid.dds", [(255, 221, 0)],
            (20, 20, 20), 0.78, []),
    "sinn_fein": ("a Celtic triple spiral triskele", "pattern_solid.dds", [(50, 106, 33)], WHITE, 0.78, []),
    "reform": ("a bold arrow pointing to the upper right", "pattern_solid.dds", [(18, 182, 207)], WHITE, 0.78, []),
    "dup": ("a flaming torch held upright", "pattern_vertical_split_01.dds", [(0, 36, 125), (200, 16, 46)], WHITE,
            0.80, []),
    "green": ("a sunflower head with petals around a round centre", "pattern_solid.dds", [(2, 167, 91)], WHITE,
              0.80, []),
    "plaid": ("a poppy flower with four broad petals and a round centre, seen from above", "pattern_solid.dds",
              [(0, 91, 84)], (255, 214, 0), 0.80, []),
    "sdlp": ("a rose flower head in full bloom, seen from above", "pattern_solid.dds", [(42, 168, 44)],
             (220, 30, 40), 0.78, []),
    "alliance": ("an abstract bold chevron arrowhead pointing upward made of two overlapping strokes",
                 "pattern_solid.dds", [(246, 203, 47)], (20, 20, 20), 0.76, []),
    "uup": ("an open right hand, palm facing forward, fingers together, thumb out", "pattern_solid.dds",
            [(0, 51, 153)], (204, 0, 0), 0.56, [("ce_circle.dds", WHITE, 1.25)]),
    "tuv": ("a megaphone loudspeaker", "pattern_solid.dds", [(12, 59, 95)], WHITE, 0.76, []),
    "independent": ("a rosette ribbon award with two ribbon tails", "pattern_solid.dds", [(112, 112, 112)], WHITE,
                    0.78, []),
    # Founded parties: made-up emblems, one per slot
    "new_1": ("an old-fashioned street lantern", "pattern_solid.dds", [(22, 46, 92)], (240, 190, 50), 0.78, []),
    "new_2": ("an arched stone bridge over water", "pattern_solid.dds", [(110, 52, 140)], WHITE, 0.82, []),
    "new_3": ("a beacon fire with tall flames in an iron brazier", "pattern_solid.dds", [(176, 38, 30)],
              (255, 170, 40), 0.80, []),
    "new_4": ("a kestrel bird of prey hovering with wings spread, side view", "pattern_solid.dds", [(122, 82, 48)],
              (240, 225, 190), 0.82, []),
    "new_5": ("a compass rose with eight points", "pattern_solid.dds", [(0, 128, 128)], WHITE, 0.80, []),
    "new_6": ("a small house with a chimney and a curl of smoke", "pattern_solid.dds", [(128, 20, 52)],
              (255, 205, 60), 0.78, []),
}


def coa_key(party):
    """The CoA's key: the party house's key (wm_house_party_<p>), or wm_coa_party_<slot> for founding slots."""
    if party == "independent":
        return build_2024.INDEPENDENT_HOUSE
    if party.startswith("new_"):
        return "wm_coa_party_" + party
    return "wm_house_party_" + party


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


def emblem(raw):
    """A black-on-white pictogram as a colored emblem (RGBA, see the module docstring): the ink becomes the shape,
    centred and scaled to fill 84% of the square, with a darker rim so light emblems read on light fields."""
    g = np.array(Image.open(raw).convert("L")).astype(np.float32) / 255
    a = np.clip((0.8 - g) / 0.5, 0, 1)
    ys, xs = np.nonzero(a > 0.3)
    if not len(ys):
        raise ValueError("no ink in %s" % raw)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    side = int(SIZE * 0.84)
    im = Image.fromarray((a * 255).astype(np.uint8))
    im.thumbnail((side, side), Image.LANCZOS)
    alpha = Image.new("L", (SIZE, SIZE), 0)
    alpha.paste(im, ((SIZE - im.width) // 2, (SIZE - im.height) // 2))
    inner = np.array(alpha.filter(ImageFilter.MinFilter(9))).astype(np.float32) / 255
    al = np.array(alpha).astype(np.float32) / 255
    rim = np.clip(al - inner, 0, 1)
    out = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    out[..., 2] = np.clip(128 - 48 * rim, 0, 255).astype(np.uint8)
    out[..., 3] = (al * 255).astype(np.uint8)
    return out


def rgb(c):
    return "rgb { %d %d %d }" % c


def coa(party):
    subject, pattern, fields, colour, scale, extras = DESIGNS[party]
    scale *= FLAG_FIT
    lines = ["%s = {" % coa_key(party), '\tpattern = "%s"' % pattern]
    for i, c in enumerate(fields):
        lines.append("\tcolor%d = %s" % (i + 1, rgb(c)))
    for tex, c, s in extras:
        lines.append('\tcolored_emblem = {\n\t\ttexture = "%s"\n\t\tcolor1 = %s\n'
                     "\t\tinstance = { position = { 0.5 0.5 } scale = { %.2f %.2f } }\n\t}" % (tex, rgb(c), s * FLAG_FIT,
                                                                                  s * FLAG_FIT))
    lines.append('\tcolored_emblem = {\n\t\ttexture = "ce_wm_party_%s.dds"\n\t\tcolor1 = %s\n'
                 "\t\tinstance = { position = { 0.5 0.5 } scale = { %.2f %.2f } }\n\t}" % (party, rgb(colour), scale, scale))
    lines.append("}")
    return "\n".join(lines)


def main():
    names = sys.argv[1:] or list(DESIGNS)
    CACHE.mkdir(parents=True, exist_ok=True)
    key = None
    for n in names:
        raw = CACHE / ("arms_%s.jpg" % n)
        if not raw.exists():
            key = key or fal_images.api_key()
            urllib.request.urlretrieve(generate(DESIGNS[n][0], key), raw)
            print("generated", raw.name)
        out = MOD / ("gfx/coat_of_arms/colored_emblems/ce_wm_party_%s.dds" % n)
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(emblem(raw)).save(out, pixel_format="DXT5")
        print("emblem", out.relative_to(ROOT.parent))

    reg = ["# Generated by westminster/tools/ui/build_party_arms.py - edit there.",
           "# The parties' emblems, listed in the coat of arms designer (one colour each)."]
    reg += ["ce_wm_party_%s.dds = { colors = 1 category = nature }" % n for n in DESIGNS]
    (MOD / "gfx/coat_of_arms/colored_emblems/wm_party_emblems.txt").write_text("\n".join(reg) + "\n", encoding="utf-8-sig")

    arms = ["# Generated by westminster/tools/ui/build_party_arms.py - edit there.",
            "# Each party's house carries the party's emblem; its dynasty and its party title share it. Founded parties",
            "# (create_dynasty in wm_party_effects.txt) take wm_coa_party_new_<n>, which their slot's title shares.", ""]
    for p in [p[0] for p in build_2024.PARTIES]:
        arms.append(coa(p))
        arms.append("wm_dyn_party_%s = wm_house_party_%s" % (p, p))
        arms.append("k_party_%s = wm_house_party_%s\n" % (p, p))
    arms.append(coa("independent"))
    arms.append("wm_dyn_independent = %s\n" % build_2024.INDEPENDENT_HOUSE)
    for slot in [s[0] for s in build_2024.NEW_PARTIES]:
        arms.append(coa(slot))
        arms.append("k_party_%s = wm_coa_party_%s\n" % (slot, slot))
    out = MOD / "common/coat_of_arms/coat_of_arms/wm_party_arms.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(arms) + "\n", encoding="utf-8-sig")
    print("wrote", out.relative_to(ROOT.parent))


if __name__ == "__main__":
    main()
