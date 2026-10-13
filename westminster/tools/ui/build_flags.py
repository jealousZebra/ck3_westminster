#!/usr/bin/env python3
"""Flags for every landed title: real flags where they exist, unique derived flags for the rest.

    .venv/bin/python westminster/tools/ui/build_flags.py [--refresh]

Real flags (the four nations, the Royal Standard, historic and ceremonial county flags registered with the Flag
Institute's UK Flag Registry, and some city flags) come from Wikimedia Commons as SVG. They are downloaded once into
westminster/data/raw/flags/ (with each file's licence and author in meta.json; --refresh downloads again), rendered
with resvg (resvg-py in the repo's .venv) and stretched to 3:2. Each real flag goes to one title only: a county's flag
to the ITL2 region (duchy) that is that county, otherwise to the seat of its county town (see FLAGS). Northern
Ireland has no official flag of its own; k_northern_ireland flies St Patrick's Saltire.

Everything else gets a derived flag built from CK3 coat-of-arms parts, so every title's design is different:

    duchy without a real flag   its nation's flag in the canton, a field layout in the region's colours, a charge
    constituency (c_)           its county's flag in the canton (or its region's, or its nation's), a field layout
                                in that flag's colours and a charge that no other seat of the county has
    ward (b_)                   a field layout and a charge in its constituency's colours (no canton)

Flags fill the middle 3:2 band of the square CoA (y from 1/6 to 5/6), which is what build_coa_frames.py's masks show.

Writes:
  westminster/gfx/coat_of_arms/textured_emblems/wm_flag_<id>.dds      each real flag, 256x256 DXT5 with mipmaps,
                                                                       the flag in the middle band, clear above/below
  westminster/gfx/coat_of_arms/colored_emblems/ce_wm_layout_*.dds     field layouts (3 colours: alpha = shape, red =
  westminster/gfx/coat_of_arms/colored_emblems/ce_wm_charge_*.dds     colour 2, green = colour 3, blue = shading)
  westminster/gfx/coat_of_arms/colored_emblems/wm_flag_emblems.txt    (so the CoA designer lists them)
  westminster/common/coat_of_arms/coat_of_arms/wm_title_flags.txt     one CoA per title (parties: build_party_arms.py)
  westminster/common/coat_of_arms/dynamic_definitions/00_dynamic_coas.txt   empty: no vanilla arms swaps
  westminster/data/README.md                                          the flags' sources and licences (between the
                                                                       <!-- flags --> markers)
  westminster/tools/test_out/flags_preview.png                        a contact sheet of every title's flag
Then runs check_title_flags.py (every title has a CoA, no two the same).
"""
import hashlib
import io
import json
import os
import math
import re
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent                                  # westminster/
MOD = ROOT / "westminster"
RAW = ROOT / "data" / "raw" / "flags"
OUT_TEX = MOD / "gfx" / "coat_of_arms" / "textured_emblems"
OUT_CE = MOD / "gfx" / "coat_of_arms" / "colored_emblems"
OUT_COA = MOD / "common" / "coat_of_arms" / "coat_of_arms" / "wm_title_flags.txt"
README = ROOT / "data" / "README.md"
PREVIEW = ROOT / "tools" / "test_out" / "flags_preview.png"
UA = os.environ.get("CK3_USER_AGENT", "WestminsterCK3ModFlagBuilder/0.2 (Crusader Kings III mod; one-off download of ~80 flag SVGs, cached locally)")	# set CK3_USER_AGENT to add a contact URL
API = "https://commons.wikimedia.org/w/api.php"

FLAG_SIZE = 256                    # real flag textures (square; the flag is the middle 3:2 band)
CE_SIZE = 256                      # layout and charge emblems
BAND = (1 / 6, 5 / 6)              # the flag's rows in the square CoA

