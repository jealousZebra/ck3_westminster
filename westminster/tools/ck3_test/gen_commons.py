#!/usr/bin/env python3
"""Writes Westminster's House of Commons tests (bills, divisions, whips, confidence motions) into the harness
(harness/common/scripted_effects/rf_test_effects.txt), in the same style as gen_gameplay.py.

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3). Everything is checked at once, so the game
needn't be unpaused. Each check logs RFT_PASS / RFT_FAIL to debug.log; the division numbers are logged as RFT_TIME
lines ("ayes>=350"), to the nearest 25 below:

    python3 westminster/tools/ck3_test/gen_commons.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/commons.log
    python3 common/ck3_test/report.py westminster/tools/test_out/commons.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  setup       the Leader of the Opposition is the Conservative leader (largest non-government party), not the
              Lib Dem leader; the Chief Whip's forecast counts a government majority.
  division    a normal bill (Public Services) with the 2024 majority: every MP but the Speaker is counted
              (ayes + noes + abstentions = 649), the Speaker doesn't vote, and the bill passes with its effect.
  whip        a Conservative MP on their third rebellion (voting with the government, as a player would) loses
              the whip: no party, serving the Prime Minister, resenting their old leader. Withdrawing the whip
              directly makes a Lib Dem MP an independent too.
  rebellion   a bill so controversial that most government MPs rebel is defeated, with the defeat's effect.
  confidence  a motion of no confidence that the government loses sets global_var:wm_election_required.
"""
import sys
from pathlib import Path

SUITES = sys.argv[1] if len(sys.argv) > 1 else "sdwrc"   # s setup, d division, w whip, r rebellion, c confidence

OUT = Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt"
blocks = []

PM = "title:e_united_kingdom.holder"
TORY_LEADER = "title:k_party_conservative.holder"
LD_LEADER = "title:k_party_lib_dem.holder"
SEATS = 650


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


def number(label, value, step=25, top=SEATS):
    """Log a number (to the nearest step below) as an RFT_TIME line: debug_log can't print values."""
    parts = []
    for n in range(top - top % step, -1, -step):
        parts.append("%s = { limit = { %s >= %d } %s }" % ("if" if not parts else "else_if", value, n,
                                                          log("RFT_TIME %s>=%d" % (label, n))))
    parts.append("else = { %s }" % log("RFT_TIME %s<0" % label))
    emit("\n".join(parts))


def division(label, bill_type, controversy=None):
    """Set up business for the current PM, optionally force its controversy, hold the division."""
    emit("wm_commons_setup_business_effect = { TYPE = %d MOVER = %s }" % (bill_type, PM))
    if controversy is not None:
        emit("set_global_variable = { name = wm_commons_bill_controversy value = %d }" % controversy)
    emit(log("RFT_TIME %s_start" % label))
    emit("wm_commons_division_effect = yes")
    emit(log("RFT_TIME %s_done" % label))
    for v in ("ayes", "noes", "abstentions", "gov_rebels"):
        number("%s_%s" % (label, v), "global_var:wm_commons_%s" % v)


def counted_all():
    return ("global_var:wm_commons_total = %d" % (SEATS - 1))


def total():
    emit("set_global_variable = { name = wm_commons_total value = global_var:wm_commons_gov_votes }\n"
         "change_global_variable = { name = wm_commons_total add = global_var:wm_commons_opp_votes }\n"
         "change_global_variable = { name = wm_commons_total add = global_var:wm_commons_abstentions }")


def setup():
    phase("commons_setup")
    emit("remove_global_variable = wm_election_required\nremove_global_variable = wm_commons_pending")
    check("pm_exists", "exists = %s" % PM)
    check("pm_has_party", "exists = var:wm_party", PM)
    check("tory_leader_is_opposition_leader", "wm_commons_is_leader_of_opposition_trigger = { WHO = %s }" % TORY_LEADER,
          TORY_LEADER)
    check("lib_dem_leader_is_not", "NOT = { wm_commons_is_leader_of_opposition_trigger = { WHO = %s } }" % LD_LEADER,
          LD_LEADER)
    check("pm_is_not", "NOT = { wm_commons_is_opposition_party_leader_trigger = yes }", PM)
    check("tory_seats_counted", "wm_commons_party_seats_value >= 100", TORY_LEADER)
    emit("wm_commons_setup_business_effect = { TYPE = 2 MOVER = %s }" % PM)
    check("business_pending", "wm_commons_house_free_trigger = no")
    emit("wm_commons_forecast_effect = yes")
    number("forecast_gov_mps", "global_var:wm_commons_gov_mps")
    number("forecast_opp_mps", "global_var:wm_commons_opp_mps")
    number("forecast_rebels", "global_var:wm_commons_forecast_rebels", step=5, top=200)
    check("forecast_majority", "global_var:wm_commons_gov_mps >= 326")
    emit("remove_global_variable = wm_commons_pending")


def whip_setup():
    """Before the normal-bill division: a Conservative backbencher with two rebellions who'll vote with the government."""
    emit("""%s = {
	set_global_variable = { name = wm_test_tory_leader value = this }
	random_vassal = {
		limit = {
			wm_is_mp_trigger = yes
			var:wm_party ?= title:k_party_conservative
			NOT = { has_title = title:k_party_conservative }
		}
		set_global_variable = { name = wm_test_tory value = this }
	}
}
global_var:wm_test_tory = {
	set_variable = { name = wm_commons_rebellions value = 2 }
	set_variable = { name = wm_commons_player_vote value = 1 }
}""" % TORY_LEADER)
    show("tory_rebel", "global_var:wm_test_tory")


