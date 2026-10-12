"""Terrain for the map: heights from the Copernicus 90 m DEM, terrain materials, colour map, paper map, water colour.

Heights: land is the DEM (metres) scaled with some vertical exaggeration so hills read on the map; the sea gets
deeper with distance from the coast. Land always stays above the game's water level and sea below it.
Materials: each pixel blends up to four of the game's terrain materials (detail_index.tga holds their indices in
gfx/map/terrain/materials.settings, detail_intensity.tga their weights), chosen by height and distance to the sea.
"""
import glob
import re

import numpy as np
import tifffile
from PIL import Image
from scipy import ndimage

from geo import RAW, SCALE, TO_LONLAT, X0, Y1

WORLD_Y = 50                     # NJominiMap WORLD_EXTENTS_Y: the height range of 0-65535
WATERLEVEL = 3.0                 # NJominiMap WATERLEVEL
H_WATER = WATERLEVEL / WORLD_Y   # as a fraction of the heightmap range
METRES_TO_H = 0.30 / 1345.0      # Ben Nevis (1345 m) ends up 0.30 above the water: about 12x exaggeration

# Material indices in vanilla's gfx/map/terrain/materials.settings (the order there is the index)
MAT = {"beach": 8, "cliff": 10, "farmland": 22, "forest": 25, "hills": 28, "hills_rocks": 29,
       "mountain": 38, "northern_plains": 49, "plains": 51, "plains_rough": 55, "wetlands": 60}


class Dem:
    """The Copernicus GLO-90 tiles (1 degree each, named by their south-west corner)."""

    def __init__(self):
        self.tiles = {}
        for f in glob.glob(str(RAW / "dem" / "*.tif")):
            m = re.search(r"_N(\d+)_00_([EW])(\d+)_00_", f)
            lat, lon = int(m.group(1)), int(m.group(3)) * (-1 if m.group(2) == "W" else 1)
            self.tiles[(lat, lon)] = f
        self.cache = {}

    def tile(self, lat, lon):
        k = (lat, lon)
        if k not in self.cache:
            f = self.tiles.get(k)
            self.cache[k] = tifffile.imread(f).astype(np.float32) if f else None
        return self.cache[k]

    def sample(self, lon, lat):
        """Heights in metres for arrays of lon/lat (0 where there is no tile: open sea)."""
        out = np.zeros(lon.shape, dtype=np.float32)
        tlat, tlon = np.floor(lat).astype(int), np.floor(lon).astype(int)
        for k in set(zip(tlat.ravel().tolist(), tlon.ravel().tolist())):
            a = self.tile(*k)
            if a is None:
                continue
            m = (tlat == k[0]) & (tlon == k[1])
            rows, cols = a.shape
            r = np.clip(((k[0] + 1 - lat[m]) * rows).astype(int), 0, rows - 1)
            c = np.clip(((lon[m] - k[1]) * cols).astype(int), 0, cols - 1)
            out[m] = a[r, c]
        return out


def elevation(width, height, chunk=256):
    """Metres above sea level for every map pixel."""
    dem = Dem()
    out = np.zeros((height, width), dtype=np.float32)
    xs = X0 + (np.arange(width) + 0.5) * SCALE
    for y0 in range(0, height, chunk):
        ys = Y1 - (np.arange(y0, min(y0 + chunk, height)) + 0.5) * SCALE
        gx, gy = np.meshgrid(xs, ys)
        lon, lat = TO_LONLAT.transform(gx, gy)
        out[y0:y0 + len(ys)] = dem.sample(lon, lat)
    return np.maximum(out, 0)