# ---------------------------------------------------------------------------------------------------------------
# Real flags: id -> (Wikimedia Commons file, the title it belongs to, what it is)
# ---------------------------------------------------------------------------------------------------------------
FLAGS = {
    # Nations and the Crown
    "uk": ("Flag of the United Kingdom (3-5).svg", "e_united_kingdom", "Union Flag"),
    "england": ("Flag of England.svg", "k_england", "St George's Cross"),
    "scotland": ("Flag of Scotland.svg", "k_scotland", "Saltire"),
    "wales": ("Flag of Wales.svg", "k_wales", "Y Ddraig Goch"),
    "st_patrick": ("Saint Patrick's Saltire.svg", "k_northern_ireland",
                   "St Patrick's Saltire (Northern Ireland has no official flag of its own)"),
    "royal_standard": ("Royal standard of the United Kingdom.svg", "k_wm_crown", "Royal Standard"),
    # Regions (ITL2 areas, the duchies) that are a county
    "northumbria": ("Flag of Northumbria.svg", "d_northumberland_durham_and_tyne_and_wear", "Northumbria"),
    "cumbria": ("Community flag of Cumbria.svg", "d_cumbria", "Cumbria"),
    "lancashire": ("Flag of Lancashire.svg", "d_lancashire", "Lancashire"),
    "cheshire": ("Flag of Cheshire.svg", "d_cheshire", "Cheshire"),
    "merseyside": ("County Flag of Merseyside.svg", "d_merseyside", "Merseyside"),
    "east_riding": ("Flag of the East Riding of Yorkshire.svg", "d_east_yorkshire_and_northern_lincolnshire",
                    "East Riding of Yorkshire"),
    "north_riding": ("Flag of North Riding of Yorkshire.svg", "d_north_yorkshire", "North Riding of Yorkshire"),
    "west_riding": ("Flag of the West Riding of Yorkshire.svg", "d_west_yorkshire", "West Riding of Yorkshire"),
    "lincolnshire": ("Flag of Lincolnshire.svg", "d_lincolnshire", "Lincolnshire"),
    "west_midlands": ("Flag of the West Midlands County.svg", "d_west_midlands", "West Midlands"),
    "essex": ("Flag of Essex.svg", "d_essex", "Essex"),
    "cambridgeshire": ("Cambridgeshire Flag.svg", "d_cambridgeshire_and_peterborough", "Cambridgeshire"),
    "norfolk": ("Flag of Norfolk.svg", "d_norfolk", "Norfolk"),
    "suffolk": ("County Flag of Suffolk.svg", "d_suffolk", "Suffolk"),
    "kent": ("Flag of Kent.svg", "d_kent", "Kent"),
    "cornwall": ("Flag of Cornwall.svg", "d_cornwall_and_isles_of_scilly", "Cornwall (St Piran's Flag)"),
    "devon": ("Flag of Devon.svg", "d_devon", "Devon (St Petroc's Flag)"),
    "middlesex": ("Flag of Middlesex.svg", "d_outer_london_west_and_north_west", "Middlesex"),
    "hampshire": ("Flag of Hampshire.svg", "d_hampshire_and_isle_of_wight", "Hampshire"),
    # Counties within a larger region: the seat of the county town
    "bedfordshire": ("Bedfordshire County Flag.svg", "c_bedford", "Bedfordshire"),
    "berkshire": ("Flag of Berkshire.svg", "c_reading_central", "Berkshire"),
    "buckinghamshire": ("Flag of Buckinghamshire.svg", "c_aylesbury", "Buckinghamshire"),
    "hertfordshire": ("County Flag of Hertfordshire.svg", "c_hertford_and_stortford", "Hertfordshire"),
    "herefordshire": ("County Flag Of Herefordshire.svg", "c_hereford_and_south_herefordshire", "Herefordshire"),
    "worcestershire": ("Flag of Worcestershire.svg", "c_worcester", "Worcestershire"),
    "warwickshire": ("Flag of Warwickshire.svg", "c_warwick_and_leamington", "Warwickshire"),
    "shropshire": ("Flag of Shropshire.svg", "c_shrewsbury", "Shropshire"),
    "staffordshire": ("Staffordshire Flag.svg", "c_stafford", "Staffordshire"),
    "derbyshire": ("Derbyshire flag.svg", "c_derbyshire_dales", "Derbyshire"),
    "nottinghamshire": ("County Flag of Nottinghamshire.svg", "c_rushcliffe", "Nottinghamshire"),
    "leicestershire": ("Flag of Leicestershire.svg", "c_mid_leicestershire", "Leicestershire"),
    "rutland": ("Rutland County Flag.svg", "c_rutland_and_stamford", "Rutland"),
    "northamptonshire": ("Flag of Northamptonshire.svg", "c_northampton_south", "Northamptonshire"),
    "oxfordshire": ("Flag of Oxfordshire.svg", "c_oxford_east", "Oxfordshire"),
    "surrey": ("Flag of Surrey.svg", "c_guildford", "Surrey"),
    "sussex": ("Flag of Sussex.svg", "c_lewes", "Sussex"),
    "isle_of_wight": ("Flag of the Isle of Wight.svg", "c_isle_of_wight_west", "Isle of Wight"),
    "somerset": ("Flag of Somerset.svg", "c_taunton_and_wellington", "Somerset"),
    "dorset": ("Flag of Dorset.svg", "c_west_dorset", "Dorset"),
    "wiltshire": ("County Flag of Wiltshire.svg", "c_south_west_wiltshire", "Wiltshire"),
    "county_durham": ("Flag of County Durham.svg", "c_city_of_durham", "County Durham"),
    "northumberland": ("Flag of Northumberland.svg", "c_north_northumberland", "Northumberland"),
    "tyne_and_wear": ("Flag of Tyne and Wear.svg", "c_newcastle_upon_tyne_central_and_west", "Tyne and Wear"),
    "cumberland": ("Flag of Cumberland.svg", "c_carlisle", "Cumberland"),
    "westmorland": ("Flag of Westmorland.svg", "c_westmorland_and_lonsdale", "Westmorland"),
    "huntingdonshire": ("Flag of Huntingdonshire.svg", "c_huntingdon", "Huntingdonshire"),
    "yorkshire": ("Flag of Yorkshire.svg", "c_york_outer", "Yorkshire"),
    "aberdeenshire": ("Flag of Aberdeenshire.svg", "c_west_aberdeenshire_and_kincardine", "Aberdeenshire"),
    "banffshire": ("Flag of Banffshire.svg", "c_aberdeenshire_north_and_moray_east", "Banffshire"),
    "angus": ("Flag of Angus.svg", "c_angus_and_perthshire_glens", "Angus"),
    "east_lothian": ("Flag of East Lothian.svg", "c_lothian_east", "East Lothian"),
    "berwickshire": ("Flag of Berwickshire.svg", "c_berwickshire_roxburgh_and_selkirk", "Berwickshire"),
    "kirkcudbrightshire": ("Flag of Kirkcudbrightshire.svg", "c_dumfries_and_galloway", "Kirkcudbrightshire"),
    "caithness": ("Flag of Caithness.svg", "c_caithness_sutherland_and_easter_ross", "Caithness"),
    "orkney": ("2007 Flag of Orkney.svg", "c_orkney_and_shetland", "Orkney"),
    "shetland": ("Flag of Shetland.svg", "b_lerwick", "Shetland (to Lerwick, as Orkney's flag has the seat)"),
    "anglesey": ("Flag of Anglesey.svg", "c_ynys_mon", "Anglesey"),
    "caernarfonshire": ("Flag of Caernarfonshire.svg", "c_bangor_aberconwy", "Caernarfonshire"),
    "merionethshire": ("Flag of Merionethshire.svg", "c_dwyfor_meirionnydd", "Merionethshire"),
    "flintshire": ("Flag of Flintshire.svg", "c_alyn_and_deeside", "Flintshire"),
    "brecknockshire": ("Flag of Brecknockshire.svg", "c_brecon_radnor_and_cwm_tawe", "Brecknockshire"),
    "pembrokeshire": ("Flag of Pembrokeshire.svg", "c_mid_and_south_pembrokeshire", "Pembrokeshire"),
    "glamorgan": ("Glamorgan Flag.svg", "c_vale_of_glamorgan", "Glamorgan"),
    "monmouthshire": ("Flag of Monmouthshire.svg", "c_monmouthshire", "Monmouthshire"),
    # Cities
    "york": ("Flag of York.svg", "c_york_central", "City of York"),
    "city_of_london": ("Flag of the City of London.svg", "c_cities_of_london_and_westminster", "City of London"),
    "birmingham": ("Banner of arms of the City of Birmingham (1976–).svg", "c_birmingham_ladywood", "Birmingham"),
    "norwich": ("Flag of Norwich.svg", "c_norwich_south", "Norwich"),
    "plymouth": ("Flag of Plymouth.svg", "c_plymouth_sutton_and_devonport", "Plymouth"),
    "glasgow": ("Flag of Glasgow.svg", "c_glasgow_north", "Glasgow"),
    "edinburgh": ("Flag of Edinburgh.svg", "c_edinburgh_east_and_musselburgh", "Edinburgh"),
    "aberdeen": ("Flag of Aberdeen.svg", "c_aberdeen_north", "Aberdeen"),
    "cardiff": ("Flag of Cardiff.svg", "c_cardiff_south_and_penarth", "Cardiff"),
    "belfast": ("Flag of Belfast.svg", "c_belfast_south_and_mid_down", "Belfast"),
}

NATION_FLAG = {"k_england": "england", "k_scotland": "scotland", "k_wales": "wales", "k_northern_ireland": "st_patrick"}

