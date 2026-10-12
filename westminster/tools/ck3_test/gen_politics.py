#!/usr/bin/env python3
"""Writes Westminster's tests for public trust, campaign spending, party wings, devolution and ideology (faith)
into the harness (harness/common/scripted_effects/rf_test_effects.txt), in the style of gen_campaign.py.

The save must be made after the ideologies and the wings were added to the bookmark (build_2024.py): run
tools/ck3_test/make_save.sh first. The suite sets global_var:wm_test_quiet (no pop-ups) and checks everything at
once, so the game can stay paused:

    python3 westminster/tools/ck3_test/gen_politics.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/politics.log
    python3 common/ck3_test/report.py westminster/tools/test_out/politics.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  faith       the PM and his seat are Social Democrat, the monarch "Not Stated"; nobody is Catholic (the ideology
              suite is gen_ideology.py)
  trust       starts at the era's level; changes are kept within 0-100; low trust raises the riot chance; low trust
              lifts a small party's poll and high trust the government's; a riot starting costs trust; a popular
              bill (the PM's modifier) adds trust once and pleases Labour's left; a broken promise and a clean
              campaign move it; the UI value matches; the monthly tick and drift run
  spend       a press campaign lifts the spender's party and costs money; a smear lowers the rival's poll and trust;
              a backfire costs the spender's party, plants the secret, ends the campaign and annoys the rival
              leader; stopping, a campaign's time limit, finding rivals, calling in a favour (a hook)
  wings       the 2024 Labour and Conservative MPs have wings from history (not the leaders), with badges and
              matching Commons leans, following their ideology; a new MP is given their ideology's wing; the
              monthly tick counts members; courting a wing; an unhappy wing resents its leader; a furious wing
              challenges; a carried challenge opens a leadership contest with the challenger on the ballot
              (Conservatives, then the PM's Labour)
  devolution  the nations' starting numbers; the monthly tick keeps support in range and marks nationalist-led
              governments; devolving and clawing back powers; a referendum request is answered; Yes and No votes;
              Stormont collapses and is restored
"""
import os
from pathlib import Path

