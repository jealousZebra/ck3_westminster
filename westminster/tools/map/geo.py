"""Source data for the map: constituencies, ITL2 areas, towns and neighbouring land, all in map pixels.

Everything is projected to British National Grid metres (EPSG:27700), then to pixels: one pixel is SCALE metres,
x grows east from X0 and y grows south from Y1. See data/README.md for where each file comes from.
"""
import csv
import glob
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import shapefile                      # pyshp
from PIL import Image, ImageDraw
from pyproj import Transformer
from shapely import make_valid
from shapely.geometry import MultiPolygon, Polygon, shape
from shapely.ops import transform as shp_transform
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parent.parent.parent      # westminster/
RAW = ROOT / "data" / "raw"

SCALE = 160                       # metres per pixel
WIDTH, HEIGHT = 6144, 8192        # multiples of 64 (heightmap tiles)
X0 = -265000                      # BNG easting of the map's left edge (takes in Ireland)
Y1 = 1240000                      # BNG northing of the top edge (north of Shetland; the bottom reaches France)

TO_BNG = Transformer.from_crs("EPSG:4326", "EPSG:27700", always_xy=True)
TO_LONLAT = Transformer.from_crs("EPSG:27700", "EPSG:4326", always_xy=True)

# Neighbouring land drawn as scenery (impassable, belongs to no title), by Natural Earth ISO code
SCENERY = {"IRL": "Ireland", "IMN": "Isle of Man", "FRA": "France", "JEY": "Jersey", "GGY": "Guernsey",
           "BEL": "Belgium", "NLD": "Netherlands"}


def key(name):
    """A title key fragment from a name: lower case ASCII, words joined by underscores."""
    import unicodedata
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower().replace("&", "and")).strip("_")


def to_px(coords):
    return [((x - X0) / SCALE, (Y1 - y) / SCALE) for x, y in coords]


def px_to_bng(px, py):
    return X0 + px * SCALE, Y1 - py * SCALE


def polygons(geom):
    if geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    if isinstance(geom, MultiPolygon):
        return list(geom.geoms)
    return [g for g in getattr(geom, "geoms", []) if isinstance(g, Polygon)]


def load_seats():
    feats = []
    for f in sorted(glob.glob(str(RAW / "pcon24_*.geojson"))):
        feats += json.load(open(f))["features"]
    seats = [{"code": f["properties"]["PCON24CD"], "name": f["properties"]["PCON24NM"],
              "geom": make_valid(shape(f["geometry"]))} for f in feats]
    seats.sort(key=lambda s: s["code"])
    assert len(seats) == 650, len(seats)
    return seats


def load_itl2():
    d = json.load(open(RAW / "itl2_2025.geojson"))
    return [{"code": f["properties"]["ITL225CD"], "name": f["properties"]["ITL225NM"],
             "geom": make_valid(shape(f["geometry"]))} for f in d["features"]]


def assign_areas(seats, areas):
    """Each seat's area = the ITL2 area it overlaps most."""
    tree = STRtree([a["geom"] for a in areas])
    for s in seats:
        best, best_area = None, -1
        for i in tree.query(s["geom"]):
            inter = s["geom"].intersection(areas[i]["geom"]).area
            if inter > best_area:
                best, best_area = areas[i], inter
        s["area"] = best


def load_places():
    """GeoNames populated places in the UK with a population, as BNG points."""
    places = []
    with open(RAW / "geonames" / "cities1000.txt", encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            if row[8] != "GB" or row[6] != "P":
                continue
            pop = int(row[14] or 0)
            if pop <= 0:
                continue
            x, y = TO_BNG.transform(float(row[5]), float(row[4]))
            places.append({"name": row[1], "pop": pop, "x": x, "y": y})
    return places


def load_scenery():
    """Neighbouring countries' land (Natural Earth 10m) as BNG polygons: [(name, geometry)]."""
    z = zipfile.ZipFile(RAW / "ne_10m_admin_0_countries.zip")
    names = {n.rsplit(".", 1)[1]: n for n in z.namelist() if n.endswith((".shp", ".shx", ".dbf"))}
    sf = shapefile.Reader(shp=z.open(names["shp"]), shx=z.open(names["shx"]), dbf=z.open(names["dbf"]))
    fields = [f[0] for f in sf.fields[1:]]
    out = []
    for rec, shp in zip(sf.records(), sf.shapes()):
        r = dict(zip(fields, rec))
        iso = r.get("ADM0_A3") or r.get("ISO_A3")
        if iso not in SCENERY:
            continue
        geom = shape(shp.__geo_interface__)
        geom = shp_transform(lambda x, y, z=None: TO_BNG.transform(x, y), geom)
        out.append((SCENERY[iso], geom))
    return out


def rasterize(items, size=(WIDTH, HEIGHT)):
    """items: [(label, geometry)], drawn biggest polygon first so enclaves drawn later win. Returns int32 grid."""
    img = Image.new("I", size, 0)
    draw = ImageDraw.Draw(img)
    parts = [(p.area, label, p) for label, g in items for p in polygons(g)]
    for _, label, p in sorted(parts, key=lambda t: -t[0]):
        draw.polygon(to_px(p.exterior.coords), fill=label)
        for hole in p.interiors:
            draw.polygon(to_px(hole.coords), fill=0)
    return np.array(img, dtype=np.int32)