# Seats whose canton is a county or city flag (not their region's). Seats not listed take their region's flag if it
# has a real one, else their nation's. A seat that holds a real flag itself is skipped.
COUNTY_SEATS = {
    "northumberland": "north_northumberland hexham blyth_and_ashington cramlington_and_killingworth",
    "county_durham": "city_of_durham bishop_auckland easington newton_aycliffe_and_spennymoor north_durham "
                     "blaydon_and_consett",
    "tyne_and_wear": "gateshead_central_and_whickham houghton_and_sunderland_south jarrow_and_gateshead_east "
                     "newcastle_upon_tyne_central_and_west newcastle_upon_tyne_east_and_wallsend "
                     "newcastle_upon_tyne_north south_shields sunderland_central tynemouth washington_and_gateshead_south",
    "cumberland": "carlisle penrith_and_solway whitehaven_and_workington",
    "westmorland": "westmorland_and_lonsdale",
    "lancashire": "morecambe_and_lunesdale",
    "lincolnshire": "brigg_and_immingham great_grimsby_and_cleethorpes scunthorpe",
    "yorkshire": "york_outer barnsley_north barnsley_south doncaster_central doncaster_north penistone_and_stocksbridge "
                 "rawmarsh_and_conisbrough rother_valley rotherham sheffield_brightside_and_hillsborough "
                 "sheffield_central sheffield_hallam sheffield_heeley sheffield_south_east",
    "york": "york_central",
    "derbyshire": "amber_valley bolsover chesterfield derby_north derby_south derbyshire_dales erewash high_peak "
                  "mid_derbyshire north_east_derbyshire south_derbyshire",
    "nottinghamshire": "ashfield bassetlaw broxtowe gedling mansfield newark nottingham_east "
                       "nottingham_north_and_kimberley nottingham_south rushcliffe sherwood_forest",
    "leicestershire": "harborough_oadby_and_wigston hinckley_and_bosworth leicester_east leicester_south leicester_west "
                      "loughborough melton_and_syston mid_leicestershire north_west_leicestershire south_leicestershire",
    "rutland": "rutland_and_stamford",
    "northamptonshire": "corby_and_east_northamptonshire daventry kettering northampton_north northampton_south "
                        "south_northamptonshire wellingborough_and_rushden",
    "herefordshire": "hereford_and_south_herefordshire north_herefordshire",
    "worcestershire": "bromsgrove droitwich_and_evesham redditch west_worcestershire worcester wyre_forest",
    "warwickshire": "kenilworth_and_southam north_warwickshire_and_bedworth nuneaton rugby stratford_on_avon "
                    "warwick_and_leamington",
    "shropshire": "north_shropshire shrewsbury south_shropshire telford the_wrekin",
    "staffordshire": "burton_and_uttoxeter cannock_chase kingswinford_and_south_staffordshire lichfield "
                     "newcastle_under_lyme stafford staffordshire_moorlands stoke_on_trent_central stoke_on_trent_north "
                     "stoke_on_trent_south stone_great_wyrley_and_penkridge tamworth",
    "birmingham": "birmingham_edgbaston birmingham_erdington birmingham_hall_green_and_moseley "
                  "birmingham_hodge_hill_and_solihull_north birmingham_ladywood birmingham_northfield "
                  "birmingham_perry_barr birmingham_selly_oak birmingham_yardley",
    "bedfordshire": "bedford dunstable_and_leighton_buzzard luton_north luton_south_and_south_bedfordshire "
                    "mid_bedfordshire north_bedfordshire",
    "hertfordshire": "broxbourne harpenden_and_berkhamsted hemel_hempstead hertford_and_stortford hertsmere hitchin "
                     "north_east_hertfordshire south_west_hertfordshire st_albans stevenage watford welwyn_hatfield",
    "huntingdonshire": "huntingdon st_neots_and_mid_cambridgeshire",
    "norwich": "norwich_north norwich_south",
    "city_of_london": "cities_of_london_and_westminster",
    "berkshire": "bracknell earley_and_woodley maidenhead newbury reading_central reading_west_and_mid_berkshire slough "
                 "windsor wokingham",
    "buckinghamshire": "aylesbury beaconsfield buckingham_and_bletchley chesham_and_amersham mid_buckinghamshire "
                       "milton_keynes_central milton_keynes_north wycombe",
    "oxfordshire": "banbury bicester_and_woodstock didcot_and_wantage henley_and_thame oxford_east "
                   "oxford_west_and_abingdon witney",
    "surrey": "dorking_and_horley east_surrey epsom_and_ewell esher_and_walton farnham_and_bordon godalming_and_ash "
              "guildford reigate runnymede_and_weybridge spelthorne surrey_heath woking",
    "sussex": "arundel_and_south_downs bexhill_and_battle bognor_regis_and_littlehampton brighton_kemptown_and_peacehaven "
              "brighton_pavilion chichester crawley east_grinstead_and_uckfield east_worthing_and_shoreham eastbourne "
              "hastings_and_rye horsham hove_and_portslade lewes mid_sussex sussex_weald worthing_west",
    "isle_of_wight": "isle_of_wight_east isle_of_wight_west",
    "plymouth": "plymouth_moor_view plymouth_sutton_and_devonport",
    "somerset": "bath north_east_somerset_and_hanham bridgwater frome_and_east_somerset glastonbury_and_somerton "
                "north_somerset taunton_and_wellington tiverton_and_minehead wells_and_mendip_hills weston_super_mare "
                "yeovil",
    "dorset": "bournemouth_east bournemouth_west christchurch mid_dorset_and_north_poole north_dorset poole south_dorset "
              "west_dorset",
    "wiltshire": "chippenham east_wiltshire melksham_and_devizes salisbury south_west_wiltshire swindon_north "
                 "swindon_south",
    "glasgow": "glasgow_east glasgow_north glasgow_north_east glasgow_south glasgow_south_west glasgow_west",
    "edinburgh": "edinburgh_east_and_musselburgh edinburgh_north_and_leith edinburgh_south edinburgh_south_west "
                 "edinburgh_west",
    "aberdeen": "aberdeen_north aberdeen_south",
    "aberdeenshire": "west_aberdeenshire_and_kincardine gordon_and_buchan",
    "banffshire": "aberdeenshire_north_and_moray_east",
    "angus": "angus_and_perthshire_glens arbroath_and_broughty_ferry",
    "east_lothian": "lothian_east",
    "berwickshire": "berwickshire_roxburgh_and_selkirk",
    "kirkcudbrightshire": "dumfries_and_galloway",
    "caithness": "caithness_sutherland_and_easter_ross",
    "orkney": "orkney_and_shetland",
    "anglesey": "ynys_mon",
    "caernarfonshire": "bangor_aberconwy",
    "merionethshire": "dwyfor_meirionnydd",
    "flintshire": "alyn_and_deeside clwyd_east",
    "brecknockshire": "brecon_radnor_and_cwm_tawe",
    "pembrokeshire": "mid_and_south_pembrokeshire ceredigion_preseli",
    "glamorgan": "vale_of_glamorgan bridgend pontypridd rhondda_and_ogmore merthyr_tydfil_and_aberdare aberafan_maesteg "
                 "gower swansea_west neath_and_swansea_east caerphilly",
    "cardiff": "cardiff_east cardiff_north cardiff_south_and_penarth cardiff_west",
    "monmouthshire": "monmouthshire newport_east newport_west_and_islwyn torfaen blaenau_gwent_and_rhymney",
    "belfast": "belfast_east belfast_north belfast_south_and_mid_down belfast_west",
}

# Colours for regions without a real flag (a field colour and a second colour); hand-picked so neighbours differ
REGION_COLOURS = {
    "d_tees_valley": ((0, 84, 147), (0, 166, 156)),
    "d_greater_manchester": ((200, 16, 46), (255, 199, 44)),
    "d_south_yorkshire": ((0, 63, 135), (255, 255, 255)),
    "d_derbyshire_and_nottinghamshire": ((0, 122, 61), (255, 205, 0)),
    "d_leicestershire_rutland_and_northamptonshire": ((0, 102, 51), (255, 255, 255)),
    "d_herefordshire_worcestershire_and_warwickshire": ((122, 30, 50), (255, 255, 255)),
    "d_shropshire_and_staffordshire": ((255, 199, 44), (24, 24, 24)),
    "d_bedfordshire_and_hertfordshire": ((0, 70, 140), (255, 205, 0)),
    "d_inner_london_west": ((190, 20, 30), (255, 255, 255)),
    "d_inner_london_east": ((24, 24, 24), (220, 36, 31)),
    "d_outer_london_east_and_north_east": ((0, 93, 170), (220, 36, 31)),
    "d_outer_london_south": ((0, 120, 80), (255, 255, 255)),
    "d_berkshire_buckinghamshire_and_oxfordshire": ((0, 51, 102), (230, 230, 230)),
    "d_surrey_east_and_west_sussex": ((0, 85, 164), (255, 205, 0)),
    "d_west_of_england": ((140, 20, 40), (240, 190, 50)),
    "d_north_somerset_somerset_and_dorset": ((180, 30, 40), (255, 205, 0)),
    "d_gloucestershire_and_wiltshire": ((0, 110, 70), (200, 16, 46)),
    "d_northern_ireland": ((255, 255, 255), (200, 16, 46)),
    "d_eastern_scotland": ((0, 94, 184), (255, 205, 0)),
    "d_east_central_scotland": ((24, 24, 24), (255, 255, 255)),
    "d_highlands_and_islands": ((0, 112, 60), (0, 94, 184)),
    "d_west_central_scotland": ((0, 94, 184), (200, 16, 46)),
    "d_north_eastern_scotland": ((0, 60, 113), (180, 180, 180)),
    "d_southern_scotland": ((0, 100, 60), (255, 255, 255)),
    "d_north_wales": ((0, 122, 61), (255, 255, 255)),
    "d_mid_and_south_west_wales": ((200, 16, 46), (0, 122, 61)),
    "d_south_east_wales": ((24, 24, 24), (255, 205, 0)),
}

