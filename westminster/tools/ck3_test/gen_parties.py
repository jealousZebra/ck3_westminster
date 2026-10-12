#!/usr/bin/env python3
"""Writes Westminster's party-house tests (parties are houses, whole names, crossing the floor, founding a party)
into the harness (harness/common/scripted_effects/rf_test_effects.txt), in the style of gen_elections.py.

The save must be made after the party houses were added (they live in the save, as do the characters' names):
run tools/ck3_test/make_save.sh first. The suite sets global_var:wm_test_quiet and needs no unpausing:

    python3 westminster/tools/ck3_test/gen_parties.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/parties.log
    python3 common/ck3_test/report.py westminster/tools/test_out/parties.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  houses     each party's house exists and knows its party; every MP of each party is in its house; independents
             and the Speaker are in the Independent house; party leaders head their party's house
  names      the Prime Minister's first name is the key for his whole name ("Keir Starmer"; logged as a detail)
  join       a Labour backbencher can take Cross the Floor (and the PM can't); joining the Liberal Democrats moves
             their house, party and liege, and the Labour leader minds; sitting as an independent moves them to the
             Independent house under the PM; rejoining Labour brings them back
  found      another backbencher founds a party: they lead the first slot's title, head a new house that knows the
             party, keep their seat and serve the PM; a third MP joins the new party, its house and its leader
  whip       losing the whip (wm_commons_withdraw_whip_effect) moves an MP to the Independent house
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "data"))
import build_2024                                         # noqa: E402  (PARTIES, NEW_PARTIES)

# RFT_OUT=<file> writes elsewhere (to look at the suite without touching the harness)
OUT = Path(os.environ.get("RFT_OUT") or Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt")
blocks = []
PM = "title:e_united_kingdom.holder"
SEATS = "title:e_united_kingdom"
PARTIES = [p[0] for p in build_2024.PARTIES]


def emit(text):
    blocks.append(text)


def log(msg):
    return 'debug_log = "%s"' % msg


def check(name, cond, scope=None):
    test = cond if scope is None else "%s = { %s }" % (scope, cond)
    emit("if = { limit = { %s } %s }\nelse = { %s }" % (test, log("RFT_PASS " + name), log("RFT_FAIL " + name)))


def show(label, scope):
    emit("%s = { %s debug_log_scopes = yes }" % (scope, log("RFT_DETAIL " + label)))


def phase(name):
    emit(log("RFT_PHASE " + name))


def backbencher(scope_name, exclude=()):
    """Saves a Labour MP who doesn't lead the party or head its house as scope:<name> and global_var:<name>."""
    excl = " ".join("NOT = { this = scope:%s }" % e for e in exclude)
    emit("""%s = {
	random_in_de_jure_hierarchy = {
		limit = {
			tier = tier_county
			holder ?= {
				var:wm_party ?= title:k_party_labour
				NOT = { this = title:k_party_labour.holder }
				is_house_head = no
				is_dynast = no
				%s
			}
		}
		holder = { save_scope_as = %s }
	}
}
set_global_variable = { name = %s value = scope:%s }""" % (SEATS, excl, scope_name, scope_name, scope_name))
    show(scope_name, "scope:" + scope_name)


def houses():
    phase("houses")
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    emit("wm_party_houses_init_effect = yes")      # on_game_start's setup (the save may predate it)
    for p in PARTIES:
        check("house_exists_%s" % p, "exists = house:wm_house_party_%s" % p)
        check("house_knows_party_%s" % p, "var:wm_house_party = title:k_party_%s" % p, "house:wm_house_party_%s" % p)
        check("mps_in_house_%s" % p,
              "NOT = { any_in_de_jure_hierarchy = { tier = tier_county holder ?= { var:wm_party ?= title:k_party_%s "
              "NOT = { house ?= house:wm_house_party_%s } } } }" % (p, p), SEATS)
        check("leader_heads_house_%s" % p, "is_house_head = yes house = house:wm_house_party_%s" % p,
              "title:k_party_%s.holder" % p)
    check("labour_house_has_400_mps", "any_in_de_jure_hierarchy = { tier = tier_county holder ?= { house ?= "
          "house:wm_house_party_labour } count >= 400 }", SEATS)
    check("independents_in_independent_house",
          "NOT = { any_in_de_jure_hierarchy = { tier = tier_county holder ?= { NOT = { has_variable = wm_party } "
          "NOT = { house ?= house:wm_house_independent } } } }", SEATS)
    check("speaker_in_independent_house", "any_in_de_jure_hierarchy = { tier = tier_county holder ?= { "
          "has_character_flag = wm_speaker house ?= house:wm_house_independent } }", SEATS)


