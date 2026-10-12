#!/usr/bin/env python3
"""Shows coats of arms as flags: a 3:2 rectangle with slightly rounded corners and a thin ink rule, instead of a
shield under a crown.

    .venv/bin/python westminster/tools/ui/build_coa_frames.py

CK3 draws a CoA as a square texture cut out by a mask, with a frame on top and, for titles and realms, a tier crown
above. This replaces those pictures (same paths and sizes as vanilla 1.20, so gui/shared/coat_of_arms.gui stays
vanilla) and points the masks the game picks by culture and government at our own:

  gfx/interface/coat_of_arms/title_mask.dds              titles: the flag shape (full width, the middle 2/3 high)
  gfx/interface/coat_of_arms/title_{28,44,62,86}.dds      the ink rule round it (sized like vanilla's frames)
  gfx/interface/coat_of_arms/title_no_holder_*.dds        a dashed grey rule for titles nobody holds
  gfx/interface/coat_of_arms/crown_strip_*.dds            empty: no crowns
  gfx/interface/coat_of_arms/topframe_*.dds               empty: no tier bars
  gfx/interface/coat_of_arms/coa_overlay.dds              flat grey (no cloth texture over house arms)
  gfx/interface/coat_of_arms/lowborn.dds                  a blank flag
  gfx/interface/coat_of_arms/frames/wm_flag.dds           house and dynasty frame (6 prestige frames, all alike)
  gfx/interface/coat_of_arms/frames/wm_flag_mask.dds      house and dynasty mask
  gfx/interface/icons/wm_realm_frames/_default_*.dds      realm (government) mask, frames and shadows
  gfx/coat_of_arms/coa_mask_texture.dds                   flat: no cloth shading inside the arms (modern, flat)
  common/defines/graphic/wm_coa_frames.txt                NCoatOfArms OVERRIDE_* (house, dynasty frame and realm mask
                                                          offset) and NGameIcons GOVERNMENT_TYPE_REALM_*_PATH

Every flag (build_flags.py) fills the CoA's middle band, y from 1/6 to 5/6, which is the shape cut out here. House
and dynasty icons are drawn at 67-80% of their frame's size depending on the widget, so their rule sits a little
outside the flag (a picture-box margin) rather than on its edge.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
MOD = ROOT / "westminster"
GAME_VERSION = "1.20"                                   # vanilla files whose sizes this copies

INK = (24, 24, 24)
GREY = (120, 116, 108)
PAPER = (243, 239, 230)
BAND = 2 / 3                                            # flag height / width
RADIUS = 0.035                                          # corner radius / width
SS = 4                                                  # supersampling


def rect(size, inset_x, width):
    """The flag rectangle, centred in a size x size texture: x from inset_x, `width` wide, 2/3 as high."""
    h = width * BAND
    y0 = (size - h) / 2
    return inset_x, y0, inset_x + width, y0 + h


def rounded(size, box, fill=None, outline=None, stroke=0.0, dash=None):
    """An RGBA picture of a rounded rectangle (anti-aliased by supersampling). stroke is in output pixels."""
    S = size * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = [v * SS for v in box]
    r = max(1, RADIUS * (x1 - x0))
    if fill:
        d.rounded_rectangle((x0, y0, x1, y1), r, fill=fill)
    if outline and stroke:
        w = max(1, round(stroke * SS))
        h = w / 2                                     # centre the rule on the flag's edge
        if dash:
            mask = Image.new("L", (S, S), 0)
            ImageDraw.Draw(mask).rounded_rectangle((x0 - h, y0 - h, x1 + h, y1 + h), r + h, outline=255, width=w)
            ys, xs = np.mgrid[0:S, 0:S]
            on = ((xs + ys) // (dash * SS)) % 2 == 0
            m = np.array(mask) * on
            layer = Image.new("RGBA", (S, S), outline + (255,))
            img.paste(layer, (0, 0), Image.fromarray(m.astype(np.uint8)))
        else:
            d.rounded_rectangle((x0 - h, y0 - h, x1 + h, y1 + h), r + h, outline=outline + (255,), width=w)
    return img.resize((size, size), Image.LANCZOS)


def mask(size, inset=0.0, rgb=(128, 128, 128)):
    """A CoA mask: alpha is the flag shape; grey RGB is neutral under the realm icon's overlay blend."""
    w = size * (1 - 2 * inset)
    a = rounded(size, rect(size, size * inset, w), fill=(255, 255, 255, 255)).split()[3]
    out = Image.new("RGBA", (size, size), rgb + (255,))
    out.putalpha(a)
    return out


def save(img, rel):
    p = MOD / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p, "DDS")                                  # uncompressed RGBA: crisp hairlines at 1:1
    return p


def stroke_for(icon):
    return max(1.0, icon / 48)


