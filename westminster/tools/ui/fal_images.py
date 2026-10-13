#!/usr/bin/env python3
"""Generates Westminster's pictures with fal.ai (FLUX) and installs them over the game's medieval ones.

    .venv/bin/python westminster/tools/ui/fal_images.py [name ...]     # all, or just the named images

The API key is read from $FAL_KEY or ~/.config/fal/key (never from the repo). Raw downloads are cached in
westminster/art/fal/ (so re-running only fetches what's missing; delete a file to regenerate it), then resized to
the size of the vanilla texture they replace and written as DDS into the mod.

The house style: British political press photography and illustration, modern (2020s), restrained colour with
newsprint tones; no medieval subjects.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent.parent          # westminster/
MOD = ROOT / "westminster"
CACHE = ROOT / "art" / "fal"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)
MODEL = "fal-ai/flux/dev"
STYLE = ("editorial press photograph for a British broadsheet newspaper, 2020s, natural light, muted colour grade "
         "with warm newsprint tones, shallow depth of field, no text, no logos, no watermark")

# name: (vanilla texture it replaces, fal image size, prompt)
IMAGES = {
    "main_menu": ("gfx/interface/frontend/wm_backdrop.dds", "full_hd",
                  "The Palace of Westminster and Elizabeth Tower seen across the River Thames at dawn, mist on the water, "
                  "Westminster Bridge with a red bus, wide shot"),
    "loading": ("gfx/interface/frontend/startscreen.dds", "full_hd",
                "A stack of folded morning newspapers seen from the side on a wooden desk beside a cup of tea, the pages "
                "blurred and unreadable, window light"),
    "pause": ("gfx/interface/skinned/illustrations/frontend/pause_bg.dds", "full_hd",
              "Evening view of Whitehall in London with the Cenotaph and government buildings, rain on the street, long exposure lights"),
    "council": ("gfx/interface/skinned/illustrations/councilchamber_bg.dds", "full_hd",
                "The Cabinet Room at 10 Downing Street, long table with green leather chairs and papers, empty, soft daylight"),
    "decisions": ("gfx/interface/skinned/illustrations/decisions.dds", "full_hd",
                  "A government minister's desk with a red despatch box, briefing papers and a fountain pen, Whitehall office"),
    "dungeon": ("gfx/interface/skinned/illustrations/dungeon.dds", "full_hd",
                "A bare police interview room in London with a table, two chairs and a recorder, cold light"),
    "faction": ("gfx/interface/skinned/illustrations/faction_bg.dds", "full_hd",
                "A crowded House of Commons committee room, backbench MPs in suits arguing around a table, papers everywhere"),
    "camp": ("gfx/interface/skinned/illustrations/camp_bg.dds", "full_hd",
             "A busy election campaign office with phones, leaflets, rosettes and campaign posters on the walls, volunteers"),
    "holy_order": ("gfx/interface/skinned/illustrations/holy_order_bg.dds", "full_hd",
                   "A think tank seminar room in Westminster with a speaker at a lectern and an audience in suits"),
    "moving": ("gfx/interface/skinned/illustrations/moving.dds", "full_hd",
               "A ministerial car with tinted windows driving through Westminster at night"),
}
# (The 2024 bookmark's background is an election map drawn from the map data: tools/ui/build_bookmark_screen.py.)

# Scenes for the scripted illustrations (tools/ui/build_illustrations.py) and loading screens: new files
LS = "gfx/interface/illustrations/loading_screens/"
SC = "gfx/interface/illustrations/wm/"
IMAGES.update({
    "office": (SC + "office.dds", "full_hd", "A Member of Parliament's office in Portcullis House, desk with papers and laptop, bookshelves, view of Big Ben"),
    "memorial": (SC + "memorial.dds", "full_hd", "Flowers and a framed photograph on a table in a quiet church side chapel, candles"),
    "street": (SC + "street.dds", "full_hd", "Parliament Square in London on an overcast day, statues, black cabs and pedestrians"),
    "church": (SC + "church.dds", "full_hd", "Interior of Westminster Abbey nave, Gothic arches, soft light, empty"),
    "town_hall": (SC + "town_hall.dds", "full_hd", "A Victorian town hall council chamber in the north of England with councillors' benches and a mayor's chair"),
    "home": (SC + "home.dds", "full_hd", "A comfortable London terraced house living room with books, a sofa and a television, evening lamps"),
    "countryside": (SC + "countryside.dds", "full_hd", "A country lane in the English countryside with hedgerows, fields and a village church tower, overcast"),
    "seaside": (SC + "seaside.dds", "full_hd", "A British seaside town promenade with a pier, beach huts and grey sea, off season"),
    "pub": (SC + "pub.dds", "full_hd", "Inside a traditional London pub near Westminster, wooden bar, pints, politicians talking in a corner booth"),
    "hospital": (SC + "hospital.dds", "full_hd", "An NHS hospital ward corridor with beds and nurses, clinical light"),
    "protest": (SC + "protest.dds", "full_hd", "A protest march in Whitehall with banners and placards, a line of police officers in high-visibility jackets"),
    # Vanilla's loading screen files, replaced by name (the game still picks them whatever the settings file says)
    "ls_lobby": (LS + "assassin.dds", "full_hd", "The Members' Lobby in the Palace of Westminster, MPs and journalists talking in small groups, Gothic stone arches"),
    "ls_pmqs": (LS + "baghdad.dds", "full_hd", "Prime Minister's Questions in a packed House of Commons chamber, MPs standing and shouting on the green benches"),
    "ls_night": (LS + "castle.dds", "full_hd", "The Palace of Westminster lit up at night reflected in the River Thames, long exposure"),
    "ls_cabinet": (LS + "council.dds", "full_hd", "A Cabinet meeting in progress around the long table in the Cabinet Room, ministers in suits with red folders"),
    "ls_debate": (LS + "duel.dds", "full_hd", "A televised general election leaders' debate in a TV studio, two podiums, bright studio lights, audience"),
    "ls_commons": (LS + "wm_commons.dds", "full_hd", "The empty House of Commons chamber with green benches and the Speaker's chair"),
    "ls_downing": (LS + "wm_downing.dds", "full_hd", "Downing Street at night, wet street, police officer outside the black door of Number 10"),
    "ls_holyrood": (LS + "wm_holyrood.dds", "full_hd", "The modern Scottish Parliament building by Enric Miralles at Holyrood, irregular "
                    "concrete and oak facades, leaf-shaped roofs and angular windows, Salisbury Crags behind, not a palace, no dome"),
    "ls_senedd": (LS + "wm_senedd.dds", "full_hd", "The Senedd building in Cardiff Bay, glass and timber, evening"),
    "ls_stormont": (LS + "wm_stormont.dds", "full_hd", "Parliament Buildings at Stormont in Belfast at the end of its long avenue"),
    "ls_polling": (LS + "wm_polling.dds", "full_hd", "A British polling station in a church hall, voting booths and a ballot box, a sign saying Polling Station"),
    "ls_count": (LS + "wm_count.dds", "full_hd", "An election night count in a sports hall, counters sorting ballot papers at long tables, candidates in rosettes"),
    "ls_conference": (LS + "wm_conference.dds", "full_hd", "A party conference hall with a speaker on stage, a large audience and bright stage lights"),
    "ls_press": (LS + "wm_press.dds", "full_hd", "A newspaper printing press running at night, rolls of newsprint, motion blur"),
})

# Main tab icons: black line art, keyed to ink on transparency (install_icon)
ICON_STYLE = ("simple bold black line icon, flat pictogram, thick even strokes, centred, pure white background, "
              "no shading, no text")
ICONS = {
    "maintab_council": "a group of three people around a table", "maintab_court": "a classical government building with columns and a triangular pediment",
    "maintab_courtview": "an open door", "maintab_military": "a plain shield with a star in the middle", "maintab_intrigue": "a magnifying glass",
    "maintab_decisions": "a ballot box with a voting paper going into the slot", "maintab_my_realm": "an outline map of Great Britain and Ireland",
    "maintab_factions": "a raised fist", "maintab_activities": "a calendar page", "maintab_camp": "a megaphone",
    "maintab_contracts": "a clipboard with a checklist", "maintab_situations": "a newspaper", "maintab_estate": "a house",
    "maintab_tax_jurisdictions": "a pound sterling coin", "maintab_administrative": "a filing cabinet",
    "maintab_college_of_cardinals": "a microphone", "maintab_administrative_china": "a filing cabinet",
    "maintab_ritsuryo_japan": "a scroll document", "maintab_soryo_japan": "a scroll document",
}
for n, subject in ICONS.items():
    IMAGES["icon_" + n] = ("gfx/interface/skinned/hud_maintab/%s.dds" % n, "square", subject + ", " + ICON_STYLE)


def api_key():
    k = os.environ.get("FAL_KEY")
    if not k:
        p = Path("~/.config/fal/key").expanduser()
        k = p.read_text().strip() if p.exists() else None
    if not k:
        sys.exit("No fal.ai key: set FAL_KEY or put it in ~/.config/fal/key")
    return k


def request(url, key, data=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Authorization": "Key " + key, "Content-Type": "application/json"},
                                 method="POST" if data is not None else "GET")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


SIZES = {"full_hd": {"width": 1920, "height": 1088}, "square": {"width": 1024, "height": 1024}}


def generate(prompt, size, key):
    full = prompt if "line icon" in prompt else prompt + ". " + STYLE
    job = request("https://queue.fal.run/" + MODEL, key,
                  {"prompt": full, "image_size": SIZES.get(size, size), "num_inference_steps": 32, "num_images": 1,
                   "enable_safety_checker": True})
    for _ in range(120):
        st = request(job["status_url"], key)
        if st.get("status") == "COMPLETED":
            break
        time.sleep(2)
    else:
        raise TimeoutError("fal job did not finish")
    res = request(job["response_url"], key)
    return res["images"][0]["url"]


def install_icon(target, raw):
    """Install a modern high-contrast HUD tile from the cached pictogram.

    The old version made the artwork nearly black on transparency. That disappeared into the night theme and looked
    like the original CK3 toolbar after the full UI build overwrote build_theme.py's brighter pass. The pictogram now
    sits in an accent-bordered navy card, with a warm-white glyph and a coloured keyline.
    """
    tw, th = Image.open(GAME / target).size
    g = np.array(Image.open(raw).convert("L")).astype(np.float32) / 255
    a = np.clip((0.85 - g) / 0.6, 0, 1)
    ys, xs = np.nonzero(a > 0.2)
    if len(ys):
        a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    side = int(min(tw, th) * 0.66)
    im = Image.fromarray((a * 255).astype(np.uint8), "L")
    im.thumbnail((side, side), Image.LANCZOS)
    alpha = Image.new("L", (tw, th), 0)
    alpha.paste(im, ((tw - im.width) // 2, (th - im.height) // 2))
    from build_theme import modern_accent
    accent = tuple(int(v) for v in modern_accent(Path(target).stem))
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    margin = max(4, round(min(tw, th) * 0.07))
    radius = max(8, round(min(tw, th) * 0.20))
    line = max(2, round(min(tw, th) * 0.035))
    draw.rounded_rectangle((margin, margin, tw - margin - 1, th - margin - 1), radius=radius,
                           fill=(24, 31, 40, 246), outline=accent + (255,), width=line)
    outline = alpha.filter(ImageFilter.MaxFilter(7))
    edge = np.maximum(np.array(outline, dtype=np.int16) - np.array(alpha, dtype=np.int16), 0).astype(np.uint8)
    accent_layer = Image.new("RGBA", (tw, th), accent + (0,))
    accent_layer.putalpha(Image.fromarray(edge, "L"))
    canvas.alpha_composite(accent_layer)
    glyph = Image.new("RGBA", (tw, th), (247, 241, 228, 0))
    glyph.putalpha(alpha)
    canvas.alpha_composite(glyph)
    rel = Path(target)
    targets = [rel] + [Path("gfx/interface/skins") / d.name / rel.relative_to("gfx/interface/skinned")
                       for d in sorted((GAME / "gfx/interface/skins").iterdir())
                       if (d / rel.relative_to("gfx/interface/skinned")).exists()]
    for t in targets:
        (MOD / t).parent.mkdir(parents=True, exist_ok=True)
        canvas.save(MOD / t)
    return tw, th


def install(name, target, raw):
    """Resize the picture to the vanilla texture's size (cropping to its aspect ratio) and write the DDS."""
    if name.startswith("icon_"):
        return install_icon(target, raw)
    van = Image.open(GAME / target) if (GAME / target).exists() else None
    tw, th = van.size if van else ((3840, 2160) if "loading_screens" in target else (1920, 1088))
    im = Image.open(raw).convert("RGB")
    scale = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * scale), round(im.height * scale)), Image.LANCZOS)
    x0, y0 = (im.width - tw) // 2, (im.height - th) // 2
    im = im.crop((x0, y0, x0 + tw, y0 + th)).convert("RGBA")
    out = MOD / target
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, pixel_format="DXT1" if tw % 4 == 0 and th % 4 == 0 else None)
    return tw, th


def main():
    Image.MAX_IMAGE_PIXELS = None
    names = sys.argv[1:] or list(IMAGES)
    key = api_key()
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "prompts.json").write_text(json.dumps({n: IMAGES[n][2] + ("" if "line icon" in IMAGES[n][2] else ". " + STYLE)
                                                    for n in IMAGES}, indent=1))
    for n in names:
        target, size, prompt = IMAGES[n]
        raw = CACHE / (n + ".jpg")
        if not raw.exists():
            url = generate(prompt, size, key)
            urllib.request.urlretrieve(url, raw)
        tw, th = install(n, target, raw)
        print("%-14s -> %s (%dx%d)" % (n, target, tw, th))


if __name__ == "__main__":
    main()