def heightmap(elev, land):
    """16-bit heightmap. Land rises with the DEM; the sea deepens offshore."""
    dist_sea = ndimage.distance_transform_edt(~land)
    e = ndimage.gaussian_filter(elev, 0.7)
    h = np.where(land,
                 H_WATER + 0.004 + e * METRES_TO_H,
                 H_WATER - 0.006 - np.minimum(dist_sea / 120.0, 1.0) * 0.03)
    h = np.where(land, np.maximum(h, H_WATER + 0.003), np.minimum(h, H_WATER - 0.003))
    return (np.clip(h, 0, 1) * 65535).astype(np.uint16)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def materials(elev, land, seed=3):
    """detail_index (material indices) and detail_intensity (weights) as (H, W, 4) uint8 arrays."""
    height, width = elev.shape
    index = np.zeros((height, width, 4), dtype=np.uint8)
    inten = np.zeros((height, width, 4), dtype=np.uint8)
    dist_coast = ndimage.distance_transform_edt(land)
    rng = np.random.default_rng(seed)
    noise = ndimage.gaussian_filter(rng.standard_normal((height // 8, width // 8)).astype(np.float32), 2)
    noise = np.kron(noise, np.ones((8, 8), dtype=np.float32))[:height, :width]
    noise = noise / (np.abs(noise).max() + 1e-6)
    e = ndimage.gaussian_filter(elev, 1.5)
    names = ["beach", "farmland", "plains", "northern_plains", "hills", "hills_rocks", "mountain"]
    mats = np.array([MAT[n] for n in names], dtype=np.uint8)
    for y0 in range(0, height, 512):          # in strips: the full weight stack would need several GB
        sl = slice(y0, min(y0 + 512, height))
        L, E, N, D = land[sl], e[sl], noise[sl], dist_coast[sl]
        w = np.stack([
            np.where(L, 1 - smoothstep(1, 4, D), 0),                                      # beach
            smoothstep(0.1, -0.4, N) * (1 - smoothstep(80, 200, E)),                      # farmland
            smoothstep(-0.3, 0.3, N) * (1 - smoothstep(120, 260, E)),                     # plains
            smoothstep(0.2, 0.7, N) * (1 - smoothstep(150, 300, E)) * 0.7,                # northern plains
            smoothstep(120, 260, E) * (1 - smoothstep(380, 520, E)),                      # hills
            smoothstep(320, 480, E) * (1 - smoothstep(650, 800, E)),                      # rocky hills
            smoothstep(620, 850, E),                                                      # mountain
        ], axis=-1).astype(np.float32)
        w[~L] = 0
        w[~L, 2] = 1                                  # under the sea: anything, it isn't seen
        w += 1e-4                                     # so a pixel with no weight still picks plains etc.
        order = np.argsort(-w, axis=-1)[..., :4]
        top = np.take_along_axis(w, order, axis=-1)
        top = top / top.sum(-1, keepdims=True)
        index[sl] = mats[order]
        inten[sl] = np.round(top * 255).astype(np.uint8)
    return index, inten


def colormap(elev, land):
    """The terrain tint (RGB): green lowlands, olive hills, brown-grey uplands; slightly lighter coasts."""
    e = ndimage.gaussian_filter(elev, 2)
    low, hill, high = np.array([96, 128, 64]), np.array([112, 118, 74]), np.array([122, 112, 96])
    t1 = smoothstep(60, 300, e)[..., None]
    t2 = smoothstep(350, 900, e)[..., None]
    rgb = low * (1 - t1) + hill * t1
    rgb = rgb * (1 - t2) + high * t2
    rgb[~land] = (70, 90, 100)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def flatmap(elev, land, provinces_edges):
    """The paper map: parchment land with faint relief shading and inked coasts, paler sea."""
    height, width = elev.shape
    e = ndimage.gaussian_filter(elev, 2)
    gy, gx = np.gradient(e)
    shade = np.clip(1 - (gx - gy) * 0.004, 0.85, 1.1)
    land_rgb = np.array([214, 196, 158], dtype=np.float32) * shade[..., None]
    sea_rgb = np.array([176, 186, 176], dtype=np.float32)
    coast = land ^ ndimage.binary_erosion(land, iterations=2)
    rgb = np.where(land[..., None], land_rgb, sea_rgb)
    rgb[provinces_edges & land] *= 0.93
    rgb[coast] = (92, 74, 50)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def watercolor(land, width, height):
    """Water colour (RGB) and specular (alpha) at half resolution: deeper blue offshore."""
    small = np.array(Image.fromarray(land.astype(np.uint8) * 255).resize((width // 2, height // 2), Image.BILINEAR)) > 127
    d = ndimage.distance_transform_edt(~small)
    t = smoothstep(0, 60, d)[..., None]
    shallow, deep = np.array([60, 96, 96]), np.array([24, 48, 70])
    rgb = shallow * (1 - t) + deep * t
    a = np.full(small.shape + (1,), 160)
    return np.concatenate([rgb, a], axis=-1).astype(np.uint8)