WHITE, INK = (255, 255, 255), (24, 24, 24)


# ---------------------------------------------------------------------------------------------------------------
# DDS
# ---------------------------------------------------------------------------------------------------------------
def save_dds(img, path, fmt="DXT5", mips=True):
    """Save an RGBA image as DDS (Pillow's BC encoder), with a full mipmap chain so small icons don't shimmer."""
    img = img.convert("RGBA")
    levels = [img]
    while mips and min(levels[-1].size) > 4:
        w, h = levels[-1].size
        levels.append(levels[-1].resize((max(w // 2, 1), max(h // 2, 1)), Image.LANCZOS))
    blobs = []
    for lv in levels:
        b = io.BytesIO()
        lv.save(b, "DDS", pixel_format=fmt)
        blobs.append(b.getvalue())
    head = bytearray(blobs[0][:128])
    if len(levels) > 1:
        flags = struct.unpack_from("<I", head, 8)[0] | 0x20000                  # DDSD_MIPMAPCOUNT
        struct.pack_into("<I", head, 8, flags)
        struct.pack_into("<I", head, 28, len(levels))
        caps = struct.unpack_from("<I", head, 108)[0] | 0x400008                # DDSCAPS_COMPLEX | DDSCAPS_MIPMAP
        struct.pack_into("<I", head, 108, caps)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(head) + b"".join(bl[128:] for bl in blobs))


# ---------------------------------------------------------------------------------------------------------------
# Downloading (the files are untrusted data: kept in their own folder, read only as SVG images)
# ---------------------------------------------------------------------------------------------------------------
def api(params):
    for attempt in range(8):
        try:
            req = urllib.request.Request(API, data=urllib.parse.urlencode(params).encode(), headers={"User-Agent": UA})
            return json.load(urllib.request.urlopen(req, timeout=60))
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            wait = min(int(e.headers.get("Retry-After") or 0) or 10 * (attempt + 1), 900)
            print("  rate-limited, waiting %ds" % wait, flush=True)
            time.sleep(wait)
    raise RuntimeError("Commons API kept refusing (429)")


def fetch(url, dest):
    for attempt in range(8):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            data = urllib.request.urlopen(req, timeout=60).read()
            dest.write_bytes(data)
            return
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            wait = min(int(e.headers.get("Retry-After") or 0) or 10 * (attempt + 1), 900)
            print("  rate-limited, waiting %ds" % wait, flush=True)
            time.sleep(wait)
    raise RuntimeError("download kept refusing (429): " + url)


def strip_html(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()


def download(refresh=False):
    RAW.mkdir(parents=True, exist_ok=True)
    meta_path = RAW / "meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() and not refresh else {}
    todo = [i for i in FLAGS if i not in meta or meta[i]["file"] != FLAGS[i][0] or not (RAW / (i + ".svg")).exists()]
    for n in range(0, len(todo), 20):
        chunk = todo[n:n + 20]
        d = api({"action": "query", "titles": "|".join("File:" + FLAGS[i][0] for i in chunk), "redirects": 1,
                 "prop": "imageinfo", "iiprop": "url|extmetadata|sha1", "format": "json"})["query"]
        alias = {r["from"]: r["to"] for r in d.get("normalized", []) + d.get("redirects", [])}
        pages = {p["title"]: p for p in d["pages"].values()}
        for i in chunk:
            t = "File:" + FLAGS[i][0]
            while t in alias:
                t = alias[t]
            info = pages.get(t, {}).get("imageinfo")
            if not info:
                raise SystemExit("not on Commons: " + FLAGS[i][0])
            m = info[0]["extmetadata"]
            meta[i] = {"file": FLAGS[i][0], "title": t, "url": info[0]["url"].split("?")[0],
                       "page": info[0]["descriptionurl"], "sha1": info[0]["sha1"],
                       "licence": strip_html(m.get("LicenseShortName", {}).get("value")),
                       "licence_url": m.get("LicenseUrl", {}).get("value", ""),
                       "author": strip_html(m.get("Artist", {}).get("value"))[:120]}
            fetch(meta[i]["url"], RAW / (i + ".svg"))
            if hashlib.sha1((RAW / (i + ".svg")).read_bytes()).hexdigest() != meta[i]["sha1"]:
                raise SystemExit("download doesn't match Commons' checksum: " + FLAGS[i][0])
            print("downloaded", i, "-", meta[i]["licence"])
            meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False))
            time.sleep(3)
        meta_path.write_text(json.dumps(meta, indent=1, ensure_ascii=False))
    return meta


# ---------------------------------------------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------------------------------------------
def render_flag(fid, w=FLAG_SIZE):
    """The flag stretched to 3:2 (w x 2w/3), RGB."""
    import resvg_py
    svg = RAW / (fid + ".svg")
    text = svg.read_text(encoding="utf-8")
    root = re.search(r"<svg\b[^>]*>", text).group(0)
    vb = re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', root)
    if vb and not (re.search(r'\swidth="[\d.]+(px)?"', root) and re.search(r'\sheight="[\d.]+(px)?"', root)):
        # a size resvg misreads (width="1e3pt", or no height): use the viewBox's
        fixed = re.sub(r'\s(width|height)="[^"]*"', "", root).replace("<svg", '<svg width="%s" height="%s"' % vb.groups(), 1)
        text = text.replace(root, fixed, 1)
    png = bytes(resvg_py.svg_to_bytes(svg_string=text, width=w * 3, resources_dir=str(RAW)))
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    return bg.convert("RGB").resize((w, round(w * 2 / 3)), Image.LANCZOS)


def band_rows(size):
    return round(size * BAND[0]), round(size * BAND[1])


def flag_texture(flag):
    """Square RGBA: the flag in the middle band, clear above and below."""
    s = FLAG_SIZE
    y0, y1 = band_rows(s)
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(flag.resize((s, y1 - y0), Image.LANCZOS).convert("RGBA"), (0, y0))
    return out


def palette(flag, n=3):
    """The flag's main colours, most common first (colours under 5% of the flag are dropped)."""
    q = flag.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    counts = sorted(q.getcolors(), reverse=True)
    total = sum(c for c, _ in counts)
    cols = []
    for c, idx in counts:
        rgb = tuple(pal[idx * 3: idx * 3 + 3])
        if c / total < 0.05:
            continue
        if all(dist(rgb, o) > 60 for o in cols):
            cols.append(snap(rgb))
    return cols[:n] or [WHITE]


def snap(c):
    """Near-white to white and near-black to ink, so derived flags use clean colours."""
    if min(c) > 225:
        return WHITE
    if max(c) < 40:
        return INK
    return c


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(c, cands):
    return max(cands, key=lambda o: abs(lum(o) - lum(c)) + 0.3 * dist(o, c))


# ---------------------------------------------------------------------------------------------------------------
# Field layouts: (name, regions(u, v) -> 0/1/2, where the charge sits (u, v), its size, the region under it,
# works under a canton). u runs hoist to fly and v top to bottom across the flag (the 3:2 band), both 0..1.
# ---------------------------------------------------------------------------------------------------------------
def _waves(u, v, base, amp=0.035, n=3):
    return v > base + amp * np.sin(u * n * 2 * np.pi)


LAYOUTS = [
    ("plain", lambda u, v: np.zeros_like(u, dtype=int), (0.75, 0.5), 1.0, 0, True),
    ("base", lambda u, v: (v > 0.70).astype(int), (0.75, 0.36), 0.8, 0, True),
    ("fly", lambda u, v: (u > 0.56).astype(int), (0.78, 0.5), 0.75, 1, True),
    ("tricolour_h", lambda u, v: np.where(v < 1 / 3, 0, np.where(v < 2 / 3, 1, 2)), (0.75, 0.5), 0.55, 1, True),
    ("bicolour_h", lambda u, v: (v >= 0.5).astype(int), (0.75, 0.75), 0.6, 1, True),
    ("bicolour_v", lambda u, v: (u >= 0.5).astype(int), (0.75, 0.5), 0.9, 1, True),
    ("bars", lambda u, v: ((v < 0.12) | (v > 0.88)).astype(int), (0.75, 0.5), 0.85, 0, True),
    ("waves", lambda u, v: np.where(_waves(u, v, 0.86), 2, np.where(_waves(u, v, 0.70), 1, 0)), (0.75, 0.36), 0.75, 0,
     True),
    ("diagonal", lambda u, v: (v > 1 - u).astype(int), (0.80, 0.74), 0.55, 1, True),
    ("border", lambda u, v: ((v < 0.08) | (v > 0.92) | (u < 0.08 / 1.5) | (u > 1 - 0.08 / 1.5)).astype(int),
     (0.75, 0.5), 0.8, 0, True),
    ("fess", lambda u, v: ((v > 0.34) & (v < 0.66)).astype(int), (0.75, 0.5), 0.55, 1, True),
    ("quarters", lambda u, v: ((u >= 0.5) != (v >= 0.5)).astype(int), (0.75, 0.75), 0.55, 0, True),
    ("fly_triangle", lambda u, v: ((1 - u) < 0.5 * (1 - 2 * np.abs(v - 0.5))).astype(int), (0.86, 0.5), 0.42, 1,
     True),
    ("base_stripes", lambda u, v: np.where(v > 0.84, 2, np.where(v > 0.68, 1, 0)), (0.75, 0.34), 0.7, 0, True),
    ("bend", lambda u, v: (np.abs(v - (1 - u)) < 0.16).astype(int), (0.80, 0.75), 0.45, 0, True),
    # Not under a canton (wards)
    ("nordic", lambda u, v: (((u > 0.30) & (u < 0.42)) | ((v > 0.41) & (v < 0.59))).astype(int), (0.72, 0.22), 0.45,
     0, False),
    ("saltire", lambda u, v: ((np.abs(v - u) < 0.12) | (np.abs(v - (1 - u)) < 0.12)).astype(int), (0.5, 0.5), 0.35,
     1, False),
    ("hoist_triangle", lambda u, v: (u < 0.42 * (1 - 2 * np.abs(v - 0.5))).astype(int), (0.14, 0.5), 0.35, 1, False),
    ("tricolour_v", lambda u, v: np.where(u < 1 / 3, 0, np.where(u < 2 / 3, 1, 2)), (0.5, 0.5), 0.6, 1, False),
    ("disc", lambda u, v: (((u - 0.5) * 1.5) ** 2 + (v - 0.5) ** 2 < 0.33 ** 2).astype(int), (0.5, 0.5), 0.62, 1,
     False),
    ("cross", lambda u, v: ((np.abs(u - 0.5) * 1.5 < 0.1) | (np.abs(v - 0.5) < 0.1)).astype(int), (0.5, 0.5), 0.3, 1,
     False),
    ("hoist_band", lambda u, v: (u < 0.25).astype(int), (0.62, 0.5), 0.8, 0, False),
]
LAYOUT = {l[0]: l for l in LAYOUTS}
CANTON_LAYOUTS = [l[0] for l in LAYOUTS if l[5]]
ALL_LAYOUTS = [l[0] for l in LAYOUTS]


def layout_texture(fn):
    """A colored emblem covering the whole square: alpha 255, red = region 1, green = region 2, blue = flat."""
    s = CE_SIZE * 2
    y, x = np.mgrid[0:s, 0:s].astype(np.float32) + 0.5
    u = x / s
    v = np.clip((y / s - BAND[0]) / (BAND[1] - BAND[0]), 0, 1)
    r = fn(u, v)
    out = np.zeros((s, s, 4), dtype=np.uint8)
    out[..., 0] = np.where(r == 1, 255, 0)
    out[..., 1] = np.where(r == 2, 255, 0)
    out[..., 2] = 128
    out[..., 3] = 255
    return Image.fromarray(out).resize((CE_SIZE, CE_SIZE), Image.LANCZOS)


def box_texture():
    out = np.zeros((64, 64, 4), dtype=np.uint8)
    out[..., 2] = 128
    out[..., 3] = 255
    return Image.fromarray(out)


# ---------------------------------------------------------------------------------------------------------------
# Charges: simple flat shapes, drawn white on a 1024 canvas (alpha is the shape)
# ---------------------------------------------------------------------------------------------------------------
C = 1024
MID = C / 2


def _star(d, n, r1, r2, rot=-90, cx=MID, cy=MID):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=255)


def _ngon(d, n, r, rot=-90, cx=MID, cy=MID, fill=255):
    d.polygon([(cx + r * math.cos(math.radians(rot + i * 360 / n)), cy + r * math.sin(math.radians(rot + i * 360 / n)))
               for i in range(n)], fill=fill)


def _circle(d, r, cx=MID, cy=MID, fill=255):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)


