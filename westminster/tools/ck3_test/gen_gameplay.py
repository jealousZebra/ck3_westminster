#!/usr/bin/env python3
"""Writes Westminster's gameplay tests (riots, the Crown) into the harness
(harness/common/scripted_effects/rf_test_effects.txt), in the same style as gen_spikes.py.

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3, remade with make_save.sh after the Crown
title and the royal family were added). The game must be unpaused: the march and the monarch's interaction
are checked again 40 days after setup (event rf_test.2). Each check logs RFT_PASS / RFT_FAIL to debug.log:

    python3 westminster/tools/ck3_test/gen_gameplay.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 UNPAUSE=1 WAIT_LOOPS=80 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/gameplay.log
    python3 common/ck3_test/report.py westminster/tools/test_out/gameplay.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  riots   a riot started in a seat has a demand, an organiser and the Rioting modifier; conceding ends it
          (Demands Met, the demand's effect, the prestige cost); policing ends it; a march sets off on its own.
  crown   the Crown exists and is held by the monarch, who isn't the PM, isn't an MP and isn't in the PM's
          realm; "Speak Out Against MP" costs the monarch the big prestige cost and hits the MP.
"""
import sys
from pathlib import Path

SUITES = sys.argv[1] if len(sys.argv) > 1 else "rc"     # r = riots, c = crown

OUT = Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt"
blocks = []
later = []          # run by event rf_test.2, 40 days after setup
LATER = False

PM = "title:e_united_kingdom.holder"
MONARCH = "title:k_wm_crown.holder"
COST = 1500         # wm_crown_speak_out_prestige_cost (common/script_values/wm_gameplay_values.txt)


def emit(text):
    (later if LATER else blocks).append(text)


def log(msg):
    return 'debug_log = "%s"' % msg


def check(name, cond, scope=None):
    test = cond if scope is None else "%s = { %s }" % (scope, cond)
    emit("if = { limit = { %s } %s }\nelse = { %s }" % (test, log("RFT_PASS " + name), log("RFT_FAIL " + name)))


def show(label, scope):
    emit("%s = { %s debug_log_scopes = yes }" % (scope, log("RFT_DETAIL " + label)))


def phase(name):
    emit(log("RFT_PHASE " + name))


def fresh_seat(seat):
    """End any riot left in the seat (saves keep variables)."""
    emit("title:%s = { if = { limit = { wm_riot_is_active_trigger = yes } wm_riot_end_effect = yes } }" % seat)


def riots():
    global LATER
    phase("riots")
    check("pm_exists", "exists = %s" % PM)

    # --- start a riot, then concede (demand 4: a U-turn, which doesn't depend on the cabinet)
    seat = "c_aldershot"
    fresh_seat(seat)
    check("seat_has_mp", "exists = holder", "title:" + seat)
    emit("title:%s = { wm_riot_start_effect = { DEMAND = 4 } }" % seat)
    check("riot_started", "wm_riot_is_active_trigger = yes", "title:" + seat)
    check("riot_has_demand", "var:wm_riot_demand = 4", "title:" + seat)
    check("riot_is_gathering", "var:wm_riot_stage = 1", "title:" + seat)
    check("riot_has_organiser", "exists = var:wm_riot_organiser var:wm_riot_organiser = { var:wm_riot_seat = title:%s }" % seat,
          "title:" + seat)
    check("riot_county_modifier", "has_county_modifier = wm_riot_county_modifier", "title:" + seat)
    check("riot_in_active_list", "is_target_in_global_variable_list = { name = wm_active_riots target = title:%s }" % seat)
    show("riot_organiser", "title:%s.var:wm_riot_organiser" % seat)

    emit("%s = { set_variable = { name = wm_test_prestige_limit value = prestige } "
         "change_variable = { name = wm_test_prestige_limit add = -340 } }" % PM)
    emit("title:%s = { save_scope_as = wm_riot_seat }" % seat)
    emit("%s = { wm_riot_concede_effect = yes }" % PM)
    check("concede_ends_riot", "NOT = { wm_riot_is_active_trigger = yes } NOT = { has_county_modifier = wm_riot_county_modifier }",
          "title:" + seat)
    check("concede_leaves_list", "NOT = { is_target_in_global_variable_list = { name = wm_active_riots target = title:%s } }" % seat)
    check("concede_demands_met", "has_county_modifier = wm_riot_demands_met_county_modifier", "title:" + seat)
    check("concede_u_turn", "has_character_modifier = wm_u_turn_modifier", PM)
    check("concede_costs_prestige", "prestige <= var:wm_test_prestige_limit", PM)

    # --- start a riot, then police it (the peaceful outcome)
    seat = "c_blackpool_south"
    fresh_seat(seat)
    check("riot2_seat_has_mp", "exists = holder", "title:" + seat)
    show("riot2_seat_mp", "title:%s.holder" % seat)
    emit("title:%s = { wm_riot_start_effect = { DEMAND = 2 } }" % seat)
    check("riot2_active", "wm_riot_is_active_trigger = yes", "title:" + seat)
    check("riot2_started", "var:wm_riot_demand = 2", "title:" + seat)
    emit("title:%s = { save_scope_as = wm_riot_seat }" % seat)
    emit("%s = { wm_riot_policed_effect = yes }" % PM)
    check("police_ends_riot", "NOT = { wm_riot_is_active_trigger = yes }", "title:" + seat)
    check("police_angers_seat", "has_county_modifier = wm_riot_policed_county_modifier", "title:" + seat)
    check("police_heavy_handed", "has_character_modifier = wm_heavy_handed_modifier", PM)

    # --- a riot left alone sets off on its march (wm_riot.2 fires 10-20 days later)
    seat = "c_bedford"
    fresh_seat(seat)
    emit("title:%s = { wm_riot_start_effect = { DEMAND = 3 } }" % seat)
    check("riot3_started", "var:wm_riot_demand = 3", "title:" + seat)
    LATER = True
    phase("riots_after_40_days")
    emit("title:%s = { if = { limit = { has_variable = wm_riot_stage } %s debug_log_scopes = yes } }"
         % (seat, log("RFT_DETAIL march_stage")))
    # Still marching (stage 2), at Westminster (3), or already answered by an AI PM (riot over)
    check("march_set_off", "OR = { NOT = { wm_riot_is_active_trigger = yes } AND = { has_variable = wm_riot_stage var:wm_riot_stage >= 2 } }",
          "title:" + seat)
    check("march_not_stuck_gathering", "NOT = { AND = { has_variable = wm_riot_stage var:wm_riot_stage = 1 } }", "title:" + seat)
    LATER = False


