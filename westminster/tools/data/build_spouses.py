#!/usr/bin/env python3
"""Fictional husbands and wives for the 2024 MPs (called by build_2024.py; not run on its own).

None of them is real: each is an invented person with a modern British name, made from the same pool as the
cultures' name lists (the 2024 MPs' given names of that nation plus common surnames). Rules:
  - About two thirds of MPs are married, fewer of the youngest. Seeded per seat, so reruns are stable.
  - Opposite-sex marriages only: vanilla CK3 can't marry two men or two women. MPs who are openly LGBT+ (Wikipedia's
    list of LGBTQ politicians in the UK, Wikidata's sexual orientation, or a same-sex spouse on Wikidata) are left
    unmarried rather than given a spouse of the wrong sex.
  - Given names are ones at least three MPs share, so none points at a particular MP.
  - Never the real spouse's name: the given names and full names of real spouses on Wikidata are excluded for that
    MP, and a spouse never shares the MP's surname (so nobody reads as a real relative).
  - Spouses are lowborn (no house). Parties are houses, so a spouse in the MP's house would count as a party member;
    lowborn they show their whole name (the name is a localization key for the full name, like the MPs') and join
    the MP's court. Marriage doesn't change anyone's house, so the MP stays in their party.
  - A male MP marries patrilineally and a female MP matrilineally, so children born in play join the MP's house.
  - No children are generated: a child in a party's house would count as a member, and 1,000 more characters would
    slow the game for little.

Sources, cached in data/raw/ (see data/README.md):
  wikidata_mps_2024_family.json         Wikidata: spouse (P26) with its sex, sexual orientation (P91), by member id
  wikipedia_lgbtq_uk_politicians.json   Wikipedia: "List of LGBTQ politicians in the United Kingdom" (wikitext)
"""
import json
import random
import re
import urllib.parse

WIKIPEDIA_URL = ("https://en.wikipedia.org/w/api.php?action=parse&page=List_of_LGBTQ_politicians_in_the_United_Kingdom"
                 "&prop=wikitext&format=json")
MARRIED_SHARE = [(30, 0.25), (40, 0.6), (65, 0.75), (200, 0.7)]     # by the MP's age: under 30, 30-39, 40-64, 65+
FEMALE = "Q6581072"
FAMOUS = {"Barry White", "John Barnes", "Gary Lineker", "Paul Daniels", "David Mitchell", "Emma Watson",
          "James Martin", "Chris Evans", "Tom Daley", "Andy Murray", "John Lewis", "Ian Wright"}   # well-known people


def load_family(ids, raw, fetch, refresh):
    path = raw / "wikidata_mps_2024_family.json"
    if refresh or not path.exists():
        print("querying Wikidata for spouses of %d members" % len(ids))
        rows = []
        for n in range(0, len(ids), 200):
            values = " ".join('"%s"' % i for i in ids[n:n + 200])
            q = """SELECT ?id ?spouseLabel ?spouseGender ?orient WHERE {
  VALUES ?id { %s }
  ?item wdt:P10428 ?id .
  OPTIONAL { ?item wdt:P26 ?spouse . OPTIONAL { ?spouse wdt:P21 ?spouseGender } }
  OPTIONAL { ?item wdt:P91 ?orient }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}""" % values
            body = urllib.parse.urlencode({"query": q}).encode()
            res = json.loads(fetch("https://query.wikidata.org/sparql", data=body, headers={
                "Accept": "application/sparql-results+json", "Content-Type": "application/x-www-form-urlencoded"}))
            rows += [{k: v["value"] for k, v in b.items()} for b in res["results"]["bindings"]]
        path.write_text(json.dumps(rows, indent=0))
    return json.loads(path.read_text())


def load_lgbt_names(raw, fetch, refresh):
    path = raw / "wikipedia_lgbtq_uk_politicians.json"
    if refresh or not path.exists():
        print("downloading", WIKIPEDIA_URL)
        path.write_bytes(fetch(WIKIPEDIA_URL))
    text = json.loads(path.read_text())["parse"]["wikitext"]["*"]
    names = set()
    for link in re.findall(r"\[\[([^\]]+)\]\]", text):
        for part in link.split("|"):
            names.add(re.sub(r"\s*\(.*?\)$", "", part.strip()))     # "Name (politician)" -> "Name"
    return names


