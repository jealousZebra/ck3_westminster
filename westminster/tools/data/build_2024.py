#!/usr/bin/env python3
"""The 2024 bookmark's data: the 650 MPs elected on 4 July 2024, their parties and the people who lead them.

    python3 westminster/tools/data/build_2024.py            # downloads once into data/raw/, then writes the mod files
    python3 westminster/tools/data/build_2024.py --refresh  # downloads again

Sources (see data/README.md for licences):
  - UK Parliament election results (electionresults.parliament.uk): every 2024 candidacy, with the winner, party,
    ONS constituency code, MNIS member id, votes and shares.
  - ONS Open Geography Portal: PCON24CD -> PCON24NM, the names the map's county titles were generated from.
  - UK Parliament Members API (members-api.parliament.uk): each MP's gender.
  - Wikidata (query.wikidata.org): dates of birth (P569, with precision), by parliament.uk member id (P10428).
  - Wikipedia (MediaWiki API): member lists of self-declared caucuses (CAUCUSES), for MPs' ideologies, matched to
    the MPs through each linked page's Wikidata item.

Writes (all generated; edit this script, not the outputs):
  westminster/history/characters/wm_2024_mps.txt         one character per MP, plus leaders who aren't MPs, the former
                                                         Prime Ministers and the MPs' fictional spouses (build_spouses.py);
                                                         likenesses (`dna = ...`) come from build_likenesses.py
  westminster/history/titles/wm_2024_seats.txt           the UK, nations, parties, devolved governments and seats
  westminster/common/dynasties/wm_party_dynasties.txt    one dynasty per party (and one for independents)
  westminster/common/dynasty_houses/wm_party_houses.txt  its one house: party membership is the character's house
  westminster/common/culture/name_lists/wm_name_lists.txt  modern full names ("Given Surname") for new characters
  westminster/common/scripted_effects/wm_party_houses.txt  per-party house switch, game-start setup, founding slots
  westminster/common/scripted_triggers/wm_party_houses.txt
  westminster/common/decisions/wm_party_decisions.txt    "Cross the Floor" (join another party) and "Found a Party"
  westminster/common/landed_titles/10_wm_parties.txt     every party that won a seat, plus slots for founded parties
  westminster/localization/english/wm_names_l_english.yml     character names (each a key: "Keir Starmer") and name lists
  westminster/localization/english/wm_party_houses_l_english.yml
  westminster/common/landed_titles/31_wm_wales_gov.txt   the Welsh Government
  westminster/common/bookmarks/bookmarks/wm_bookmarks.txt
  westminster/localization/english/wm_parties_l_english.yml   (the block between the BEGIN/END build_2024 markers)
  westminster/localization/english/wm_bookmarks_l_english.yml
  data/ge2024_results.csv                                vote shares per seat, for polling and seat lean later, and
                                                         the seat's ideology (winner_ideology)
  westminster/history/provinces/k_*.txt                  each seat's faith (its ideology); build_map.py writes the rest
  tools/test_out/ideology_2024.txt                       every politician's ideology and the reason for it
"""
import concurrent.futures
import csv
import hashlib
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_likenesses import DNA_KEYS  # noqa: E402
from build_spouses import make_spouses  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent          # westminster/
RAW = ROOT / "data" / "raw"
MOD = ROOT / "westminster"
REFRESH = "--refresh" in sys.argv
UA = os.environ.get("CK3_USER_AGENT", "WestminsterCK3Mod/0.1 (Crusader Kings III mod data build; open-source tooling)")	# set CK3_USER_AGENT to add a contact URL

START = "2024.7.5"
CANDIDACIES_URL = "https://electionresults.parliament.uk/general-elections/6/candidacies.csv"
ONS_URL = ("https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/"
           "Westminster_Parliamentary_Constituencies_July_2024_Boundaries_UK_BGC/FeatureServer/0/query"
           "?where=1%3D1&outFields=PCON24CD,PCON24NM&returnGeometry=false&f=json&resultRecordCount=2000")
MEMBER_URL = "https://members-api.parliament.uk/api/Members/%s"
WIKIDATA_URL = "https://query.wikidata.org/sparql"

CULTURE = {"E": "english", "S": "scottish", "W": "welsh", "N": "irish"}      # by the ONS code's first letter

# Parties that won seats, by the results' "Main party abbreviation". The leader is the leader of the party's MPs
# at Westminster on 5 July 2024 (given by seat key), which is the party leader except for the SNP (Stephen Flynn;
# leader John Swinney is an MSP), Plaid Cymru (Liz Saville Roberts; leader Rhun ap Iorwerth is an MS), Alliance
# (Sorcha Eastwood; leader Naomi Long is an MLA) and the UUP (Robin Swann; leader Doug Beattie is an MLA).
# Sinn Féin's MPs don't take their seats, so its leader is Mary Lou McDonald, who isn't an MP.
PARTIES = [
    # key,        abbrev, name,                                   adjective,           colour,          capital,                 leader seat or extra id, leader surname
    ("labour",       "Lab",   "Labour Party",                      "Labour",            (228, 0, 59),    "holborn_and_st_pancras", "holborn_and_st_pancras", "Starmer"),
    ("conservative", "Con",   "Conservative Party",                "Conservative",      (0, 135, 220),   "richmond_and_northallerton", "richmond_and_northallerton", "Sunak"),
    ("lib_dem",      "LD",    "Liberal Democrats",                 "Liberal Democrat",  (250, 166, 26),  "kingston_and_surbiton",  "kingston_and_surbiton", "Davey"),
    ("snp",          "SNP",   "Scottish National Party",           "SNP",               (253, 243, 142), "aberdeen_south",         "aberdeen_south", "Flynn"),
    ("sinn_fein",    "SF",    "Sinn Féin",                         "Sinn Féin",         (50, 106, 33),   "belfast_west",           "wm_char_mary_lou_mcdonald", "McDonald"),
    ("reform",       "RUK",   "Reform UK",                         "Reform",            (18, 182, 207),  "clacton",                "clacton", "Farage"),
    ("dup",          "DUP",   "Democratic Unionist Party",         "DUP",               (212, 106, 76),  "belfast_east",           "belfast_east", "Robinson"),
    ("green",        "Green", "Green Party",                       "Green",             (2, 167, 91),    "bristol_central",        "bristol_central", "Denyer"),
    ("plaid",        "PC",    "Plaid Cymru",                       "Plaid",             (0, 91, 84),     "dwyfor_meirionnydd",     "dwyfor_meirionnydd", "Saville Roberts"),
    ("sdlp",         "SDLP",  "Social Democratic and Labour Party", "SDLP",             (42, 168, 44),   "foyle",                  "foyle", "Eastwood"),
    ("alliance",     "APNI",  "Alliance Party",                    "Alliance",          (246, 203, 47),  "lagan_valley",           "lagan_valley", "Eastwood"),
    ("uup",          "UUP",   "Ulster Unionist Party",             "UUP",               (72, 160, 220),  "south_antrim",           "south_antrim", "Swann"),
    ("tuv",          "TUV",   "Traditional Unionist Voice",        "TUV",               (12, 59, 95),    "north_antrim",           "north_antrim", "Allister"),
]
PARTY_BY_ABBR = {p[1]: p for p in PARTIES}
PARTY_KEY_NAME = {p[0]: p[2] for p in PARTIES}

# Parties are families: each party is a dynasty with one house (wm_dyn_party_<key> / wm_house_party_<key>), every
# member is in their party's house, and the house's coat of arms is the party's emblem (tools/ui/build_party_arms.py).
# Independents and the Speaker share an "Independent" house, so every politician has a shield and nobody is lowborn.
# Characters carry their whole name as their first name ("Keir Starmer"); the name formats don't show the house
# (tools/ui/build_colleagues.py), so the party never appears as a surname.
INDEPENDENT_HOUSE = "wm_house_independent"

# Founded parties: landless title slots a politician can found a party in ("Found a Party", wm_party_decisions.txt).
# Made-up names and emblems (build_party_arms.py). (slot, name, adjective, colour)
NEW_PARTIES = [
    ("new_1", "Lantern Party", "Lantern", (22, 46, 92)),
    ("new_2", "Bridge Party", "Bridge", (110, 52, 140)),
    ("new_3", "Beacon Alliance", "Beacon", (176, 38, 30)),
    ("new_4", "Kestrel Party", "Kestrel", (122, 82, 48)),
    ("new_5", "Compass Movement", "Compass", (0, 128, 128)),
    ("new_6", "Hearth Party", "Hearth", (128, 20, 52)),
]


def house_of(c):
    return "wm_house_party_" + c["party"] if c["party"] else INDEPENDENT_HOUSE


def name_key(c):
    """Localization key of a character's (full) name: wm_name_mp_<seat> / wm_name_char_<id>."""
    return "wm_name_" + c["id"][3:]

