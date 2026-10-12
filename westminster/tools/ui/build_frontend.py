#!/usr/bin/env python3
"""Westminster's main menu: a newspaper masthead panel over a photograph of Westminster.

    .venv/bin/python westminster/tools/ui/build_frontend.py

- gfx/interface/frontend/frontend_main_menu_bg.dds: the menu panel (vanilla: stained glass) becomes a newspaper
  front page: masthead "Westminster", a dateline and column rules, on newsprint.
- frontend_main_menu_frame.dds (vanilla: a gothic arch) becomes a plain ruled border; its mask becomes a rectangle;
  the colour-dodge glows become black so they do nothing on paper.
- gui/frontend_main.gui: vanilla's, with the backdrop set to gfx/interface/frontend/wm_backdrop.dds (from
  fal_images.py) instead of the culture's hall, and the 3D portraits hidden.
"""
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_theme import GAME, INK, MOD, PAPER, grain, save_dds   # noqa: E402

FRONT = MOD / "gfx" / "interface" / "frontend"
FONTS = MOD / "fonts"
W, H = 1000, 1828                       # vanilla panel texture size (shown at 500 x 915)


def font(path, size):
    return ImageFont.truetype(str(path), size)


def panel():
    img = np.dstack([np.clip(PAPER + grain(H, W, 7), 0, 255), np.full((H, W), 255.0)]).astype(np.uint8)
    im = Image.fromarray(img, "RGBA")
    d = ImageDraw.Draw(im)
    ink = tuple(int(v) for v in INK) + (255,)
    m = 56
    # Masthead
    d.line([(m, 70), (W - m, 70)], fill=ink, width=3)
    title = font(FONTS / "Fondamento" / "Fondamento-Regular.ttf", 132)        # Playfair Display Bold
    d.text((W / 2, 175), "Westminster", font=title, fill=ink, anchor="mm")
    small = font(FONTS / "Gitan" / "GitanLatin-Regular.otf", 30)
    d.line([(m, 262), (W - m, 262)], fill=ink, width=6)
    d.line([(m, 274), (W - m, 274)], fill=ink, width=2)
    d.text((m, 300), "THE POLITICAL GAME", font=small, fill=ink, anchor="lt")
    d.text((W - m, 300), "EST. 1937", font=small, fill=ink, anchor="rt")
    d.line([(m, 348), (W - m, 348)], fill=ink, width=2)
    # Column rules down the page (behind the buttons) and a footer rule
    for x in (m, W - m):
        d.line([(x, 348), (x, H - 120)], fill=ink + (0,) if False else ink, width=2)
    d.line([(m, H - 120), (W - m, H - 120)], fill=ink, width=3)
    d.text((W / 2, H - 80), "Late edition", font=small, fill=ink, anchor="mm")
    return np.array(im)


def frame():
    out = np.zeros((H, W, 4), dtype=np.uint8)
    out[..., :3] = INK.astype(np.uint8)
    for t, inset in ((4, 0), (2, 14)):
        out[inset:inset + t, inset:W - inset, 3] = 255
        out[H - inset - t:H - inset, inset:W - inset, 3] = 255
        out[inset:H - inset, inset:inset + t, 3] = 255
        out[inset:H - inset, W - inset - t:W - inset, 3] = 255
    return out


def logo_banner():
    """The loading screen's little banner (vanilla: the CK3 shield): a black masthead card with a white W."""
    w, h = 72, 90
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([2, 2, w - 3, h - 3], fill=(24, 24, 24, 255))
    d.rectangle([6, 6, w - 7, h - 7], outline=(243, 239, 230, 255), width=1)
    d.text((w / 2, h / 2 + 2), "W", font=font(FONTS / "Fondamento" / "Fondamento-Regular.ttf", 56), fill=(243, 239, 230, 255), anchor="mm")
    return np.array(im)


def patch_gui():
    # Start from build_theme's glow-free copy if there is one
    mine = MOD / "gui" / "frontend_main.gui"
    src = mine.read_text(encoding="utf-8-sig") if mine.exists() else ""
    first, _, rest = src.partition("\n")
    if "build_theme.py" in first and "build_frontend.py" not in first:
        src = rest                                          # drop build_theme's header; this script writes its own
    else:                                                   # none yet, or this script's own output: start again
        src = (GAME / "gui" / "frontend_main.gui").read_text(encoding="utf-8-sig")
    s = src.replace('texture = "[FrontEndMainView.GetBackground]"', 'texture = "gfx/interface/frontend/wm_backdrop.dds"')
    assert s != src, "backdrop line not found"
    # Hide the 3D portraits and their shadows (medieval characters in a hall)
    s, n = re.subn(r'(portrait_button = \{\n(\t+)name = "menu_portrait[^"]*")', r'\1\n\2visible = no', s)
    s, n2 = re.subn(r'(name = "shadow_[a-z_]+")', r'\1\n\t\t\t\tvisible = no', s)
    out = MOD / "gui" / "frontend_main.gui"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("# Westminster: Crusader Kings III's own gui/frontend_main.gui (Paradox Interactive), with a photo backdrop "
                   "and no 3D portraits, by westminster/tools/ui/build_frontend.py (glows: build_theme.py) - edit there.\n"
                   + s, encoding="utf-8-sig")
    return n, n2


def main():
    FRONT.mkdir(parents=True, exist_ok=True)
    save_dds(panel(), FRONT / "frontend_main_menu_bg.dds")
    save_dds(frame(), FRONT / "frontend_main_menu_frame.dds")
    save_dds(logo_banner(), FRONT / "ck3_logo_banner.dds")
    mask = np.full((H, W, 4), 255, dtype=np.uint8)
    save_dds(mask, FRONT / "frontend_main_menu_bg_mask.dds")
    for g in ("frontend_main_menu_bg_glow.dds", "frontend_main_menu_bg_button_glow.dds"):
        van = Image.open(GAME / "gfx" / "interface" / "frontend" / g)
        black = np.zeros((van.height, van.width, 4), dtype=np.uint8)
        black[..., 3] = 255
        save_dds(black, FRONT / g)
    print("panel, frame, mask, glows written; gui patched (portraits, shadows hidden: %d, %d)" % patch_gui())


if __name__ == "__main__":
    main()
