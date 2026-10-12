#!/usr/bin/env python3
"""Writes Westminster's shortlist-ballot tests (party leadership contests and the Speaker's election) into the
harness (harness/common/scripted_effects/rf_test_effects.txt), in the style of gen_elections.py.

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3). Everything is checked at once (each round is
closed by removing its timer and calling the effect the weekly watcher would), so the game needn't be unpaused. The
suite sets global_var:wm_test_quiet, so players are treated like the AI and no events or toasts open:

    python3 westminster/tools/ck3_test/gen_leadership.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/leadership.log
    python3 common/ck3_test/report.py westminster/tools/test_out/leadership.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  resign     the Conservative leader stands down: nominations open with candidates (not the leader) and the party's
             MPs as electors; when they close every MP has nominated once and at most two are shortlisted; the
             members' ballot shares add up to 100%; the winner leads the party (not the old leader), serves the PM,
             the old leader serves them, and the contest's state is gone
  government Labour's leader (the Prime Minister) stands down: the new Labour leader becomes Prime Minister, holds
             the nations, and the old PM and every Labour MP serve the right people
  challenge  a Lib Dem MP challenges their leader: either the challenge fails to reach the ballot (the leader stays)
             or the leader and one challenger go to the members; either way the party has a leader who won
  death      the SNP's leader dies: the engine hands the party to an acting leader, and a day's processing opens a
             contest (a vacancy) that ends with a living SNP MP in charge
  speaker    the Speaker dies: nominations open with up to four backbench candidates; the House votes in rounds
             until someone has a majority; the new Speaker has the flag, no party, serves the PM, and is counted as
             the Speaker in the seat counts
  values     the AI challenge chance is between 0 and 15 for every party leader
"""
import os
import sys
from pathlib import Path

