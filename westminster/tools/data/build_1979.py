#!/usr/bin/env python3
"""Build the 4 May 1979 Thatcher bookmark from dated parliamentary records.

The 1979 Commons membership comes from mySociety's ParlParse export of UK Parliament data. Party affiliations are
resolved against the UK Parliament Members API at the bookmark date and cached in data/raw. Historical constituencies
are mapped once, deterministically, onto Westminster's fixed 2024 map; the fifteen additional modern seats receive
notional backbenchers so every map county remains playable.
"""
import concurrent.futures
import csv
import hashlib
import json
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
MOD = ROOT / "westminster"
RAW = ROOT / "data" / "raw"
START = "1979.5.4"
DATE = "1979-05-04T12:00:00.000Z"
UA = "WestminsterCK3Mod/0.5 (historical bookmark data build)"
PEOPLE_URL = "https://raw.githubusercontent.com/mysociety/parlparse/master/members/people.json"
DOB_URL = "https://raw.githubusercontent.com/mysociety/parlparse/master/members/dates-of-birth.xml"
SEARCH_URL = "https://members-api.parliament.uk/api/Members/SearchHistorical"

PARTY = {
    "Conservative": "conservative", "Labour": "labour", "Liberal": "lib_dem",
    "Scottish National Party": "snp", "SNP": "snp", "Plaid Cymru": "plaid",
    "Ulster Unionist Party": "uup", "UUP": "uup", "Democratic Unionist Party": "dup", "DUP": "dup",
    "Social Democratic and Labour Party": "sdlp", "SDLP": "sdlp",
    "Social Democratic & Labour Party": "sdlp",
}
IDEOLOGY = {
    "conservative": "wm_ideo_one_nation", "labour": "wm_ideo_social_democrat",
    "lib_dem": "wm_ideo_liberal", "snp": "wm_ideo_scottish_nationalist", "plaid": "wm_ideo_welsh_nationalist",
    "uup": "wm_ideo_unionist", "dup": "wm_ideo_unionist", "sdlp": "wm_ideo_social_democrat",
}
LEADERS = {"Margaret Thatcher": "conservative", "James Callaghan": "labour", "David Steel": "lib_dem"}
PARTY_LEADERS = {
    **LEADERS, "Gordon Wilson": "snp", "Dafydd Wigley": "plaid", "James Molyneaux": "uup",
    "Ian Paisley": "dup", "Gerry Fitt": "sdlp",
}
FEATURED = [
    ("Margaret Thatcher", "Prime Minister", "personality_bold", "EASY",
     "Britain's first woman Prime Minister begins work with a Commons majority and a programme to transform the economy."),
    ("James Callaghan", "Leader of the Opposition", "disapproval", "MEDIUM",
     "Labour's defeated Prime Minister must hold his party together after the Winter of Discontent."),
    ("David Steel", "Leader of the Liberal Party", "personality_rational", "HARD",
     "The Liberal leader has eleven MPs and the difficult task of making a third force matter."),
    ("Michael Foot", "Labour MP for Ebbw Vale", "personality_compassionate", "HARD",
     "A leading voice of Labour's left, poised to shape the party's response to Thatcherism."),
    ("Geoffrey Howe", "Chancellor of the Exchequer", "personality_rational", "MEDIUM",
     "The new Chancellor must turn radical economic promises into a workable first Budget."),
]
MANUAL_SEATS = {
    "Margaret Thatcher": "finchley_and_golders_green", "James Callaghan": "cardiff_south_and_penarth",
    "David Steel": "dumfriesshire_clydesdale_and_tweeddale", "Michael Foot": "blaenau_gwent_and_rhymney",
    "Geoffrey Howe": "east_surrey", "William Whitelaw": "penrith_and_solway",
    "Michael Heseltine": "henley_and_thame", "Keith Joseph": "leeds_north_east",
    "Nigel Lawson": "south_leicestershire", "Norman Tebbit": "chingford_and_woodford_green",
    "Ian Gilmour": "chesham_and_amersham", "John Nott": "st_ives", "Peter Walker": "worcester",
    "Denis Healey": "leeds_south", "Tony Benn": "bristol_south", "Shirley Williams": "hertford_and_stortford",
    "Dafydd Wigley": "dwyfor_meirionnydd", "James Molyneaux": "lagan_valley", "Enoch Powell": "south_down",
}
SIGNIFICANT_BIRTHS = {
    "Margaret Thatcher": "1925.10.13", "James Callaghan": "1912.3.27", "David Steel": "1938.3.31",
    "Michael Foot": "1913.7.23", "Geoffrey Howe": "1926.12.20", "William Whitelaw": "1918.6.28",
    "Michael Heseltine": "1933.3.21", "Keith Joseph": "1918.1.17", "Nigel Lawson": "1932.3.11",
    "Norman Tebbit": "1931.3.29", "Ian Gilmour": "1926.7.8", "John Nott": "1932.2.1",
    "Peter Walker": "1932.3.25", "Denis Healey": "1917.8.30", "Tony Benn": "1925.4.3",
    "Shirley Williams": "1930.7.27",
}