def main():
    out = []
    # Titles: icon N drawn in a frame texture of size F (vanilla 1.20 sizes)
    out.append(save(mask(88, inset=0.0, rgb=(255, 255, 255)), "gfx/interface/coat_of_arms/title_mask.dds"))
    for icon, frame, nh in ((28, 36, 36), (44, 52, 56), (62, 72, 80), (86, 96, 104)):
        out.append(save(rounded(frame, rect(frame, (frame - icon) / 2, icon), outline=INK, stroke=stroke_for(icon)),
                        "gfx/interface/coat_of_arms/title_%d.dds" % icon))
        out.append(save(rounded(nh, rect(nh, (nh - icon) / 2, icon), outline=GREY, stroke=stroke_for(icon),
                                dash=max(2, icon // 14)),
                        "gfx/interface/coat_of_arms/title_no_holder_%d.dds" % icon))
    # No crowns, no tier bars
    for name, size in (("crown_strip_28", (224, 22)), ("crown_strip_44", (364, 32)), ("crown_strip_62", (448, 40)),
                       ("crown_strip_86", (672, 60)), ("crown_strip_115", (896, 80)),
                       ("crown_strip_115_gameconcept", (624, 104)), ("topframe_28", (224, 32)),
                       ("topframe_44", (364, 52)), ("topframe_62", (448, 64)), ("topframe_86", (672, 96)),
                       ("topframe_115", (896, 128))):
        out.append(save(Image.new("RGBA", size, (0, 0, 0, 0)), "gfx/interface/coat_of_arms/%s.dds" % name))
    out.append(save(Image.new("RGBA", (116, 116), (128, 128, 128, 255)), "gfx/interface/coat_of_arms/coa_overlay.dds"))
    # Someone with no house: a blank paper flag
    lb = rounded(160, rect(160, 8, 144), fill=PAPER + (255,), outline=INK, stroke=2.5)
    d = ImageDraw.Draw(lb)
    d.line((62, 80, 98, 80), fill=INK + (255,), width=3)
    out.append(save(lb, "gfx/interface/coat_of_arms/lowborn.dds"))

    # Houses and dynasties: one frame for every culture (the defines below), icon at 67-80% of the frame
    icon = 160 * 0.80
    hm = mask(160, inset=0.0)
    out.append(save(hm, "gfx/interface/coat_of_arms/frames/wm_flag_mask.dds"))
    one = rounded(160, rect(160, (160 - icon) / 2 - 2, icon + 4), outline=INK, stroke=2.2)
    strip = Image.new("RGBA", (960, 160), (0, 0, 0, 0))
    for k in range(6):
        strip.alpha_composite(one, (k * 160, 0))
    out.append(save(strip, "gfx/interface/coat_of_arms/frames/wm_flag.dds"))

    # Realms (the government's mask and frame, drawn the same size as the icon)
    inset = 0.04
    out.append(save(mask(128, inset=inset), "gfx/interface/icons/wm_realm_frames/_default_mask.dds"))
    for tier, size in ((28, 32), (44, 52), (62, 64), (86, 96), (115, 128)):
        box = rect(size, size * inset, size * (1 - 2 * inset))
        out.append(save(rounded(size, box, outline=INK, stroke=max(1.0, size / 48)),
                        "gfx/interface/icons/wm_realm_frames/_default_%d_frame.dds" % tier))
        out.append(save(Image.new("RGBA", (size, size), (0, 0, 0, 0)),          # flat print: no drop shadow
                        "gfx/interface/icons/wm_realm_frames/_default_%d_shadow.dds" % tier))

    # Flat arms: no cloth shading (the CoA shaders overlay this texture's blue and scale emblem alpha by green*2)
    out.append(save(Image.new("RGBA", (256, 256), (128, 128, 128, 255)), "gfx/coat_of_arms/coa_mask_texture.dds"))

    defines = MOD / "common/defines/graphic/wm_coa_frames.txt"
    defines.write_text("""# Generated by westminster/tools/ui/build_coa_frames.py - edit there. (Checked against CK3 %s.)
# Coats of arms are flags: every culture's house and dynasty use frames/wm_flag(_mask).dds, every government
# the realm frames in gfx/interface/icons/wm_realm_frames (only _default_*, which the game falls back to).
NCoatOfArms = {
	OVERRIDE_DYNASTY_COA_FRAME_NAME = "wm_flag"
	OVERRIDE_DYNASTY_COA_FRAME_OFFSET = { 0.0 0.0 }
	OVERRIDE_DYNASTY_COA_FRAME_SCALE = { 1.0 1.0 }
	OVERRIDE_HOUSE_COA_FRAME_NAME = "wm_flag"
	OVERRIDE_HOUSE_COA_FRAME_OFFSET = { 0.0 0.0 }
	OVERRIDE_HOUSE_COA_FRAME_SCALE = { 1.0 1.0 }
	OVERRIDE_REALM_MASK_ENABLED = yes
	OVERRIDE_REALM_MASK_OFFSET = { 0.0 0.0 }
	OVERRIDE_REALM_MASK_SCALE = { 1.0 1.0 }
}
NGameIcons = {
	GOVERNMENT_TYPE_REALM_MASK_PATH = "gfx/interface/icons/wm_realm_frames"
	GOVERNMENT_TYPE_REALM_FRAME_PATH = "gfx/interface/icons/wm_realm_frames"
	GOVERNMENT_TYPE_REALM_FRAME_SHADOW_PATH = "gfx/interface/icons/wm_realm_frames"
}
""" % GAME_VERSION, encoding="utf-8-sig")
    out.append(defines)
    for p in out:
        print("wrote", p.relative_to(ROOT.parent))


if __name__ == "__main__":
    main()