def _rect(d, x0, y0, x1, y1, fill=255):
    d.rectangle((x0, y0, x1, y1), fill=fill)


def ch_sun(d):
    _star(d, 16, 480, 300)
    _circle(d, 290)


def ch_ring_star(d):
    _circle(d, 470)
    _circle(d, 380, fill=0)
    _star(d, 5, 350, 140)


def ch_quatrefoil(d):
    for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
        _circle(d, 210, MID + dx * 220, MID + dy * 220)
    _circle(d, 200)


def ch_trefoil(d):
    for k in range(3):
        a = math.radians(-90 + k * 120)
        _circle(d, 220, MID + 230 * math.cos(a), MID + 230 * math.sin(a) + 30)
    _rect(d, MID - 40, MID + 100, MID + 40, 980)


def ch_flower(d):
    for k in range(6):
        a = math.radians(k * 60)
        _circle(d, 190, MID + 260 * math.cos(a), MID + 260 * math.sin(a))
    _circle(d, 170, fill=0)
    _circle(d, 120)


def ch_crescent(d):
    _circle(d, 430)
    _circle(d, 380, MID + 170, MID - 60, fill=0)


def ch_heart(d):
    _circle(d, 240, MID - 205, MID - 120)
    _circle(d, 240, MID + 205, MID - 120)
    d.polygon([(MID - 432, MID - 30), (MID + 432, MID - 30), (MID, MID + 440)], fill=255)


def ch_chevron(d):
    d.polygon([(80, 760), (MID, 300), (944, 760), (944, 560), (MID, 100), (80, 560)], fill=255)


def ch_waves(d):
    for k in range(3):
        y0 = 260 + k * 230
        pts = [(x, y0 + 60 * math.sin(x / C * 4 * math.pi)) for x in range(60, 965, 8)]
        pts += [(x, y + 110) for x, y in reversed(pts)]
        d.polygon(pts, fill=255)


def ch_bars(d):
    for k in range(3):
        _rect(d, 90, 200 + k * 240, 934, 330 + k * 240)


def ch_pellets(d):
    for cx, cy in ((MID, 270), (290, 700), (734, 700)):
        _circle(d, 190, cx, cy)


def ch_arrow(d):
    d.polygon([(MID, 60), (920, 480), (650, 480), (650, 960), (374, 960), (374, 480), (104, 480)], fill=255)


def ch_bolt(d):
    d.polygon([(600, 40), (200, 580), (470, 580), (380, 990), (820, 420), (540, 420), (700, 40)], fill=255)