def names():
    phase("names")
    check("pm_is_keir_starmer", "has_first_name = wm_name_mp_holborn_and_st_pancras", PM)
    check("pm_holds_his_seat", "holder = %s" % PM, "title:c_holborn_and_st_pancras")
    show("pm_name_keir_starmer", PM)              # the scope dump shows the name the game displays
    check("sunak_is_rishi_sunak", "has_first_name = wm_name_mp_richmond_and_northallerton",
          "title:c_richmond_and_northallerton.holder")


def join():
    phase("join")
    check("pm_cannot_cross_the_floor", "NOT = { can_execute_decision = wm_party_join_decision }", PM)
    backbencher("wm_test_crosser")
    emit("scope:wm_test_crosser = { add_prestige = 2000 }")
    check("backbencher_can_cross_the_floor", "can_execute_decision = wm_party_join_decision", "scope:wm_test_crosser")
    emit("scope:wm_test_crosser = { wm_party_join_effect = { PARTY = title:k_party_lib_dem } }")
    check("joined_party_var", "var:wm_party = title:k_party_lib_dem", "scope:wm_test_crosser")
    check("joined_party_house", "house = house:wm_house_party_lib_dem", "scope:wm_test_crosser")
    check("joined_party_liege", "liege = title:k_party_lib_dem.holder", "scope:wm_test_crosser")
    check("joined_still_mp", "wm_is_mp_trigger = yes", "scope:wm_test_crosser")
    check("old_leader_minds", "has_opinion_modifier = { target = scope:wm_test_crosser modifier = wm_party_crossed_floor_opinion }",
          "title:k_party_labour.holder")
    show("crosser_after_join", "scope:wm_test_crosser")
    emit("scope:wm_test_crosser = { wm_party_leave_effect = yes }")
    check("left_no_party", "NOT = { has_variable = wm_party }", "scope:wm_test_crosser")
    check("left_independent_house", "house = house:wm_house_independent", "scope:wm_test_crosser")
    check("left_serves_pm", "liege = %s" % PM, "scope:wm_test_crosser")
    emit("scope:wm_test_crosser = { wm_party_join_effect = { PARTY = title:k_party_labour } }")
    check("rejoined_labour_house", "house = house:wm_house_party_labour var:wm_party = title:k_party_labour",
          "scope:wm_test_crosser")
    check("rejoined_labour_serves_leader", "liege = title:k_party_labour.holder", "scope:wm_test_crosser")


def found():
    phase("found")
    slot = build_2024.NEW_PARTIES[0][0]
    check("slot_free", "wm_party_free_slot_trigger = yes")
    backbencher("wm_test_founder", exclude=["wm_test_crosser"])
    emit("scope:wm_test_founder = { add_prestige = 2000 }")
    check("backbencher_can_found_party", "can_execute_decision = wm_party_found_decision", "scope:wm_test_founder")
    emit("scope:wm_test_founder = { wm_party_found_effect = yes }")
    check("founder_leads_party", "has_title = title:k_party_%s var:wm_party = title:k_party_%s" % (slot, slot),
          "scope:wm_test_founder")
    check("founder_new_house", "exists = house NOT = { house = house:wm_house_party_labour } is_house_head = yes",
          "scope:wm_test_founder")
    check("founder_house_knows_party", "house.var:wm_house_party ?= title:k_party_%s" % slot, "scope:wm_test_founder")
    check("founder_keeps_seat", "wm_is_mp_trigger = yes", "scope:wm_test_founder")
    check("founder_serves_pm", "liege = %s" % PM, "scope:wm_test_founder")
    check("founded_party_elects_leader", "has_title_law = wm_party_succession_law", "title:k_party_%s" % slot)
    show("founder", "scope:wm_test_founder")
    show("founded_house", "scope:wm_test_founder.house")
    backbencher("wm_test_follower", exclude=["wm_test_crosser", "wm_test_founder"])
    emit("scope:wm_test_follower = { wm_party_join_effect = { PARTY = title:k_party_%s } }" % slot)
    check("follower_in_founders_house", "house = scope:wm_test_founder.house var:wm_party = title:k_party_%s" % slot,
          "scope:wm_test_follower")
    check("follower_serves_founder", "liege = scope:wm_test_founder", "scope:wm_test_follower")


def whip():
    phase("whip")
    backbencher("wm_test_rebel", exclude=["wm_test_crosser", "wm_test_founder", "wm_test_follower"])
    emit("scope:wm_test_rebel = { wm_commons_withdraw_whip_effect = yes }")
    check("whipless_independent_house", "NOT = { has_variable = wm_party } house = house:wm_house_independent",
          "scope:wm_test_rebel")
    emit("remove_global_variable = wm_test_quiet")


houses()
names()
join()
found()
whip()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_parties.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(blocks) + "\n\tdebug_log = \"RFT done\"\n}\n"
               + "rf_test_effect_later = {\n\tdebug_log = \"RFT done\"\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
