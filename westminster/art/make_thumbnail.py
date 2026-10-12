#!/usr/bin/env python3
"""Builds westminster/westminster/thumbnail.png (1024x1024), the Workshop and launcher image.

    .venv/bin/python westminster/art/make_thumbnail.py

A newspaper front page: the masthead WESTMINSTER, a dateline with the version, and a lead photograph of the Palace of
Westminster and Elizabeth Tower at dusk. The Paradox launcher shows the thumbnail in a wide box and crops it to fill
("object-fit: cover") while Steam shows it square, so the masthead, the dateline and the photo sit inside the middle
band (they survive a 2:1 crop); the folio line above and the headline below only show in the square view.

The photograph comes from fal.ai (FLUX.1 [dev], via tools/ui/fal_images.py) and is cached in
art/fal/thumb_westminster.jpg, so a rebuild needs no network. Delete it to generate a new one (needs the API key in
$FAL_KEY or ~/.config/fal/key). The text is set in the mod's own fonts: Playfair Display and Source Serif 4.
"""
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent                          # westminster/art/
ROOT = HERE.parent                                              # westminster/
MOD = ROOT / "westminster"
OUT = MOD / "thumbnail.png"
RAW = HERE / "fal" / "thumb_westminster.jpg"
VERSION = sys.argv[1] if len(sys.argv) > 1 else "0.3"
PROMPT = ("Wide panoramic view of the Palace of Westminster with Elizabeth Tower standing tall on the right, "
          "silhouetted against a dramatic deep orange and red evening sky after sunset, seen from across the River "
          "Thames, reflections on the water, lamps lit along the embankment")

SIZE = 1024
PAPER, PAPER_DARK, INK, GREY, RED = (243, 239, 230), (228, 221, 207), (24, 24, 24), (88, 86, 82), (176, 26, 31)
FONTS = MOD / "fonts"
PLAYFAIR = FONTS / "Fondamento" / "Fondamento-Regular.ttf"      # Playfair Display, at the game's file name
PLAYFAIR_ITALIC = FONTS / "Fondamento" / "Fondamento-Italic.ttf"
SERIF = FONTS / "Gitan" / "GitanLatin-Regular.otf"              # Source Serif 4
SERIF_BOLD = FONTS / "Gitan" / "GitanLatin-Bold.otf"
SERIF_ITALIC = FONTS / "Gitan" / "GitanLatin-Italic.otf"
M = 56                                                          # page margin


def photo():
    """The lead photograph, generated once and cached."""
    if not RAW.exists():
        sys.path.insert(0, str(ROOT / "tools" / "ui"))
        import fal_images                                   # the key never leaves its functions
        fal_images.SIZES["thumb"] = {"width": 1536, "height": 640}
        url = fal_images.generate(PROMPT, "thumb", fal_images.api_key())
        tmp = RAW.with_suffix(".download")
        urllib.request.urlretrieve(url, tmp)
        Image.open(tmp).convert("RGB").save(RAW, quality=90, progressive=True)
        tmp.unlink()
    return Image.open(RAW).convert("RGB")


def fit(img, w, h):
    """Scale and centre-crop to w x h."""
    s = max(w / img.width, h / img.height)
    img = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    x, y = (img.width - w) // 2, (img.height - h) // 2
    return img.crop((x, y, x + w, y + h))


def font(path, size):
    return ImageFont.truetype(str(path), size)


def centred(d, y, text, f, fill, cx=SIZE / 2):
    d.text((cx - d.textlength(text, font=f) / 2, y), text, font=f, fill=fill)


def spaced(text, n=1):
    return (" " * n).join(text)