def division_suite():
    phase("commons_division")
    if "w" in SUITES:
        whip_setup()
    emit("%s = { remove_character_modifier = wm_commons_public_services_modifier }" % PM)
    division("normal_bill", 2)
    total()
    number("normal_bill_total", "global_var:wm_commons_total")
    check("all_but_speaker_counted", counted_all())
    check("speaker_did_not_vote", """title:e_united_kingdom = {
	any_in_de_jure_hierarchy = {
		tier = tier_county
		holder ?= { has_character_flag = wm_speaker }
	}
	NOT = {
		any_in_de_jure_hierarchy = {
			tier = tier_county
			holder ?= {
				has_character_flag = wm_speaker
				is_target_in_global_variable_list = { name = wm_commons_voters target = this }
			}
		}
	}
}""")
    check("normal_bill_passes", "global_var:wm_commons_result = 1 global_var:wm_commons_ayes > global_var:wm_commons_noes")
    check("normal_bill_majority", "global_var:wm_commons_margin >= 50")
    check("business_cleared", "wm_commons_house_free_trigger = yes")
    emit("%s = { wm_commons_apply_result_effect = yes }" % PM)
    check("passed_bill_effect", "has_character_modifier = wm_commons_public_services_modifier", PM)


def whip_suite():
    phase("commons_whip")
    if "d" not in SUITES:
        whip_setup()
        division("whip_bill", 2)
    check("rebel_lost_whip", "NOT = { exists = var:wm_party }", "global_var:wm_test_tory")
    check("rebel_serves_pm", "liege ?= %s" % PM, "global_var:wm_test_tory")
    check("rebel_resents_leader",
          "has_opinion_modifier = { modifier = wm_commons_whip_withdrawn_opinion target = global_var:wm_test_tory_leader }",
          "global_var:wm_test_tory")
    check("rebel_in_rebel_list", "is_target_in_global_variable_list = { name = wm_commons_rebel_list target = global_var:wm_test_tory }")
    # Withdrawing the whip directly
    emit("""%s = {
	random_vassal = {
		limit = {
			wm_is_mp_trigger = yes
			var:wm_party ?= title:k_party_lib_dem
		}
		set_global_variable = { name = wm_test_lib_dem value = this }
	}
}
global_var:wm_test_lib_dem = { wm_commons_withdraw_whip_effect = yes }""" % LD_LEADER)
    check("withdrawn_mp_independent", "NOT = { exists = var:wm_party } liege ?= %s" % PM, "global_var:wm_test_lib_dem")
    check("withdrawn_mp_still_mp", "wm_is_mp_trigger = yes", "global_var:wm_test_lib_dem")
    check("lib_dem_leader_lost_a_vassal", "NOT = { any_vassal = { this = global_var:wm_test_lib_dem } }", LD_LEADER)


def rebellion():
    phase("commons_rebellion")
    emit("%s = { remove_character_modifier = wm_commons_defeated_in_commons_modifier }" % PM)
    division("revolt_bill", 3, controversy=200)
    total()
    check("revolt_all_counted", counted_all())
    check("revolt_many_rebels", "global_var:wm_commons_gov_rebels >= 150")
    check("revolt_bill_defeated", "global_var:wm_commons_result = 2 global_var:wm_commons_noes >= global_var:wm_commons_ayes")
    emit("%s = { wm_commons_apply_result_effect = yes }" % PM)
    check("defeat_effect", "has_character_modifier = wm_commons_defeated_in_commons_modifier", PM)
    check("no_election_after_bill_defeat", "NOT = { has_global_variable = wm_election_required }")


def confidence():
    phase("commons_confidence")
    emit("remove_global_variable = wm_election_required")
    # A confidence motion the government wins: its MPs are loyal
    emit("wm_commons_setup_business_effect = { TYPE = 5 MOVER = %s }" % TORY_LEADER)
    emit("wm_commons_division_effect = yes")
    for v in ("ayes", "noes", "gov_rebels"):
        number("confidence_won_%s" % v, "global_var:wm_commons_%s" % v)
    check("confidence_won", "global_var:wm_commons_result = 1 global_var:wm_commons_noes > global_var:wm_commons_ayes")
    emit("%s = { wm_commons_apply_result_effect = yes }" % PM)
    check("won_no_election", "NOT = { has_global_variable = wm_election_required }")
    check("pm_resents_mover", "has_opinion_modifier = { modifier = wm_commons_tabled_no_confidence_opinion target = %s }"
          % TORY_LEADER, PM)
    # One it loses: the government's own MPs turn on it
    emit("wm_commons_setup_business_effect = { TYPE = 5 MOVER = %s }" % TORY_LEADER)
    emit("set_global_variable = { name = wm_commons_bill_controversy value = 200 }")
    emit("wm_commons_division_effect = yes")
    for v in ("ayes", "noes", "gov_rebels"):
        number("confidence_lost_%s" % v, "global_var:wm_commons_%s" % v)
    check("confidence_lost", "global_var:wm_commons_result = 2 global_var:wm_commons_ayes > global_var:wm_commons_noes")
    emit("%s = { wm_commons_apply_result_effect = yes }" % PM)
    check("election_required", "has_global_variable = wm_election_required")
    check("lost_confidence_modifier", "has_character_modifier = wm_commons_lost_confidence_modifier", PM)
    emit("remove_global_variable = wm_election_required")


for letter in SUITES:
    {"s": setup, "d": division_suite, "w": whip_suite, "r": rebellion, "c": confidence}[letter]()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_commons.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(blocks) + "\n\tdebug_log = \"RFT done\"\n}\n"
               + "rf_test_effect_later = {\n\tdebug_log = \"RFT done\"\n}\n", encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
EVENTS.parent.mkdir(exist_ok=True)
EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
