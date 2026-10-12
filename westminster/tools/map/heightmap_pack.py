"""CK3's packed heightmap: map_data/packed_heightmap.png, indirection_heightmap.png and heightmap.heightmap.

The game doesn't read heightmap.png directly; it reads a packed copy made of tiles. Format, worked out from the
vanilla files (see decode() and the check in __main__):

- The heightmap is cut into 64x64 tiles. Each tile is stored as a (tile_size)x(tile_size) block (65 at full detail,
  one extra row and column overlapping the next tile) at one of 5 detail levels: 65, 33, 17, 9 or 5 samples,
  taking every 1st, 2nd, 4th, 8th or 16th pixel.
- indirection_heightmap.png has one RGBA pixel per tile (row 0 = top of the map):
  R = column and G = row of the block within its level, B = sample step (1, 2, 4, 8, 16), A = level (0-4).
- In packed_heightmap.png (16-bit grey) each level's blocks are laid out in rows, counted from the BOTTOM of the
  image: level L starts level_offsets[L] pixels up from the bottom, and block (col, row) has its top-left corner at
  x = col * size, y = height - offset - (row + 1) * size. Blocks are not flipped.
- Columns and rows are bytes, so a level holds at most 256 blocks per row and 256 rows.

encode() writes full detail (level 0) for tiles with any variation and one shared 5x5 block (level 4) for flat
tiles such as open sea. That's bigger than the game's own packing but simple and exact.
"""
import numpy as np
from PIL import Image

TILE = 64
SIZES = [65, 33, 17, 9, 5]


def decode(packed, indirection, offsets, width, height):
    """Rebuild a (height, width) heightmap from the packed form (for checking)."""
    out = np.zeros((height, width), dtype=np.uint16)
    H = packed.shape[0]
    th, tw = indirection.shape[:2]
    for ty in range(th):
        for tx in range(tw):
            c, r, step, lvl = (int(v) for v in indirection[ty, tx])
            size = SIZES[lvl]
            y0 = H - offsets[lvl] - (r + 1) * size
            block = packed[y0:y0 + size, c * size:c * size + size]
            # Nearest-neighbour fill between samples, so lower levels give a whole (blocky) tile
            block = np.repeat(np.repeat(block, step, axis=0), step, axis=1)
            y1, x1 = min(ty * TILE + TILE + 1, height), min(tx * TILE + TILE + 1, width)
            out[ty * TILE:y1, tx * TILE:x1] = block[:y1 - ty * TILE, :x1 - tx * TILE]
    return out


def encode(hm, cols=49):
    """hm: (height, width) uint16 heightmap, both multiples of 64. Returns (packed, indirection, offsets)."""
    height, width = hm.shape
    assert height % TILE == 0 and width % TILE == 0, "heightmap size must be a multiple of 64"
    th, tw = height // TILE, width // TILE
    # Pad by one row/column so the overlapping edge sample exists for the last tiles
    padded = np.pad(hm, ((0, 1), (0, 1)), mode="edge")
    full, flat = [], {}
    indirection = np.zeros((th, tw, 4), dtype=np.uint8)
    for ty in range(th):
        for tx in range(tw):
            block = padded[ty * TILE:ty * TILE + 65, tx * TILE:tx * TILE + 65]
            if block.min() == block.max():
                v = int(block[0, 0])
                flat.setdefault(v, []).append((ty, tx))
            else:
                full.append(((ty, tx), block))
    # Level 0 blocks
    rows0 = (len(full) + cols - 1) // cols
    assert cols <= 256 and rows0 <= 256, "too many detailed tiles for one level"
    # Level 4: one 5x5 block per distinct flat value
    flat_values = sorted(flat)
    rows4 = (len(flat_values) + 255) // 256
    offsets = [0, rows0 * 65, rows0 * 65, rows0 * 65, rows0 * 65]
    H = rows0 * 65 + rows4 * 5
    W = max(cols * 65, min(len(flat_values), 256) * 5)
    packed = np.zeros((H, W), dtype=np.uint16)
    for i, ((ty, tx), block) in enumerate(full):
        c, r = i % cols, i // cols
        y0 = H - offsets[0] - (r + 1) * 65
        packed[y0:y0 + 65, c * 65:c * 65 + 65] = block
        indirection[ty, tx] = (c, r, 1, 0)
    for i, v in enumerate(flat_values):
        c, r = i % 256, i // 256
        y0 = H - offsets[4] - (r + 1) * 5
        packed[y0:y0 + 5, c * 5:c * 5 + 5] = v
        for ty, tx in flat[v]:
            indirection[ty, tx] = (c, r, 16, 4)
    return packed, indirection, offsets


def write(hm, map_data_dir):
    """Write packed_heightmap.png, indirection_heightmap.png, heightmap.heightmap and heightmap.png."""
    height, width = hm.shape
    packed, indirection, offsets = encode(hm)
    Image.fromarray(packed, mode="I;16").save(f"{map_data_dir}/packed_heightmap.png")
    Image.fromarray(indirection, mode="RGBA").save(f"{map_data_dir}/indirection_heightmap.png")
    Image.fromarray(hm, mode="I;16").save(f"{map_data_dir}/heightmap.png")
    empty = next(((int(c), int(r)) for c, r, s, lvl in indirection.reshape(-1, 4) if lvl == 4), (0, 0))
    with open(f"{map_data_dir}/heightmap.heightmap", "w", encoding="utf-8-sig") as f:
        f.write('heightmap_file="map_data/packed_heightmap.png"\n'
                'indirection_file="map_data/indirection_heightmap.png"\n'
                "original_heightmap_size={ %d %d }\n"
                "tile_size=65\n"
                "should_wrap_x=no\n"
                "level_offsets={ %s }\n"
                "max_compress_level=4\n"
                "empty_tile_offset={ %d %d }\n"
                % (width, height, " ".join("{ 0 %d }" % o for o in offsets), empty[0], empty[1]))
    return packed.shape


if __name__ == "__main__":
    # Self-check against the vanilla map: decoding the game's own packed heightmap must reproduce heightmap.png
    # (closely: the game's files differ by small rounding), and encode -> decode must be exact.
    import sys
    Image.MAX_IMAGE_PIXELS = None
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
    from ck3paths import GAME
    game = str(GAME / "map_data")
    rng = np.random.default_rng(0)
    test = rng.integers(0, 60000, size=(256, 320)).astype(np.uint16)
    test[:128, :128] = 1234                          # flat tiles
    packed, ind, offs = encode(test)
    back = decode(packed, ind, offs, 320, 256)
    assert (back == test).all(), "round trip failed"
    print("round trip ok")
    if "--vanilla" in sys.argv:
        ind = np.array(Image.open(game + "/indirection_heightmap.png"))
        pk = np.array(Image.open(game + "/packed_heightmap.png"))
        hm = np.array(Image.open(game + "/heightmap.png")).astype(np.int32)
        offs = [0, 1397, 3129, 3690, 3861]
        dec = decode(pk, ind, offs, hm.shape[1], hm.shape[0]).astype(np.int32)
        sampled = dec[::16, ::16] - hm[::16, ::16]           # every 16th pixel is stored at every level
        print("vanilla decode rmse (0-65535): %.1f" % np.sqrt((sampled ** 2).mean()))