# RFT_OUT=<file> writes elsewhere (to look at the suite without touching the harness)
OUT = Path(os.environ.get("RFT_OUT") or Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt")
blocks = []
PM = "title:e_united_kingdom.holder"
CON = "title:k_party_conservative.holder"
LD = "title:k_party_lib_dem.holder"


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


def gvar(name, value):
    emit("set_global_variable = { name = %s value = %s }" % (name, value))


def setup():
    phase("setup")
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    emit("wm_election_init_effect = yes")
    for v in ("wm_el_scheduled", "wm_el_campaign", "wm_trust_campaign_seen", "wm_trust_promise_pm"):
        emit("remove_global_variable = %s" % v)
    gvar("wm_public_trust", "wm_trust_start")
    emit("wm_wing_init_effect = yes")
    emit("wm_devolution_init_effect = yes")
    check("pm_exists", "exists = %s" % PM)
    check("con_leader_exists", "exists = %s" % CON)
    check("ld_leader_exists", "exists = %s" % LD)


def faith():
    phase("faith")
    check("pm_social_democrat", "faith = faith:wm_ideo_social_democrat", PM)
    check("monarch_faith_not_stated", "faith = faith:wm_faith_not_stated", "title:k_wm_crown.holder")
    check("seat_social_democrat", "faith = faith:wm_ideo_social_democrat", "title:c_aldershot")
    check("nobody_catholic", "NOT = { any_living_character = { faith = faith:catholic } }")
    check("no_catholic_seat", "NOT = { title:e_united_kingdom = { any_in_de_jure_hierarchy = { tier = tier_county faith = faith:catholic } } }")


def trust():
    phase("trust")
    check("trust_starts_at_era_level", "global_var:wm_public_trust = wm_trust_start")
    check("ui_value_matches", "wm_ui_public_trust = global_var:wm_public_trust")
    gvar("wm_public_trust", 99)
    emit("wm_trust_change_effect = { AMOUNT = 5 }")
    check("trust_capped_at_100", "global_var:wm_public_trust = 100")
    gvar("wm_public_trust", 1)
    emit("wm_trust_change_effect = { AMOUNT = -5 }")
    check("trust_floored_at_0", "global_var:wm_public_trust = 0")
    # Riot chance
    gvar("wm_public_trust", 10)
    gvar("wm_test_riot_low", "wm_trust_riot_chance")
    gvar("wm_public_trust", 70)
    check("low_trust_more_riots", "wm_trust_riot_chance < global_var:wm_test_riot_low")
    check("riot_chance_in_range", "wm_trust_riot_chance >= 50 global_var:wm_test_riot_low <= 95")
    # Polls: low trust lifts a small party; high trust the government's party; a big opposition party is untouched
    gvar("wm_public_trust", 10)
    gvar("wm_test_before", "global_var:wm_poll_grn")
    emit("wm_trust_poll_effect = { P = grn }")
    check("low_trust_lifts_small_party", "global_var:wm_poll_grn > global_var:wm_test_before")
    gvar("wm_public_trust", 50)
    gvar("wm_test_before", "global_var:wm_poll_grn")
    emit("wm_trust_poll_effect = { P = grn }")
    check("trust_50_no_small_party_lift", "global_var:wm_poll_grn = global_var:wm_test_before")
    gvar("wm_public_trust", 80)
    gvar("wm_test_before", "global_var:wm_poll_lab")
    emit("wm_trust_poll_effect = { P = lab }")
    check("high_trust_lifts_government", "global_var:wm_poll_lab > global_var:wm_test_before")
    gvar("wm_test_before", "global_var:wm_poll_con")
    emit("wm_trust_poll_effect = { P = con }")
    check("big_opposition_party_untouched", "global_var:wm_poll_con = global_var:wm_test_before")
    check("governs_trigger_lab", "wm_polls_governs_lab = yes")
    check("governs_trigger_not_con", "wm_polls_governs_con = no")
    emit("wm_polls_drift_all_effect = yes")
    check("polls_still_add_up", "wm_polls_total > 990 wm_polls_total < 1010")
    # A riot starting costs trust
    gvar("wm_public_trust", 40)
    emit("title:c_aldershot = { if = { limit = { wm_riot_is_active_trigger = yes } wm_riot_end_effect = yes } }")
    emit("title:c_aldershot = { wm_riot_start_effect = { DEMAND = 1 } }")
    check("riot_costs_trust", "global_var:wm_public_trust < 40")
    emit("title:c_aldershot = { wm_riot_end_effect = yes }")
    # The government's record: a popular bill, counted once, and Labour's wings react
    gvar("wm_public_trust", 40)
    gvar("wm_test_w1", "global_var:wm_wing_approval_1")
    gvar("wm_test_w3", "global_var:wm_wing_approval_3")
    emit("%s = { remove_character_flag = wm_trust_seen_wm_commons_public_services_modifier "
         "add_character_modifier = { modifier = wm_commons_public_services_modifier years = 1 } wm_trust_watch_pm_effect = yes }" % PM)
    check("popular_bill_adds_trust", "global_var:wm_public_trust = 43")
    emit("%s = { wm_trust_watch_pm_effect = yes }" % PM)
    check("popular_bill_counted_once", "global_var:wm_public_trust = 43")
    check("left_wing_likes_spending", "global_var:wm_wing_approval_1 > global_var:wm_test_w1")
    check("centrists_less_keen", "global_var:wm_wing_approval_3 < global_var:wm_test_w3")
    emit("%s = { remove_character_modifier = wm_commons_public_services_modifier wm_trust_watch_pm_effect = yes }" % PM)
    check("seen_flag_cleared", "NOT = { has_character_flag = wm_trust_seen_wm_commons_public_services_modifier }", PM)
    # A promise to protesters that lapses is broken
    gvar("wm_public_trust", 40)
    gvar("wm_el_months", 20)
    emit("%s = { add_character_flag = wm_early_election_promised }" % PM)
    emit("wm_trust_promise_watch_effect = yes")
    check("promise_noted", "exists = global_var:wm_trust_promise_pm")
    emit("%s = { remove_character_flag = wm_early_election_promised }" % PM)
    emit("wm_trust_promise_watch_effect = yes")
    check("broken_promise_costs_trust", "global_var:wm_public_trust = 34 NOT = { exists = global_var:wm_trust_promise_pm }")
    # A clean general election campaign
    gvar("wm_public_trust", 40)
    gvar("wm_el_scheduled", "yes")
    emit("wm_trust_campaign_watch_effect = yes")
    emit("remove_global_variable = wm_el_scheduled")
    emit("wm_trust_campaign_watch_effect = yes")
    check("clean_campaign_adds_trust", "global_var:wm_public_trust = 43")
    # The month: drift back towards the era's level
    gvar("wm_public_trust", 80)
    emit("wm_trust_monthly_effect = yes")
    check("trust_drifts_to_baseline", "global_var:wm_public_trust < 80 global_var:wm_public_trust > 70")
    emit("wm_trust_set_piece_effect = yes")
    check("set_piece_keeps_range", "global_var:wm_public_trust >= 0 global_var:wm_public_trust <= 100")
    emit("%s = { wm_trust_clean_up_pledge_effect = yes }" % PM)
    check("clean_up_pledge_flag", "has_character_flag = wm_trust_clean_pledge", PM)
    emit("wm_trust_scandal_effect = { AMOUNT = -1 }")
    check("scandal_breaks_pledge", "NOT = { has_character_flag = wm_trust_clean_pledge }", PM)
    gvar("wm_public_trust", "wm_trust_start")


def spend():
    phase("spend")
    emit("%s = { add_gold = 1000 } %s = { add_gold = 1000 }" % (CON, LD))
    emit("%s = { wm_spend_start_effect = { KIND = 1 TARGET = var:wm_party } }" % CON)
    check("press_campaign_started", "var:wm_spend_kind = 1 var:wm_spend_months = 0", CON)
    check("press_on_campaigner_list", "any_in_global_list = { variable = wm_spend_campaigners this = %s }" % CON)
    gvar("wm_test_before", "global_var:wm_poll_con")
    emit("%s = { set_variable = { name = wm_test_gold value = gold } wm_spend_month_effect = yes }" % CON)
    check("press_lifts_own_party", "global_var:wm_poll_con > global_var:wm_test_before")
    check("press_costs_money", "gold < var:wm_test_gold var:wm_spend_months = 1", CON)
    # Smear: the Lib Dem leader targets the government's party
    emit("%s = { wm_spend_find_rivals_effect = yes }" % LD)
    check("ld_first_rival_is_pm", "scope:wm_spend_rival_1 = %s" % PM)
    check("ld_rival_party_is_labour", "scope:wm_spend_party_1 = title:k_party_labour")
    emit("%s = { wm_spend_start_effect = { KIND = 2 TARGET = title:k_party_labour } }" % LD)
    gvar("wm_public_trust", 40)
    gvar("wm_test_before", "global_var:wm_poll_lab")
    # Run the smear's month without the backfire roll: the poll and trust part of wm_spend_month_effect
    emit("%s = { set_global_variable = { name = wm_campaign_amount value = wm_spend_smear_leader } "
         "wm_campaign_party_poll_effect = { PARTY = var:wm_spend_target } wm_trust_smear_month_effect = yes }" % LD)
    check("smear_lowers_rival", "global_var:wm_poll_lab < global_var:wm_test_before")
    check("smear_costs_trust", "global_var:wm_public_trust < 40")
    gvar("wm_test_before", "global_var:wm_poll_ld")
    emit("%s = { wm_spend_backfire_effect = yes }" % LD)
    check("backfire_costs_own_party", "global_var:wm_poll_ld < global_var:wm_test_before")
    check("backfire_plants_secret", "any_secret = { type = wm_secret_smear_campaign }", LD)
    check("backfire_ends_campaign", "NOT = { exists = var:wm_spend_kind }", LD)
    emit("%s = { save_scope_as = wm_test_ld }" % LD)
    check("backfire_annoys_rival_leader", "has_opinion_modifier = { target = scope:wm_test_ld modifier = wm_spend_smeared_opinion }", PM)
    # Time limit and stopping
    emit("%s = { set_variable = { name = wm_spend_months value = wm_spend_max_months } wm_spend_month_effect = yes }" % CON)
    check("campaign_ends_after_a_year", "NOT = { exists = var:wm_spend_kind }", CON)
    emit("%s = { wm_spend_start_effect = { KIND = 1 TARGET = var:wm_party } wm_spend_stop_effect = yes }" % CON)
    check("stop_ends_campaign", "NOT = { exists = var:wm_spend_kind } NOT = { any_in_global_list = { variable = wm_spend_campaigners this = %s } }" % CON, CON)
    # Calling in a favour
    emit("%s = { wm_spend_find_rivals_effect = yes }" % CON)
    check("con_first_rival_is_pm", "scope:wm_spend_rival_1 = %s" % PM)
    emit("%s = { save_scope_as = wm_test_pm }" % PM)
    emit("%s = { wm_spend_favour_effect = { RIVAL = scope:wm_test_pm } }" % CON)
    check("favour_gives_hook", "has_hook = scope:wm_test_pm", CON)
    emit("wm_spend_monthly_effect = yes")
    check("monthly_runs", "exists = %s" % PM)
    gvar("wm_public_trust", "wm_trust_start")


def wings():
    phase("wings")
    check("labour_mps_have_wings", "any_living_character = { var:wm_wing ?= 2 count >= 50 }")
    check("all_three_labour_wings", "any_living_character = { var:wm_wing ?= 1 } any_living_character = { var:wm_wing ?= 3 }")
    check("conservative_wings", "any_living_character = { var:wm_wing ?= 4 } any_living_character = { var:wm_wing ?= 5 } "
          "any_living_character = { var:wm_wing ?= 6 }")
    check("leaders_have_no_wing", "NOT = { has_variable = wm_wing }", PM)
    check("con_leader_no_wing", "NOT = { has_variable = wm_wing }", CON)
    check("wing_badges", "NOT = { any_living_character = { var:wm_wing ?= 1 NOT = { has_character_modifier = wm_wing_badge_1 } } }")
    check("wing_commons_lean", "NOT = { any_living_character = { var:wm_wing ?= 5 NOT = { var:wm_commons_wing ?= 1 } } } "
          "NOT = { any_living_character = { var:wm_wing ?= 1 NOT = { var:wm_commons_wing ?= -1 } } }")
    check("no_wings_outside_lab_con", "NOT = { any_living_character = { has_variable = wm_wing "
          "NOT = { var:wm_party ?= title:k_party_labour } NOT = { var:wm_party ?= title:k_party_conservative } } }")
    # A new MP gets a wing
    emit("%s = { random_vassal = { limit = { has_variable = wm_wing wm_is_mp_trigger = yes } save_scope_as = wm_test_mp } }" % PM)
    emit("scope:wm_test_mp = { wm_wing_leave_effect = yes }")
    check("leave_removes_wing", "NOT = { has_variable = wm_wing } NOT = { has_character_modifier = wm_wing_badge_1 }", "scope:wm_test_mp")
    emit("scope:wm_test_mp = { wm_wing_assign_effect = yes }")
    check("new_mp_gets_labour_wing", "var:wm_wing >= 1 var:wm_wing <= 3", "scope:wm_test_mp")
    check("new_mp_wing_follows_ideology", "OR = { AND = { var:wm_wing = 1 faith = faith:wm_ideo_socialist } "
          "AND = { var:wm_wing = 2 faith = faith:wm_ideo_social_democrat } AND = { var:wm_wing = 3 faith = faith:wm_ideo_centrist } }",
          "scope:wm_test_mp")
    # The month
    emit("wm_wing_monthly_effect = yes")
    for w in range(1, 7):
        check("wing_%d_counted" % w, "global_var:wm_wing_size_%d >= 1 global_var:wm_wing_approval_%d >= 0 global_var:wm_wing_approval_%d <= 100" % (w, w, w))
    emit("%s = { save_scope_as = wm_test_pm }" % PM)
    # Courting a wing
    gvar("wm_wing_approval_1", 50)
    gvar("wm_wing_approval_2", 50)
    emit("%s = { wm_wing_court_effect = { WING = 1 } }" % PM)
    check("courted_wing_up", "global_var:wm_wing_approval_1 = 65")
    check("other_wing_down", "global_var:wm_wing_approval_2 = 46")
    # An unhappy wing resents the leader
    gvar("wm_wing_approval_1", 5)
    gvar("wm_wing_furious_1", 0)
    emit("wm_wing_month_effect = { WING = 1 PARTY = k_party_labour KEY = labour }")
    check("unhappy_wing_resents_leader", "any_living_character = { var:wm_wing ?= 1 "
          "has_opinion_modifier = { target = scope:wm_test_pm modifier = wm_wing_disgruntled_opinion } }")
    check("fury_counted", "global_var:wm_wing_furious_1 = 1")
    # A furious wing challenges (the AI leader concedes or faces them down)
    emit("remove_global_variable = wm_wing_challenge_cd_conservative")
    gvar("wm_wing_approval_5", 2)
    gvar("wm_wing_furious_5", 2)
    emit("%s = { save_scope_as = wm_test_con_leader }" % CON)
    emit("wm_wing_month_effect = { WING = 5 PARTY = k_party_conservative KEY = conservative }")
    check("challenge_happened", "has_global_variable = wm_wing_challenge_cd_conservative global_var:wm_wing_furious_5 = 0")
    emit("if = { limit = { title:k_party_conservative.holder = scope:wm_test_con_leader } %s } else = { %s }"
         % (log("RFT_DETAIL challenge_survived"), log("RFT_DETAIL challenge_carried")))
    # A carried challenge (non-PM) goes to a Conservative leadership contest with the challenger on the ballot
    # (the furious-wing step above may already have opened a contest, if its duel went the challenger's way)
    emit("title:k_party_conservative = { if = { limit = { has_variable = wm_lead_state } wm_election_leadership_end_effect = yes } }")
    emit("%s = { ordered_vassal = { limit = { var:wm_wing ?= 6 wm_is_mp_trigger = yes } order_by = prestige save_scope_as = wm_test_challenger } }" % CON)
    emit("%s = { save_scope_as = wm_test_con_leader }" % CON)
    gvar("wm_wing_challenge_wing", 6)
    gvar("wm_wing_challenger", "scope:wm_test_challenger")
    emit("scope:wm_test_con_leader = { wm_wing_challenge_carried_effect = yes }")
    check("challenge_opens_contest", "var:wm_lead_state = 1 var:wm_lead_kind = 2 var:wm_lead_incumbent = scope:wm_test_con_leader",
          "title:k_party_conservative")
    check("challenger_on_ballot", "is_target_in_variable_list = { name = wm_lead_candidates target = scope:wm_test_challenger }",
          "title:k_party_conservative")
    check("leader_keeps_party_meanwhile", "title:k_party_conservative.holder = scope:wm_test_con_leader")


def devolution():
    phase("devolution")
    check("scotland_start", "var:wm_dev_support = wm_dev_start_support_scotland var:wm_dev_powers = 7", "title:k_gov_scotland")
    check("wales_start", "var:wm_dev_powers = 5", "title:k_gov_wales")
    check("ni_start", "var:wm_dev_stability = wm_dev_start_stability NOT = { has_variable = wm_dev_suspended }", "title:k_gov_northern_ireland")
    emit("wm_devolution_monthly_effect = yes")
    check("support_in_range", "var:wm_dev_support >= 5 var:wm_dev_support <= 90", "title:k_gov_scotland")
    check("scotland_nationalist_led", "has_variable = wm_dev_nationalist_led", "title:k_gov_scotland")
    check("wales_not_nationalist_led", "NOT = { has_variable = wm_dev_nationalist_led }", "title:k_gov_wales")
    check("ui_support_matches", "wm_ui_dev_support_scotland = title:k_gov_scotland.var:wm_dev_support")
    # Devolve and claw back
    emit("title:k_gov_scotland = { save_scope_as = wm_dev_gov set_variable = { name = wm_dev_support value = 50 } }")
    emit("%s = { wm_devolution_devolve_effect = yes }" % PM)
    check("devolve_adds_power", "var:wm_dev_powers = 8 var:wm_dev_support = 47", "title:k_gov_scotland")
    check("devolve_pleases_fm", "has_opinion_modifier = { target = scope:wm_test_pm modifier = wm_dev_devolved_opinion }", "title:k_gov_scotland.holder")
    emit("%s = { wm_devolution_claw_back_effect = yes }" % PM)
    check("claw_back_removes_power", "var:wm_dev_powers = 7 var:wm_dev_support = 50", "title:k_gov_scotland")
    # A request for a referendum is answered (the AI path)
    emit("title:k_gov_scotland = { remove_variable = wm_dev_ref_cooldown remove_variable = wm_dev_ref_months "
         "set_variable = { name = wm_dev_support value = 60 } save_scope_as = wm_dev_gov wm_devolution_request_effect = yes }")
    check("request_answered", "has_variable = wm_dev_ref_cooldown OR = { has_variable = wm_dev_ref_months var:wm_dev_powers = 8 var:wm_dev_support = 64 }",
          "title:k_gov_scotland")
    # Referendums
    emit("title:k_gov_scotland = { set_variable = { name = wm_dev_support value = 85 } wm_devolution_referendum_effect = { NAT = scotland } }")
    check("yes_vote", "var:wm_dev_ref_yes > 50 has_variable = wm_dev_indep_mandate var:wm_dev_powers = 10 has_variable = wm_dev_ref_cooldown",
          "title:k_gov_scotland")
    emit("title:k_gov_wales = { set_variable = { name = wm_dev_support value = 10 } wm_devolution_referendum_effect = { NAT = wales } }")
    check("no_vote", "var:wm_dev_ref_yes < 50 NOT = { has_variable = wm_dev_indep_mandate } var:wm_dev_support = 5", "title:k_gov_wales")
    # Stormont
    emit("title:k_gov_northern_ireland = { wm_devolution_stormont_collapse_effect = yes }")
    check("stormont_suspended", "has_variable = wm_dev_suspended", "title:k_gov_northern_ireland")
    check("fm_suspended_modifier", "has_character_modifier = wm_dev_assembly_suspended_modifier", "title:k_gov_northern_ireland.holder")
    emit("title:k_gov_northern_ireland = { wm_devolution_stormont_restore_effect = yes }")
    check("stormont_restored", "NOT = { has_variable = wm_dev_suspended } var:wm_dev_stability = 60", "title:k_gov_northern_ireland")
    check("fm_modifier_cleared", "NOT = { has_character_modifier = wm_dev_assembly_suspended_modifier }", "title:k_gov_northern_ireland.holder")


def pm_challenge():
    # Last: a Labour wing topples the Prime Minister
    phase("pm_challenge")
    emit("%s = { save_scope_as = wm_test_old_pm ordered_vassal = { limit = { var:wm_wing ?= 2 wm_is_mp_trigger = yes } "
         "order_by = prestige save_scope_as = wm_test_challenger } }" % PM)
    gvar("wm_wing_challenge_wing", 2)
    gvar("wm_wing_challenger", "scope:wm_test_challenger")
    emit("scope:wm_test_old_pm = { wm_wing_challenge_carried_effect = yes }")
    # The contest itself (and a new PM if the challenger wins) is tested in gen_leadership.py
    check("pm_challenge_opens_contest", "var:wm_lead_state = 1 var:wm_lead_kind = 2 var:wm_lead_incumbent = scope:wm_test_old_pm",
          "title:k_party_labour")
    check("pm_challenger_on_ballot", "is_target_in_variable_list = { name = wm_lead_candidates target = scope:wm_test_challenger }",
          "title:k_party_labour")
    check("pm_still_pm_meanwhile", "title:e_united_kingdom.holder = scope:wm_test_old_pm")
    emit("remove_global_variable = wm_test_quiet")


setup()
faith()
trust()
spend()
wings()
devolution()
pm_challenge()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_politics.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(b for b in blocks if b) + "\n\tdebug_log = \"RFT done\"\n}\nrf_test_effect_later = {\n}\n", encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
if not os.environ.get("RFT_OUT"):
    EVENTS.parent.mkdir(exist_ok=True)
    EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