def fetch(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def cached(name, url):
    p = RAW / name
    if "--refresh" in sys.argv or not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(fetch(url))
    return p


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def display_name(person, date="1979-05-04"):
    names = person.get("other_names", [])
    valid = [n for n in names if n.get("note") == "Main" and n.get("start_date", "0000") <= date
             and n.get("end_date", "9999") >= date]
    n = (valid or [n for n in names if n.get("note") == "Main"] or names)[0]
    return (n.get("given_name", "") + " " + n.get("family_name", n.get("lordname", ""))).strip()


def party_for(name):
    q = urllib.parse.urlencode({"name": name, "dateToSearchFor": DATE, "take": 20})
    try:
        d = json.loads(fetch(SEARCH_URL + "?" + q, timeout=15))
        items = d.get("items", [])
        exact = [x["value"] for x in items if norm(x["value"].get("nameDisplayAs", "")) == norm(name)]
        v = (exact or [x["value"] for x in items])[0]
        return v.get("latestParty", {}).get("name", ""), v.get("gender", "M"), v.get("id")
    except Exception:
        return "", "M", None


def culture_for(seat):
    s = seat.lower()
    if any(x in s for x in ("belfast", "ulster", "antrim", "down", "armagh", "londonderry", "fermanagh")):
        return "irish"
    if any(x in s for x in ("edinburgh", "glasgow", "aberdeen", "dundee", "fife", "ayr", "lothian", "perth",
                            "renfrew", "lanark", "inverness", "argyll", "orkney", "shetland")):
        return "scottish"
    if any(x in s for x in ("cardiff", "swansea", "gwent", "wales", "monmouth", "caerphilly", "aber", "rhondda",
                            "carmarthen", "pembroke", "flint", "wrexham")):
        return "welsh"
    return "english"


def score(old, new):
    a, b = norm(old), norm(new)
    at, bt = set(a.split("_")), set(b.split("_"))
    overlap = len(at & bt) / max(1, len(at | bt))
    return SequenceMatcher(None, a, b).ratio() + overlap * 1.5


def stable_birth(name):
    h = int(hashlib.sha1(name.encode()).hexdigest(), 16)
    return "%d.%d.%d" % (1924 + h % 31, (h // 31) % 12 + 1, (h // 372) % 28 + 1)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="\n") as f:
        f.write(text)
    print("wrote", path.relative_to(ROOT.parent))


def load_members():
    data = json.loads(cached("parlparse_people.json", PEOPLE_URL).read_text())
    people = {p["id"]: p for p in data["persons"]}
    posts = {p["id"]: p for p in data["posts"]}
    active = []
    for m in data["memberships"]:
        if not m.get("post_id", "").startswith("uk.org.publicwhip/cons/"):
            continue
        if m.get("start_date", "9999") <= "1979-05-04" <= m.get("end_date", "0000"):
            p, post = people[m["person_id"]], posts[m["post_id"]]
            active.append({"name": display_name(p), "old_seat": post["area"]["name"], "person_id": p["id"]})
    assert len(active) == 635, len(active)
    cache_path = RAW / "members_api_1979.json"
    cache = {} if "--refresh" in sys.argv or not cache_path.exists() else json.loads(cache_path.read_text())
    todo = [m["name"] for m in active if m["name"] not in cache]
    if todo:
        print("resolving %d historical party records" % len(todo))
        with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
            for name, result in zip(todo, pool.map(party_for, todo)):
                cache[name] = result
        cache_path.write_text(json.dumps(cache, indent=2, ensure_ascii=False))
    for m in active:
        party_name, gender, member_id = cache.get(m["name"], ("", "M", None))
        m.update(party=LEADERS.get(m["name"]) or PARTY.get(party_name), female=gender == "F", mnis=member_id)
    return active


def map_seats(members):
    with open(ROOT / "data/ge2024_results.csv", encoding="utf-8-sig") as f:
        modern = list(csv.DictReader(f))
    remaining = {r["title"][2:]: r for r in modern}
    for m in members:
        target = MANUAL_SEATS.get(m["name"])
        if target in remaining:
            m["seat"] = target
            remaining.pop(target)
    for m in sorted((m for m in members if "seat" not in m), key=lambda x: x["old_seat"]):
        target = max(remaining, key=lambda s: score(m["old_seat"], remaining[s]["constituency"]))
        m["seat"] = target
        remaining.pop(target)
    # The 1979 Commons had 635 constituencies and the fixed game map has 650. Fill the new-map difference with
    # deterministic notional backbenchers, preserving the 1979 governing-party balance closely.
    counts = {}
    for m in members:
        counts[m["party"]] = counts.get(m["party"], 0) + 1
    sequence = ["conservative"] * 8 + ["labour"] * 6 + ["lib_dem"]
    for i, seat in enumerate(sorted(remaining)):
        party = sequence[i]
        members.append({"name": "Notional Member for " + remaining[seat]["constituency"], "old_seat": "notional",
                        "seat": seat, "party": party, "female": False, "mnis": None, "notional": True})
    return modern


def main():
    members = load_members()
    # Any unresolved API affiliation is assigned from the known 1979 result totals, using seat-name-stable order.
    targets = {"conservative": 339, "labour": 269, "lib_dem": 11, "snp": 2, "uup": 5, "dup": 3, "sdlp": 1,
               "plaid": 2, None: 3}
    known = {k: sum(m["party"] == k for m in members) for k in targets}
    vacancies = [k for k, n in targets.items() for _ in range(max(0, n - known.get(k, 0)))]
    unresolved = [m for m in members if not m["party"]]
    for m, party in zip(sorted(unresolved, key=lambda x: x["name"]), vacancies + [None] * len(unresolved)):
        m["party"] = party
    modern = map_seats(members)
    by_name = {m["name"]: m for m in members}
    for m in members:
        m["id"] = "wm_1979_" + norm(m["name"])
        # These are distinct MPs with the same name, not duplicate records.
        # Keep the established ids for the former PM and the Hackney MP.
        if (m["name"], m["old_seat"]) in {
            ("James Callaghan", "Middleton and Prestwich"),
            ("Ronald Brown", "Edinburgh Leith"),
        }:
            m["id"] += "_" + norm(m["old_seat"])
        if m["name"] == "James Callaghan" and m["old_seat"] == "Cardiff South East":
            by_name[m["name"]] = m
        m["birth"] = SIGNIFICANT_BIRTHS.get(m["name"], stable_birth(m["name"]))
        m["culture"] = culture_for(m["old_seat"])

    leaders = {p: by_name[n]["id"] for n, p in PARTY_LEADERS.items()}
    pm = leaders["conservative"]
    lines = ["# Generated by westminster/tools/data/build_1979.py - edit there.",
             "# The 1979 Commons on Westminster's fixed 2024 constituency map."]
    loc = ["l_english:", " # Generated by westminster/tools/data/build_1979.py - edit there."]
    for m in members:
        lines += ["%s = {\t# %s; 1979 seat: %s" % (m["id"], m["name"], m["old_seat"]),
                  "\tname = wm_name_%s" % m["id"][3:],
                  "\tdynasty_house = %s" % ("wm_house_party_" + m["party"] if m["party"] else "wm_house_independent")]
        if m["id"] in SIGNIFICANT_IDS:
            lines.append("\tdna = wm_dna_%s" % m["id"][3:])
        if m["female"]:
            lines.append("\tfemale = yes")
        lines += ["\tculture = %s" % m["culture"], "\treligion = %s" % IDEOLOGY.get(m["party"], "wm_faith_not_stated"),
                  "\t%s = { birth = yes }" % m["birth"]]
        if m["party"]:
            lines.append("\t%s = { effect = { set_variable = { name = wm_party value = title:k_party_%s } } }" %
                         (START, m["party"]))
        lines.append("}")
        loc.append(' wm_name_%s: "%s"' % (m["id"][3:], m["name"].replace('"', "'")))
    write(MOD / "history/characters/wm_1979_mps.txt", "\n".join(lines) + "\n")
    write(MOD / "localization/english/wm_1979_names_l_english.yml", "\n".join(loc) + "\n")

    events = {}
    def entry(t, holder, liege=None, laws=False):
        b = ["\t\tholder = %s" % holder]
        if liege: b.append('\t\tliege = "%s"' % liege)
        if laws: b.append("\t\tsuccession_laws = { wm_party_succession_law }")
        events[t] = "\t# BEGIN 1979 BOOKMARK (generated by build_1979.py)\n\t%s = {\n%s\n\t}\n\t# END 1979 BOOKMARK\n" % (START, "\n".join(b))
    for t in ("e_united_kingdom", "k_england", "k_scotland", "k_wales", "k_northern_ireland"):
        entry(t, pm)
    for p, holder in leaders.items():
        entry("k_party_" + p, holder, None if p == "conservative" else "e_united_kingdom", True)
    for m in members:
        liege = None if m["id"] == pm else ("e_united_kingdom" if m["id"] in leaders.values() or not m["party"]
                                            else "k_party_" + m["party"])
        entry("c_" + m["seat"], m["id"], liege)
    # CK3 replaces duplicate top-level title keys rather than merging files. Insert the dated 1979 holder events into
    # the canonical title history produced by build_2024.py, keeping both bookmarks in a single block per title.
    title_path = MOD / "history/titles/wm_2024_seats.txt"
    title_text = title_path.read_text(encoding="utf-8-sig")
    title_text = re.sub(r"\t# BEGIN 1979 BOOKMARK .*?\t# END 1979 BOOKMARK\n", "", title_text, flags=re.S)
    for t, event in events.items():
        title_text, n = re.subn(r"^" + re.escape(t) + r" = \{\n", t + " = {\n" + event, title_text, count=1, flags=re.M)
        if n != 1:
            raise RuntimeError("1979 title missing from canonical history: " + t)
    write(title_path, title_text)
    old = MOD / "history/titles/wm_1979_seats.txt"
    if old.exists():
        old.unlink()

    # A compact notional constituency baseline derived from the 1979 winner. The national poll uses the exact 1979
    # result; these local shares preserve the historical seat map while still allowing swings and upsets.
    lean_sets = {
        "conservative": {"con": 520, "lab": 300, "ld": 120, "oth": 60},
        "labour": {"lab": 520, "con": 300, "ld": 120, "oth": 60},
        "lib_dem": {"ld": 430, "con": 280, "lab": 250, "oth": 40},
        "snp": {"snp": 450, "lab": 300, "con": 180, "ld": 70},
        "plaid": {"pc": 450, "lab": 350, "con": 150, "ld": 50},
        "uup": {"uup": 500, "dup": 180, "sdlp": 160, "oth": 160},
        "dup": {"dup": 500, "uup": 220, "sdlp": 140, "oth": 140},
        "sdlp": {"sdlp": 500, "uup": 200, "dup": 150, "oth": 150},
        None: {"oth": 450, "lab": 250, "con": 220, "ld": 80},
    }
    leans = ["# Generated by westminster/tools/data/build_1979.py - edit there.",
             "wm_init_1979_seat_leans_effect = {"]
    for m in sorted(members, key=lambda x: x["seat"]):
        leans.append("\ttitle:c_%s = {" % m["seat"])
        for p, value in lean_sets[m["party"]].items():
            leans.append("\t\tset_variable = { name = wm_lean_%s value = %s }" % (p, value))
        leans.append("\t}")
    leans.append("}")
    write(MOD / "common/scripted_effects/wm_1979_seat_leans.txt", "\n".join(leans) + "\n")

    bm = ["# Generated by westminster/tools/data/build_1979.py - edit there.",
          "bm_1979_thatcher = {", "\tstart_date = %s" % START, "\tis_playable = yes", "\tgroup = bm_group_1979",
          "\tweight = { value = 110 }"]
    bloc = ["l_english:", ' bm_group_1979: "1979"', ' bm_1979_thatcher: "1979: Thatcher Enters Downing Street"',
            ' bm_1979_thatcher_desc: "The Conservatives have defeated James Callaghan’s Labour government. Margaret Thatcher enters Downing Street with 339 seats and a working majority, while inflation and industrial conflict divide the country.\\n\\n#bold The full 1979 Commons is playable on the fixed constituency map.#!"']
    # Kept in sync with tools/ui/build_bookmark_screen.py --1979: placed around the map without covering Britain.
    positions = [(335, 315), (510, 780), (880, 295), (1055, 835), (1130, 595)]
    for (name, sub, anim, difficulty, desc), (x, y) in zip(FEATURED, positions):
        m = by_name[name]; key = "bookmark_1979_" + norm(name)
        featured_title = "e_united_kingdom" if name == "Margaret Thatcher" else (
            "k_party_" + m["party"] if name in LEADERS else "c_" + m["seat"])
        bm += ["\tcharacter = {", '\t\tname = "%s"' % key, "\t\tdynasty_house = wm_house_party_%s" % m["party"],
               "\t\ttype = %s" % ("female" if m["female"] else "male"), "\t\tbirth = %s" % m["birth"],
               "\t\ttitle = %s" % featured_title, "\t\tgovernment = feudal_government", "\t\tculture = %s" % m["culture"],
               "\t\treligion = %s" % IDEOLOGY[m["party"]], '\t\tdifficulty = "BOOKMARK_CHARACTER_DIFFICULTY_%s"' % difficulty,
               "\t\thistory_id = %s" % m["id"], "\t\tposition = { %d %d }" % (x, y), "\t\tanimation = %s" % anim, "\t}"]
        bloc += [' %s: "%s"' % (key, name), ' %s_subheading: "%s"' % (key, sub),
                 ' %s_desc: "%s"' % (key, desc.replace('"', "'"))]
    bm.append("}")
    write(MOD / "common/bookmarks/bookmarks/wm_1979_bookmark.txt", "\n".join(bm) + "\n")
    write(MOD / "localization/english/wm_1979_bookmark_l_english.yml", "\n".join(bloc) + "\n")

    # Personal names stay the same in every supported language. Until the short historical copy receives native
    # translations, use the English prose as an explicit fallback rather than exposing raw localization keys.
    for language in ("french", "german", "japanese", "korean", "polish", "russian", "simp_chinese", "spanish"):
        write(MOD / ("localization/%s/wm_1979_names_l_%s.yml" % (language, language)),
              "\n".join(["l_" + language + ":"] + loc[1:]) + "\n")
        write(MOD / ("localization/%s/wm_1979_bookmark_l_%s.yml" % (language, language)),
              "\n".join(["l_" + language + ":"] + bloc[1:]) + "\n")
        event_loc = (MOD / "localization/english/wm_1979_events_l_english.yml").read_text(encoding="utf-8-sig").splitlines()
        write(MOD / ("localization/%s/wm_1979_events_l_%s.yml" % (language, language)),
              "\n".join(["l_" + language + ":"] + event_loc[1:]) + "\n")

    # Dated snapshot consumed by future bookmark builders and audits.
    snapshot = {"date": "1979-05-04", "election": "1979-05-03", "prime_minister": "Margaret Thatcher",
                "monarch": "Elizabeth II", "members": members}
    (ROOT / "data/snapshots").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/snapshots/1979.json").write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n")
    print("1979 members:", len(members), "party counts:", {p: sum(m["party"] == p for m in members) for p in targets})


SIGNIFICANT_IDS = {"wm_1979_" + norm(n) for n in SIGNIFICANT_BIRTHS}


if __name__ == "__main__":
    main()
