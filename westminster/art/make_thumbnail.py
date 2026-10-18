#!/usr/bin/env python3
"""Build the mod thumbnail from the approved adaptive artwork.

Steam shows the thumbnail square. The Paradox launcher center-crops it to a wide
2:1 card, so the source keeps both leaders, Big Ben, title, and date range inside
the middle horizontal band.
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "westminster" / "thumbnail.png"
SOURCE = HERE / "thumbnail_westminster_v4.png"
SIZE = 1024


def main():
    page = Image.open(SOURCE).convert("RGB").resize(
        (SIZE, SIZE), Image.Resampling.LANCZOS
    )
    page.quantize(
        colors=256,
        method=Image.Quantize.MEDIANCUT,
        dither=Image.Dither.FLOYDSTEINBERG,
    ).save(OUT, optimize=True)
    print("wrote", OUT, OUT.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
