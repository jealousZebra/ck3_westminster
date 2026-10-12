#!/usr/bin/env python3
"""A small reader for Paradox script (.txt): enough for the game's genes and ethnicities.

    parse(text) -> [(key, value), ...]   value is a token (str) or a nested list of the same shape

Keys can repeat (ethnicities list `10 = { ... }` many times), so blocks stay lists of pairs. Bare values inside a
block (`{ 0.4 0.7 0.7 0.85 }`) come back as (value, None). `@name = value` lines are substituted in later tokens.
"""
import re

TOKEN = re.compile(r'"[^"]*"|[{}=]|[^\s{}=#"]+|#[^\n]*')


def tokens(text):
    out = []
    for t in TOKEN.findall(text):
        if t.startswith("#"):
            continue
        out.append(t)
    return out


def parse(text):
    toks = tokens(text)
    vars_ = {}
    pos = 0

    def val(t):
        if t.startswith("@") and t in vars_:
            return vars_[t]
        return t.strip('"') if t.startswith('"') else t

    def block():
        nonlocal pos
        items = []
        while pos < len(toks):
            t = toks[pos]
            if t == "}":
                pos += 1
                return items
            if t == "{":
                pos += 1
                items.append((block(), None))
                continue
            if pos + 1 < len(toks) and toks[pos + 1] == "=":
                pos += 2
                if toks[pos] == "{":
                    pos += 1
                    v = block()
                else:
                    v = val(toks[pos])
                    pos += 1
                if t.startswith("@"):
                    vars_[t] = v
                else:
                    items.append((t, v))
            else:
                items.append((val(t), None))
                pos += 1
        return items

    return block()


def get(items, key, default=None):
    for k, v in items:
        if k == key:
            return v
    return default


def get_all(items, key):
    return [v for k, v in items if k == key]