def crown():
    global LATER
    phase("crown")
    check("crown_held", "exists = %s" % MONARCH)
    show("monarch", MONARCH)
    check("crown_not_held_by_pm", "NOT = { %s = %s }" % (MONARCH, PM))
    check("monarch_not_an_mp", "NOT = { wm_is_mp_trigger = yes }", MONARCH)
    check("monarch_not_in_pm_realm", "NOT = { top_liege = %s }" % PM, MONARCH)
    check("pm_not_monarch_vassal", "NOT = { top_liege = %s }" % MONARCH, PM)
    check("monarch_has_crown_government", "has_government = wm_crown_government", MONARCH)

    # A test MP with a seat, serving the PM
    emit("""create_character = { name = "Test Backbencher" age = 45 gender = male culture = culture:english faith = faith:wm_faith_not_stated
	location = root.capital_province save_scope_as = wm_test_mp }
create_title_and_vassal_change = { type = granted save_scope_as = wm_change add_claim_on_loss = no }
title:c_basingstoke = { change_title_holder = { holder = scope:wm_test_mp change = scope:wm_change } }
scope:wm_test_mp = { change_liege = { liege = %s change = scope:wm_change } }
resolve_title_and_vassal_change = scope:wm_change
set_global_variable = { name = wm_test_mp value = scope:wm_test_mp }""" % PM)
    check("test_mp_is_mp", "wm_is_mp_trigger = yes", "scope:wm_test_mp")

    # Give the monarch prestige to spend, and note the most they may have left after paying the cost
    # (allowing 100 for 40 days of monthly prestige)
    emit("""%s = {
	save_scope_as = wm_test_monarch
	remove_character_flag = wm_crown_spoke_out_recently
	add_prestige = 3000
	set_global_variable = { name = wm_test_monarch value = this }
	set_global_variable = { name = wm_test_monarch_prestige_limit value = prestige }
	change_global_variable = { name = wm_test_monarch_prestige_limit add = %d }
}""" % (MONARCH, -(COST - 100)))
    check("monarch_can_afford", "prestige >= %d" % COST, "scope:wm_test_monarch")
    emit("scope:wm_test_monarch = { wm_crown_speak_out_by_script_effect = { TARGET = scope:wm_test_mp } }")
    emit("scope:wm_test_mp = { if = { limit = { has_character_modifier = wm_rebuked_by_the_crown_modifier } %s } else = { %s } }"
         % (log("RFT_DETAIL speak_out_applied_at_once"), log("RFT_DETAIL speak_out_not_yet_applied")))

    LATER = True
    phase("crown_after_40_days")
    check("speak_out_costs_prestige", "prestige <= global_var:wm_test_monarch_prestige_limit", "global_var:wm_test_monarch")
    check("speak_out_flag", "has_character_flag = wm_crown_spoke_out_recently", "global_var:wm_test_monarch")
    check("speak_out_mp_modifier", "has_character_modifier = wm_rebuked_by_the_crown_modifier", "global_var:wm_test_mp")
    check("speak_out_mp_opinion",
          "has_opinion_modifier = { modifier = wm_spoken_against_by_crown_opinion target = global_var:wm_test_monarch }",
          "global_var:wm_test_mp")
    check("speak_out_seat_modifier", "has_county_modifier = wm_crown_criticism_county_modifier", "title:c_basingstoke")
    check("speak_out_pm_annoyed",
          "has_opinion_modifier = { modifier = wm_crown_meddling_opinion target = global_var:wm_test_monarch }", PM)
    LATER = False


for letter in SUITES:
    {"r": riots, "c": crown}[letter]()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_gameplay.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n\tset_global_variable = { name = wm_test_quiet value = yes }\t# no player pop-ups (they pause the game)\n"
               + "\n".join(blocks) + ("\n\ttrigger_event = { id = rf_test.2 days = 40 }\n}\n" if later else "\n\tdebug_log = \"RFT done\"\n}\n")
               + "rf_test_effect_later = {\n" + "\n".join(later) + "\n\tdebug_log = \"RFT done\"\n}\n", encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
EVENTS.parent.mkdir(exist_ok=True)
EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
