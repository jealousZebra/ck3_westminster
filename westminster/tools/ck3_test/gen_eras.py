#!/usr/bin/env python3
"""Fresh-campaign assertions, run once automatically by the test harness widget."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from era_definitions import ERAS
from build_1979 import norm

out = [
    "rf_test_effect = {",
    'debug_log = "RFT start"',
    "wm_election_count_seats_effect = yes",
]
for year, cfg in ERAS.items():
    cid = f"wm_{year}_" + norm(cfg["pm"])
    tests = {
        f"{year}_prime_minister": f"title:e_united_kingdom.holder = character:{cid}",
        f"{year}_all_seats": "wm_election_total_seats = 650",
        f"{year}_governing_state": "has_global_variable = wm_gov_reserve",
        f"{year}_cabinet": f"title:e_united_kingdom.holder.cp:councillor_steward = character:wm_{year}_"
        + norm(cfg["cabinet"][0]),
        f"{year}_era_poll_anchor": "has_global_variable = wm_start_poll_lab",
        f"{year}_monarch": "title:k_wm_crown.holder = character:wm_royal_"
        + ("george_vi" if year == 1945 else "elizabeth_ii"),
    }
    if year == 2010:
        tests["2010_coalition"] = (
            "global_var:wm_coalition_partner ?= title:k_party_lib_dem"
        )
    if year == 2016:
        tests["2016_brexit_mandate"] = "global_var:wm_brexit_phase = 1"
    out.append(f'if = {{ limit = {{ game_start_date = {cfg["date"]} }}')
    for n, c in tests.items():
        out.append(
            f'if = {{ limit = {{ {c} }} debug_log = "RFT_PASS {n}" }} else = {{ debug_log = "RFT_FAIL {n}" }}'
        )
    out.append("}")
out += ['debug_log = "RFT done"', "}", "rf_test_effect_later = {}"]
p = Path(__file__).parent / "harness/common/scripted_effects/rf_test_effects.txt"
p.write_text("\n".join(out) + "\n", encoding="utf-8-sig")
print(p)
