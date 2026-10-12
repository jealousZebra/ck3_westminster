#!/usr/bin/env python3
"""Writes Westminster's coalition tests (hung parliaments, coalitions, confidence-and-supply, breakdown) into the
harness (harness/common/scripted_effects/rf_test_effects.txt), in the style of gen_elections.py.

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3). The suite runs wm_election_init_effect
itself and sets global_var:wm_test_quiet, so no events or toasts open for players (a player Prime Minister is
treated like the AI: the deals resolve at once). Everything is checked at once, so the game needn't be unpaused.
Each check logs RFT_PASS / RFT_FAIL to debug.log; numbers are logged as RFT_TIME lines ("gov_mps>=300"):

    python3 westminster/tools/ck3_test/gen_coalitions.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/coalitions.log
    python3 common/ck3_test/report.py westminster/tools/test_out/coalitions.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  values      the working majority is 325; Labour and the Lib Dems are 3 apart on the left-right scale
  majority    a general election on the 2024 polls gives a majority: no deal, outcome 1
  hung        a general election on polls with no party near 33% leaves no majority (forced hung parliament); the
              government is a coalition, confidence-and-supply or minority by the rules: the partner is the
              best-ranked party and its offer's margin is >= 0, or nobody would accept (all margins negative);
              a coalition partner's leader is the Deputy Prime Minister (diarchy on the PM)
  coalition   a forced coalition (Lib Dems, or the Conservatives if the Lib Dems govern): the partner's MPs are
              government MPs in a Commons vote (the Chief Whip counts both parties' seats, they vote aye), its
              leader is Deputy PM and not an opposition party leader
  supply      a forced confidence-and-supply deal: the partner's MPs take the government whip on a motion of no
              confidence and the Finance Bill, not on the Reform Bill; they back the government in the
              confidence vote; no Deputy PM
  ai          an AI-to-AI negotiation ends in the deal the scores say (or a minority government)
  breakdown   the junior partner walks out: the deal and the diarchy end, outcome 6, the PM resents the partner's
              leader, and its MPs no longer take the government whip
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt"
blocks = []

PM = "title:e_united_kingdom.holder"
SEATS = 650


def emit(text):
    blocks.append(text)


def log(msg):
    return 'debug_log = "%s"' % msg


def check(name, cond, scope=None):
    test = cond if scope is None else "%s = { %s }" % (scope, cond)
    emit("if = { limit = { %s } %s }\nelse = { %s }" % (test, log("RFT_PASS " + name), log("RFT_FAIL " + name)))


def check_if(name, guard, cond, skipped):
    """A check that only applies when guard holds; otherwise an RFT_DETAIL line says why it was skipped."""
    emit("if = { limit = { %s } if = { limit = { %s } %s } else = { %s } }\nelse = { %s }"
         % (guard, cond, log("RFT_PASS " + name), log("RFT_FAIL " + name), log("RFT_DETAIL %s_skipped_%s" % (name, skipped))))


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


def outcome(label):
    emit(" ".join("%s = { limit = { global_var:wm_coalition_outcome = %d } %s }"
                  % ("if" if i == 1 else "else_if", i, log("RFT_DETAIL %s_outcome_%d" % (label, i))) for i in range(1, 7))
         + " else = { %s }" % log("RFT_DETAIL %s_outcome_unset" % label))


# Party leaders with a seat serve the PM, and party MPs their leader (as gen_elections.py checks)
LEADERS_SERVE_PM = ("NOT = { any_in_de_jure_hierarchy = { tier = tier_county exists = holder holder = { "
                    "var:wm_party.holder ?= this NOT = { this = %s } NOT = { liege = %s } } } }" % (PM, PM))
NO_DEAL = ("NOT = { has_global_variable = wm_coalition_junior } NOT = { has_global_variable = wm_coalition_partner } "
           "NOT = { has_global_variable = wm_coalition_supply_partner }")
PM_NO_DPM = "%s = { NOT = { has_diarchy_type = wm_coalition_deputyship } }" % PM


def setup():
    phase("setup")
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    emit("wm_election_init_effect = yes")
    emit("remove_global_variable = wm_election_required\nremove_global_variable = wm_commons_pending")
    check("majority_is_325", "wm_coalition_majority_value = 325")
    emit("set_global_variable = { name = wm_coalition_senior value = title:k_party_labour }")
    check("lab_ld_distance_3", "wm_coalition_distance_value = 3", "title:k_party_lib_dem")
    emit("set_global_variable = { name = wm_coalition_senior value = title:k_party_conservative }")
    check("con_dup_close", "wm_coalition_distance_value = 1", "title:k_party_dup")
    check("con_ld_apart", "wm_coalition_distance_value = 5", "title:k_party_lib_dem")


def majority():
    phase("majority_election")
    emit("wm_polls_init_effect = yes")
    emit("wm_election_general_effect = yes")
    number("majority_largest_seats", "global_var:wm_el_largest_seats")
    show("majority_pm", PM)
    check("majority_election_has_majority", "global_var:wm_el_largest_seats >= wm_coalition_majority_value")
    check("majority_outcome_1", "global_var:wm_coalition_outcome = 1")
    check("majority_no_deal", NO_DEAL)
    check("majority_pm_no_deputy", PM_NO_DPM)


def hung():
    phase("hung_election")
    # No party near a third of the vote: a hung parliament
    emit("wm_polls_init_effect = yes\n"
         "set_global_variable = { name = wm_poll_lab value = 240 }\n"
         "set_global_variable = { name = wm_poll_con value = 280 }\n"
         "set_global_variable = { name = wm_poll_ld value = 150 }\n"
         "set_global_variable = { name = wm_poll_ruk value = 180 }\n"
         "set_global_variable = { name = wm_poll_grn value = 60 }\n"
         "wm_polls_normalise_effect = yes")
    emit("wm_election_general_effect = yes")
    for p in ("lab", "con", "ld", "ruk", "snp"):
        number("hung_seats_%s" % p, "global_var:wm_seats_%s" % p, step=10, top=400)
    show("hung_pm", PM)
    show("hung_largest", "global_var:wm_el_largest")
    outcome("hung")
    emit("if = { limit = { has_global_variable = wm_coalition_choice_1 } global_var:wm_coalition_choice_1 = { %s debug_log_scopes = yes } }"
         % log("RFT_DETAIL hung_best_partner"))
    check("hung_no_majority", "global_var:wm_el_largest_seats < wm_coalition_majority_value")
    check("hung_leaders_serve_pm", LEADERS_SERVE_PM, "title:e_united_kingdom")
    check("hung_senior_is_pm_party", "has_global_variable = wm_coalition_senior global_var:wm_coalition_senior = %s.var:wm_party" % PM)
    check("hung_not_majority_outcome", "OR = { global_var:wm_coalition_outcome = 2 global_var:wm_coalition_outcome = 3 "
          "global_var:wm_coalition_outcome = 4 }")
    # The rules: a deal is with the best-ranked partner on an offer it accepts; minority only if nobody would
    check("hung_follows_rules", """OR = {
	AND = {
		OR = {
			global_var:wm_coalition_outcome = 3
			global_var:wm_coalition_outcome = 4
		}
		has_global_variable = wm_coalition_junior
		global_var:wm_coalition_junior = global_var:wm_coalition_choice_1
		NOT = { global_var:wm_coalition_junior = global_var:wm_coalition_senior }
		global_var:wm_coalition_junior = { wm_coalition_offer_margin_value >= 0 }
	}
	AND = {
		global_var:wm_coalition_outcome = 2
		NOT = { has_global_variable = wm_coalition_junior }
		OR = {
			NOT = { has_global_variable = wm_coalition_choice_1 }
			global_var:wm_coalition_choice_1 = {
				wm_coalition_margin_coalition_1p_value < 0
				wm_coalition_margin_coalition_2p_value < 0
				wm_coalition_margin_supply_value < 0
			}
		}
	}
}""")
    check_if("hung_coalition_has_deputy_pm", "global_var:wm_coalition_outcome = 3",
             "has_global_variable = wm_coalition_partner global_var:wm_coalition_dpm = global_var:wm_coalition_partner.holder "
             "global_var:wm_coalition_dpm = { is_diarch_of_target = %s has_character_modifier = wm_coalition_deputy_pm_modifier } "
             "%s = { has_diarchy_type = wm_coalition_deputyship }" % (PM, PM), "no_coalition")
    check_if("hung_supply_partner_set", "global_var:wm_coalition_outcome = 4",
             "has_global_variable = wm_coalition_supply_partner NOT = { has_global_variable = wm_coalition_partner } " + PM_NO_DPM,
             "no_supply_deal")


def pick_partner():
    """The Lib Dems, or the Conservatives if the Lib Dems lead the government."""
    emit("wm_coalition_clear_effect = yes")
    emit("set_global_variable = { name = wm_coalition_senior value = %s.var:wm_party }" % PM)
    emit("if = { limit = { global_var:wm_coalition_senior = title:k_party_lib_dem } "
         "set_global_variable = { name = wm_test_partner value = title:k_party_conservative } }\n"
         "else = { set_global_variable = { name = wm_test_partner value = title:k_party_lib_dem } }")
    emit("wm_election_count_seats_effect = yes")
    emit("global_var:wm_coalition_senior = { set_global_variable = { name = wm_test_senior_seats value = wm_coalition_party_seats_value } }\n"
         "global_var:wm_test_partner = { set_global_variable = { name = wm_test_partner_seats value = wm_coalition_party_seats_value } }\n"
         "set_global_variable = { name = wm_test_expected value = global_var:wm_test_senior_seats }\n"
         "change_global_variable = { name = wm_test_expected add = global_var:wm_test_partner_seats }")
    number("senior_seats", "global_var:wm_test_senior_seats")
    number("partner_seats", "global_var:wm_test_partner_seats")
    show("test_partner", "global_var:wm_test_partner")


def form(kind, seats, policy):
    emit("set_global_variable = { name = wm_coalition_talks_partner value = global_var:wm_test_partner }\n"
         "set_global_variable = { name = wm_coalition_offer_kind value = %d }\n"
         "set_global_variable = { name = wm_coalition_offer_seats value = %d }\n"
         "set_global_variable = { name = wm_coalition_offer_policy value = %d }\n"
         "wm_coalition_form_effect = yes" % (kind, seats, policy))


def find_partner_mp():
    emit("remove_global_variable = wm_test_partner_mp\n"
         "global_var:wm_test_partner.holder ?= { random_vassal = { limit = { wm_is_mp_trigger = yes "
         "var:wm_party ?= global_var:wm_test_partner } set_global_variable = { name = wm_test_partner_mp value = this } } }")
    check("partner_backbencher_found", "has_global_variable = wm_test_partner_mp")


def coalition():
    phase("coalition")
    pick_partner()
    form(1, 1, 1)
    check("coalition_outcome_3", "global_var:wm_coalition_outcome = 3")
    check("coalition_partner_set", "global_var:wm_coalition_partner = global_var:wm_test_partner "
          "global_var:wm_coalition_junior = global_var:wm_test_partner NOT = { has_global_variable = wm_coalition_supply_partner }")
    check("coalition_deputy_pm_diarchy", "is_diarch_of_target = %s" % PM, "global_var:wm_test_partner.holder")
    check("coalition_pm_has_diarchy", "has_diarchy_type = wm_coalition_deputyship", PM)
    check("coalition_deputy_pm_modifier", "has_character_modifier = wm_coalition_deputy_pm_modifier", "global_var:wm_test_partner.holder")
    check("coalition_compromise_modifier", "has_character_modifier = wm_coalition_compromise_modifier", PM)
    check("coalition_partner_opinion", "has_opinion_modifier = { modifier = wm_coalition_partner_opinion target = global_var:wm_test_partner.holder }", PM)
    check("coalition_partner_leader_not_opposition", "NOT = { wm_commons_is_opposition_party_leader_trigger = yes }",
          "global_var:wm_test_partner.holder")
    check("coalition_breakdown_chance_in_range", "wm_coalition_breakdown_chance_value >= 0 wm_coalition_breakdown_chance_value <= 30")
    find_partner_mp()
    # A Commons vote: the partner's MPs are government MPs
    emit("wm_commons_setup_business_effect = { TYPE = 2 MOVER = %s }" % PM)
    check("coalition_partner_mp_is_government", "wm_commons_is_government_mp_trigger = yes wm_commons_whipped_with_government_trigger = yes",
          "global_var:wm_test_partner_mp")
    emit("wm_commons_forecast_effect = yes")
    number("coalition_gov_mps", "global_var:wm_commons_gov_mps")
    check("coalition_whip_counts_both_parties", "global_var:wm_commons_gov_mps = global_var:wm_test_expected")
    emit("wm_commons_division_effect = yes")
    for v in ("ayes", "noes", "abstentions", "gov_rebels"):
        number("coalition_vote_%s" % v, "global_var:wm_commons_%s" % v)
    check("coalition_partner_votes_with_government", "global_var:wm_commons_gov_votes > global_var:wm_test_senior_seats")
    emit("set_global_variable = { name = wm_test_floor value = global_var:wm_test_expected }\n"
         "change_global_variable = { name = wm_test_floor add = -40 }")
    check("coalition_vote_nearly_all_government", "global_var:wm_commons_gov_votes >= global_var:wm_test_floor")
    check("coalition_partner_mp_voted", "is_target_in_global_variable_list = { name = wm_commons_voters target = global_var:wm_test_partner_mp }")
    emit("remove_global_variable = wm_commons_pending")


def supply():
    phase("supply")
    pick_partner()
    form(2, 0, 0)
    check("supply_outcome_4", "global_var:wm_coalition_outcome = 4")
    check("supply_partner_set", "global_var:wm_coalition_supply_partner = global_var:wm_test_partner "
          "NOT = { has_global_variable = wm_coalition_partner }")
    check("supply_no_deputy_pm", PM_NO_DPM)
    check("supply_deal_modifier", "has_character_modifier = wm_coalition_supply_deal_modifier", "global_var:wm_test_partner.holder")
    find_partner_mp()
    # Not on the Reform Bill
    emit("wm_commons_setup_business_effect = { TYPE = 3 MOVER = %s }" % PM)
    check("supply_mp_free_on_reform_bill", "NOT = { wm_commons_whipped_with_government_trigger = yes } "
          "NOT = { wm_commons_is_government_mp_trigger = yes }", "global_var:wm_test_partner_mp")
    emit("wm_commons_forecast_effect = yes")
    check("supply_reform_bill_counts_senior_only", "global_var:wm_commons_gov_mps = global_var:wm_test_senior_seats")
    emit("remove_global_variable = wm_commons_pending")
    # The Finance Bill: with the government
    emit("wm_commons_setup_business_effect = { TYPE = 1 MOVER = %s }" % PM)
    check("supply_mp_backs_finance_bill", "wm_commons_whipped_with_government_trigger = yes", "global_var:wm_test_partner_mp")
    emit("remove_global_variable = wm_commons_pending")
    # A motion of no confidence: with the government
    emit("wm_commons_setup_business_effect = { TYPE = 5 MOVER = %s }" % PM)
    check("supply_mp_backs_government_on_confidence", "wm_commons_whipped_with_government_trigger = yes "
          "NOT = { wm_commons_is_government_mp_trigger = yes }", "global_var:wm_test_partner_mp")
    emit("wm_commons_forecast_effect = yes")
    number("supply_confidence_gov_mps", "global_var:wm_commons_gov_mps")
    check("supply_confidence_counts_both_parties", "global_var:wm_commons_gov_mps = global_var:wm_test_expected")
    emit("wm_commons_division_effect = yes")
    for v in ("ayes", "noes", "abstentions", "gov_rebels"):
        number("supply_confidence_%s" % v, "global_var:wm_commons_%s" % v)
    emit("set_global_variable = { name = wm_test_floor value = global_var:wm_test_expected }\n"
         "change_global_variable = { name = wm_test_floor add = -15 }")
    check("supply_partner_backs_confidence", "global_var:wm_commons_gov_votes >= global_var:wm_test_floor "
          "global_var:wm_commons_gov_votes > global_var:wm_test_senior_seats")
    check_if("supply_government_survives", "global_var:wm_test_expected >= wm_coalition_majority_value",
             "global_var:wm_commons_result = 1", "deal_short_of_majority")
    emit("remove_global_variable = wm_commons_pending\nremove_global_variable = wm_election_required")


def ai():
    phase("ai_negotiation")
    pick_partner()
    emit("set_global_variable = { name = wm_coalition_talks_partner value = global_var:wm_test_partner }\n"
         "wm_coalition_ai_negotiate_effect = yes")
    outcome("ai")
    check("ai_deal_by_score", """OR = {
	AND = {
		OR = {
			global_var:wm_coalition_outcome = 3
			global_var:wm_coalition_outcome = 4
		}
		global_var:wm_coalition_junior = global_var:wm_test_partner
		global_var:wm_test_partner = { wm_coalition_offer_margin_value >= 0 }
	}
	AND = {
		global_var:wm_coalition_outcome = 2
		NOT = { has_global_variable = wm_coalition_junior }
		global_var:wm_test_partner = {
			wm_coalition_margin_coalition_1p_value < 0
			wm_coalition_margin_coalition_2p_value < 0
			wm_coalition_margin_supply_value < 0
		}
	}
}""")


def breakdown():
    phase("breakdown")
    pick_partner()
    form(1, 1, 0)
    find_partner_mp()
    check("breakdown_setup_coalition", "global_var:wm_coalition_outcome = 3 has_global_variable = wm_coalition_dpm")
    emit("set_global_variable = { name = wm_test_dpm value = global_var:wm_coalition_dpm }")
    emit("global_var:wm_test_partner.holder = { wm_coalition_breakdown_effect = yes }")
    check("breakdown_outcome_6", "global_var:wm_coalition_outcome = 6")
    check("breakdown_deal_ended", NO_DEAL)
    check("breakdown_diarchy_ended", PM_NO_DPM)
    check("breakdown_dpm_modifier_removed", "NOT = { has_character_modifier = wm_coalition_deputy_pm_modifier }", "global_var:wm_test_dpm")
    check("breakdown_pm_resents_partner", "has_opinion_modifier = { modifier = wm_coalition_walked_out_opinion target = global_var:wm_test_dpm }", PM)
    emit("wm_commons_setup_business_effect = { TYPE = 2 MOVER = %s }" % PM)
    check("breakdown_partner_mp_not_government", "NOT = { wm_commons_is_government_mp_trigger = yes } "
          "NOT = { wm_commons_whipped_with_government_trigger = yes }", "global_var:wm_test_partner_mp")
    emit("remove_global_variable = wm_commons_pending")


setup()
majority()
hung()
coalition()
supply()
ai()
breakdown()
emit("wm_coalition_clear_effect = yes\nremove_global_variable = wm_test_quiet")

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_coalitions.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(blocks) + "\n\tdebug_log = \"RFT done\"\n}\n"
               + "rf_test_effect_later = {\n\tdebug_log = \"RFT done\"\n}\n", encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
EVENTS.parent.mkdir(exist_ok=True)
EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
