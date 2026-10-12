#!/usr/bin/env python3
"""Checks the translated Workshop texts in workshop/translations/<language>/ against the English
in workshop/: all three files present, the same BBCode tags (and counts) as the English, the
version line kept, and the short description under 250 characters."""
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
EN = HERE.parent
LANGS = ["french", "german", "spanish", "russian", "polish", "simp_chinese", "korean", "japanese"]
FILES = ["title.txt", "description.bbcode.txt", "short_description.txt", "change_notes_0.3.txt", "change_notes_0.3.1.txt"]


def tags(s):
    return Counter(re.findall(r"\[/?[a-z0-9*]+\]", s))


problems = []


def steam_bytes(s):
    """Steam counts limits in UTF-8 bytes, with each line break sent as CRLF (2 bytes)."""
    s = s.rstrip("\n")
    return len(s.encode("utf-8")) + s.count("\n")


for d in [EN] + [HERE / l for l in (sys.argv[1:] or LANGS)]:
    t, desc = d / "title.txt", d / "description.bbcode.txt"
    if t.is_file() and steam_bytes(t.read_text(encoding="utf-8")) > 128:
        problems.append("%s: title over Steam's 128 bytes" % d.name)
    if desc.is_file() and steam_bytes(desc.read_text(encoding="utf-8")) > 8000:
        problems.append("%s: description over Steam's 8,000 bytes (line breaks count 2)" % d.name)
for lang in sys.argv[1:] or LANGS:
    for f in FILES:
        p = HERE / lang / f
        if not p.is_file():
            problems.append("%s: missing %s" % (lang, f))
            continue
        text, en = p.read_text(encoding="utf-8"), (EN / f).read_text(encoding="utf-8")
        if tags(text) != tags(en):
            problems.append("%s/%s: tags differ: %s" % (lang, f, dict((tags(text) - tags(en)) + (tags(en) - tags(text)))))
        if f == "short_description.txt" and len(text.strip()) >= 250:
            problems.append("%s/%s: %d characters (limit 250)" % (lang, f, len(text.strip())))
        if "1.5.0" in en and "1.5.0" not in text:
            problems.append("%s/%s: version number missing" % (lang, f))
print("\n".join(problems) or "ok: all Workshop translations")
sys.exit(1 if problems else 0)