def ch_tree(d):
    for k, (w, y) in enumerate(((330, 80), (400, 300), (460, 520))):
        d.polygon([(MID, y), (MID + w, y + 330), (MID - w, y + 330)], fill=255)
    _rect(d, MID - 70, 840, MID + 70, 990)


def ch_tower(d):
    _rect(d, 230, 330, 794, 980)
    for k in range(4):
        x = 230 + k * 160
        _rect(d, x, 180, x + 84, 340)
    _rect(d, 230 + 3 * 160, 180, 794, 340)
    d.pieslice((MID - 110, 700, MID + 110, 920), 180, 360, fill=0)
    _rect(d, MID - 110, 810, MID + 110, 980, fill=0)


def ch_bridge(d):
    _rect(d, 40, 380, 984, 520)
    _rect(d, 40, 520, 984, 860)
    for cx in (230, MID, 794):
        d.ellipse((cx - 130, 600, cx + 130, 1120), fill=0)
    _rect(d, 40, 870, 984, 1024, fill=0)


def ch_ship(d):
    d.polygon([(80, 640), (944, 640), (800, 860), (224, 860)], fill=255)
    d.polygon([(540, 90), (540, 600), (880, 600)], fill=255)
    d.polygon([(480, 160), (480, 600), (170, 600)], fill=255)


def ch_key(d):
    _circle(d, 200, 300, MID)
    _circle(d, 100, 300, MID, fill=0)
    _rect(d, 470, MID - 55, 980, MID + 55)
    _rect(d, 800, MID + 55, 870, MID + 200)
    _rect(d, 910, MID + 55, 980, MID + 160)


def ch_wheel(d):
    _circle(d, 470)
    _circle(d, 380, fill=0)
    _circle(d, 110)
    for k in range(8):
        a = math.radians(k * 45)
        d.line((MID, MID, MID + 400 * math.cos(a), MID + 400 * math.sin(a)), fill=255, width=60)


def ch_leaf(d):                                           # a vesica: two overlapping circles
    y, x = np.mgrid[0:C, 0:C]
    a = ((x - (MID - 300)) ** 2 + (y - MID) ** 2 < 560 ** 2) & ((x - (MID + 300)) ** 2 + (y - MID) ** 2 < 560 ** 2)
    d.bitmap((0, 0), Image.fromarray((a * 255).astype(np.uint8)), fill=255)


def ch_hourglass(d):
    d.polygon([(160, 80), (864, 80), (MID, MID)], fill=255)
    d.polygon([(160, 944), (864, 944), (MID, MID)], fill=255)


def ch_saltire(d):
    d.line((150, 150, 874, 874), fill=255, width=190)
    d.line((874, 150, 150, 874), fill=255, width=190)


def ch_cross(d):
    _rect(d, MID - 110, 80, MID + 110, 944)
    _rect(d, 80, MID - 110, 944, MID + 110)


def ch_cross_pattee(d):
    for rot in range(4):
        a = math.radians(rot * 90)
        def p(x, y):
            return (MID + x * math.cos(a) - y * math.sin(a), MID + x * math.sin(a) + y * math.cos(a))
        d.polygon([p(-70, 0), p(-260, -450), p(260, -450), p(70, 0)], fill=255)


def ch_ring_dot(d):
    _circle(d, 460)
    _circle(d, 340, fill=0)
    _circle(d, 190)


def ch_half_disc(d):
    d.pieslice((60, 230, 964, 1134), 180, 360, fill=255)
    _rect(d, 60, 720, 964, 800)


def ch_mountain(d):
    d.polygon([(40, 880), (380, 260), (560, 560), (700, 380), (984, 880)], fill=255)


CHARGES = [
    ("star5", lambda d: _star(d, 5, 480, 190)),
    ("star6", lambda d: _star(d, 6, 470, 240)),
    ("star7", lambda d: _star(d, 7, 470, 230)),
    ("star8", lambda d: _star(d, 8, 470, 260, rot=-90 + 22.5)),
    ("star4", lambda d: _star(d, 4, 490, 150)),
    ("disc", lambda d: _circle(d, 420)),
    ("ring", lambda d: (_circle(d, 450), _circle(d, 320, fill=0))),
    ("ring_dot", ch_ring_dot),
    ("diamond", lambda d: _ngon(d, 4, 480)),
    ("square", lambda d: _ngon(d, 4, 470, rot=45)),
    ("triangle", lambda d: _ngon(d, 3, 500, cy=MID + 100)),
    ("triangle_down", lambda d: _ngon(d, 3, 500, rot=90, cy=MID - 100)),
    ("hexagon", lambda d: _ngon(d, 6, 460)),
    ("octagon", lambda d: _ngon(d, 8, 460, rot=-90 + 22.5)),
    ("crescent", ch_crescent),
    ("sun", ch_sun),
    ("ring_star", ch_ring_star),
    ("cross", ch_cross),
    ("cross_pattee", ch_cross_pattee),
    ("saltire", ch_saltire),
    ("chevron", ch_chevron),
    ("waves", ch_waves),
    ("bars", ch_bars),
    ("pellets", ch_pellets),
    ("quatrefoil", ch_quatrefoil),
    ("trefoil", ch_trefoil),
    ("flower", ch_flower),
    ("heart", ch_heart),
    ("arrow", ch_arrow),
    ("bolt", ch_bolt),
    ("tree", ch_tree),
    ("tower", ch_tower),
    ("bridge", ch_bridge),
    ("ship", ch_ship),
    ("key", ch_key),
    ("wheel", ch_wheel),
    ("leaf", ch_leaf),
    ("hourglass", ch_hourglass),
    ("half_disc", ch_half_disc),
    ("mountain", ch_mountain),
]
CHARGE = dict(CHARGES)


def charge_alpha(name):
    im = Image.new("L", (C, C), 0)
    CHARGE[name](ImageDraw.Draw(im))
    return im


def charge_texture(name):
    a = charge_alpha(name).resize((CE_SIZE, CE_SIZE), Image.LANCZOS)
    out = np.zeros((CE_SIZE, CE_SIZE, 4), dtype=np.uint8)
    out[..., 2] = 128
    out[..., 3] = np.array(a)
    return Image.fromarray(out)


# ---------------------------------------------------------------------------------------------------------------
# Titles
# ---------------------------------------------------------------------------------------------------------------
def read_titles():
    """Every landed title, in file order, as {key: (parent key or None, file name)}."""
    titles = {}
    for f in sorted((MOD / "common" / "landed_titles").glob("*.txt")):
        stack = []
        depth = 0
        for line in f.read_text(encoding="utf-8-sig").splitlines():
            line = line.split("#")[0]
            m = re.match(r"\s*([ekdcb]_[a-z0-9_]+)\s*=\s*\{", line)
            if m:
                parent = stack[-1][0] if stack else None
                titles[m.group(1)] = (parent, f.name)
                stack.append((m.group(1), depth))
            depth += line.count("{") - line.count("}")
            while stack and depth <= stack[-1][1]:
                stack.pop()
    return titles


def stable(s):
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def rgb(c):
    return "rgb { %d %d %d }" % tuple(c)


