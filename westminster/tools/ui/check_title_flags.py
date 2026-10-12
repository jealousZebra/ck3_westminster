#!/usr/bin/env python3
"""Checks that every landed title has its own coat of arms and that no two titles share one.

    .venv/bin/python westminster/tools/ui/check_title_flags.py

Reads the mod's final files, not the generators: every common/coat_of_arms/coat_of_arms/*.txt definition (an alias
`a = b` resolves to b's body) and every title in common/landed_titles. A title's design is its definition's body with
whitespace normalised; titles whose bodies hash the same fail. Each textured emblem a definition uses must exist,
and no two textured emblem files may hold the same image. Counts real flags (a full-size textured emblem) and
derived ones.
"""
import hashlib
import re
import sys
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent.parent / "westminster"


def blocks(text):
    """Top-level `key = { ... }` and `key = other` entries."""
    text = re.sub(r"#[^\n]*", "", text)
    out, i = {}, 0
    for m in re.finditer(r"([A-Za-z0-9_]+)\s*=\s*", text):
        if m.start() < i:
            continue
        key, j = m.group(1), m.end()
        if text.startswith("{", j):
            depth, k = 0, j
            while True:
                if text[k] == "{":
                    depth += 1
                elif text[k] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                k += 1
            out[key] = ("body", text[j + 1:k])
            i = k + 1
        else:
            v = re.match(r"[A-Za-z0-9_]+", text[j:])
            out[key] = ("alias", v.group(0))
            i = j + v.end()
    return out


def titles():
    found = []
    for f in sorted((MOD / "common" / "landed_titles").glob("*.txt")):
        found += re.findall(r"^\s*([ekdcb]_[a-z0-9_]+)\s*=\s*\{", f.read_text(encoding="utf-8-sig"), re.M)
    return found


def main():
    defs = {}
    for f in sorted((MOD / "common" / "coat_of_arms" / "coat_of_arms").glob("*.txt")):
        defs.update(blocks(f.read_text(encoding="utf-8-sig")))

    def body(k, seen=()):
        kind, v = defs[k]
        if kind == "alias":
            if v in seen:
                raise ValueError("alias loop at " + k)
            return body(v, seen + (k,))
        return v

    bad, by_hash, real, derived = [], {}, 0, 0
    tex_dir = MOD / "gfx" / "coat_of_arms" / "textured_emblems"
    for t in titles():
        if t not in defs:
            bad.append("no coat of arms: " + t)
            continue
        b = " ".join(body(t).split())
        h = hashlib.sha1(b.encode()).hexdigest()
        by_hash.setdefault(h, []).append(t)
        for tex in re.findall(r'textured_emblem\s*=\s*\{\s*texture\s*=\s*"([^"]+)"', b):
            if not (tex_dir / tex).exists():
                bad.append("%s uses a missing texture %s" % (t, tex))
        if re.search(r'textured_emblem = \{ texture = "[^"]+" instance = \{ position = \{ 0.5 0.5 \} scale = \{ 1 1 \}', b):
            real += 1
        else:
            derived += 1
    for h, ts in by_hash.items():
        if len(ts) > 1:
            bad.append("same coat of arms: " + ", ".join(ts))
    seen = {}
    for f in sorted(tex_dir.glob("wm_*.dds")):
        h = hashlib.sha1(f.read_bytes()[128:]).hexdigest()
        if h in seen:
            bad.append("same texture: %s and %s" % (seen[h], f.name))
        seen[h] = f.name
    n = real + derived
    print("\n".join(bad) or "ok: %d titles, %d distinct coats of arms (%d real flags, %d derived or party arms), "
          "%d flag textures all different" % (n, len(by_hash), real, derived, len(seen)))
    return not bad


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
