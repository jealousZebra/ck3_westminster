#!/usr/bin/env python3
"""Westminster's newspaper UI theme: fonts, text colours and the shared interface textures.

    .venv/bin/python westminster/tools/ui/build_theme.py

- Fonts: the medieval headline font (Fondamento) becomes Playfair Display, the body font (Gitan) Source Serif 4.
  The files go at vanilla's paths, so fonts.font needn't change. Both are SIL Open Font Licence.
- Colours: THEME (below) is the palette of the whole interface. LOOK = "night" (the default since 0.4) is the
  "night edition": charcoal paper, off-white text, light hairline rules, the red accent; LOOK = "day" is the light
  newsprint of 0.1-0.3. The other UI generators (main menu, polls panel, bookmark screen...) import THEME from here.
- Text: gui/preload/textformatting.gui with the look's palette (TEXT, FORMATS; red accent, no glows). Run with
  --contrast to print each text colour's contrast against the panels (WCAG AA: 4.5:1).
- Textures: the UI skin (gfx/interface/skinned and every gfx/interface/skins/<culture>) redrawn: window, tooltip
  and panel backgrounds become plain paper (dark by night) with a little grain; ornamental borders become plain
  rules; medieval ornaments that have no modern equivalent are removed. Each texture keeps its size and alpha
  shape, so the GUI layouts work unchanged. Lifestyle, trait and HUD tab icons get a bright flat duotone treatment;
  scene illustrations are replaced separately (fal.ai images).
"""
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent.parent          # westminster/
MOD = ROOT / "westminster"
RAW = ROOT / "data" / "raw"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)

# ---------------------------------------------------------------- the palette
# One place for every colour of the look. LOOK picks the set; the other UI generators import THEME (and TEXT, FORMATS)
# from here, so switching the whole interface between the night edition and the old light newsprint is this one line.
LOOK = "night"                  # "night": charcoal panels, off-white text (0.4 default); "day": ink on newsprint (0.1-0.3)

# Colours are (r, g, b) 0-255.
#   paper         panel and window backgrounds (newsprint / dark paper)
#   paper_raised  inset and raised areas: sidebars, sub-windows, HUD bars (slightly darker by day, lighter by night)
#   heading       the tint behind window headings (color_theme.dds)
#   ink           text-coloured marks drawn into textures (masthead lettering, the polls panel's Speaker)
#   line          rules, borders and bevels (ink rules by day, light hairlines by night)
#   muted         secondary marks (leader lines, faint labels in textures)
#   empty         an empty bar or seat behind party colours
#   red           the accent (the Times-red #c8102e family): selection rules, the majority line, a selected seat
#   sea, land     the bookmark screen's election map: sea and neighbouring countries (seats keep party colours)
#   coast         the UK's coastline there; seam: the borders between seats
#   alert_dark, alert_light   the alert diamonds' body and glyph
#   grain         strength of the paper grain (1 = the light look's)
#   soften        how much paper is mixed into party colours on the map (printed on newsprint)
THEMES = {
    "day": {
        "paper": (243, 239, 230), "paper_raised": (232, 226, 214), "heading": (226, 220, 207),
        "ink": (24, 24, 24), "line": (24, 24, 24), "muted": (120, 120, 114), "empty": (214, 209, 196),
        "red": (176, 26, 31), "sea": (205, 214, 214), "land": (226, 222, 212), "coast": (70, 70, 66),
        "seam": (250, 247, 240), "land_line": (160, 160, 152),
        "alert_dark": (24, 24, 24), "alert_light": (243, 239, 230), "grain": 1.0, "soften": 0.12,
    },
    "night": {
        "paper": (29, 31, 34), "paper_raised": (39, 42, 46), "heading": (47, 50, 55),
        "ink": (236, 231, 220), "line": (118, 116, 110), "muted": (128, 126, 120), "empty": (58, 61, 66),
        "red": (200, 16, 46), "sea": (22, 27, 32), "land": (44, 46, 49), "coast": (150, 148, 140),
        "seam": (29, 31, 34), "land_line": (82, 84, 86),
        "alert_dark": (67, 82, 104), "alert_light": (245, 202, 116), "grain": 0.45, "soften": 0.06,
    },
}
THEME = THEMES[LOOK]
DARK = LOOK == "night"


def rgb01(c):
    """A palette colour as 0-1 floats (GUI colour = { r g b a })."""
    return tuple(round(v / 255, 3) for v in c)


def gui_color(name, alpha=1):
    """A palette colour written for a .gui file: 'r g b a'."""
    return "%.3f %.3f %.3f %g" % (rgb01(THEME[name]) + (alpha,))


PAPER = np.array(THEME["paper"], dtype=np.float32)            # newsprint
PAPER_DARK = np.array(THEME["paper_raised"], dtype=np.float32)  # inset panels (the name is the light look's)
INK = np.array(THEME["ink"], dtype=np.float32)
LINE = np.array(THEME["line"], dtype=np.float32)
RED = rgb01(THEME["red"])                                       # the one accent colour