SUITES = sys.argv[1] if len(sys.argv) > 1 else "rgcdsv"
# RFT_OUT=<file> writes elsewhere (to look at the suite without touching the shared harness)
OUT = Path(os.environ.get("RFT_OUT") or Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt")
blocks = []

PM = "title:e_united_kingdom.holder"
SEATS = "title:e_united_kingdom"


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


def number(label, value, steps=(0, 1, 2, 3, 5, 10, 20, 50, 100, 200, 400)):
    """Logs a value as RFT_DETAIL <label>>=<step> (the largest step it reaches)."""
    chain = []
    for i, s in enumerate(reversed(steps)):
        kw = "if" if i == 0 else "else_if"
        chain.append("%s = { limit = { %s >= %d } %s }" % (kw, value, s, log("RFT_DETAIL %s>=%d" % (label, s))))
    chain.append("else = { %s }" % log("RFT_DETAIL %s<0" % label))
    emit("\n".join(chain))


MPS_SERVE_LEADER = ("NOT = { any_in_de_jure_hierarchy = { tier = tier_county exists = holder holder = { has_variable = wm_party "
                    "NOT = { this = %s } NOT = { this = var:wm_party.holder } NOT = { liege = var:wm_party.holder } } } }" % PM)
LEADERS_SERVE_PM = ("NOT = { any_in_de_jure_hierarchy = { tier = tier_county exists = holder holder = { "
                    "var:wm_party.holder ?= this NOT = { this = %s } NOT = { liege = %s } } } }" % (PM, PM))


def close_round(party):
    """Closes the current round of $party's contest as the weekly watcher would."""
    emit("title:%s = { remove_variable = wm_lead_timer }" % party)
    emit("wm_election_leadership_process_due_effect = yes")


def contest_checks(tag, party):
    """After the contest has run to the end."""
    t = "title:" + party
    check("%s_contest_over" % tag, "NOT = { has_variable = wm_lead_state } "
          "NOT = { is_target_in_global_variable_list = { name = wm_lead_contests target = %s } }" % t, t)
    check("%s_winner_leads" % tag, "exists = holder exists = var:wm_lead_last_winner holder = var:wm_lead_last_winner", t)
    check("%s_leader_is_mp_of_party" % tag, "is_alive = yes wm_is_mp_trigger = yes var:wm_party = %s" % t, t + ".holder")
    check("%s_honeymoon" % tag, "has_variable = wm_lead_honeymoon", t + ".holder")
    check("%s_mps_serve_leader" % tag, MPS_SERVE_LEADER, SEATS)
    check("%s_leaders_serve_pm" % tag, LEADERS_SERVE_PM, SEATS)
    show("%s_winner" % tag, t + ".holder")
    emit("if = { limit = { %s.var:wm_lead_last_outcome = 1 } %s } else_if = { limit = { %s.var:wm_lead_last_outcome = 2 } %s } "
         "else = { %s }" % (t, log("RFT_DETAIL %s_outcome_ballot" % tag), t, log("RFT_DETAIL %s_outcome_unopposed" % tag),
                           log("RFT_DETAIL %s_outcome_failed_challenge" % tag)))


def setup():
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    emit("wm_election_init_effect = yes")
    emit("wm_majority_reset_effect = yes")


def resign():
    phase("leadership_resign")
    party, t = "k_party_conservative", "title:k_party_conservative"
    emit("set_global_variable = { name = wm_test_old_con value = %s.holder }" % t)
    emit("%s.holder = { wm_election_leadership_stand_down_effect = yes }" % t)
    check("resign_contest_open", "var:wm_lead_state = 1 var:wm_lead_kind = 3 has_variable = wm_lead_timer", t)
    check("resign_listed", "is_target_in_global_variable_list = { name = wm_lead_contests target = %s }" % t)
    check("resign_electors_are_the_mps", "var:wm_lead_electors = global_var:wm_seats_con", t)
    check("resign_threshold_15pct", "var:wm_lead_threshold >= { value = var:wm_lead_electors multiply = 0.15 } "
          "var:wm_lead_threshold <= { value = var:wm_lead_electors multiply = 0.15 add = 1 }", t)
    check("resign_candidates", "any_in_list = { variable = wm_lead_candidates count >= 2 }", t)
    check("resign_leader_not_standing", "NOT = { var:wm_lead_cand ?= %s }" % t, "global_var:wm_test_old_con")
    check("resign_leader_still_leads", "holder = global_var:wm_test_old_con", t)
    close_round(party)
    # Every MP nominated exactly once
    check("resign_every_mp_nominated", "OR = { var:wm_lead_noms_cast = var:wm_lead_electors var:wm_lead_noms_cast = var:wm_lead_last_electors }", t)
    check("resign_shortlist_at_most_two", "NOT = { any_in_list = { variable = wm_lead_ballot count >= 3 } }", t)
    emit("if = { limit = { %s = { has_variable = wm_lead_state } } %s } else = { %s }"
         % (t, log("RFT_DETAIL resign_went_to_ballot"), log("RFT_DETAIL resign_decided_at_nominations")))
    check("resign_ballot_stage_or_done", "OR = { var:wm_lead_state = 2 NOT = { has_variable = wm_lead_state } }", t)
    emit("if = { limit = { %s = { has_variable = wm_lead_state } } %s = { remove_variable = wm_lead_timer } wm_election_leadership_process_due_effect = yes }"
         % (t, t))
    # The shares: 1000 between them on a ballot, 1000 for an unopposed winner
    emit("set_global_variable = { name = wm_test_shares value = 0 }\n"
         "%s = { every_in_list = { variable = wm_lead_ballot limit = { has_variable = wm_lead_share } "
         "change_global_variable = { name = wm_test_shares add = var:wm_lead_share } } }" % t)
    contest_checks("resign", party)
    check("resign_new_leader", "NOT = { holder = global_var:wm_test_old_con }", t)
    check("resign_old_leader_serves_new", "liege = %s.holder" % t, "global_var:wm_test_old_con")
    check("resign_new_leader_heads_house", "is_house_head = yes", t + ".holder")
    check("resign_winner_share", "var:wm_lead_last_share >= 500 var:wm_lead_last_share <= 1000", t)


def government():
    phase("leadership_government")
    party, t = "k_party_labour", "title:k_party_labour"
    emit("set_global_variable = { name = wm_test_old_pm value = %s }" % PM)
    emit("%s = { wm_election_leadership_stand_down_effect = yes }" % PM)
    check("gov_contest_open", "var:wm_lead_state = 1 var:wm_lead_kind = 3", t)
    check("gov_pm_unchanged_during_contest", "%s = global_var:wm_test_old_pm" % PM)
    close_round(party)
    emit("if = { limit = { %s = { has_variable = wm_lead_state } } %s = { remove_variable = wm_lead_timer } wm_election_leadership_process_due_effect = yes }"
         % (t, t))
    contest_checks("gov", party)
    check("gov_new_leader_is_pm", "holder = %s" % PM, t)
    check("gov_new_pm", "NOT = { %s = global_var:wm_test_old_pm }" % PM)
    check("gov_pm_independent", "is_independent_ruler = yes", PM)
    for n in ("k_england", "k_scotland", "k_wales", "k_northern_ireland"):
        check("gov_new_pm_holds_%s" % n, "holder = %s" % PM, "title:" + n)
    check("gov_old_pm_serves_new_leader", "liege = %s" % PM, "global_var:wm_test_old_pm")
    check("gov_old_pm_keeps_seat", "wm_is_mp_trigger = yes", "global_var:wm_test_old_pm")


def challenge():
    phase("leadership_challenge")
    party, t = "k_party_lib_dem", "title:k_party_lib_dem"
    emit("set_global_variable = { name = wm_test_old_ld value = %s.holder }" % t)
    emit("""title:e_united_kingdom = {
	random_in_de_jure_hierarchy = {
		limit = { tier = tier_county holder ?= { var:wm_party ?= title:k_party_lib_dem NOT = { has_title = title:k_party_lib_dem } } }
		holder = { save_scope_as = wm_test_challenger }
	}
}
set_global_variable = { name = wm_test_challenger value = scope:wm_test_challenger }""")
    check("challenge_can_challenge", "wm_election_leadership_can_challenge_trigger = yes", "global_var:wm_test_challenger")
    emit("global_var:wm_test_challenger = { wm_election_leadership_challenge_effect = yes }")
    check("challenge_open", "var:wm_lead_state = 1 var:wm_lead_kind = 2 var:wm_lead_incumbent = global_var:wm_test_old_ld", t)
    check("challenge_both_stand", "var:wm_lead_cand = %s" % t, "global_var:wm_test_challenger")
    check("challenge_leader_stands", "var:wm_lead_cand = %s" % t, "global_var:wm_test_old_ld")
    check("challenge_threshold_20pct", "var:wm_lead_threshold >= { value = var:wm_lead_electors multiply = 0.2 }", t)
    check("challenge_no_second_challenge", "NOT = { can_execute_decision = wm_leadership_challenge_decision }", "global_var:wm_test_challenger")
    close_round(party)
    emit("if = { limit = { %s = { has_variable = wm_lead_state } } %s %s = { remove_variable = wm_lead_timer } wm_election_leadership_process_due_effect = yes }"
         % (t, log("RFT_DETAIL challenge_went_to_ballot"), t))
    check("challenge_leader_on_ballot_or_failed", "OR = { var:wm_lead_last_outcome = 1 var:wm_lead_last_outcome = 3 }", t)
    contest_checks("challenge", party)
    check("challenge_failed_means_leader_stays",
          "OR = { NOT = { var:wm_lead_last_outcome = 3 } holder = global_var:wm_test_old_ld }", t)


def death():
    phase("leadership_death")
    party, t = "k_party_snp", "title:k_party_snp"
    emit("set_global_variable = { name = wm_test_old_snp value = %s.holder }" % t)
    emit("global_var:wm_test_old_snp = { death = natural }")
    check("death_leader_dead", "is_alive = no", "global_var:wm_test_old_snp")
    check("death_pending", "is_target_in_global_variable_list = { name = wm_lead_pending_open target = %s }" % t)
    check("death_acting_leader", "exists = holder holder = { is_alive = yes }", t)
    show("death_acting_leader", t + ".holder")
    emit("wm_election_leadership_process_due_effect = yes")
    check("death_contest_open", "var:wm_lead_state = 1 var:wm_lead_kind = 1", t)
    close_round(party)
    emit("if = { limit = { %s = { has_variable = wm_lead_state } } %s = { remove_variable = wm_lead_timer } wm_election_leadership_process_due_effect = yes }"
         % (t, t))
    contest_checks("death", party)


def speaker():
    phase("speaker")
    emit("""title:e_united_kingdom = {
	random_in_de_jure_hierarchy = {
		limit = { tier = tier_county holder ?= { has_character_flag = wm_speaker } }
		holder = { save_scope_as = wm_test_speaker }
	}
}
set_global_variable = { name = wm_test_speaker value = scope:wm_test_speaker }""")
    check("speaker_at_start", "wm_speaker_chair_filled_trigger = yes")
    show("speaker_old", "global_var:wm_test_speaker")
    emit("global_var:wm_test_speaker = { death = natural }")
    check("speaker_chair_empty", "NOT = { wm_speaker_chair_filled_trigger = yes }")
    emit("wm_speaker_open_effect = yes")
    check("speaker_nominations_open", "has_global_variable = wm_speaker_state has_global_variable = wm_speaker_timer")
    check("speaker_candidates", "any_in_global_list = { variable = wm_speaker_candidates count >= 2 } "
          "NOT = { any_in_global_list = { variable = wm_speaker_candidates count >= 5 } }")
    check("speaker_candidates_backbenchers", "NOT = { any_in_global_list = { variable = wm_speaker_candidates "
          "OR = { wm_commons_is_party_leader_trigger = yes has_title = title:e_united_kingdom } } }")
    emit("remove_global_variable = wm_speaker_timer")
    emit("wm_speaker_process_due_effect = yes")
    check("speaker_elected", "wm_speaker_chair_filled_trigger = yes NOT = { has_global_variable = wm_speaker_state }")
    emit("""title:e_united_kingdom = {
	random_in_de_jure_hierarchy = {
		limit = { tier = tier_county holder ?= { has_character_flag = wm_speaker is_alive = yes } }
		holder = { save_scope_as = wm_test_new_speaker }
	}
}""")
    show("speaker_new", "scope:wm_test_new_speaker")
    check("speaker_no_party", "NOT = { has_variable = wm_party }", "scope:wm_test_new_speaker")
    check("speaker_serves_pm", "liege = %s" % PM, "scope:wm_test_new_speaker")
    check("speaker_majority_of_final_ballot", "OR = { global_var:wm_speaker_last_votes > { value = global_var:wm_speaker_last_turnout divide = 2 } "
          "NOT = { any_in_global_list = { variable = wm_speaker_candidates count >= 2 } } }")
    check("speaker_turnout", "global_var:wm_speaker_last_turnout >= 600")
    number("speaker_rounds", "global_var:wm_speaker_rounds", steps=(1, 2, 3, 4, 5))
    emit("wm_election_count_seats_effect = yes")
    check("speaker_counted", "global_var:wm_seats_spk = 1")
    check("speaker_independent_house", "house = house:wm_house_independent", "scope:wm_test_new_speaker")


def values():
    phase("leadership_values")
    check("challenge_chance_in_range", "NOT = { any_in_de_jure_hierarchy = { tier = tier_county holder ?= { "
          "wm_commons_is_party_leader_trigger = yes OR = { wm_election_leadership_challenge_chance_value < 0 "
          "wm_election_leadership_challenge_chance_value > 15 } } } }", SEATS)
    emit("wm_election_leadership_quarterly_effect = yes")
    emit("if = { limit = { has_global_variable_list = wm_lead_contests any_in_global_list = { variable = wm_lead_contests count >= 1 } } "
         "%s } else = { %s }" % (log("RFT_DETAIL quarterly_challenge_started"), log("RFT_DETAIL quarterly_no_challenge")))


setup()
for letter in SUITES:
    {"r": resign, "g": government, "c": challenge, "d": death, "s": speaker, "v": values}[letter]()
emit("remove_global_variable = wm_test_quiet")

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_leadership.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(blocks) + "\n\tdebug_log = \"RFT done\"\n}\nrf_test_effect_later = {\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