# People in the bookmark who aren't MPs (dates of birth from Wikidata). party: their wm_party; office: what they hold.
EXTRAS = [
    # id suffix,          given,        family,     female, birth,       culture,    party,       office
    ("mary_lou_mcdonald", "Mary Lou",   "McDonald", True,  "1969.5.1",  "irish",    "sinn_fein", None),
    ("john_swinney",      "John",       "Swinney",  False, "1964.4.13", "scottish", "snp",       "k_gov_scotland"),
    ("michelle_oneill",   "Michelle",   "O'Neill",  True,  "1977.1.10", "irish",    "sinn_fein", "k_gov_northern_ireland"),
    ("vaughan_gething",   "Vaughan",    "Gething",  False, "1974.3.15", "welsh",    "labour",    "k_gov_wales"),
]

# Former Prime Ministers, alive in 2024 and out of the Commons: party members (their party's house and var:wm_party)
# at the Crown's court, which has no council, so a PM can't appoint them. David Cameron (Baron Cameron of Chipping
# Norton, 2023) and Theresa May (named for a life peerage in the dissolution honours of 4 July 2024) are peers; they
# get their peerage titles when peerages exist beyond spike d (a flag nothing reads is an error-log error).
# (id suffix, given, family, female, birth, culture, party, peer)
FORMER_PMS = [
    ("john_major",     "John",    "Major",   False, "1943.3.29",  "english",  "conservative", False),
    ("tony_blair",     "Tony",    "Blair",   False, "1953.5.6",   "english",  "labour",       False),
    ("gordon_brown",   "Gordon",  "Brown",   False, "1951.2.20",  "scottish", "labour",       False),
    ("david_cameron",  "David",   "Cameron", False, "1966.10.9",  "english",  "conservative", True),
    ("theresa_may",    "Theresa", "May",     True,  "1956.10.1",  "english",  "conservative", True),
    ("boris_johnson",  "Boris",   "Johnson", False, "1964.6.19",  "english",  "conservative", False),
    ("liz_truss",      "Liz",     "Truss",   True,  "1975.7.26",  "english",  "conservative", False),
]
CROWN = "wm_royal_charles"      # the monarch (history/characters/wm_royal_family.txt)

# Featured characters on the bookmark screen: (seat key, loc name, animation, the line under the name, whether the
# map highlights their party's seats when they're selected). Their places on the screen come from the bookmark map
# (tools/ui/build_bookmark_screen.py layout(): beside their seat), their portraits from common/bookmark_portraits.
FEATURED = [
    ("holborn_and_st_pancras", "Keir Starmer", "personality_rational", "Prime Minister", True),
    ("richmond_and_northallerton", "Rishi Sunak", "disapproval", "Leader of the Opposition", True),
    ("kingston_and_surbiton", "Ed Davey", "happiness", "Leader of the Liberal Democrats", True),
    ("north_west_cambridgeshire", "Sam Carling", "personality_bold", "MP for North West Cambridgeshire", False),
]

# Playable activists with no seat (unlanded careers, wm_career_effects.txt): fictional, they start as landless
# adventurers (a campaign team) in their party, looking for a seat. (id suffix, given, family, female, birth, culture,
# party, starting seat, animation, screen position, bookmark description)
ACTIVISTS = [
    ("jess_okafor", "Jess", "Okafor", True, "2000.3.14", "english", "labour", "leeds_central_and_headingley",
     "personality_bold", (520, 720), "A fictional Labour activist from Leeds, 24, with a campaign team of friends and "
     "a lot of leaflets. No seat, no job, no money: just ambition. Play the long game from doorstep to green benches."),
]

# Vote-share columns in ge2024_results.csv, by party abbreviation (independents, the Speaker and others grouped)
SHARE_COLS = ["Lab", "Con", "LD", "RUK", "Green", "SNP", "PC", "SF", "DUP", "SDLP", "APNI", "UUP", "TUV", "Ind", "Spk", "Oth"]


def key(name):
    """Title key fragment from a name, exactly as westminster/tools/map/geo.py key() makes the map's titles."""
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower().replace("&", "and")).strip("_")


# ------------------------------------------------------------------------------------------------ downloads