# Text palette (gui/preload/textformatting.gui): name -> (r, g, b) in 0-1. Everything else stays as vanilla, whose
# own colours were made for its dark stone and read on the night edition's charcoal. The night colours are checked
# against the panels (contrast_report(): WCAG AA, 4.5:1 for text).
TEXT_DAY = {
    "highlight": (0.69, 0.10, 0.12), "color_white": (0.09, 0.09, 0.09), "color_gray": (0.22, 0.22, 0.21),
    "color_dark_gray": (0.42, 0.41, 0.40), "color_red": (0.72, 0.11, 0.12), "color_light_red": (0.82, 0.18, 0.18),
    "color_green": (0.10, 0.45, 0.18), "color_yellow": (0.69, 0.10, 0.12), "color_light_blue": (0.10, 0.32, 0.56),
    "color_dark_blue": (0.08, 0.20, 0.42), "color_blue_gray": (0.30, 0.32, 0.38), "color_goldy_yellow": (0.45, 0.33, 0.16),
    "color_black": (0.05, 0.05, 0.05), "color_dark_green": (0.08, 0.38, 0.12),
}
TEXT_NIGHT = {
    "highlight": (0.96, 0.45, 0.47), "color_white": (0.925, 0.906, 0.863), "color_gray": (0.73, 0.71, 0.67),
    "color_dark_gray": (0.60, 0.585, 0.56), "color_red": (0.95, 0.42, 0.42), "color_light_red": (1.0, 0.58, 0.56),
    "color_green": (0.49, 0.79, 0.49), "color_yellow": (0.96, 0.45, 0.47), "color_light_blue": (0.55, 0.73, 0.93),
    "color_dark_blue": (0.55, 0.67, 0.95), "color_blue_gray": (0.64, 0.68, 0.76), "color_goldy_yellow": (0.89, 0.73, 0.46),
    # "text on a light background" (letters, parchment): those backgrounds are dark paper now
    "color_black": (0.925, 0.906, 0.863), "color_dark_green": (0.42, 0.75, 0.46),
}
TEXT = TEXT_NIGHT if DARK else TEXT_DAY
PALETTE = TEXT                  # (the old name)
# Formats whose whole definition is replaced: light colours with dark glows, made for stone (the HUD date, difficulty).
FORMATS_DAY = {
    "date": "color:{0.09, 0.09, 0.09};glow_color:{0,0,0,0}",
    "difficulty_easy": "bold;color:{0.10, 0.45, 0.18}", "difficulty_medium": "bold;color:{0.45, 0.33, 0.16}",
    "difficulty_hard": "bold;color:{0.72, 0.11, 0.12}", "difficulty_very_hard": "bold;color:{0.45, 0.06, 0.08}",
    "charioteer_blue": "bold;color:{0.10, 0.32, 0.56}", "color_porple": "color:{0.40, 0.18, 0.55}",
    "defender_color": "color:{0.18, 0.30, 0.45}", "Xlight": "color:{0.72, 0.11, 0.12};italic",
    "flatulence": "bold;italic;color:{0.08, 0.38, 0.12}",
}
FORMATS_NIGHT = {
    "date": "color:{0.86, 0.84, 0.79};glow_color:{0,0,0,0}",
    "difficulty_easy": "bold;color:{0.49, 0.79, 0.49}", "difficulty_medium": "bold;color:{0.89, 0.73, 0.46}",
    "difficulty_hard": "bold;color:{1.0, 0.58, 0.56}", "difficulty_very_hard": "bold;color:{0.95, 0.42, 0.42}",
    "charioteer_blue": "bold;color:{0.55, 0.73, 0.93}", "color_porple": "color:{0.76, 0.62, 0.93}",
    "defender_color": "color:{0.58, 0.70, 0.86}", "attacker_color": "color:{0.95, 0.47, 0.42}",
    "Xlight": "color:{1.0, 0.58, 0.56};italic", "flatulence": "bold;italic;color:{0.49, 0.79, 0.52}",
    "G": "color:{0.74, 0.68, 0.86};italic", "G_light": "color:{0.74, 0.68, 0.86};italic",
}
FORMATS = FORMATS_NIGHT if DARK else FORMATS_DAY


def luminance(c):
    """WCAG relative luminance of an (r, g, b) colour, 0-1 floats or 0-255 ints."""
    c = [v / 255 if max(c) > 1 else v for v in c]
    lin = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def contrast_report():
    """Every text colour this look sets, against the panel and the raised panel: (name, worst ratio, ok)."""
    rows = []
    fmts = {k: tuple(float(x) for x in re.search(r"color:\{([^}]*)\}", v).group(1).split(","))
            for k, v in FORMATS.items() if "color:" in v}
    for name, c in list(TEXT.items()) + list(fmts.items()):
        worst = min(contrast(c, THEME["paper"]), contrast(c, THEME["paper_raised"]))
        rows.append((name, worst, worst >= 4.5))
    return rows


# ---------------------------------------------------------------- fonts

def build_fonts():
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    fonts = RAW / "fonts"
    out = MOD / "fonts"

    def playfair(src, weight, dest):
        f = instancer.instantiateVariableFont(TTFont(fonts / src), {"wght": weight})
        dest.parent.mkdir(parents=True, exist_ok=True)
        f.save(dest)

    playfair("PlayfairDisplay[wght].ttf", 700, out / "Fondamento" / "Fondamento-Regular.ttf")
    playfair("PlayfairDisplay-Italic[wght].ttf", 400, out / "Fondamento" / "Fondamento-Italic.ttf")
    playfair("PlayfairDisplay[wght].ttf", 700, out / "mapfont" / "Paradox_King_Script.otf")     # map labels
    for d in ("Fondamento", "mapfont"):                     # the licence ships beside every Playfair file
        (out / d / "OFL.txt").write_bytes((fonts / "OFL_playfair.txt").read_bytes())
    ss = fonts / "sourceserif" / "source-serif-4.005_Desktop" / "TTF"
    gitan = out / "Gitan"
    gitan.mkdir(parents=True, exist_ok=True)
    for src, dest in (("SourceSerif4-Regular.ttf", "GitanLatin-Regular.otf"), ("SourceSerif4-Bold.ttf", "GitanLatin-Bold.otf"),
                      ("SourceSerif4-It.ttf", "GitanLatin-Italic.otf"), ("SourceSerif4-BoldIt.ttf", "GitanLatin-Bold-Italic.otf")):
        (gitan / dest).write_bytes((ss / src).read_bytes())    # FreeType reads TrueType whatever the extension
    (gitan / "LICENSE.md").write_bytes((ss.parent / "LICENSE.md").read_bytes())
    (out / "README.txt").write_text("Westminster replaces the game's medieval fonts at their original paths:\n"
                                    "Fondamento/* and mapfont/* are Playfair Display (OFL), Gitan/* is Source Serif 4 (OFL).\n")