class Design:
    """A derived flag: layout + colours, an optional canton (a real flag's texture) and a charge."""

    def __init__(self, layout, colours, charge, charge_colour, canton=None, charge_scale=0.30):
        self.layout, self.colours, self.charge = layout, colours, charge
        self.charge_colour, self.canton, self.charge_scale = charge_colour, canton, charge_scale

    def text(self, key):
        name, _, (cu, cv), size, _, _ = LAYOUT[self.layout]
        c1, c2, c3 = self.colours
        out = ["%s = {" % key, '\tpattern = "pattern_solid.dds"', "\tcolor1 = " + rgb(c1),
               '\tcolored_emblem = {\n\t\ttexture = "ce_wm_layout_%s.dds"\n\t\tcolor1 = %s\n\t\tcolor2 = %s\n'
               '\t\tcolor3 = %s\n\t\tinstance = { position = { 0.5 0.5 } scale = { 1 1 } depth = 9.01 }\n\t}'
               % (name, rgb(c1), rgb(c2), rgb(c3))]
        if self.canton:
            f = 0.018
            out.append('\tcolored_emblem = {\n\t\ttexture = "ce_wm_box.dds"\n\t\tcolor1 = %s\n'
                       '\t\tinstance = { position = { %.4f %.4f } scale = { %.4f %.4f } depth = 3.01 }\n\t}'
                       % (rgb(WHITE), (0.5 + f) / 2, BAND[0] + (1 / 3 + f) / 2, 0.5 + f, 1 / 3 + f))
            out.append('\ttextured_emblem = {\n\t\ttexture = "wm_flag_%s.dds"\n'
                       '\t\tinstance = { position = { 0.25 %.4f } scale = { 0.5 0.5 } depth = 2.01 }\n\t}'
                       % (self.canton, BAND[0] + 1 / 6))
        s = self.charge_scale * size
        out.append('\tcolored_emblem = {\n\t\ttexture = "ce_wm_charge_%s.dds"\n\t\tcolor1 = %s\n'
                   '\t\tinstance = { position = { %.4f %.4f } scale = { %.4f %.4f } depth = 1.01 }\n\t}'
                   % (self.charge, rgb(self.charge_colour), cu, BAND[0] + cv * (BAND[1] - BAND[0]), s, s))
        out.append("}")
        return "\n".join(out)

    def body(self):
        return self.text("x").split("\n", 1)[1]


def real_text(key, fid, pal):
    return ('%s = {\n\tpattern = "pattern_solid.dds"\n\tcolor1 = %s\n\ttextured_emblem = {\n'
            '\t\ttexture = "wm_flag_%s.dds"\n\t\tinstance = { position = { 0.5 0.5 } scale = { 1 1 } }\n\t}\n}'
            % (key, rgb(pal[0]), fid))


def colours_for(pal, i):
    """Three colours from a palette (rotated by i), padded with white and ink."""
    base = list(dict.fromkeys(pal))
    for extra in (WHITE, INK):
        if len(base) < 3 and all(dist(extra, c) > 60 for c in base):
            base.append(extra)
    k = i % len(base)
    rot = base[k:] + base[:k]
    while len(rot) < 3:
        rot.append(rot[-1])
    return tuple(rot[:3])