def main():
    rng = np.random.default_rng(7)
    grain = rng.normal(0, 5, (SIZE, SIZE, 1))
    page = Image.fromarray(np.clip(np.array(PAPER, dtype=np.float32) + grain, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(page)

    # Folio line (square view only): above the band
    small = font(SERIF, 21)
    small_b = font(SERIF_BOLD, 21)
    d.line((M, 60, SIZE - M, 60), fill=INK, width=2)
    d.text((M, 70), "CRUSADER KINGS III", font=small_b, fill=INK)
    centred(d, 70, "A TOTAL CONVERSION", small, GREY)
    t = "MODERN BRITAIN"
    d.text((SIZE - M - d.textlength(t, font=small_b), 70), t, font=small_b, fill=INK)
    d.line((M, 104, SIZE - M, 104), fill=INK, width=1)
    sub = font(PLAYFAIR_ITALIC, 34)
    centred(d, 124, "The front page of British politics", sub, GREY)
    d.line((M, 186, SIZE - M, 186), fill=INK, width=1)
    date = font(SERIF_ITALIC, 21)
    d.text((M, 196), "No. %s" % VERSION, font=date, fill=GREY)
    centred(d, 196, "Friday 5 July 2024", date, GREY)
    t = "650 seats"
    d.text((SIZE - M - d.textlength(t, font=date), 196), t, font=date, fill=GREY)
    d.line((M, 230, SIZE - M, 230), fill=INK, width=1)

    # The band (y 256-768): masthead, dateline, photograph
    word = "WESTMINSTER"
    size = 200
    while True:
        mast = font(PLAYFAIR, size)
        w = d.textlength(word, font=mast)
        if w <= SIZE - 2 * M - 8:
            break
        size -= 2
    box = d.textbbox((0, 0), word, font=mast)
    top = 286
    d.text(((SIZE - w) / 2, top - box[1]), word, font=mast, fill=INK)
    y = top + (box[3] - box[1]) + 22
    d.line((M, y, SIZE - M, y), fill=INK, width=5)
    d.line((M, y + 10, SIZE - M, y + 10), fill=INK, width=2)

    # Dateline: the search words on the left, the version in a red box on the right
    dl = font(SERIF_BOLD, 25)
    y += 22
    d.text((M, y), "ELECTIONS  ·  PARLIAMENT  ·  PRIME MINISTER", font=dl, fill=INK)
    tag = "BETA %s" % VERSION
    tw = d.textlength(tag, font=dl)
    bx1 = SIZE - M
    bx0 = bx1 - tw - 28
    d.rectangle((bx0, y - 7, bx1, y + 33), fill=RED)
    d.text((bx0 + 14, y - 1), tag, font=dl, fill=PAPER)
    y += 46
    d.line((M, y, SIZE - M, y), fill=INK, width=2)

    # Lead photograph, to the bottom of the band, with a thin ink frame
    py0, py1 = y + 14, 734
    pic = fit(photo(), SIZE - 2 * M, py1 - py0)
    page.paste(pic, (M, py0))
    d.rectangle((M - 1, py0 - 1, SIZE - M, py1), outline=INK, width=2)
    cap = font(SERIF_ITALIC, 19)
    d.text((M, py1 + 5), "The Palace of Westminster at dusk. 650 seats are up for grabs.", font=cap, fill=GREY)

    # Below the band (square view only): the headline and three columns
    head = font(PLAYFAIR, 52)
    centred(d, 790, "From Activist to Prime Minister", head, INK)
    cols = [
        "All 650 MPs of the 2024 Parliament, on a map of the real constituencies.",
        "Win selection, fight elections, whip the Commons and survive a confidence vote.",
        "Cross the floor, found a party, call an election. Rise, or fall at the polls.",
    ]
    body = font(SERIF, 21)
    cw = (SIZE - 2 * M - 2 * 30) / 3
    for i, text in enumerate(cols):
        x = M + i * (cw + 30)
        if i:
            d.line((x - 15, 870, x - 15, 985), fill=GREY, width=1)
        line, yy = "", 870
        for wd in text.split():
            trial = (line + " " + wd).strip()
            if d.textlength(trial, font=body) > cw:
                d.text((x, yy), line, font=body, fill=INK)
                line, yy = wd, yy + 27
            else:
                line = trial
        d.text((x, yy), line, font=body, fill=INK)
    d.line((M, 1000, SIZE - M, 1000), fill=INK, width=2)

    # Quantise to keep the PNG small (Steam's preview limit is 1 MB)
    page.quantize(colors=256, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.FLOYDSTEINBERG).save(OUT, optimize=True)
    print("wrote", OUT, OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