# ---------------------------------------------------------------- text colours

def build_textformatting():
    src = (GAME / "gui" / "preload" / "textformatting.gui").read_text(encoding="utf-8-sig")

    def recolor(m):
        name = m.group(1)
        if name in PALETTE:
            r, g, b = PALETTE[name]
            return '%sformat = "color:{%.2f, %.2f, %.2f}"' % (m.group(0)[:m.group(0).index("format = ")], r, g, b)
        return m.group(0)
    s = re.sub(r'name = (\w+)\s*\n\s*format = "color:\{[^}]*\}"', lambda m: re.sub(
        r'format = "color:\{[^}]*\}"', lambda _: 'format = "color:{%.2f, %.2f, %.2f}"' % PALETTE[m.group(1)], m.group(0))
        if m.group(1) in PALETTE else m.group(0), src)
    for name, fmt in FORMATS.items():
        s = re.sub(r'(name = %s\s*\n\s*format = )"[^"]*"' % name, lambda m: m.group(1) + '"%s"' % fmt, s)
    # Glows help light text on dark stone; on paper they smudge. Make them all transparent.
    for g in ("weak_glow", "medium_glow", "strong_glow"):
        s = re.sub(r'(name = %s\s*\n\s*format = )"[^"]*"' % g, r'\1"glow_color:{0.0,0.0,0.0,0.0}"', s)
    out = MOD / "gui" / "preload" / "textformatting.gui"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(provenance("gui/preload/textformatting.gui", "with the %s palette" % ("night edition's" if DARK else "ink-on-paper")) + s, encoding="utf-8-sig")


# ---------------------------------------------------------------- textures

BACKGROUND = re.compile(r"tile_window_background|tooltip_bg|interaction_menu_bg|resource_panel|hud_bg_|hud_maintab_bg|"
                        r"hud_stress_bg|button_hud_character|tile_letter|overlay_letter|paper_texture|overlay_stone|"
                        r"raise_armies_button\.dds")
RULE = re.compile(r"component_decoration|tile_title_big_top|"
                  r"raise_armies_button_trim|letter_event_edge|marginalia|tile_frame_top")
FRAME = re.compile(r"tooltip_frame")
CLEAR = re.compile(r"letter_event_pattern|ornament_frame|decoration_attacker|decoration_defender|"
                   r"speed_indicator_frame|hud_spike|hud_pause_indicator")   # the date bar's ornaments: as rules they crossed the date
SKIP = re.compile(r"illustrations/|hud_maintab/maintab_|sigil|asia_house_mask")   # done elsewhere / kept


