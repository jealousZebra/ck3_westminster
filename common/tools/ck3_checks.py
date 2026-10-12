#!/usr/bin/env python3
"""Checks shared by every mod in this repo (see docs/ck3-modding-notes.md for why each matters).

    python3 common/tools/ck3_checks.py static <mod folder>
        Every script, GUI and localization file has a UTF-8 BOM, braces balance in .txt/.gui files,
        every localization language has every key the English has, and no localization key is defined
        twice in one language (replace/ included).

    python3 common/tools/ck3_checks.py errorlog <prefix> [<error.log>]
        Fails on errors from the mod's own files in the game's error.log: lines whose script
        location is a file named <prefix>* (other than the test harness, <prefix>test*), and
        "variable set but never used / used but never set" warnings for <prefix>* variables.
        Use the mod's file and variable prefix, e.g. wm_ for Westminster.
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ck3paths import DOCS, GAME  # noqa: E402  (CK3_GAME_DIR / CK3_DOCS_DIR override the Steam defaults)


def same_as_vanilla(f, mod, diff):
    """A copied vanilla file with vanilla's own (harmless) brace imbalance, e.g. braces inside format strings."""
    v = os.path.join(str(GAME), os.path.relpath(f, mod))
    if not os.path.exists(v):
        return False
    t = re.sub(r'"[^"]*"', "", open(v, encoding="utf-8-sig", errors="replace").read())
    t = re.sub(r"#.*", "", t)
    return t.count("{") - t.count("}") == diff


def static(mod):
    bad = []
    files = [f for ext in ("txt", "gui", "yml") for f in glob.glob(os.path.join(mod, "**", "*." + ext), recursive=True)
             if os.sep + "fonts" + os.sep not in f]                     # font licences aren't game script
    for f in files:
        raw = open(f, "rb").read()
        if not raw.startswith(b"\xef\xbb\xbf"):
            bad.append("no UTF-8 BOM: " + f)
        if f.endswith((".txt", ".gui")):
            t = re.sub(r'"[^"]*"', "", raw.decode("utf-8-sig"))
            t = re.sub(r"#.*", "", t)
            if t.count("{") != t.count("}") and not same_as_vanilla(f, mod, t.count("{") - t.count("}")):
                bad.append("unbalanced braces: " + f)
    keys, where = {}, {}
    loc = os.path.join(mod, "localization")
    for f in sorted(glob.glob(os.path.join(loc, "*", "**", "*.yml"), recursive=True)):
        lang = os.path.relpath(f, loc).split(os.sep)[0]
        for k in re.findall(r"^ (\S+?):", open(f, encoding="utf-8-sig").read(), re.M):
            if (lang, k) in where and where[(lang, k)] != f:
                bad.append("%s defined twice: %s and %s" % (k, where[(lang, k)], f))
            where[(lang, k)] = f
            keys.setdefault(lang, set()).add(k)
    for lang, ks in keys.items():
        missing = keys.get("english", set()) - ks
        if missing:
            bad.append("%s is missing %d keys, e.g. %s" % (lang, len(missing), sorted(missing)[:3]))
    print("\n".join(bad) or "ok: %d files, %d languages" % (len(files), len(keys)))
    return not bad


def errorlog(prefix, path):
    lines = open(path, errors="replace").read().split("\n")
    own_file = re.compile(r"/%s(?!test)[a-z_]+\.(txt|gui)" % re.escape(prefix))
    own_var = re.compile(r"Variable '%s(?!test)" % re.escape(prefix))
    bad = []
    for i, l in enumerate(lines):
        if "is set but is never used" in l or "is used but is never set" in l:
            # These have no script location, so match the variable name
            if own_var.search(l):
                bad.append(l.strip())
            continue
        if "Error:" not in l:
            continue
        loc = next((x for x in lines[i + 1:i + 3] if "Script location" in x), "")
        if own_file.search(loc):
            bad.append(l.strip() + "  @ " + loc.strip())
    print("\n".join(["Errors from %s files in error.log:" % prefix] + bad[:20]) if bad else "error.log: no %s errors" % prefix)
    return not bad


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "static":
        ok = static(sys.argv[2])
    elif len(sys.argv) >= 3 and sys.argv[1] == "errorlog":
        ok = errorlog(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else os.path.join(DOCS, "logs", "error.log"))
    else:
        sys.exit(__doc__)
    sys.exit(0 if ok else 1)