def fetch(url, data=None, headers=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def cached(name, url):
    path = RAW / name
    if REFRESH or not path.exists():
        print("downloading", url)
        path.write_bytes(fetch(url))
    return path


def load_candidacies():
    with open(cached("ge2024_candidacies.csv", CANDIDACIES_URL), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_ons_names():
    d = json.loads(cached("pcon24_names.json", ONS_URL).read_text())
    return {f["attributes"]["PCON24CD"]: f["attributes"]["PCON24NM"] for f in d["features"]}


def load_members(ids):
    """Members API record per MNIS id (gender, display name), cached in one file."""
    path = RAW / "members_api_2024.json"
    have = {} if REFRESH or not path.exists() else json.loads(path.read_text())
    todo = [i for i in ids if i not in have]
    if todo:
        print("downloading %d Members API records" % len(todo))

        def one(i):
            return i, json.loads(fetch(MEMBER_URL % i, headers={"Accept": "application/json"}))["value"]
        with concurrent.futures.ThreadPoolExecutor(8) as pool:
            for i, v in pool.map(one, todo):
                have[i] = v
        path.write_text(json.dumps(have, indent=0, sort_keys=True))
    return have


def load_wikidata(ids):
    """Wikidata date of birth (with precision) and gender per parliament.uk member id (P10428)."""
    path = RAW / "wikidata_mps_2024.json"
    if REFRESH or not path.exists():
        print("querying Wikidata for %d members" % len(ids))
        rows = []
        for n in range(0, len(ids), 200):
            values = " ".join('"%s"' % i for i in ids[n:n + 200])
            q = """SELECT ?id ?item ?dob ?prec ?gender WHERE {
  VALUES ?id { %s }
  ?item wdt:P10428 ?id .
  OPTIONAL { ?item p:P569/psv:P569 [ wikibase:timeValue ?dob ; wikibase:timePrecision ?prec ] }
  OPTIONAL { ?item wdt:P21 ?gender }
}""" % values
            body = urllib.parse.urlencode({"query": q}).encode()
            res = json.loads(fetch(WIKIDATA_URL, data=body, headers={
                "Accept": "application/sparql-results+json", "Content-Type": "application/x-www-form-urlencoded"}))
            rows += [{k: v["value"] for k, v in b.items()} for b in res["results"]["bindings"]]
        path.write_text(json.dumps(rows, indent=0))
    out = {}
    for r in json.loads(path.read_text()):
        best = out.setdefault(r["id"], {})
        if "gender" in r:
            best["gender"] = r["gender"].rsplit("/", 1)[-1]
        if "dob" in r and int(r.get("prec", 0)) > best.get("prec", 0):
            best["dob"], best["prec"] = r["dob"], int(r["prec"])
    return out


# ------------------------------------------------------------------------------------------------ helpers

def ck3_date(y, m, d):
    return "%d.%d.%d" % (y, m, d)


def birth_date(wd, seed):
    """CK3 birth date: Wikidata's when known to the day; month or year precision keep what's known; unknown
    dates estimate an age of about 50 on polling day. Missing parts come from a stable hash of the seat."""
    h = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    m_guess, d_guess = h % 12 + 1, (h // 12) % 28 + 1
    if wd and "dob" in wd:
        m = re.match(r"(-?\d+)-(\d\d)-(\d\d)", wd["dob"])
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if wd["prec"] >= 11:
            return ck3_date(y, mo, d), "day"
        if wd["prec"] == 10:
            return ck3_date(y, mo, d_guess), "month"
        if wd["prec"] == 9:
            return ck3_date(y, m_guess, d_guess), "year"
    return ck3_date(1974 + (h // 336) % 3 - 1, m_guess, d_guess), "estimated"


def q(s):
    return '"%s"' % s.replace('"', "'")


def write(path, text, bom=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig" if bom else "utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", path.relative_to(ROOT.parent))


GEN = "# Generated by westminster/tools/data/build_2024.py - edit there.\n"

# ------------------------------------------------------------------------------------------------ ideology

# Ideology replaces religion (tools/data/build_ideology.py, PLAN.md). Every politician has an ideology (their faith);
# the royal family, the MPs' spouses and the Speaker are "Not Stated". An MP gets their own ideology only when it is
# obvious from public record: membership of a self-declared caucus, from the member lists on Wikipedia (CAUCUSES,
# cached in data/raw/, matched to the MPs by Wikidata item, so by parliament.uk member id). Anyone else takes their
# party's mainstream ideology with a little seeded variation inside the party's range (PARTY_FALLBACK). The reason
# for each MP is in a comment in the history file and in tools/test_out/ideology_2024.txt.
from build_ideology import (IDEO, NOT_STATED, PARTY_FALLBACK, PARTY_RANGE, faith_key,  # noqa: E402
                            wing_for)

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
# Caucus pages: (page title, ideology, section start, section end, what the list is). Only the first link of each
# list item or table row is read (the member); everything else on the line (constituencies, notes) is ignored.
CAUCUSES = [
    ("Socialist Campaign Group", "socialist", r"^=== *Current members", r"^=== *Former members",
     "Socialist Campaign Group: current members"),
    ("Socialist Campaign Group", "socialist", r"^==== *Expelled", r"^==== *Deselected",
     "Socialist Campaign Group: members expelled from Labour in 2024 or later"),
    ("Socialist Campaign Group", "socialist", r"^==== *Defected", r"^==== *Resigned",
     "Socialist Campaign Group: members who defected in 2024 or later"),
    ("One Nation Conservatives (caucus)", "one_nation", r"^== *Membership", r"^== *Leadership",
     "One Nation Conservatives caucus: members identified by the press"),
    ("European Research Group", "national_conservative", r"^== *Structure", r"^=+ *Past subscribers",
     "European Research Group: chairs and subscribers"),
    ("Common Sense Group", "national_conservative", r"Conservative MPs", r"Members of the House of Lords",
     "Common Sense Group: Conservative MP members"),
    ("New Conservatives (UK)", "national_conservative", r"^== *Membership", r"^== *See also",
     "New Conservatives: members"),
    ("Free Market Forum", "free_market", r"listed the following MPs", r"^== *See also",
     "Free Market Forum: parliamentary supporters"),
]
# Lists that need a year: only entries that mention 2024 or later (members when the 2024 Parliament met)
CAUCUS_NEEDS_RECENT_YEAR = {"Socialist Campaign Group: members expelled from Labour in 2024 or later",
                            "Socialist Campaign Group: members who defected in 2024 or later"}

# Not MPs, so not matched through the lists: obvious from public record. (char id suffix: (ideology, source))
MANUAL_IDEOLOGY = {
    "liz_truss": ("free_market", "Conservative Growth Group, the faction that backs her (Wikipedia)"),
    "tony_blair": ("centrist", "New Labour; founding patron of Progress (Wikipedia)"),
}
# Independents: the party they came from, where known (Wikipedia); otherwise the neutral centre
INDEPENDENT_FORMER_PARTY = {
    "north_down": ("dup", "former DUP member"),
    "birmingham_perry_barr": ("lib_dem", "former Liberal Democrat councillor"),
}
INDEPENDENT_DEFAULT = "centrist"


def wiki_slug(title):
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def load_caucus_page(title):
    """Wikitext of a Wikipedia page (MediaWiki API, cached in data/raw/wikipedia_caucus_<slug>.json)."""
    path = RAW / ("wikipedia_caucus_%s.json" % wiki_slug(title))
    if REFRESH or not path.exists():
        print("downloading Wikipedia:", title)
        q = urllib.parse.urlencode({"action": "parse", "page": title, "prop": "wikitext", "redirects": 1,
                                    "format": "json", "formatversion": 2})
        path.write_bytes(fetch(WIKIPEDIA_API + "?" + q))
    return json.loads(path.read_text())["parse"]["wikitext"]


def caucus_members(text, start, end, recent_only):
    """Link targets of the members listed between the two headings: the first link of each list item, or of the
    first cell of each table row."""
    m = re.search(start, text, re.M)
    if not m:
        raise SystemExit("caucus list heading not found: %s" % start)
    e = re.compile(end, re.M).search(text, m.end())
    section = text[m.end():e.start() if e else len(text)]
    out, prev = [], ""
    for line in section.splitlines():
        line = line.strip()
        first_cell = line.startswith("|") and not line.startswith(("|-", "|}", "|+")) and prev.startswith("|-")
        if line.startswith("*") or first_cell:
            link = re.search(r"\[\[([^\]|#]+)(?:\|[^\]]*)?\]\]", line)
            if link and (not recent_only or any(int(y) >= 2024 for y in re.findall(r"\b(20\d\d)\b", line))):
                out.append(link.group(1).strip())
        if line:
            prev = line
    return out


def load_page_qids(titles):
    """Wikidata item of each Wikipedia page title (following redirects), cached in data/raw/wikipedia_caucus_qids.json."""
    path = RAW / "wikipedia_caucus_qids.json"
    have = {} if REFRESH or not path.exists() else json.loads(path.read_text())
    todo = sorted({t for t in titles if t not in have})
    for n in range(0, len(todo), 50):
        batch = todo[n:n + 50]
        q = urllib.parse.urlencode({"action": "query", "titles": "|".join(batch), "prop": "pageprops",
                                    "ppprop": "wikibase_item", "redirects": 1, "format": "json", "formatversion": 2})
        res = json.loads(fetch(WIKIPEDIA_API + "?" + q))["query"]
        alias = {t: t for t in batch}
        for key in ("normalized", "redirects"):
            for r in res.get(key, []):
                for t, a in alias.items():
                    if a == r["from"]:
                        alias[t] = r["to"]
        qid = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in res.get("pages", [])}
        for t in batch:
            have[t] = qid.get(alias[t])
    if todo:
        print("looked up %d Wikipedia pages' Wikidata items" % len(todo))
        path.write_text(json.dumps(have, indent=0, sort_keys=True))
    return have


def caucus_ideologies():
    """MNIS id -> [(ideology, list description)] from the caucus lists."""
    qid_mnis = {}
    for r in json.loads((RAW / "wikidata_mps_2024.json").read_text()):
        qid_mnis[r["item"].rsplit("/", 1)[-1]] = r["id"]
    lists = []
    for page, ideo, start, end, what in CAUCUSES:
        members = caucus_members(load_caucus_page(page), start, end, what in CAUCUS_NEEDS_RECENT_YEAR)
        lists.append((ideo, what, members))
    qids = load_page_qids([t for _, _, ms in lists for t in ms])
    found = {}
    for ideo, what, members in lists:
        n = 0
        for t in members:
            mid = qid_mnis.get(qids.get(t) or "")
            if mid:
                found.setdefault(mid, []).append((ideo, what))
                n += 1
        print("caucus list %-75s %3d listed, %3d of them 2024 MPs" % (what, len(members), n))
    return found


def seeded_choice(char_id, weights):
    roll = int(hashlib.sha256(("wm_ideo:" + char_id).encode()).hexdigest(), 16) % 100
    for ideo, w in weights:
        if roll < w:
            return ideo
        roll -= w
    raise AssertionError("ideology weights must add up to 100")


def assign_ideology(c, caucus, leaders):
    """(ideology key or NOT_STATED, source) for a character. Party leaders, former Prime Ministers and the other
    leaders outside the Commons take their party's mainstream unless a list or public record says otherwise: the
    seeded variation is for the backbenches."""
    if c["speaker"]:
        return NOT_STATED, "the Speaker: impartial"
    sid = c["id"].split("_", 2)[2]
    if sid in MANUAL_IDEOLOGY:
        return MANUAL_IDEOLOGY[sid][0], "public record: " + MANUAL_IDEOLOGY[sid][1]
    party = c["party"]
    hits = caucus.get(c["mnis"]) if c["mnis"] else None
    if hits:
        ideos = sorted({i for i, _ in hits})
        if len(ideos) == 1 and (party is None or ideos[0] in PARTY_RANGE[party]):
            return ideos[0], "caucus: " + "; ".join(sorted({w for _, w in hits}))
        why = ("conflicting caucus lists (%s)" % ", ".join(sorted({w for _, w in hits})) if len(ideos) > 1 else
               "caucus %s outside the party's range" % ideos[0])
    else:
        why = None
    if party is None:
        former = INDEPENDENT_FORMER_PARTY.get(c["seat"])
        if former:
            return PARTY_RANGE[former[0]][0], "independent, %s: that party's mainstream" % former[1]
        return INDEPENDENT_DEFAULT, "independent, no former party known: the neutral centre" + (" (%s)" % why if why else "")
    if party in PARTY_FALLBACK and c["id"] not in leaders and not c["id"].startswith("wm_char_"):
        ideo = seeded_choice(c["id"], PARTY_FALLBACK[party])
        return ideo, "party fallback (seeded within the %s range)%s" % (party, " after " + why if why else "")
    return PARTY_RANGE[party][0], "party fallback (the %s mainstream)%s" % (party, " after " + why if why else "")


def seat_ideology(c):
    """A seat's ideology: the mainstream ideology of the party that won it in 2024; an independent's own; the
    Speaker's seat is Not Stated."""
    if c["speaker"]:
        return NOT_STATED
    if c["party"]:
        return PARTY_RANGE[c["party"]][0]
    return c["ideology"]


def write_province_faiths(seat_faith):
    """Sets each seat's baronies' faith in the province history (as tools/map/build_map.py writes it)."""
    titles = (MOD / "common/landed_titles/00_westminster_titles.txt").read_text(encoding="utf-8-sig")
    prov_seat, seat = {}, None
    for line in titles.splitlines():
        m = re.match(r"^\t*c_([a-z0-9_]+) = \{", line)
        if m:
            seat = m.group(1)
        m = re.match(r"^\t*province = (\d+)", line)
        if m and seat:
            prov_seat[int(m.group(1))] = seat
    changed = 0
    for path in sorted((MOD / "history/provinces").glob("k_*.txt")):
        text = path.read_text(encoding="utf-8-sig")

        def one(m):
            nonlocal changed
            s = prov_seat.get(int(m.group(1)))
            f = seat_faith.get(s, NOT_STATED) if s else NOT_STATED
            changed += 1
            return "%s%s" % (m.group(0)[:m.start(2) - m.start(0)], f)
        new = re.sub(r"^(\d+) = \{[^\n]*\n(?:\t[^\n]*\n)*?\tfaith = ([a-z_]+)", one, text, flags=re.M)
        if new != text:
            write(path, new)
    return changed


# Party wings (common/scripted_effects/wm_wing_effects.txt) follow ideology: build_ideology.wing_for. Party leaders
# stand above the wings.
# ------------------------------------------------------------------------------------------------ names

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)
# The cultures' name lists (vanilla common/culture/name_lists), overridden by key with modern full names
NAME_LISTS = {"english": ("name_list_english", "00_west_germanic.txt"), "scottish": ("name_list_scottish", "00_west_germanic.txt"),
              "welsh": ("name_list_welsh", "00_brythonic.txt"), "irish": ("name_list_irish", "00_goidelic.txt")}
NAMES_PER_GENDER = 80
# Common surnames by nation (not the MPs' own, so a new character isn't taken for a famous MP's relative)
SURNAMES = {
    "english": "Smith Jones Taylor Brown Williams Wilson Johnson Davies Robinson Wright Thompson Evans Walker White Roberts "
               "Green Hall Wood Jackson Clarke Patel Khan Lewis Harris Martin Cooper King Lee Baker Harrison Morgan Allen "
               "Clark Scott Young Mitchell Turner Hill Moore Ward Parker Price Bennett Shaw Holmes Mills Ahmed Begum Hussain "
               "Ali Singh Kaur Okafor Mensah Adeyemi Chen Nowak Kowalski Murray Fletcher Lawson Barnes Fisher Hughes Dixon "
               "Pearce Knight Marsh Gibson Hart Hunt Ellis Webb Rowe Dawson Booth Atkins Holt Brooks Carter Hayes Nash".split(),
    "scottish": "Smith Brown Wilson Campbell Stewart Thomson Robertson Anderson MacDonald Scott Reid Murray Taylor Clark "
                "Ross Watson Morrison Paterson Young Mitchell Walker Fraser Miller McDonald Gray Henderson Hamilton Johnston "
                "Duncan Graham Ferguson Kerr Davidson Bell Cameron Kelly Martin MacKenzie Grant Allan Simpson McLean Black "
                "Hunter Wallace Russell Gibson Sinclair Munro Craig Baird Dunlop Rennie Shaw Ahmed".split(),
    "welsh": "Jones Williams Davies Evans Thomas Roberts Hughes Lewis Morgan Griffiths Edwards Owen Price Jenkins James "
             "Rees Phillips Powell Pritchard Parry Morris Lloyd Howells Watkins Bowen Pugh Vaughan Rowlands Prosser "
             "Llewellyn Harries Probert Gwynne Meredith Bevan Cadwaladr Pryce Hopkins Rogers Walters".split(),
    "irish": "Murphy Kelly O'Neill Doherty Quinn McLaughlin Wilson Campbell Smyth Gallagher Brennan O'Hara Devlin "
             "McCann Boyle Maguire Hughes Burns Johnston Moore Thompson Stewart Robinson Patterson Graham Kennedy "
             "McKenna Lynch Donnelly Hamilton Montgomery Bell Mulholland O'Reilly Gilmore Ferguson McCartney Rafferty "
             "Agnew Henderson".split(),
}


def vanilla_block(text, start, key):
    """The text of `key = { ... }` inside the block that starts at `start` (balanced braces), or None."""
    m = re.compile(r"\n\s*%s\s*=\s*\{" % key).search(text, start)
    if not m:
        return None
    depth, i = 0, text.index("{", m.start())
    for j in range(i, len(text)):
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        if depth == 0:
            return text[m.start():j + 1].strip()
    return None


def write_name_lists(chars):
    """Name lists for the four cultures in which every name is a whole modern name ("Priya Hughes"), made by pairing
    the 2024 MPs' given names of that nation with common surnames (never a real MP's own pair). New characters (by-election
    winners, activists, children) then carry a surname although their house is their party. Children aren't named
    after relatives (all the *_name_chance values are 0): no one is born "Keir Starmer". Returns the loc lines."""
    import random
    real = {(c["given"], c["family"]) for c in chars}
    by_culture = {}
    for c in chars:
        by_culture.setdefault(c["culture"], []).append(c)
    loc = ["", " # Name lists (common/culture/name_lists/wm_name_lists.txt): whole modern names"]
    out = [GEN, "# The cultures' name lists, overridden by key (vanilla's are in 00_west_germanic.txt, 00_brythonic.txt and\n"
           "# 00_goidelic.txt). Every name is a whole name, made from the 2024 MPs' given names and common surnames, because a\n"
           "# character's house is their party and the name formats don't show it (tools/ui/build_colleagues.py).\n"]
    english = by_culture["english"]
    for culture, (list_key, vfile) in NAME_LISTS.items():
        people = by_culture.get(culture, [])
        rnd = random.Random("wm_names_" + culture)
        surnames = sorted(set(SURNAMES[culture]))
        lists = {}
        for g, female in (("m", False), ("f", True)):
            given = sorted({c["given"] for c in people if c["female"] == female})
            if len(given) < 20:
                given = sorted(set(given) | {c["given"] for c in english if c["female"] == female})
            names = []
            while len(names) < NAMES_PER_GENDER:
                pair = (rnd.choice(given), rnd.choice(surnames))
                if pair not in real and pair not in names:
                    names.append(pair)
            keys = []
            for i, (gv, sn) in enumerate(names):
                k = "wm_gn_%s_%s_%d" % (culture, g, i)
                keys.append(k)
                loc.append(' %s: "%s %s"' % (k, gv.replace('"', "'"), sn.replace('"', "'")))
            lists[g] = keys
        dyn_keys = []
        for sn in surnames[:120]:
            k = "wm_sn_" + key(sn)
            if k not in dyn_keys:
                dyn_keys.append(k)
                if (' %s:' % k) not in "\n".join(loc):
                    loc.append(' %s: "%s"' % (k, sn.replace('"', "'")))
        vtext = (GAME / "common/culture/name_lists" / vfile).read_text(encoding="utf-8-sig")
        merc = vanilla_block(vtext, vtext.index(list_key + " = {"), "mercenary_names")

        def wrap(ks):
            return "\n".join("\t\t" + " ".join(ks[i:i + 6]) for i in range(0, len(ks), 6))
        out.append("%s = {\n\tcadet_dynasty_names = {\n%s\n\t}\n\tdynasty_names = {\n%s\n\t}\n\tmale_names = {\n%s\n\t}\n"
                   "\tfemale_names = {\n%s\n\t}\n\tdynasty_of_location_prefix = \"dynnp_of\"\n\n"
                   "\t# Nobody is named after a relative: every name is a whole name\n"
                   "\tpat_grf_name_chance = 0\n\tmat_grf_name_chance = 0\n\tfather_name_chance = 0\n"
                   "\tpat_grm_name_chance = 0\n\tmat_grm_name_chance = 0\n\tmother_name_chance = 0\n%s}\n"
                   % (list_key, wrap(dyn_keys), wrap(dyn_keys), wrap(lists["m"]), wrap(lists["f"]),
                      ("\n\t" + merc + "\n") if merc else ""))
    write(MOD / "common/culture/name_lists/wm_name_lists.txt", "\n".join(out))
    return loc


# ------------------------------------------------------------------------------------------------ party houses

PARTY_CULTURE = {"snp": "scottish", "plaid": "welsh", "sinn_fein": "irish", "dup": "irish", "sdlp": "irish",
                 "alliance": "irish", "uup": "irish", "tuv": "irish"}


def write_party_houses(chars):
    """Party dynasties and houses, the per-party script (house switch, game-start setup, founding slots), the
    Cross the Floor / Found a Party decisions and their localization."""
    dyn = [GEN, "# One dynasty per party, each with one house (common/dynasty_houses/wm_party_houses.txt). A character's\n"
           "# house is their party; the royal family keeps its own (wm_royal_dynasties.txt). Founded parties get a new\n"
           "# dynasty in play (create_dynasty, wm_party_effects.txt).\n"]
    hs = [GEN, "# Each party's house: every member is in it (history/characters/wm_2024_mps.txt, set_house in play).\n"
          "# Coats of arms: common/coat_of_arms/coat_of_arms/wm_party_arms.txt (tools/ui/build_party_arms.py).\n"]
    loc = ["l_english:", " # Generated by westminster/tools/data/build_2024.py - edit there."]
    houses = [(p[0], p[2]) for p in PARTIES]
    for pk, name in houses:
        dyn.append("wm_dyn_party_%s = {\n\tname = \"wm_dyn_party_%s\"\n\tculture = %s\n}" % (pk, pk, PARTY_CULTURE.get(pk, "english")))
        hs.append("wm_house_party_%s = {\n\tname = \"wm_house_party_%s\"\n\tdynasty = wm_dyn_party_%s\n}" % (pk, pk, pk))
        loc.append(' wm_dyn_party_%s: "%s"' % (pk, name))
        loc.append(' wm_house_party_%s: "%s"' % (pk, name))
    dyn.append("wm_dyn_independent = {\n\tname = \"wm_dyn_independent\"\n\tculture = english\n}")
    hs.append("%s = {\t# independents and the Speaker\n\tname = \"%s\"\n\tdynasty = wm_dyn_independent\n}" % (INDEPENDENT_HOUSE, INDEPENDENT_HOUSE))
    loc.append(' wm_dyn_independent: "Independent"')
    loc.append(' %s: "Independent"' % INDEPENDENT_HOUSE)
    for slot, name, _, _ in NEW_PARTIES:
        loc.append(' wm_party_%s_house: "%s"' % (slot, name))
    write(MOD / "common/dynasties/wm_party_dynasties.txt", "\n".join(dyn) + "\n")
    write(MOD / "common/dynasty_houses/wm_party_houses.txt", "\n".join(hs) + "\n")

    # ---- script
    e = [GEN, "# Parties are houses (see wm_party_effects.txt for joining, leaving and founding a party).\n"]
    e.append("# Game start (wm_party_on_actions.txt): each party's house knows its party (var:wm_house_party on the house)\n"
             "# and the party leader heads the house.\nwm_party_houses_init_effect = {")
    for pk, _ in houses:
        e.append("\thouse:wm_house_party_%s ?= {\n\t\tset_variable = { name = wm_house_party value = title:k_party_%s }\n\t}\n"
                 "\ttitle:k_party_%s.holder ?= {\n\t\tsave_scope_as = wm_house_leader\n"
                 "\t\tif = {\n\t\t\tlimit = {\n\t\t\t\thouse ?= house:wm_house_party_%s\n\t\t\t\tis_house_head = no\n\t\t\t}\n"
                 "\t\t\thouse = { set_house_head = scope:wm_house_leader }\n\t\t}\n\t}" % (pk, pk, pk, pk))
    e.append("}\n")
    e.append("# Character: put them in the house of their party (var:wm_party); without a party, a member of a party's house\n"
             "# moves to the Independent house. Founded parties: the house of the party's leader.\nwm_party_sync_house_effect = {\n"
             "\tif = {\n\t\tlimit = { exists = var:wm_party }")
    for i, (pk, _) in enumerate(houses):
        e.append("\t\t%s = {\n\t\t\tlimit = { var:wm_party = title:k_party_%s }\n"
                 "\t\t\tif = {\n\t\t\t\tlimit = { NOT = { house ?= house:wm_house_party_%s } }\n"
                 "\t\t\t\tset_house = house:wm_house_party_%s\n\t\t\t}\n\t\t}" % ("if" if i == 0 else "else_if", pk, pk, pk))
    e.append("\t\telse_if = {\n\t\t\tlimit = {\n\t\t\t\texists = var:wm_party.holder.house\n"
             "\t\t\t\tvar:wm_party.holder.house.var:wm_house_party ?= var:wm_party\n\t\t\t}\n"
             "\t\t\tif = {\n\t\t\t\tlimit = { NOT = { house ?= var:wm_party.holder.house } }\n"
             "\t\t\t\tset_house = var:wm_party.holder.house\n\t\t\t}\n\t\t}\n\t}")
    e.append("\telse_if = {\n\t\tlimit = {\n\t\t\thouse ?= { has_variable = wm_house_party }\n\t\t}\n"
             "\t\tset_house = house:%s\n\t}\n"
             "\t# Their ideology fits their party (wm_ideo_effects.txt): crossing the floor or being elected moves it\n"
             "\twm_ideo_fit_party_effect = yes\n}\n" % INDEPENDENT_HOUSE)
    all_parties = [(p[0], p[2]) for p in PARTIES] + [(s[0], s[1]) for s in NEW_PARTIES]
    e.append("# Cross the Floor (wm_party_decisions.txt): the party picked in the decision's list (scope:wm_join_<party>).\n"
             "wm_party_join_chosen_effect = {")
    for i, (pk, _) in enumerate(all_parties):
        e.append("\t%s = {\n\t\tlimit = { scope:wm_join_%s ?= yes }\n\t\twm_party_join_effect = { PARTY = title:k_party_%s }\n\t}"
                 % ("if" if i == 0 else "else_if", pk, pk))
    e.append("\telse_if = {\n\t\tlimit = { scope:wm_join_independent ?= yes }\n\t\twm_party_leave_effect = yes\n\t}\n}\n")
    e.append("# Found a Party: the first free slot (k_party_new_<n> with no holder).\nwm_party_found_effect = {")
    for i, (slot, *_r) in enumerate(NEW_PARTIES):
        e.append("\t%s = {\n\t\tlimit = { NOT = { exists = title:k_party_%s.holder } }\n\t\twm_party_found_in_slot_effect = { SLOT = %s }\n\t}"
                 % ("if" if i == 0 else "else_if", slot, slot))
    e.append("}")
    write(MOD / "common/scripted_effects/wm_party_houses.txt", "\n".join(e) + "\n")
    write(MOD / "common/scripted_triggers/wm_party_houses.txt", GEN +
          "# A slot for founding a party is free (wm_party_found_effect)\nwm_party_free_slot_trigger = {\n\tOR = {\n" +
          "".join("\t\tNOT = { exists = title:k_party_%s.holder }\n" % s[0] for s in NEW_PARTIES) + "\t}\n}\n")

    # ---- decisions
    items = []
    for pk, name in all_parties:
        items.append("\t\titem = {\n\t\t\tvalue = wm_join_%s\n\t\t\tis_shown = {\n\t\t\t\texists = title:k_party_%s.holder\n"
                     "\t\t\t\tNOT = { var:wm_party ?= title:k_party_%s }\n\t\t\t}\n"
                     "\t\t\tcurrent_description = wm_join_%s_desc\n\t\t\tlocalization = wm_join_%s\n\t\t\tai_chance = { value = 1 }\n\t\t}"
                     % (pk, pk, pk, pk, pk))
        loc.append(' wm_join_%s: "%s"' % (pk, name))
        loc.append(' wm_join_%s_desc: "Cross the floor to the %s, led by [GetTitleByKey(\'k_party_%s\').GetHolder.GetName]."'
                   % (pk, name, pk))
    items.append("\t\titem = {\n\t\t\tvalue = wm_join_independent\n\t\t\tis_shown = { has_variable = wm_party }\n"
                 "\t\t\tcurrent_description = wm_join_independent_desc\n\t\t\tlocalization = wm_join_independent\n"
                 "\t\t\tai_chance = { value = 0 }\n\t\t}")
    loc.append(' wm_join_independent: "Sit as an independent"')
    loc.append(' wm_join_independent_desc: "Resign the party whip and sit as an independent, answering to no party leader."')
    write(MOD / "common/decisions/wm_party_decisions.txt", DECISIONS.replace("$ITEMS$", "\n".join(items)))
    loc += DECISIONS_LOC
    write(MOD / "localization/english/wm_party_houses_l_english.yml", "\n".join(loc) + "\n")


DECISIONS = GEN + """# Parties are houses (wm_party_effects.txt). Players only: the AI doesn't cross the floor or found parties.

# Join another party: the character moves to its house, takes its whip (var:wm_party) and serves its leader.
wm_party_join_decision = {
	picture = {
		reference = "gfx/interface/illustrations/loading_screens/wm_commons.dds"
	}
	decision_group_type = major
	sort_order = 80
	ai_check_interval = 0
	cooldown = { years = 1 }

	desc = wm_party_join_decision_desc
	selection_tooltip = wm_party_join_decision_tooltip
	confirm_text = wm_party_join_decision_confirm

	is_shown = {
		is_adult = yes
		NOT = { has_character_flag = wm_speaker }
		OR = {
			has_variable = wm_party
			wm_is_mp_trigger = yes
		}
		NOT = { var:wm_party.holder ?= this }			# a party leader leads; they don't cross the floor
		NOT = { title:e_united_kingdom.holder ?= this }
	}

	is_valid_showing_failures_only = {
		is_imprisoned = no
	}

	cost = {
		prestige = 100
	}

	widget = {
		gui = "decision_view_widget_option_list_generic"
		controller = decision_option_list_controller
		decision_to_second_step_button = "wm_party_join_decision_choose"
		show_from_start = yes

$ITEMS$
	}

	effect = {
		custom_tooltip = wm_party_join_decision_effect_tt
		hidden_effect = {
			wm_party_join_chosen_effect = yes
		}
	}

	ai_potential = {
		always = no
	}

	ai_will_do = {
		base = 0
	}
}

# Found a new party: a new house with a made-up emblem, and a party title (a free slot, k_party_new_<n>) it leads.
wm_party_found_decision = {
	picture = {
		reference = "gfx/interface/illustrations/loading_screens/wm_commons.dds"
	}
	decision_group_type = major
	sort_order = 79
	ai_check_interval = 0

	desc = wm_party_found_decision_desc
	selection_tooltip = wm_party_found_decision_tooltip
	confirm_text = wm_party_found_decision_confirm

	is_shown = {
		wm_is_mp_trigger = yes
		NOT = { has_character_flag = wm_speaker }
		NOT = { var:wm_party.holder ?= this }
		NOT = { title:e_united_kingdom.holder ?= this }
	}

	is_valid = {
		custom_tooltip = {
			text = wm_party_found_decision_slot_tt
			wm_party_free_slot_trigger = yes
		}
		custom_tooltip = {
			text = wm_party_found_decision_head_tt
			is_house_head = no
			is_dynast = no
		}
	}

	is_valid_showing_failures_only = {
		is_imprisoned = no
	}

	cost = {
		prestige = 500
	}

	effect = {
		custom_tooltip = wm_party_found_decision_effect_tt
		hidden_effect = {
			wm_party_found_effect = yes
		}
	}

	ai_potential = {
		always = no
	}

	ai_will_do = {
		base = 0
	}
}
"""

DECISIONS_LOC = [
    "",
    " # Decisions (common/decisions/wm_party_decisions.txt)",
    ' wm_party_join_decision: "Cross the Floor"',
    ' wm_party_join_decision_desc: "Leave my party for another. My old colleagues will not forgive it quickly, but a new party means a new leader, a new whip and new friends."',
    ' wm_party_join_decision_tooltip: "Join another party, or sit as an independent"',
    ' wm_party_join_decision_confirm: "Cross the floor"',
    ' wm_party_join_decision_choose: "Choose a party"',
    ' wm_party_join_decision_effect_tt: "You join the party you chose: you take its whip, join its ranks (your [house|E]) and serve its leader. Your old party leader will remember it."',
    ' wm_party_found_decision: "Found a Party"',
    ' wm_party_found_decision_desc: "The old parties have failed. Start a new one, with a name, an emblem and a leader: me."',
    ' wm_party_found_decision_tooltip: "Found a new party and lead it"',
    ' wm_party_found_decision_confirm: "Launch the party"',
    ' wm_party_found_decision_slot_tt: "There is room for another party (at most six new parties)"',
    ' wm_party_found_decision_head_tt: "Not the head of your party\'s [house|E]"',
    ' wm_party_found_decision_effect_tt: "You found a new party and become its leader, serving the Prime Minister. It has its own [house|E] and emblem, and your old party leader will remember it. New parties don\'t yet stand in the polls."',
    "",
    " # Opinions (common/opinion_modifiers/wm_party_opinions.txt)",
    ' wm_party_crossed_floor_opinion: "Crossed the floor"',
    ' wm_party_split_opinion: "Split the party"',
]


# ------------------------------------------------------------------------------------------------ main

def main():
    RAW.mkdir(parents=True, exist_ok=True)
    rows = load_candidacies()
    ons = load_ons_names()

    titles_txt = (MOD / "common/landed_titles/00_westminster_titles.txt").read_text(encoding="utf-8-sig")
    counties = set(re.findall(r"^\t*(c_[a-z0-9_]+) = \{", titles_txt, re.M))

    # The seat of each 2024 constituency: by ONS code -> ONS name -> key (as the map was built), else by name
    by_seat = {}
    unmatched = []
    for r in rows:
        code = r["Constituency geographic code"]
        name = ons.get(code) or r["Constituency name"]
        seat = key(name)
        if "c_" + seat not in counties:
            seat = key(r["Constituency name"])
        if "c_" + seat not in counties:
            unmatched.append((code, r["Constituency name"]))
            continue
        by_seat.setdefault(seat, []).append(r)
    unmatched = sorted(set(unmatched))
    via_code = sum(1 for s, rs in by_seat.items() if key(ons.get(rs[0]["Constituency geographic code"], "")) == s)

    winners = {}
    for seat, rs in by_seat.items():
        w = [r for r in rs if r["Candidate result position"] == "1"]
        assert len(w) == 1, seat
        winners[seat] = w[0]

    ids = sorted({w["Candidate MNIS ID"] for w in winners.values() if w["Candidate MNIS ID"]})
    members = load_members(ids)
    wikidata = load_wikidata(ids)

    # ---------------------------------------------------------------- per-seat results CSV
    out_rows = []
    for seat in sorted(by_seat):
        rs = by_seat[seat]
        r0 = rs[0]
        valid = int(r0["Election valid vote count"])
        share = dict.fromkeys(SHARE_COLS, 0)
        for r in rs:
            if r["Candidate is standing as Commons Speaker"] == "true":
                col = "Spk"
            elif r["Candidate is standing as independent"] == "true":
                col = "Ind"
            else:
                col = r["Main party abbreviation"] if r["Main party abbreviation"] in SHARE_COLS else "Oth"
            share[col] += int(r["Candidate vote count"])
        w = winners[seat]
        out_rows.append({
            "ons_code": r0["Constituency geographic code"], "title": "c_" + seat, "constituency": r0["Constituency name"],
            "nation": r0["Country name"], "region": r0["English region name"], "electorate": r0["Electorate"],
            "valid_votes": valid, "turnout": "%.4f" % (valid / int(r0["Electorate"])),
            "winner": "%s %s" % (w["Candidate given name"], w["Candidate family name"]),
            "winner_party": "Spk" if w["Candidate is standing as Commons Speaker"] == "true" else
            ("Ind" if w["Candidate is standing as independent"] == "true" else w["Main party abbreviation"]),
            "result": r0["Election result summary"], "majority": w["Majority"],
            **{"share_" + c: "%.4f" % (share[c] / valid) for c in SHARE_COLS}})
    # (written below, once the winners' ideologies are known)

    # ---------------------------------------------------------------- characters
    chars = []          # dicts: id, given, family, female, birth, culture, party, flag, seat
    precision = {}
    for seat in sorted(winners):
        w = winners[seat]
        mid = w["Candidate MNIS ID"]
        g = (members.get(mid) or {}).get("gender")
        if g not in ("M", "F"):
            g = {"Q6581072": "F", "Q6581097": "M"}.get(wikidata.get(mid, {}).get("gender"), "M")
        birth, prec = birth_date(wikidata.get(mid), seat)
        precision[prec] = precision.get(prec, 0) + 1
        speaker = w["Candidate is standing as Commons Speaker"] == "true"
        party = None if speaker or w["Candidate is standing as independent"] == "true" else PARTY_BY_ABBR[w["Main party abbreviation"]][0]
        chars.append({"id": "wm_mp_" + seat, "given": w["Candidate given name"].strip(), "family": w["Candidate family name"].strip(),
                      "female": g == "F", "birth": birth, "culture": CULTURE[w["Constituency geographic code"][0]],
                      "party": party, "speaker": speaker, "seat": seat, "mnis": mid,
                      "coop": w["Adjunct party abbreviation"] == "Co-op"})
    for sid, given, family, female, birth, culture, party, office in EXTRAS:
        chars.append({"id": "wm_char_" + sid, "given": given, "family": family, "female": female, "birth": birth,
                      "culture": culture, "party": party, "speaker": False, "seat": None, "mnis": None, "office": office,
                      "coop": False})
    for sid, given, family, female, birth, culture, party, peer in FORMER_PMS:
        chars.append({"id": "wm_char_" + sid, "given": given, "family": family, "female": female, "birth": birth,
                      "culture": culture, "party": party, "speaker": False, "seat": None, "mnis": None, "office": None,
                      "coop": False, "former_pm": True, "peer": peer})
    for sid, given, family, female, birth, culture, party, *_ in ACTIVISTS:
        chars.append({"id": "wm_char_" + sid, "given": given, "family": family, "female": female, "birth": birth,
                      "culture": culture, "party": party, "speaker": False, "seat": None, "mnis": None, "office": None,
                      "coop": False, "activist": True})
    by_id = {c["id"]: c for c in chars}


    # Party leaders: check the seat holds the expected person
    leader = {}
    for p in PARTIES:
        lid = p[6] if p[6].startswith("wm_char_") else "wm_mp_" + p[6]
        c = by_id[lid]
        assert c["family"] == p[7] and c["party"] == p[0], (p, c)
        leader[p[0]] = lid
    pm = leader["labour"]

    # Ideologies (faiths): caucus lists, public record, else the party's range
    caucus = caucus_ideologies()
    for c in chars:
        c["ideology"], c["ideology_source"] = assign_ideology(c, caucus, set(leader.values()))
    seat_faith = {c["seat"]: faith_key(seat_ideology(c)) for c in chars if c["seat"]}
    for row in out_rows:
        row["winner_ideology"] = seat_faith[row["title"][2:]]
    with open(ROOT / "data/ge2024_results.csv", "w", newline="", encoding="utf-8") as f:
        wr = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        wr.writeheader()
        wr.writerows(out_rows)
    print("wrote westminster/data/ge2024_results.csv")

    spouses, spouse_report = make_spouses(chars, SURNAMES, int(START.split(".")[0]), RAW, fetch, REFRESH)
    spouse_of = {sp["mp"]: sp for sp in spouses}

    lines = [GEN, "# The MPs elected at the general election of 4 July 2024, the leaders who aren't MPs, the former Prime\n"
             "# Ministers and the MPs' spouses (fictional: build_spouses.py).\n"
             "# Party membership is var:wm_party = title:k_party_<party> (set on the start date) and the party's house.\n"
             "# Religion is political ideology (tools/data/build_ideology.py): each MP's comes from a self-declared caucus\n"
             "# list where one is obvious, otherwise the party's range (seeded); the reason is in the comment after it.\n"
             "# Labour and Conservative MPs' wings (var:wm_wing, var:wm_commons_wing) follow their ideology. The royal\n"
             "# family, the spouses and the Speaker are \"Not Stated\".\n"
             "# Each name is a localization key for the whole name (wm_names_l_english.yml).\n"]
    for c in chars:
        lines.append("%s = {\t# %s %s%s%s%s" % (c["id"], c["given"], c["family"], (" (MNIS %s)" % c["mnis"]) if c["mnis"] else "",
                                               (", " + c["seat"].replace("_", " ")) if c["seat"] else "",
                                               ", life peer" if c.get("peer") else ""))
        lines.append("\tname = %s" % name_key(c))
        if c["id"] in DNA_KEYS:
            lines.append("\tdna = %s\t# likeness: build_likenesses.py" % DNA_KEYS[c["id"]])
        lines.append("\tdynasty_house = %s" % house_of(c))
        if c["female"]:
            lines.append("\tfemale = yes")
        lines.append("\tculture = %s" % c["culture"])
        lines.append("\treligion = %s\t# %s" % (faith_key(c["ideology"]), c["ideology_source"]))
        lines.append("\t%s = { birth = yes }" % c["birth"])
        sp = spouse_of.get(c["id"])
        if sp:
            lines.append("\t%s = { %s = %s }" % (sp["married"], "add_matrilineal_spouse" if c["female"] else "add_spouse", sp["id"]))
        eff = []
        if c["party"]:
            eff.append("set_variable = { name = wm_party value = title:k_party_%s }" % c["party"])
            wing = (wing_for(c["ideology"], c["party"]) if c["seat"] and c["id"] not in leader.values()
                    and c["ideology"] != NOT_STATED else None)
            if wing:
                eff.append("set_variable = { name = wm_wing value = %d }" % wing[0])
                eff.append("set_variable = { name = wm_commons_wing value = %d }" % wing[1])
        if c["speaker"]:
            eff.append("add_character_flag = wm_speaker")
        if c.get("activist"):
            eff.append("set_variable = { name = wm_standing value = 20 }")	# joins the ladder at game start
        if c.get("former_pm"):
            lines.append("\t%s = {\n\t\temployer = %s" % (START, CROWN))
            lines.append("\t\teffect = {\n%s\n\t\t}\n\t}" % "\n".join("\t\t\t" + e for e in eff))
        elif eff:
            lines.append("\t%s = {\n\t\teffect = {\n%s\n\t\t}\n\t}" % (START, "\n".join("\t\t\t" + e for e in eff)))
        lines.append("}")
    lines.append("\n# The MPs' husbands and wives: invented people, never the real ones (build_spouses.py). Lowborn: a house\n"
                 "# would be a party.")
    for sp in spouses:
        lines.append("%s = {\t# %s %s, spouse of %s" % (sp["id"], sp["given"], sp["family"], sp["mp"]))
        lines.append("\tname = wm_name_%s" % sp["id"][3:])
        if sp["female"]:
            lines.append("\tfemale = yes")
        lines.append("\tculture = %s\n\treligion = wm_faith_not_stated\n\t%s = { birth = yes }\n}" % (sp["culture"], sp["birth"]))
    write(MOD / "history/characters/wm_2024_mps.txt", "\n".join(lines) + "\n")

    # ---------------------------------------------------------------- names, party dynasties and houses
    names = ["l_english:", " # Generated by westminster/tools/data/build_2024.py - edit there.",
             " # Character names: each is the whole name, so the house (the party) is never shown as a surname"]
    for c in chars:
        names.append(' %s: "%s %s"' % (name_key(c), c["given"].replace('"', "'"), c["family"].replace('"', "'")))
    names.append(" # The MPs' spouses (fictional)")
    for sp in spouses:
        names.append(' wm_name_%s: "%s %s"' % (sp["id"][3:], sp["given"].replace('"', "'"), sp["family"].replace('"', "'")))
    names += write_name_lists(chars)
    write(MOD / "localization/english/wm_names_l_english.yml", "\n".join(names) + "\n")
    write_party_houses(chars)
    # The old one-dynasty-per-character files
    for old in ("common/dynasties/wm_2024_dynasties.txt", "localization/english/wm_dynasties_l_english.yml"):
        if (MOD / old).exists():
            (MOD / old).unlink()
            print("removed", old)

    # ---------------------------------------------------------------- party titles
    pt = [GEN, "# Political parties: landless kingdom-tier titles held by the party leader (spike b).\n"
          "# MPs who are members carry var:wm_party = title:k_party_<name>; only they vote in and stand for leadership elections.\n"
          "# k_party_new_<n> are uncreated slots for parties founded in play (Found a Party, wm_party_decisions.txt).\n"]
    for p in PARTIES:
        pt.append("k_party_%s = {\n\tcolor = { %d %d %d }\n\tcapital = c_%s\n\tlandless = yes\n\tallow_domicile = no\n"
                  "\tno_automatic_claims = yes\n\tdefinite_form = yes\n\truler_uses_title_name = no\n}" % ((p[0],) + p[4] + (p[5],)))
        assert "c_" + p[5] in counties, p
    for slot, _, _, colour in NEW_PARTIES:
        pt.append("k_party_%s = {\n\tcolor = { %d %d %d }\n\tcapital = c_cities_of_london_and_westminster\n\tlandless = yes\n"
                  "\tallow_domicile = no\n\tno_automatic_claims = yes\n\tdefinite_form = yes\n\truler_uses_title_name = no\n}"
                  % ((slot,) + colour))
    assert "c_cities_of_london_and_westminster" in counties
    write(MOD / "common/landed_titles/10_wm_parties.txt", "\n".join(pt) + "\n")
    write(MOD / "common/landed_titles/31_wm_wales_gov.txt", GEN +
          "# The Welsh Government: a landless kingdom-tier title held by the First Minister of Wales (as k_gov_scotland).\n"
          "k_gov_wales = {\n\tcolor = { 200 16 46 }\n\tcapital = c_cardiff_south_and_penarth\n\tlandless = yes\n"
          "\tallow_domicile = no\n\tno_automatic_claims = yes\n\tdefinite_form = yes\n\truler_uses_title_name = no\n}\n")

    # Localization block in wm_parties_l_english.yml
    yml_path = MOD / "localization/english/wm_parties_l_english.yml"
    yml = yml_path.read_text(encoding="utf-8-sig")
    yml = re.sub(r"\n # BEGIN build_2024.*? # END build_2024\n", "\n", yml, flags=re.S)
    yml = "\n".join(l for l in yml.splitlines() if not re.match(r" (k_party_(labour|conservative)(_adj)?):", l)) + "\n"
    block = [" # BEGIN build_2024 (generated by westminster/tools/data/build_2024.py - edit there)"]
    for p in PARTIES:
        block.append(' k_party_%s: "%s"' % (p[0], p[2]))
        block.append(' k_party_%s_adj: "%s"' % (p[0], p[3]))
    for slot, name, adj, _ in NEW_PARTIES:
        block.append(' k_party_%s: "%s"' % (slot, name))
        block.append(' k_party_%s_adj: "%s"' % (slot, adj))
    block.append(' k_gov_wales: "Welsh Government"')
    block.append(" # END build_2024")
    write(yml_path, yml.rstrip("\n") + "\n" + "\n".join(block) + "\n")

    # ---------------------------------------------------------------- title history
    th = [GEN, "# Who holds what on %s: the Prime Minister holds the United Kingdom and its nations; each party is held by\n"
          "# its leader, who serves the Prime Minister; each MP holds their seat and serves their party leader. The Speaker\n"
          "# and independents serve the Prime Minister directly.\n" % START]

    def entry(title, holder, liege=None, extra=""):
        body = ["holder = %s" % holder]
        if liege:
            body.append('liege = "%s"' % liege)
        if extra:
            body.append(extra)
        th.append("%s = {\n\t%s = {\n%s\n\t}\n}" % (title, START, "\n".join("\t\t" + b for b in body)))

    for t in ("e_united_kingdom", "k_england", "k_scotland", "k_wales", "k_northern_ireland"):
        entry(t, pm)
    for p in PARTIES:
        entry("k_party_" + p[0], leader[p[0]], None if p[0] == "labour" else "e_united_kingdom",
              "succession_laws = { wm_party_succession_law }")
    for c in chars:
        if c.get("office"):
            entry(c["office"], c["id"], "e_united_kingdom")
    leaders = set(leader.values())
    for c in chars:
        if not c["seat"]:
            continue
        if c["id"] == pm:
            liege = None
        elif c["id"] in leaders or not c["party"]:
            liege = "e_united_kingdom"
        else:
            liege = "k_party_" + c["party"]
        entry("c_" + c["seat"], c["id"], liege)
    write(MOD / "history/titles/wm_2024_seats.txt", "\n".join(th) + "\n")

    # ---------------------------------------------------------------- bookmark
    title_of = {pm: "e_united_kingdom"}
    title_of.update({lid: "k_party_" + p for p, lid in leader.items() if lid != pm})
    bm = [GEN + "bm_2024_starmer = {\n\tstart_date = %s\n\tis_playable = yes\n\tgroup = bm_group_2024\n\tweight = { value = 100 }\n" % START]
    bloc = ["l_english:", ' bm_2024_starmer: "2024: A Change of Government"',
            ' bm_2024_starmer_desc: "Labour has won the general election of 4 July 2024 with 411 seats, a majority of 174. '
            'Keir Starmer is Prime Minister; the Conservatives, reduced to 121 seats, must choose a new leader; the Liberal '
            'Democrats have their best result in a century; and Reform UK, the Greens and a group of independents have '
            'broken into the Commons.\\n\\n#bold Every one of the 650 MPs is playable.#!"',
            ' bm_group_2024: "2024"']
    descs = {
        "holborn_and_st_pancras": "Prime Minister with a landslide behind him and a full in-tray in front of him.",
        "richmond_and_northallerton": "Leader of the Opposition for now, after the Conservatives' worst defeat. His party will soon choose his successor.",
        "kingston_and_surbiton": "Leader of the Liberal Democrats, back as the third party with 72 seats.",
        "north_west_cambridgeshire": "The youngest MP in the new Parliament, elected in his early twenties. A long career lies ahead, if he wants it.",
    }
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ui"))
    from build_bookmark_screen import layout       # the same projection as the bookmark's map
    places = layout()
    for seat, name, anim, subheading, _ in FEATURED:
        c = by_id["wm_mp_" + seat]
        bk = "bookmark_2024_" + key(name)
        x, y = places[bk]
        y_, m_, d_ = c["birth"].split(".")
        bm.append("\tcharacter = {\n\t\tname = %s\n\t\tdynasty_house = %s\n\t\ttype = %s\n\t\tbirth = %s\n\t\ttitle = %s\n"
                  "\t\tdynasty_splendor_level = 1\n\t\tgovernment = feudal_government\n\t\tculture = %s\n\t\treligion = %s\n"
                  "\t\tdifficulty = \"BOOKMARK_CHARACTER_DIFFICULTY_%s\"\n\t\thistory_id = %s\n\t\tposition = { %d %d }\n"
                  "\t\tanimation = %s\n\t}" % (q(bk), house_of(c), "female" if c["female"] else "male", c["birth"],
                                               title_of.get(c["id"], "c_" + seat), c["culture"], faith_key(c["ideology"]),
                                               "EASY" if c["id"] == pm else ("MEDIUM" if c["id"] in leaders else "HARD"),
                                               c["id"], x, y, anim))
        bloc.append(' %s: "%s"' % (bk, name))
        bloc.append(' %s_subheading: "%s"' % (bk, subheading))
        bloc.append(' %s_desc: "%s"' % (bk, descs[seat]))
    # Activists aren't on the bookmark screen: 1.20 rejects bookmark_type, and a featured character must already
    # hold a title (an activist's campaign team is only created at game start). They're in the game regardless.
    for sid, given, family, female, birth, culture, party, seat, anim, (x, y), desc in ([] if True else ACTIVISTS):
        bk = "bookmark_2024_" + sid
        bm.append("\tcharacter = {\n\t\tname = %s\n\t\tdynasty_house = wm_house_party_%s\n\t\ttype = %s\n\t\tbirth = %s\n"
                  "\t\tbookmark_type = new_landless_adventurer\n\t\ttitle = c_%s\n"
                  "\t\tgovernment = landless_adventurer_government\n\t\tculture = %s\n\t\treligion = wm_faith_not_stated\n"
                  "\t\tdifficulty = \"BOOKMARK_CHARACTER_DIFFICULTY_HARD\"\n\t\thistory_id = wm_char_%s\n"
                  "\t\tposition = { %d %d }\n\t\tanimation = %s\n\t}"
                  % (q(bk), party, "female" if female else "male", birth, seat, culture, sid, x, y, anim))
        bloc.append(' %s: "%s %s"' % (bk, given, family))
        bloc.append(' %s_subheading: "Activist, %s"' % (bk, PARTY_KEY_NAME[party]))
        bloc.append(' %s_desc: "%s"' % (bk, desc))
    bm.append("}")
    write(MOD / "common/bookmarks/bookmarks/wm_bookmarks.txt", "\n".join(bm) + "\n")
    write(MOD / "localization/english/wm_bookmarks_l_english.yml", "\n".join(bloc) + "\n")

    # Old spike placeholders
    for old in ("history/characters/wm_spike.txt", "history/titles/wm_spike.txt", "localization/english/wm_spike_l_english.yml"):
        if (MOD / old).exists():
            (MOD / old).unlink()
            print("removed", old)

    # ---------------------------------------------------------------- report
    seats = {}
    for c in chars:
        if c["seat"]:
            k = "Speaker" if c["speaker"] else (c["party"] or "independent")
            seats[k] = seats.get(k, 0) + 1
    print("\nseats matched: %d of %d constituencies in the results (%d via ONS code), %d map counties"
          % (len(winners), len({r['Constituency geographic code'] for r in rows}), via_code, len(counties)))
    if unmatched:
        print("UNMATCHED:", unmatched)
    missing = sorted(counties - {"c_" + s for s in winners})
    if missing:
        print("map counties with no MP:", missing)
    print("seats by party:", ", ".join("%s %d" % kv for kv in sorted(seats.items(), key=lambda kv: -kv[1])))
    print("birth dates:", precision)
    print("women:", sum(c["female"] for c in chars if c["seat"]))
    print(spouse_report)
    print("likenesses referenced:", sum(1 for c in chars if c["id"] in DNA_KEYS))
    print("province history faiths set:", write_province_faiths(seat_faith))
    write_ideology_report(chars, spouses)


def write_ideology_report(chars, spouses):
    """tools/test_out/ideology_2024.txt: every politician's ideology and why, with counts."""
    from collections import Counter
    mps = [c for c in chars if c["seat"]]
    kind = lambda c: c["ideology_source"].split(":")[0].split(" (")[0].split(",")[0]  # noqa: E731
    by = Counter(c["ideology"] for c in mps)
    how = Counter(kind(c) for c in mps)
    out = ["# The 2024 bookmark's ideologies, generated by westminster/tools/data/build_2024.py.",
           "# Caucus lists: Wikipedia (en.wikipedia.org), text CC BY-SA 4.0; see westminster/data/README.md.", "",
           "MPs by ideology (650):"]
    for ideo, n in by.most_common():
        out.append("  %-24s %3d   (caucus %d, fallback %d)" % (
            IDEO[ideo][1] if ideo in IDEO else "Not Stated", n,
            sum(1 for c in mps if c["ideology"] == ideo and c["ideology_source"].startswith("caucus")),
            sum(1 for c in mps if c["ideology"] == ideo and not c["ideology_source"].startswith("caucus"))))
    out += ["", "MPs by source:"] + ["  %-40s %3d" % kv for kv in how.most_common()]
    out += ["", "Seats by ideology:"]
    seats = Counter(seat_ideology(c) for c in mps)
    out += ["  %-24s %3d" % (IDEO[k][1] if k in IDEO else "Not Stated", n) for k, n in seats.most_common()]
    out += ["", "Everyone (id, party, ideology, source):"]
    for c in chars:
        out.append("%s\t%s\t%s %s\t%s\t%s" % (c["id"], c["party"] or ("Speaker" if c["speaker"] else "independent"),
                                             c["given"], c["family"], faith_key(c["ideology"]), c["ideology_source"]))
    out.append("%d spouses: Not Stated" % len(spouses))
    path = ROOT / "tools/test_out/ideology_2024.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out) + "\n", encoding="utf-8")
    print("\n".join(out[3:out.index("Everyone (id, party, ideology, source):") - 1]))
    print("wrote", path.relative_to(ROOT.parent))


if __name__ == "__main__":
    main()