def grain(h, w, seed):
    rng = np.random.default_rng(seed)
    fine = rng.normal(0, 4.0, (h, w))
    from scipy import ndimage
    mottle = ndimage.gaussian_filter(rng.normal(0, 1, (h // 16 + 1, w // 16 + 1)), 1.5)
    mottle = np.kron(mottle, np.ones((16, 16)))[:h, :w] * 9
    return (fine + mottle)[..., None] * THEME["grain"]


def paper(rgba, name):
    h, w = rgba.shape[:2]
    base = PAPER_DARK if re.search(r"subwindow|sidebar|resource_panel_piece\.|hud_bg|button_hud", name) else PAPER
    rgb = np.clip(base + grain(h, w, hash(name) & 0xffff), 0, 255)
    a = rgba[..., 3].astype(np.float32)
    # A thin ink border on the outermost solid pixels: window edges once the texture is nine-sliced
    solid = a > 128
    if solid.any() and min(h, w) >= 32 and "letter" not in name and "stone" not in name:
        ys, xs = np.nonzero(solid)
        y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
        t = 2 if min(h, w) >= 200 else 1
        sides = [np.s_[y0:y1 + 1, x0:x0 + t], np.s_[y0:y1 + 1, x1 - t + 1:x1 + 1]]
        if not re.search(r"(^|/)tile_", name):
            # Tiles repeat vertically in windows (spriteborder = { 18 0 }): a top or bottom rule would show at every
            # seam, as a line across the middle of a panel. Only other textures get them.
            sides += [np.s_[y0:y0 + t, x0:x1 + 1], np.s_[y1 - t + 1:y1 + 1, x0:x1 + 1]]
        for sl in sides:
            rgb[sl] = LINE
    return np.dstack([rgb, a]).astype(np.uint8)


def rule(rgba, name):
    """Replace an ornamental border with a newspaper rule: a thick and a thin line (ink, or a light hairline by
    night) along its long axis, where the ornament was."""
    h, w = rgba.shape[:2]
    a = rgba[..., 3].astype(np.float32) / 255
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = LINE
    horizontal = w >= h
    prof = a.sum(axis=1 if horizontal else 0)              # mass per row (horizontal) or column
    if prof.sum() == 0:
        return out
    centre = int(round((prof * np.arange(len(prof))).sum() / prof.sum()))
    span = a.sum(axis=0 if horizontal else 1) > 0          # where along the axis the ornament exists
    thick = max(2, min(h, w) // 12) if min(h, w) >= 12 else 1
    lines = [(centre - thick // 2, thick), (centre + thick // 2 + 2, 1)]
    for start, n in lines:
        for k in range(start, start + n):
            if 0 <= k < (h if horizontal else w):
                if horizontal:
                    out[k, span, 3] = 255
                else:
                    out[span, k, 3] = 255
    return out


def frame(rgba, name):
    h, w = rgba.shape[:2]
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = LINE
    out[:2, :, 3] = out[-2:, :, 3] = out[:, :2, 3] = out[:, -2:, 3] = 255
    return out


def save_dds(arr, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    im = Image.fromarray(arr, "RGBA")
    h, w = arr.shape[:2]
    if h % 4 == 0 and w % 4 == 0 and h * w >= 4096:
        im.save(path, pixel_format="DXT5")
    else:
        im.save(path)                                       # uncompressed RGBA for tiny or odd sizes


def build_textures():
    src_dirs = [GAME / "gfx" / "interface" / "skinned"] + sorted((GAME / "gfx" / "interface" / "skins").iterdir())
    counts = {"background": 0, "rule": 0, "frame": 0, "clear": 0, "kept": 0}
    for d in src_dirs:
        for f in sorted(d.rglob("*.dds")):
            rel = f.relative_to(GAME)
            name = str(f.relative_to(d))
            if SKIP.search(name):
                counts["kept"] += 1
                continue
            try:
                im = Image.open(f)
                im.load()
                rgba = np.array(im.convert("RGBA"))
            except Exception as e:                           # noqa: BLE001
                print("  can't read %s: %s" % (rel, e))
                continue
            if name == "color_theme.dds":
                # The theme tint behind window headings: a shade off the paper, so the heading reads (black hid it)
                arr = np.full(rgba.shape, 255, np.uint8)
                arr[..., :3] = THEME["heading"]
                kind = "background"
            elif name == "mask_pattern.dds":
                # A lattice of crosses laid over buttons and rows: subtle on dark stone, a loud cross-hatch on paper
                arr = np.full(rgba.shape, 255, np.uint8)
                kind = "background"
            elif CLEAR.search(name):
                arr, kind = np.zeros_like(rgba), "clear"
            elif FRAME.search(name):
                arr, kind = frame(rgba, name), "frame"
            elif RULE.search(name):
                arr, kind = rule(rgba, name), "rule"
            elif BACKGROUND.search(name):
                arr, kind = paper(rgba, name), "background"
            else:
                counts["kept"] += 1
                continue
            counts[kind] += 1
            save_dds(arr, MOD / rel)
    return counts


# UI chrome outside the skin: buttons, HUD bars, title tiles, tooltips, scrollbars, frames. Recoloured as a
# "newsprint negative": dark fills become paper and bright gilding becomes ink, so every button state, border and
# bevel keeps its shape. Icons and pictures are left alone.
NEGATIVE_DIRS = ["buttons", "hud", "component_tiles", "tooltips", "scrollbars", "frontend", "window_event"]
RULE_DIRS = ["component_decoration"]          # ornamental bands: plain newspaper rules instead
NEGATIVE_SKIP = re.compile(r"icon|illustration|startscreen|logo|portrait|coa|flag|mask|_bg\.dds$|background_image")


def negative(rgba, name):
    rgb = rgba[..., :3].astype(np.float32) / 255
    a = rgba[..., 3]
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    solid = a > 32
    if solid.sum() < 16:
        return rgba
    lo, hi = np.percentile(lum[solid], 3), np.percentile(lum[solid], 97)
    t = np.clip((lum - lo) / max(hi - lo, 0.05), 0, 1) ** 1.3          # 0 = darkest (paper), 1 = brightest (ink)
    h, w = a.shape
    if re.search(r"overlay|paper_texture", name):
        return np.zeros_like(rgba)            # grunge laid over other textures: on paper it only smudges the text
    # Text sits on the inside of these textures: stretched to full contrast, vanilla's stained parchment became
    # black-and-white blotches. Keep the contrast near the edges (bevels, borders) and keep the inside light.
    from scipy import ndimage
    edge = min(max(3, min(h, w) // 10), 24)
    inside = solid.copy()
    inside[:edge, :] = inside[-edge:, :] = False
    inside[:, :edge] = inside[:, -edge:] = False
    dist = ndimage.distance_transform_edt(inside)
    keep = np.clip(1 - dist / edge, 0, 1)                               # 1 at the edge, 0 well inside
    t = keep * t + (1 - keep) * np.minimum(ndimage.gaussian_filter(t, 2), 0.10 if min(h, w) < 256 else 0.02)
    out = PAPER * (1 - t[..., None]) + LINE * t[..., None] + grain(h, w, hash(name) & 0xffff) * 0.6
    return np.dstack([np.clip(out, 0, 255), a]).astype(np.uint8)


def build_rules_and_misc():
    """Ornamental bands become rules; the bookmark screen's medieval "create a ruler" figures are removed."""
    n = 0
    for d in RULE_DIRS:
        for f in sorted((GAME / "gfx" / "interface" / d).rglob("*.dds")):
            rgba = np.array(Image.open(f).convert("RGBA"))
            save_dds(rule(rgba, f.name), MOD / f.relative_to(GAME))
            n += 1
    bm = GAME / "gfx" / "interface" / "bookmarks"
    for name in ("custom_ruler.dds", "custom_ruler_glow.dds"):
        van = Image.open(bm / name)
        save_dds(np.zeros((van.height, van.width, 4), np.uint8), MOD / "gfx/interface/bookmarks" / name)
    van = np.array(Image.open(bm / "custom_ruler_backdrop.dds").convert("RGBA"))
    save_dds(paper(van, "custom_ruler_backdrop"), MOD / "gfx/interface/bookmarks/custom_ruler_backdrop.dds")
    return n


MONO_DIRS = ["icons/alerts"]                  # the purple alert diamonds along the top: ink and paper, no colour


def mono(rgba, name):
    rgb = rgba[..., :3].astype(np.float32) / 255
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    t = np.clip((lum - 0.15) / 0.7, 0, 1)                     # dark body, light glyph, in either look
    dark, light = (np.array(THEME[k], np.float32) for k in ("alert_dark", "alert_light"))
    out = dark * (1 - t[..., None]) + light * t[..., None]
    return np.dstack([out, rgba[..., 3]]).astype(np.uint8)


def build_mono():
    n = 0
    for d in MONO_DIRS:
        for f in sorted((GAME / "gfx" / "interface" / d).rglob("*.dds")):
            try:
                rgba = np.array(Image.open(f).convert("RGBA"))
            except Exception:                                    # noqa: BLE001
                continue
            save_dds(mono(rgba, f.name), MOD / f.relative_to(GAME))
            n += 1
    return n


# Bright, flat accents for screens that still used black medieval line art.  These are deliberately generated from
# vanilla's masks rather than hand-painted one by one: new DLC tabs and traits inherit the Westminster treatment too.
MODERN_ACCENTS = {
    "diplomacy": (78, 174, 218), "foreign": (78, 174, 218), "family": (78, 174, 218), "majesty": (78, 174, 218),
    "martial": (224, 92, 86), "strategy": (224, 92, 86), "authority": (224, 92, 86), "chivalry": (224, 92, 86),
    "stewardship": (88, 190, 142), "wealth": (88, 190, 142), "domain": (88, 190, 142), "duty": (88, 190, 142),
    "intrigue": (174, 120, 219), "skulduggery": (174, 120, 219), "temptation": (174, 120, 219), "intimidation": (174, 120, 219),
    "learning": (235, 185, 75), "scholarship": (235, 185, 75), "medicine": (235, 185, 75), "theology": (235, 185, 75),
    "wanderer": (74, 186, 181), "wayfarer": (74, 186, 181), "voyager": (74, 186, 181), "surveyor": (74, 186, 181),
    "decisions": (235, 185, 75), "situations": (237, 133, 86), "factions": (224, 92, 86),
    "council": (78, 174, 218), "court": (174, 120, 219),
    "military": (224, 92, 86), "realm": (88, 190, 142), "activities": (74, 186, 181),
    "camp": (237, 133, 86), "contracts": (235, 185, 75), "estate": (88, 190, 142),
}


def modern_accent(name):
    low = name.lower()
    for word, color in MODERN_ACCENTS.items():
        if word in low:
            return np.array(color, dtype=np.float32)
    return np.array((120, 178, 210), dtype=np.float32)


def modern_duotone(rgba, name, card=False):
    """Turn old dark/gold art into a crisp modern icon with a bright accent and dark navy depth."""
    rgb = rgba[..., :3].astype(np.float32)
    alpha = rgba[..., 3].astype(np.float32)
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32) / 255
    accent = modern_accent(name)
    light = np.array((245, 239, 226), dtype=np.float32)
    deep = np.array((27, 34, 43), dtype=np.float32)
    solid = alpha > 24
    lo, hi = np.percentile(lum[solid], (5, 95)) if solid.any() else (0, 1)
    tone = np.clip((lum - lo) / max(hi - lo, 0.08), 0, 1)[..., None]
    # A dark base and category colour retain the original silhouette, while the brightest quarter becomes an
    # off-white highlight. This reads as a flat vector mark at HUD size but keeps enough detail in a trait portrait.
    out = deep * (1 - tone) + accent * tone
    highlight = np.clip((tone - 0.72) / 0.28, 0, 1)
    out = out * (1 - 0.45 * highlight) + light * (0.45 * highlight)
    if card:
        # Lifestyle paths are full-bleed pictures. A restrained gradient makes each tree distinct while leaving
        # perk connectors and labels readable.
        h, w = alpha.shape
        yy = np.linspace(0, 1, h)[:, None, None]
        base = deep[None, None, :] * (0.75 - 0.15 * yy) + accent[None, None, :] * (0.25 + 0.15 * yy)
        detail = (tone - 0.5) * 38
        out = np.clip(base + detail, 0, 255)
        alpha[:] = 255
    return np.dstack([np.clip(out, 0, 255), alpha]).astype(np.uint8)


def build_modern_icons():
    """Fallback treatment for the right-hand HUD tabs; fal_images.py installs the final generated pictograms."""
    if not DARK:
        return {"hud tabs": 0}
    counts = {"hud tabs": 0}
    hud_roots = [GAME / "gfx/interface/skinned/hud_maintab"] + sorted((GAME / "gfx/interface/skins").glob("*/hud_maintab"))
    for directory in hud_roots:
        for f in sorted(directory.glob("maintab_*.dds")):
            if f.name.startswith("maintab_bg"):
                continue
            rgba = np.array(Image.open(f).convert("RGBA"))
            save_dds(modern_duotone(rgba, f.stem), MOD / f.relative_to(GAME))
            counts["hud tabs"] += 1
    return counts


GENERATED_UI = ROOT / "art" / "generated_ui"
TRAIT_ATLAS = [
    "brave", "craven", "diligent", "lazy", "content",
    "greedy", "generous", "honest", "deceitful", "compassionate",
    "callous", "stubborn", "fickle", "gregarious", "shy",
    "just", "arbitrary", "patient", "impatient", "calm",
    "wrathful", "humble", "arrogant", "zealous", "cynical",
    "temperate", "gluttonous", "ambitious", "suspicious", "patient_alt",
]
LIFESTYLE_ATLAS = [
    "_frame_lifestyle", "node_diplomacy", "node_intrigue", "node_learning", "node_martial",
    "node_stewardship", "node_wanderer", "trait_administrator", "trait_architect", "trait_august",
    "trait_avaricious", "trait_diplomat", "trait_erudite", "trait_family_first", "trait_gallant",
    "trait_overseer", "trait_schemer", "trait_seducer", "trait_strategist", "trait_surveyor",
    "trait_theologian", "trait_torturer", "trait_voyager", "trait_wayfarer", "trait_whole_of_body",
]
LIFESTYLE_MAIN = {
    "diplomacy_lifestyle": 1, "intrigue_lifestyle": 2, "learning_lifestyle": 3,
    "martial_lifestyle": 4, "stewardship_lifestyle": 5, "wanderer_lifestyle": 6,
}
BACKGROUND_CELLS = {
    "foreign_affairs": 0, "majesty": 0, "family": 0,
    "strategy": 1, "authority": 1, "chivalry": 1,
    "wealth": 2, "domain": 2, "duty": 2,
    "skulduggery": 3, "temptation": 3, "intimidation": 3,
    "learning_lifestyle": 4, "scholarship": 4, "medicine": 4, "theology": 4,
    "wayfarer": 5, "voyager": 5, "surveyor": 5,
}


def atlas_cell(atlas, columns, rows, index):
    """Crop one exact grid cell, avoiding accumulated rounding at the atlas edge."""
    col, row = index % columns, index // columns
    return atlas.crop((round(col * atlas.width / columns), round(row * atlas.height / rows),
                       round((col + 1) * atlas.width / columns), round((row + 1) * atlas.height / rows)))


def generated_icon_card(cell, size, name):
    """Put a generated transparent pictogram in the same high-contrast card language as the HUD tabs."""
    # Lifestyle and perk textures are horizontal sprite strips (usually normal, hover, selected). Build one square
    # tile and repeat it into every state instead of shrinking a single icon across the whole strip.
    if size[0] > size[1] and size[0] % size[1] == 0:
        frame = generated_icon_card(cell, (size[1], size[1]), name)
        return np.concatenate([frame] * (size[0] // size[1]), axis=1)
    cell = cell.convert("RGBA")
    alpha = cell.getchannel("A")
    box = alpha.getbbox()
    if box:
        cell = cell.crop(box)
    side = round(min(size) * 0.69)
    cell.thumbnail((side, side), Image.Resampling.LANCZOS)
    accent = tuple(int(v) for v in modern_accent(name))
    canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    margin = max(3, round(min(size) * 0.055))
    radius = max(7, round(min(size) * 0.17))
    line = max(2, round(min(size) * 0.025))
    draw.rounded_rectangle((margin, margin, size[0] - margin - 1, size[1] - margin - 1), radius=radius,
                           fill=(24, 31, 40, 246), outline=accent + (255,), width=line)
    x, y = (size[0] - cell.width) // 2, (size[1] - cell.height) // 2
    canvas.alpha_composite(cell, (x, y))
    return np.array(canvas)


def build_generated_political_icons():
    """Install the generated modern political art; no vanilla pixels are used by these assets."""
    counts = {"lifestyle backgrounds": 0, "lifestyle icons": 0, "lifestyle perks": 0, "personality traits": 0}
    bg_atlas = Image.open(GENERATED_UI / "lifestyle_backgrounds.png").convert("RGB")
    bg_dir = GAME / "gfx/interface/icons/lifestyle_tree_backgrounds"
    for name, index in BACKGROUND_CELLS.items():
        target = bg_dir / f"{name}.dds"
        tw, th = Image.open(target).size
        cell = atlas_cell(bg_atlas, 3, 2, index)
        # Fill the original tall canvas. Slight path-specific crops keep the three trees in a category from being
        # pixel-identical while retaining a coherent lifestyle identity.
        shift = sum(name.encode("utf-8")) % max(1, cell.width // 14)
        scale = max(tw / cell.width, th / cell.height)
        cell = cell.resize((round(cell.width * scale), round(cell.height * scale)), Image.Resampling.LANCZOS)
        x = max(0, min(cell.width - tw, (cell.width - tw) // 2 + shift - cell.width // 28))
        y = max(0, (cell.height - th) // 2)
        save_dds(np.array(cell.crop((x, y, x + tw, y + th)).convert("RGBA")), MOD / target.relative_to(GAME))
        counts["lifestyle backgrounds"] += 1

    icon_atlas = Image.open(GENERATED_UI / "lifestyle_icons.png").convert("RGBA")
    perk_dir = GAME / "gfx/interface/icons/lifestyles_perks"
    for index, name in enumerate(LIFESTYLE_ATLAS):
        target = perk_dir / f"{name}.dds"
        size = Image.open(target).size
        save_dds(generated_icon_card(atlas_cell(icon_atlas, 5, 5, index), size, name), MOD / target.relative_to(GAME))
        counts["lifestyle perks"] += 1
    lifestyle_dir = GAME / "gfx/interface/icons/lifestyles"
    for name, index in LIFESTYLE_MAIN.items():
        target = lifestyle_dir / f"{name}.dds"
        size = Image.open(target).size
        save_dds(generated_icon_card(atlas_cell(icon_atlas, 5, 5, index), size, name), MOD / target.relative_to(GAME))
        counts["lifestyle icons"] += 1

    trait_atlas = Image.open(GENERATED_UI / "personality_traits.png").convert("RGBA")
    trait_dir = GAME / "gfx/interface/icons/traits"
    for index, name in enumerate(TRAIT_ATLAS[:28]):       # final two cells are alternate concepts, not CK3 traits
        target = trait_dir / f"{name}.dds"
        if not target.exists():
            continue
        size = Image.open(target).size
        save_dds(generated_icon_card(atlas_cell(trait_atlas, 5, 6, index), size, name), MOD / target.relative_to(GAME))
        counts["personality traits"] += 1
    return counts


# Paintings that the GUI uses as panel backdrops behind text (the decision window's Effects box, the interaction
# windows): faded most of the way to paper, so ink text on them reads.
PALE = ["gfx/interface/icons/lifestyle_tree_backgrounds/skulduggery.dds",
        "gfx/interface/icons/lifestyle_tree_backgrounds/temptation.dds"]


def build_pale():
    for rel in PALE:
        rgba = np.array(Image.open(GAME / rel).convert("RGBA")).astype(np.float32)
        rgba[..., :3] = rgba[..., :3] * 0.15 + np.array(PAPER, dtype=np.float32) * 0.85
        save_dds(np.clip(rgba, 0, 255).astype(np.uint8), MOD / rel)
    return len(PALE)


# Grunge masks (component_masks/): the GUI multiplies or overlays them on panels for an aged look. On paper their
# blotches put grey clouds behind the text. Evened out: the same overall level or shape, without the texture.
MASKS_FLAT = ["mask_clouds", "mask_clouds_solid", "mask_texture_01", "mask_rough_texture_02", "mask_brushed"]
MASKS_SOLID = ["mask_scratches"]
MASKS_SOFT = ["mask_rough_edges", "mask_fade_textured_vertical_down", "mask_fade_textured_vertical_up"]


def build_masks():
    from scipy import ndimage
    d = GAME / "gfx/interface/component_masks"
    n = 0
    for name in MASKS_FLAT + MASKS_SOLID + MASKS_SOFT:
        f = d / (name + ".dds")
        if not f.exists():
            continue
        rgba = np.array(Image.open(f).convert("RGBA")).astype(np.float32)
        a = rgba[..., 3]
        if name in MASKS_FLAT:
            a[:] = a.mean()
        elif name in MASKS_SOLID:
            a[:] = 255
        else:                                     # keep the shape (edges, fades), lose the ragged texture
            a[:] = ndimage.gaussian_filter(ndimage.median_filter(a, size=9), max(2, min(a.shape) / 60))
        save_dds(np.clip(rgba, 0, 255).astype(np.uint8), MOD / f.relative_to(GAME))
        n += 1
    return n


def build_overlays():
    """component_overlay/*: textures blended onto panels in overlay mode for stains, noise and worn frames (the grey
    clouds behind event text). Mid grey is overlay's neutral: the panel shows as drawn."""
    n = 0
    for f in sorted((GAME / "gfx/interface/component_overlay").glob("*.dds")):
        rgba = np.array(Image.open(f).convert("RGBA"))
        rgba[..., :3] = 128
        save_dds(rgba, MOD / f.relative_to(GAME))
        n += 1
    return n


def build_negative():
    n = 0
    for d in NEGATIVE_DIRS:
        for f in sorted((GAME / "gfx" / "interface" / d).rglob("*.dds")):
            rel = f.relative_to(GAME)
            if NEGATIVE_SKIP.search(f.name.lower()):
                continue
            try:
                im = Image.open(f)
                im.load()
                rgba = np.array(im.convert("RGBA"))
            except Exception as e:                                       # noqa: BLE001
                print("  can't read %s: %s" % (rel, e))
                continue
            save_dds(negative(rgba, f.name), MOD / rel)
            n += 1
    return n


def provenance(rel, change):
    """First line of every vanilla GUI file this script copies: where it came from and where to change it."""
    return ("# Westminster: Crusader Kings III's own %s (Paradox Interactive), %s, by westminster/tools/ui/build_theme.py"
            " - edit there.\n" % (rel, change))


DARK_GLOW = re.compile(r"glow_color:\{ ?0(\.[0-9]+)?, ?0(\.[0-9]+)?, ?0(\.[0-9]+)?, ?[01](\.[0-9]+)? ?\}")


def build_glowless_gui():
    """Vanilla GUI files that hard-code a dark glow around text (for light text on dark stone) are copied with
    the glow made transparent: on newsprint it only smudges. Rebuilt from vanilla each time."""
    n = 0
    for f in sorted((GAME / "gui").rglob("*.gui")):
        if f.name == "textformatting.gui":          # has its own palette (build_textformatting)
            continue
        out = MOD / f.relative_to(GAME)
        src = f.read_text(encoding="utf-8-sig")         # always from vanilla: this pass runs first
        if not DARK_GLOW.search(src):
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        head = provenance(f.relative_to(GAME).as_posix(), "with its dark text glows made transparent")
        out.write_text(head + DARK_GLOW.sub("glow_color:{0,0,0,0}", src), encoding="utf-8-sig")
        n += 1
    return n


TINT = re.compile(r"(\b(?:color|tintcolor) = \{\s*)([0-9.]+)\s+([0-9.]+)\s+([0-9.]+)(\s+[0-9.]+)?(\s*\})")


def paper_tint(m):
    r, g, b = (float(m.group(i)) for i in (2, 3, 4))
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    if lum >= 0.3:
        return m.group(0)
    k = 1 - lum / 0.3                         # 0 (grey) .. 1 (black)
    if DARK:
        # Vanilla's dark tints suit dark paper; only the near-blacks are lifted to the charcoal of the panels, a
        # little darker than the paper for the darkest (wells), up to the raised tone
        paper, raised = np.array(rgb01(THEME["paper"])), np.array(rgb01(THEME["paper_raised"]))
        base = raised - k * (raised - paper * 0.8)
    else:
        # Dark backdrop tints become paper: the darker the original, the deeper the paper tone
        base = np.array([0.95, 0.93, 0.88]) - k * np.array([0.10, 0.10, 0.11])
    return "%s%.3f %.3f %.3f%s%s" % (m.group(1), base[0], base[1], base[2], m.group(5) or "", m.group(6))


ACTION_STATUS_COLORS = {
    "Status_Suggestion": "0.31 0.39 0.47 1",       # slate blue: neutral actions
    "Status_Suggestion_Bad": "0.48 0.22 0.20 1",  # warm red: urgent actions
    "Status_Suggestion_Good": "0.22 0.38 0.30 1", # teal: positive actions
}


def accent_suggestion_colors(text):
    """Give the current-situation rows distinct slate, red, and teal fills in the night edition."""
    if not DARK:
        return text
    lines = text.splitlines(keepends=True)
    for name, color in ACTION_STATUS_COLORS.items():
        start = next((i for i, line in enumerate(lines) if line.strip() == f"template {name}"), None)
        if start is None:
            continue
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("}") and lines[i].strip() == "}"), None)
        if end is None:
            continue
        for i in range(start + 1, end):
            if re.match(r"\s*color\s*=\s*\{", lines[i]):
                lines[i] = re.sub(r"(?<=\{)[^}]+", f" {color} ", lines[i], count=1)
                break
    return "".join(lines)


def build_paper_tints():
    """The shared background templates (gui/shared/*.gui: Background_Area_Solid etc.) tint their textures nearly
    black. Those tints become paper tones, so panels everywhere are light behind the ink text."""
    n = 0
    for f in sorted((GAME / "gui" / "shared").glob("*.gui")):
        rel = f.relative_to(GAME)
        dest = MOD / rel
        # Always from vanilla (with the glow pass's change, if it makes one): an earlier run's output has the other
        # look's tints, which this pass wouldn't recognise as dark
        src = f.read_text(encoding="utf-8-sig")
        glows = bool(DARK_GLOW.search(src))
        src = DARK_GLOW.sub("glow_color:{0,0,0,0}", src)
        out, k = TINT.subn(paper_tint, src)
        if rel.as_posix() == "gui/shared/backgrounds.gui":
            out = accent_suggestion_colors(out)
        if k and out != f.read_text(encoding="utf-8-sig"):
            change = "with its dark text glows made transparent and dark tints made paper" if glows else \
                "with its dark tints made paper"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(provenance(rel.as_posix(), change) + out, encoding="utf-8-sig")
            n += 1
    return n


def build_colors():
    """gfx/interface/colors/black.dds is laid over panels at part opacity to darken them; on paper that greys
    them, so it becomes a light warm grey (overlays now tint the paper)."""
    van = Image.open(GAME / "gfx/interface/colors/black.dds")
    arr = np.full((van.height, van.width, 4), 255, dtype=np.uint8)
    arr[..., :3] = (214, 208, 196)
    save_dds(arr, MOD / "gfx/interface/colors/black.dds")


def build_event_text_panel():
    """The character event's text panel is 70% opaque paper over the event photo, overlaid with stains: the blurred
    photo showed through as grey clouds behind the text. Made opaque and plain. Edits the glow-free copy."""
    rel = Path("gui/event_windows/character_event.gui")
    dest = MOD / rel
    src = (dest if dest.exists() else GAME / rel).read_text(encoding="utf-8-sig")
    old = re.compile(r'(texture = "gfx/interface/component_tiles/tile_window_background_no_edge\.dds"\s*'
                     r'spriteType = Corneredtiled\s*spriteborder = \{ 18 0 \}\s*texture_density = 2\s*)alpha = 0\.7(\s*)'
                     r'modify_texture = \{\s*texture = "gfx/interface/component_overlay/overlay_effect\.dds"\s*blend_mode = overlay\s*\}\s*')
    out, n = old.subn(lambda m: m.group(1) + "alpha = 1" + m.group(2), src)
    if n:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out, encoding="utf-8-sig")
    return n


def main():
    if "--contrast" in sys.argv:
        for n, r, ok in contrast_report():
            print("%-22s %5.2f:1 %s" % (n, r, "" if ok else "LOW"))
        return
    Image.MAX_IMAGE_PIXELS = None
    build_fonts()
    print("fonts: Playfair Display (headlines), Source Serif 4 (text)")
    build_textformatting()
    print("textformatting.gui: %s palette, no glows" % LOOK)
    for n, r, ok in contrast_report():
        if not ok:
            print("  low contrast: %s %.2f:1" % (n, r))
    print("pale panel backdrops:", build_pale())
    print("grunge masks evened out:", build_masks())
    print("overlay textures neutral:", build_overlays())
    print("textures:", build_textures())
    print("chrome recoloured:", build_negative())
    print("decoration bands as rules:", build_rules_and_misc())
    print("alert icons in ink:", build_mono())
    print("generated modern political artwork:", build_generated_political_icons())
    print("modern HUD fallback icons:", build_modern_icons())
    print("gui files with dark glows patched:", build_glowless_gui())
    build_textformatting()
    print("shared gui files with dark tints made paper:", build_paper_tints())   # after: edits the glow-free copies
    print("event text panel made opaque:", build_event_text_panel())
    # Not build_colors(): a light black.dds also sits behind light text (the pause banner, top bar), which then vanished


if __name__ == "__main__":
    main()