def married_share(age):
    for limit, share in MARRIED_SHARE:
        if age < limit:
            return share
    return MARRIED_SHARE[-1][1]


def make_spouses(chars, surnames, start_year, raw, fetch, refresh):
    """Returns (spouses, report): spouse dicts (id, given, family, female, birth, culture, mp, married) for the MPs in
    chars that get one."""
    mps = [c for c in chars if c["seat"]]
    family = load_family(sorted({c["mnis"] for c in mps if c["mnis"]}), raw, fetch, refresh)
    lgbt_names = load_lgbt_names(raw, fetch, refresh)
    real_spouses, same_sex, orientation = {}, set(), set()
    by_mnis = {c["mnis"]: c for c in mps}
    for r in family:
        c = by_mnis.get(r["id"])
        if not c:
            continue
        if "orient" in r:
            orientation.add(r["id"])
        if "spouseLabel" in r:
            real_spouses.setdefault(r["id"], set()).add(r["spouseLabel"])
            if "spouseGender" in r and (r["spouseGender"].endswith(FEMALE)) == c["female"]:
                same_sex.add(r["id"])
    taken = {(c["given"], c["family"]) for c in chars}
    # Given names shared by at least three MPs, so a distinctive one doesn't point at a particular MP
    counts = {}
    for c in mps:
        counts[(c["given"], c["female"])] = counts.get((c["given"], c["female"]), 0) + 1
    given_by = {}
    for c in mps:
        if counts[(c["given"], c["female"])] >= 3:
            given_by.setdefault((c["culture"], c["female"]), set()).add(c["given"])
    spouses, skipped_lgbt = [], 0
    for c in mps:
        name = "%s %s" % (c["given"], c["family"])
        if name in lgbt_names or c["mnis"] in orientation or c["mnis"] in same_sex:
            skipped_lgbt += 1
            continue
        rnd = random.Random("wm_spouse_" + c["seat"])
        y, m, d = (int(x) for x in c["birth"].split("."))
        age = start_year - y
        if rnd.random() >= married_share(age):
            continue
        female = not c["female"]
        # Age: husbands tend to be a little older than wives
        gap = rnd.gauss(2.5, 3.5) * (1 if female else -1)
        sy = int(round(y + gap))
        sy = max(min(sy, start_year - 22), y - 15)
        sy = min(sy, y + 15)
        birth = "%d.%d.%d" % (sy, rnd.randint(1, 12), rnd.randint(1, 28))
        # Name: a given name of the spouse's sex from MPs of that nation (all English names if few), a common surname
        pool = given_by.get((c["culture"], female), set())
        if len(pool) < 20:
            pool = pool | given_by.get(("english", female), set())
        real = real_spouses.get(c["mnis"], set())
        real_given = {r.split()[0] for r in real}
        pool = sorted(g for g in pool if g not in real_given)
        sn_pool = sorted(s for s in set(surnames[c["culture"]]) if s != c["family"])
        while True:
            pair = (rnd.choice(pool), rnd.choice(sn_pool))
            if pair[0] != pair[1] and pair not in taken and "%s %s" % pair not in real and "%s %s" % pair not in FAMOUS:
                break
        taken.add(pair)
        wed_year = max(y, sy) + rnd.randint(24, 34)
        wed_year = min(wed_year, start_year - 1)
        wed_year = max(wed_year, max(y, sy) + 18)
        spouses.append({"id": "wm_sp_" + c["seat"], "given": pair[0], "family": pair[1], "female": female,
                        "birth": birth, "culture": c["culture"], "mp": c["id"], "mp_female": c["female"],
                        "married": "%d.%d.%d" % (wed_year, rnd.randint(1, 12), rnd.randint(1, 28))})
    report = "spouses: %d of %d MPs married (%.0f%%); %d openly LGBT+ MPs left unmarried (opposite-sex marriage only)" % (
        len(spouses), len(mps), 100 * len(spouses) / len(mps), skipped_lgbt)
    return spouses, report
