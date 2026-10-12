#!/usr/bin/env python3
"""Summarises an RFT test log (from run_test.sh): PASS/FAIL per check, offenders for failures, timings."""
import re, sys
L = open(sys.argv[1], errors="replace").read().split("\n")

def cur(i):
    m = re.search(r"effectimpl.cpp:642\]: (.*?)( weak|$)", L[i + 1]) if i + 1 < len(L) else None
    return m.group(1) if m else "?"

passed = failed = 0
for i, l in enumerate(L):
    m = re.search(r"(RFT_\w+) ?(.*)$", l)
    if not m or "jomini_effect_impl" not in l and "RFT start" not in l and "RFT done" not in l:
        continue
    kind, rest = m.group(1), m.group(2).strip()
    t = l[1:9]
    if kind == "RFT_PHASE": print("\n== %s" % rest)
    elif kind == "RFT_PASS": passed += 1; print("  pass  %s" % rest)
    elif kind == "RFT_FAIL": failed += 1; print("  FAIL  %s" % rest)
    elif kind == "RFT_DETAIL": print("          -> %s" % cur(i))
    elif kind == "RFT_TIME": print("  time  %s %s" % (t, rest))
print("\n%d passed, %d failed" % (passed, failed))
if not any("RFT done" in l for l in L): print("WARNING: the suite did not reach the end")