class Assigner:
    def __init__(self):
        self.used = set()

    def make(self, key, layouts, pal, i, charge_seed, canton, scale):
        """A design for key no other title has: walks the charges, then the layouts, until it is new."""
        for lstep in range(len(layouts)):
            layout = layouts[(stable(key + "L") // 7 + i + lstep) % len(layouts)] if lstep else \
                layouts[(charge_seed + i) % len(layouts)]
            colours = colours_for(pal, i // len(layouts) + stable(key) % 2 if len(pal) > 1 else 0)
            region = LAYOUT[layout][4]
            if colours[region] == colours[0] and region != 0:
                colours = (colours[0], colours[1] if colours[1] != colours[0] else WHITE, colours[2])
            for cstep in range(len(CHARGES)):
                charge = CHARGES[(charge_seed + i + cstep) % len(CHARGES)][0]
                under = colours[region]
                ccol = contrast(under, [c for c in list(pal) + [WHITE, INK, (255, 205, 0)] if dist(c, under) > 80])
                d = Design(layout, colours, charge, ccol, canton, scale)
                if d.body() not in self.used:
                    self.used.add(d.body())
                    return d
        raise RuntimeError("no free design for " + key)


def build_designs(titles, flags):
    """{title: ("real", flag id) or ("derived", Design)}, plus each title's palette for its children."""
    pals = {fid: palette(img) for fid, img in flags.items()}
    real_of = {t: fid for fid, (_, t, _) in FLAGS.items()}
    seat_county = {"c_" + s: fid for fid, seats in COUNTY_SEATS.items() for s in seats.split()}
    out, pal_of, canton_of = {}, {}, {}
    A = Assigner()

    def nation_of(t):
        while t and not t.startswith("k_"):
            t = titles[t][0]
        return t

    for t, fid in real_of.items():
        if t not in titles:
            raise SystemExit("FLAGS names a title that doesn't exist: %s (%s)" % (t, fid))
        out[t] = ("real", fid)
        pal_of[t] = pals[fid]
        A.used.add(real_text("x", fid, pals[fid]).split("\n", 1)[1])

    # Duchies without a real flag: their nation's flag in the canton, the region's colours
    duchies = [t for t in titles if t.startswith("d_") and titles[t][1].startswith("00_")]
    for n, d in enumerate(duchies):
        if d in out:
            continue
        nat = NATION_FLAG[nation_of(d)]
        pal = list(REGION_COLOURS[d])
        out[d] = ("derived", A.make(d, CANTON_LAYOUTS, pal, 0, stable(d), nat, 0.36))
        pal_of[d] = pal
        canton_of[d] = nat

    # Constituencies: grouped by the flag in their canton; each group's seats get different charges
    groups = {}
    for c in [t for t in titles if t.startswith("c_") and titles[t][1].startswith("00_")]:
        if c in out:
            continue
        d = titles[c][0]
        if c in seat_county:
            parent, pal = seat_county[c], pals[seat_county[c]]
        elif out[d][0] == "real":
            parent, pal = out[d][1], pal_of[d]
        else:
            parent, pal = canton_of[d], pal_of[d]
        groups.setdefault((parent, tuple(pal)), []).append(c)
    for (parent, pal), seats in groups.items():
        seed = stable(parent + str(pal))
        for i, c in enumerate(seats):
            out[c] = ("derived", A.make(c, CANTON_LAYOUTS, list(pal), i, seed, parent, 0.30))
            pal_of[c] = list(pal)

    # Wards: their constituency's colours, no canton
    for b in [t for t in titles if t.startswith("b_")]:
        if b in out:
            continue
        c = titles[b][0]
        sibs = [t for t in titles if titles[t][0] == c and t.startswith("b_")]
        i = sibs.index(b)
        out[b] = ("derived", A.make(b, ALL_LAYOUTS, pal_of[c], i, stable(c), None, 0.30))

    # Landless titles (offices, mayoralties, peerages); party titles have build_party_arms.py's arms
    landless = {
        "k_gov_scotland": ("scotland", [(0, 94, 184), WHITE]),
        "k_gov_wales": ("wales", [(200, 16, 46), (0, 122, 61), WHITE]),
        "k_gov_northern_ireland": ("st_patrick", [(0, 60, 113), WHITE]),
        "d_mayor_greater_manchester": ("england", list(REGION_COLOURS["d_greater_manchester"])),
        "c_council_test": ("england", [(0, 84, 147), (255, 199, 44)]),
    }
    for t in titles:
        if t in out or t.startswith("k_party_"):
            continue
        canton, pal = landless.get(t, ("uk", [(150, 26, 52), (255, 205, 0)]))
        out[t] = ("derived", A.make(t, CANTON_LAYOUTS, pal, stable(t) % 5, stable(t), canton, 0.34))
    return out, pals


# ---------------------------------------------------------------------------------------------------------------
# Preview (an approximation of what the game draws, for the contact sheet)
# ---------------------------------------------------------------------------------------------------------------
_charge_cache = {}


def preview(kind, val, flags, w=90):
    h = round(w * 2 / 3)
    if kind == "real":
        return flags[val].resize((w, h), Image.LANCZOS)
    d = val
    y, x = np.mgrid[0:h, 0:w].astype(np.float32) + 0.5
    r = LAYOUT[d.layout][1](x / w, y / h)
    img = np.array(d.colours, dtype=np.uint8)[r]
    im = Image.fromarray(img)
    if d.canton:
        f = round(0.018 * w)
        ImageDraw.Draw(im).rectangle((0, 0, w // 2 + f - 1, h // 2 + f - 1), fill=WHITE)
        im.paste(flags[d.canton].resize((w // 2, h // 2), Image.LANCZOS), (0, 0))
    _, _, (cu, cv), size, _, _ = LAYOUT[d.layout]
    s = max(2, round(d.charge_scale * size * w))
    key = (d.charge, s)
    if key not in _charge_cache:
        _charge_cache[key] = charge_alpha(d.charge).resize((s, s), Image.LANCZOS)
    im.paste(Image.new("RGB", (s, s), d.charge_colour), (round(cu * w - s / 2), round(cv * h - s / 2)),
             _charge_cache[key])
    return im


def contact_sheet(designs, flags, titles, path):
    order = [t for t in titles if t in designs]
    groups = [("nations and regions", [t for t in order if t[0] in "ekd" and not t.startswith("k_party")]),
              ("constituencies", [t for t in order if t.startswith("c_")]),
              ("wards (first 300)", [t for t in order if t.startswith("b_")][:300])]
    w, h, cols = 72, 48, 30
    rows = sum((len(g) + cols - 1) // cols for _, g in groups)
    sheet = Image.new("RGB", (cols * (w + 6) + 6, rows * (h + 6) + len(groups) * 20 + 6), (243, 239, 230))
    dr = ImageDraw.Draw(sheet)
    y = 4
    for name, ts in groups:
        dr.text((6, y), name, fill=INK)
        y += 16
        for n, t in enumerate(ts):
            x = 6 + (n % cols) * (w + 6)
            if n and n % cols == 0:
                y += h + 6
            sheet.paste(preview(*designs[t], flags, w), (x, y))
            dr.rectangle((x - 1, y - 1, x + w, y + h), outline=INK)
        y += h + 10
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)


# ---------------------------------------------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------------------------------------------
def write_readme(meta):
    rows = ["<!-- flags:begin (generated by tools/ui/build_flags.py) -->", "## Flags (title coats of arms)", "",
            "`tools/ui/build_flags.py` downloads these SVGs from Wikimedia Commons into `raw/flags/` once (with "
            "`raw/flags/meta.json`; `--refresh` downloads again), renders them with resvg and stretches them to 3:2. "
            "The textures made from CC BY-SA files are under the same licence, with the attribution below. "
            "Every other title's flag is derived (generated) and needs no attribution.", "",
            "| Flag | Title | Commons file | Author | Licence |", "|---|---|---|---|---|"]
    for fid, (_, title, what) in FLAGS.items():
        m = meta[fid]
        lic = m["licence"] + (" (%s)" % m["licence_url"] if m["licence_url"] else "")
        rows.append("| %s | `%s` | [%s](%s) | %s | %s |" % (what, title, m["title"][5:], m["page"],
                                                            (m["author"] or "unknown").replace("|", "/"), lic))
    rows.append("<!-- flags:end -->")
    text = README.read_text(encoding="utf-8")
    block = "\n".join(rows)
    if "<!-- flags:begin" in text:
        text = re.sub(r"<!-- flags:begin.*?<!-- flags:end -->", lambda _: block, text, flags=re.S)
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    README.write_text(text, encoding="utf-8")


def main():
    refresh = "--refresh" in sys.argv
    titles = read_titles()
    meta = download(refresh)
    flags = {fid: render_flag(fid) for fid in FLAGS}

    # Real flags
    digests = {}
    for fid, img in flags.items():
        tex = flag_texture(img)
        dg = hashlib.md5(tex.tobytes()).hexdigest()
        if dg in digests:
            raise SystemExit("flags %s and %s are the same image" % (fid, digests[dg]))
        digests[dg] = fid
        save_dds(tex, OUT_TEX / ("wm_flag_%s.dds" % fid))
    for old in OUT_TEX.glob("wm_flag_*.dds"):
        if old.stem[len("wm_flag_"):] not in FLAGS:
            old.unlink()

    # Layouts and charges
    for name, fn, *_ in LAYOUTS:
        save_dds(layout_texture(fn), OUT_CE / ("ce_wm_layout_%s.dds" % name))
    for name, _ in CHARGES:
        save_dds(charge_texture(name), OUT_CE / ("ce_wm_charge_%s.dds" % name))
    save_dds(box_texture(), OUT_CE / "ce_wm_box.dds", mips=False)
    reg = ["# Generated by westminster/tools/ui/build_flags.py - edit there.",
           "# Flag layouts (3 colours) and charges, listed in the coat of arms designer."]
    reg += ["ce_wm_layout_%s.dds = { colors = 3 category = patterns }" % l[0] for l in LAYOUTS]
    reg += ["ce_wm_charge_%s.dds = { colors = 1 category = abstract }" % c[0] for c in CHARGES]
    reg += ["ce_wm_box.dds = { colors = 1 category = patterns }"]
    (OUT_CE / "wm_flag_emblems.txt").write_text("\n".join(reg) + "\n", encoding="utf-8-sig")

    designs, pals = build_designs(titles, flags)
    out = ["# Generated by westminster/tools/ui/build_flags.py - edit there.",
           "# Every landed title's flag (party titles: wm_party_arms.txt). Flags fill the middle 3:2 band of the CoA;",
           "# real flags are textured emblems (gfx/coat_of_arms/textured_emblems/wm_flag_*.dds), derived ones are a",
           "# layout, a canton with the county's (or region's, or nation's) flag and a charge.", ""]
    for t in titles:
        if t not in designs:
            continue
        kind, val = designs[t]
        out.append(real_text(t, val, pals[val]) if kind == "real" else val.text(t))
    OUT_COA.parent.mkdir(parents=True, exist_ok=True)
    # Vanilla swaps some titles to variant arms (k_england to the Norman lions) in ways the empty dynamic file below
    # doesn't stop: give the variants the title's own flag too.
    for variant, title in (("k_england_norman", "k_england"), ("k_england_france", "k_england")):
        block = next(b for b in out if b.startswith(title + " = {"))
        out.append(variant + block[len(title):])
    OUT_COA.write_text("\n".join(out) + "\n", encoding="utf-8-sig")
    # Vanilla's dynamic coats of arms swap titles to other arms by trigger (k_england to the Norman lions, the
    # North Sea empire...). Replaced by an empty file of the same name, so every title keeps its flag.
    dyn = MOD / "common" / "coat_of_arms" / "dynamic_definitions" / "00_dynamic_coas.txt"
    dyn.parent.mkdir(parents=True, exist_ok=True)
    dyn.write_text("# Westminster: replaces the game's dynamic coats of arms (none: titles keep their flags).\n"
                   "# Generated by westminster/tools/ui/build_flags.py - edit there.\n", encoding="utf-8-sig")
    write_readme(meta)
    contact_sheet(designs, flags, titles, PREVIEW)

    real = sum(1 for k, _ in designs.values() if k == "real")
    by_tier = {}
    for t, (k, _) in designs.items():
        by_tier.setdefault((t[0], k), 0)
        by_tier[(t[0], k)] += 1
    print("wrote", OUT_COA.relative_to(ROOT.parent))
    print("titles: %d real flags, %d derived" % (real, len(designs) - real))
    for tier in "ekdcb":
        print("  %s_: %d real, %d derived" % (tier, by_tier.get((tier, "real"), 0), by_tier.get((tier, "derived"), 0)))
    print("preview", PREVIEW.relative_to(ROOT.parent))
    sys.stdout.flush()
    sys.exit(subprocess.call([sys.executable, str(HERE / "check_title_flags.py")]))


if __name__ == "__main__":
    main()
