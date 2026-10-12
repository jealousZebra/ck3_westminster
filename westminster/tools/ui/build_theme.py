#!/usr/bin/env python3
"""Westminster's newspaper UI theme: fonts, text colours and the shared interface textures.

    .venv/bin/python westminster/tools/ui/build_theme.py

- Fonts: the medieval headline font (Fondamento) becomes Playfair Display, the body font (Gitan) Source Serif 4.
  The files go at vanilla's paths, so fonts.font needn't change. Both are SIL Open Font Licence.
- Text: gui/preload/textformatting.gui with an ink palette (dark text on paper, red accent, no glows).
- Textures: the UI skin (gfx/interface/skinned and every gfx/interface/skins/<culture>) redrawn: window, tooltip
  and panel backgrounds become newsprint; ornamental borders become plain ink rules; medieval ornaments that
  have no modern equivalent are removed. Each texture keeps its size and alpha shape, so the GUI layouts work
  unchanged. Illustrations and tab icons are replaced separately (images generated with fal.ai).
"""
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent          # westminster/
MOD = ROOT / "westminster"
RAW = ROOT / "data" / "raw"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)

PAPER = np.array([243, 239, 230], dtype=np.float32)            # newsprint
PAPER_DARK = np.array([232, 226, 214], dtype=np.float32)       # inset panels
INK = np.array([24, 24, 24], dtype=np.float32)
RED = (0.69, 0.10, 0.12)                                        # the one accent colour

# Text palette: name -> (r, g, b) in 0-1. Everything else in textformatting.gui stays as vanilla.
PALETTE = {
    "highlight": RED, "color_white": (0.09, 0.09, 0.09), "color_gray": (0.22, 0.22, 0.21),
    "color_dark_gray": (0.42, 0.41, 0.40), "color_red": (0.72, 0.11, 0.12), "color_light_red": (0.82, 0.18, 0.18),
    "color_green": (0.10, 0.45, 0.18), "color_yellow": RED, "color_light_blue": (0.10, 0.32, 0.56),
    "color_dark_blue": (0.08, 0.20, 0.42), "color_blue_gray": (0.30, 0.32, 0.38), "color_goldy_yellow": (0.45, 0.33, 0.16),
    "color_black": (0.05, 0.05, 0.05), "color_dark_green": (0.08, 0.38, 0.12),
}
# Formats whose whole definition is replaced: light colours with dark glows, made for stone (the HUD date, difficulty).
FORMATS = {
    "date": "color:{0.09, 0.09, 0.09};glow_color:{0,0,0,0}",
    "difficulty_easy": "bold;color:{0.10, 0.45, 0.18}", "difficulty_medium": "bold;color:{0.45, 0.33, 0.16}",
    "difficulty_hard": "bold;color:{0.72, 0.11, 0.12}", "difficulty_very_hard": "bold;color:{0.45, 0.06, 0.08}",
    "charioteer_blue": "bold;color:{0.10, 0.32, 0.56}", "color_porple": "color:{0.40, 0.18, 0.55}",
    "defender_color": "color:{0.18, 0.30, 0.45}", "Xlight": "color:{0.72, 0.11, 0.12};italic",
    "flatulence": "bold;italic;color:{0.08, 0.38, 0.12}",
}


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
    out.write_text(provenance("gui/preload/textformatting.gui", "with an ink-on-paper palette") + s, encoding="utf-8-sig")


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
    return (fine + mottle)[..., None]


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
            rgb[sl] = INK
    return np.dstack([rgb, a]).astype(np.uint8)


def rule(rgba, name):
    """Replace an ornamental border with a newspaper rule: a thick and a thin ink line along its long axis,
    where the ornament was."""
    h, w = rgba.shape[:2]
    a = rgba[..., 3].astype(np.float32) / 255
    out = np.zeros((h, w, 4), dtype=np.uint8)
    out[..., :3] = INK
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
    out[..., :3] = INK
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
                # The theme tint behind window headings: light newsprint grey, so the ink heading reads (black hid it)
                arr = np.full(rgba.shape, 255, np.uint8)
                arr[..., :3] = (226, 220, 207)
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
    out = PAPER * (1 - t[..., None]) + INK * t[..., None] + grain(h, w, hash(name) & 0xffff) * 0.6
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
    t = np.clip((lum - 0.15) / 0.7, 0, 1)                     # dark -> ink, light -> paper
    out = INK * (1 - t[..., None]) + PAPER * t[..., None]
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
    # Dark backdrop tints become paper: the darker the original, the deeper the paper tone
    k = 1 - lum / 0.3                         # 0 (grey) .. 1 (black)
    base = np.array([0.95, 0.93, 0.88]) - k * np.array([0.10, 0.10, 0.11])
    return "%s%.3f %.3f %.3f%s%s" % (m.group(1), base[0], base[1], base[2], m.group(5) or "", m.group(6))


def build_paper_tints():
    """The shared background templates (gui/shared/*.gui: Background_Area_Solid etc.) tint their textures nearly
    black. Those tints become paper tones, so panels everywhere are light behind the ink text."""
    n = 0
    for f in sorted((GAME / "gui" / "shared").glob("*.gui")):
        rel = f.relative_to(GAME)
        dest = MOD / rel
        mine = dest.read_text(encoding="utf-8-sig") if dest.exists() else ""
        first, _, rest = mine.partition("\n")
        if "build_theme.py" in first:                    # the glow-free copy (or this pass's own earlier output)
            src, glows = rest, "dark text glows made transparent" in first
        else:
            src, glows = f.read_text(encoding="utf-8-sig"), False
        out, k = TINT.subn(paper_tint, src)
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
    Image.MAX_IMAGE_PIXELS = None
    build_fonts()
    print("fonts: Playfair Display (headlines), Source Serif 4 (text)")
    build_textformatting()
    print("textformatting.gui: ink palette, no glows")
    print("pale panel backdrops:", build_pale())
    print("grunge masks evened out:", build_masks())
    print("overlay textures neutral:", build_overlays())
    print("textures:", build_textures())
    print("chrome recoloured:", build_negative())
    print("decoration bands as rules:", build_rules_and_misc())
    print("alert icons in ink:", build_mono())
    print("gui files with dark glows patched:", build_glowless_gui())
    build_textformatting()
    print("shared gui files with dark tints made paper:", build_paper_tints())   # after: edits the glow-free copies
    print("event text panel made opaque:", build_event_text_panel())
    # Not build_colors(): a light black.dds also sits behind light text (the pause banner, top bar), which then vanished


if __name__ == "__main__":
    main()
