#!/usr/bin/env python3
"""Writes Westminster's unlanded-career tests (jobs, selections, candidates becoming MPs) into the harness
(harness/common/scripted_effects/rf_test_effects.txt), in the style of gen_elections.py.

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3). The save predates the election system, so the
suite runs wm_election_init_effect itself. It sets global_var:wm_test_quiet so no event or toast opens for the player.
Everything happens in one go (no game time needed). Each check logs RFT_PASS / RFT_FAIL to debug.log:

    python3 westminster/tools/ck3_test/gen_career.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 WAIT_LOOPS=120 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/career.log
    python3 common/ck3_test/report.py westminster/tools/test_out/career.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  jobs        a Labour activist gets a campaign team (a landless adventurer) and joins the hopefuls; each job
              (canvassing, fundraising, speechwriting, research) is taken and done well, raising standing by its
              amount and paying money and profile; the candidate assessment puts them on the approved list; a failed
              job costs standing; a job whose three weeks are up is settled by wm_career_resolve_jobs_effect; the
              party offers jobs
  selection   Labour opens a selection in a Conservative seat; the activist applies and gives a hustings speech;
              when it closes the activist (given top standing and hustings) is Labour's candidate for the seat, and a
              local rival was found; a Lib Dem selection nobody applies to still picks a local activist
  election    a general election with Labour far ahead and the seat leaning Labour: the candidate becomes its MP,
              serves the Labour leader, and is no longer a landless adventurer or a hopeful; the defeated Conservative
              has var:wm_lost_seat; defeated MPs become hopefuls on the approved list
  byelection  a Labour MP dies: Labour opens a selection for the by-election; a second activist wins it, and at the
              by-election (held at once) becomes the MP and serves the Labour leader
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt"
blocks = []

PM = "title:e_united_kingdom.holder"
LAB = "title:k_party_labour"
H1 = "global_var:wm_test_hopeful"
H2 = "global_var:wm_test_hopeful2"
SEAT = "global_var:wm_test_sel_seat"
BYSEAT = "global_var:wm_test_by_seat"


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


SEATS_ALL = "title:e_united_kingdom"
NO_EMPTY_SEAT = "NOT = { any_in_de_jure_hierarchy = { tier = tier_county NOT = { exists = holder } } }"
MPS_SERVE_LEADER = ("NOT = { any_in_de_jure_hierarchy = { tier = tier_county exists = holder holder = { has_variable = wm_party "
                    "NOT = { this = %s } NOT = { this = var:wm_party.holder } NOT = { liege = var:wm_party.holder } } } }" % PM)


def new_hopeful(var, name):
    """A Labour activist with a campaign team, on the hopefuls' list."""
    emit("""create_character = { name = "%s" age = 28 gender = female culture = culture:english faith = faith:wm_faith_not_stated
	location = root.capital_province save_scope_as = wm_test_new }
scope:wm_test_new = {
	set_variable = { name = wm_party value = %s }
	wm_career_start_campaign_effect = yes
}
set_global_variable = { name = %s value = scope:wm_test_new }""" % (name, LAB, var))


def job(hopeful, ctype, outcome="success_standard"):
    """The hopeful takes a job of type ctype from the Labour leader and it ends with outcome."""
    emit("""%s = {
	create_task_contract = {
		task_contract_employer = %s.holder
		task_contract_type = %s
		task_contract_tier = 1
		location = %s.holder.location
		save_scope_as = wm_test_job
	}
	accept_task_contract = scope:wm_test_job
}""" % (hopeful, LAB, ctype, LAB))
    check("%s_taken" % ctype, "task_contract_taker ?= %s" % hopeful, "scope:wm_test_job")
    check("%s_waits_three_weeks" % ctype, "has_variable = wm_job_wait", "scope:wm_test_job")
    if outcome:
        emit("scope:wm_test_job = { complete_task_contract = %s }" % outcome)


def standing(name, hopeful, value):
    check(name, "has_variable = wm_standing var:wm_standing = %d" % value, hopeful)


def jobs():
    phase("jobs")
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    emit("wm_election_init_effect = yes")
    emit("set_global_variable = { name = wm_el_months value = 12 }")
    new_hopeful("wm_test_hopeful", "Test Activist")
    check("hopeful_is_landless_adventurer", "is_landless_adventurer = yes", H1)
    check("hopeful_has_campaign_team", "exists = var:wm_career_camp var:wm_career_camp.holder = this", H1)
    check("hopeful_on_ladder", "has_variable = wm_career_hopeful", H1)
    check("hopeful_listed", "is_target_in_global_variable_list = { name = wm_career_hopefuls target = %s }" % H1)
    standing("hopeful_starts_at_10", H1, 10)
    check("hopeful_cannot_apply_yet", "NOT = { wm_career_can_apply_trigger = yes }", H1)
    emit("%s = { set_variable = { name = wm_test_gold value = gold } set_variable = { name = wm_test_prestige value = prestige } }" % H1)
    job(H1, "wm_job_canvassing")
    standing("canvassing_standing_16", H1, 16)
    job(H1, "wm_job_fundraising")
    standing("fundraising_standing_20", H1, 20)
    check("fundraising_paid", "gold > var:wm_test_gold", H1)
    job(H1, "wm_job_speechwriting")
    standing("speechwriting_standing_25", H1, 25)
    check("jobs_raise_profile", "prestige > var:wm_test_prestige", H1)
    job(H1, "wm_job_research")
    standing("research_standing_30", H1, 30)
    check("employer_has_contact", "has_contact = %s.holder" % LAB, H1)
    check("employer_likes_good_work", "has_opinion_modifier = { target = %s modifier = wm_career_good_work_opinion }" % H1,
          "%s.holder" % LAB)
    job(H1, "wm_selection_contract", None)
    check("assessment_accepted", "has_variable = wm_seeking_selection", H1)
    emit("scope:wm_test_job = { complete_task_contract = success_standard }")
    check("assessment_puts_on_approved_list", "has_variable = wm_on_shortlist NOT = { has_variable = wm_seeking_selection }", H1)
    standing("assessment_standing_40", H1, 40)
    job(H1, "wm_job_canvassing", "failure_standard")
    standing("failed_job_standing_37", H1, 37)
    # A job whose three weeks are up is settled (success or failure) by the event's effect
    job(H1, "wm_job_research", None)
    emit("scope:wm_test_job = { remove_variable = wm_job_wait }")
    emit("%s = { wm_career_resolve_jobs_effect = yes }" % H1)
    check("due_job_settled", "NOT = { any_character_active_contract = { has_task_contract_type = wm_job_research } }", H1)
    check("due_job_changed_standing", "has_variable = wm_standing NOT = { var:wm_standing = 37 }", H1)
    emit("%s = { wm_career_offer_jobs_effect = yes }" % H1)
    check("party_offers_jobs", "any_character_task_contract = { wm_career_is_job_trigger = yes }", H1)
    check("hopeful_can_apply", "wm_career_can_apply_trigger = yes", H1)
    emit("%s = { remove_variable = wm_test_gold remove_variable = wm_test_prestige }" % H1)


def selection():
    phase("selection")
    emit("""title:e_united_kingdom = {
	random_in_de_jure_hierarchy = {
		limit = {
			tier = tier_county
			has_variable = wm_lean_lab
			NOT = { has_variable = wm_byelection_due }
			NOT = { has_variable_list = wm_sel_parties }
			holder ?= { var:wm_party ?= title:k_party_conservative NOT = { wm_election_safe_seat_trigger = yes } is_ai = yes }
		}
		save_scope_as = wm_test_sel_seat
	}
}
set_global_variable = { name = wm_test_sel_seat value = scope:wm_test_sel_seat }
set_global_variable = { name = wm_test_sel_old_mp value = scope:wm_test_sel_seat.holder }""")
    show("selection_seat", SEAT)
    emit("%s = { wm_career_open_selection_effect = { P = lab PARTY = k_party_labour } }" % SEAT)
    check("selection_open", "has_variable_list = wm_sel_parties is_target_in_variable_list = { name = wm_sel_parties target = %s } "
          "has_variable = wm_sel_wait_lab" % LAB, SEAT)
    check("selection_listed", "is_target_in_global_variable_list = { name = wm_career_selection_seats target = %s }" % SEAT)
    check("hopeful_may_apply_here", "wm_career_seat_open_for_trigger = { CHAR = %s }" % H1, SEAT)
    # AI hopefuls may already have applied; otherwise apply now
    emit("%s = { if = { limit = { NOT = { has_variable = wm_career_applied } } %s = { save_scope_as = wm_sel_seat } "
         "wm_career_apply_effect = yes } }" % (H1, SEAT))
    check("hopeful_applied", "var:wm_career_applied = %s" % SEAT, H1)
    check("hopeful_on_applicants_list", "is_target_in_variable_list = { name = wm_sel_applicants target = %s }" % H1, SEAT)
    check("hopeful_gave_hustings_speech", "has_variable = wm_hustings_score var:wm_hustings_score >= 20", H1)
    check("cannot_apply_twice", "NOT = { wm_career_can_apply_trigger = yes }", H1)
    # Make sure they win the members' vote
    emit("%s = { set_variable = { name = wm_standing value = 100 } set_variable = { name = wm_hustings_score value = 300 } }" % H1)
    emit("%s = { remove_variable = wm_sel_wait_lab wm_career_close_due_selections_effect = yes }" % SEAT)
    check("candidate_stored_on_seat", "var:wm_candidate_lab ?= %s" % H1, SEAT)
    check("candidate_knows_seat", "var:wm_career_selected_seat = %s NOT = { has_variable = wm_career_applied }" % SEAT, H1)
    check("selection_closed", "NOT = { has_variable = wm_sel_wait_lab } "
          "NOT = { has_variable_list = wm_sel_parties is_target_in_variable_list = { name = wm_sel_parties target = %s } }" % LAB, SEAT)
    check("selection_delisted", "NOT = { is_target_in_global_variable_list = { name = wm_career_selection_seats target = %s } }" % SEAT)
    check("rival_found", "any_in_global_list = { variable = wm_career_hopefuls var:wm_party ?= %s NOT = { this = %s } count >= 1 }" % (LAB, H1))
    check("winner_standing_capped", "var:wm_standing = 100", H1)
    # A selection with no applicants still finds a candidate: the Lib Dems somewhere they stood
    emit("""title:e_united_kingdom = {
	random_in_de_jure_hierarchy = {
		limit = {
			tier = tier_county
			has_variable = wm_lean_ld
			NOT = { this = %s }
			NOT = { has_variable_list = wm_sel_parties }
			NOT = { exists = var:wm_candidate_ld }
		}
		save_scope_as = wm_test_ld_seat
	}
}
set_global_variable = { name = wm_test_ld_seat value = scope:wm_test_ld_seat }""" % SEAT)
    emit("global_var:wm_test_ld_seat = { wm_career_open_selection_effect = { P = ld PARTY = k_party_lib_dem } }")
    emit("global_var:wm_test_ld_seat = { remove_variable = wm_sel_wait_ld wm_career_close_due_selections_effect = yes }")
    check("empty_selection_finds_local_activist", "var:wm_candidate_ld ?= { is_alive = yes var:wm_party ?= title:k_party_lib_dem "
          "has_variable = wm_career_selected_seat }", "global_var:wm_test_ld_seat")
    show("ld_candidate", "global_var:wm_test_ld_seat.var:wm_candidate_ld")


def election():
    phase("general_election")
    emit("wm_polls_init_effect = yes")
    emit("set_global_variable = { name = wm_poll_lab value = 600 }")
    emit("set_global_variable = { name = wm_poll_con value = 100 }")
    emit("wm_polls_normalise_effect = yes")
    emit("%s = { set_variable = { name = wm_lean_lab value = 950 } }" % SEAT)
    emit(log("RFT_TIME election_start"))
    emit("wm_election_general_effect = yes")
    emit(log("RFT_TIME election_done"))
    check("election_all_seats_have_mps", NO_EMPTY_SEAT, SEATS_ALL)
    check("election_mps_serve_their_leader", MPS_SERVE_LEADER, SEATS_ALL)
    show("election_seat_holder", "%s.holder" % SEAT)
    check("candidate_is_mp", "holder ?= %s" % H1, SEAT)
    check("candidate_holds_a_seat", "wm_is_mp_trigger = yes is_alive = yes", H1)
    check("candidate_serves_party_leader", "liege ?= var:wm_party.holder", H1)
    check("candidate_campaign_wound_up", "is_landless_adventurer = no NOT = { has_variable = wm_career_camp }", H1)
    check("candidate_off_ladder", "NOT = { has_variable = wm_career_hopeful } NOT = { has_variable = wm_career_selected_seat }", H1)
    check("candidate_delisted", "NOT = { is_target_in_global_variable_list = { name = wm_career_hopefuls target = %s } }" % H1)
    check("seat_candidate_cleared", "NOT = { exists = var:wm_candidate_lab }", SEAT)
    check("old_mp_lost_seat", "has_variable = wm_lost_seat NOT = { wm_is_mp_trigger = yes }", "global_var:wm_test_sel_old_mp")
    emit("wm_career_recruit_defeated_effect = yes")
    check("defeated_mps_become_hopefuls", "any_living_character = { has_variable = wm_career_former_mp has_variable = wm_career_hopeful "
          "has_variable = wm_on_shortlist var:wm_standing >= 50 }")
    emit("""global_var:wm_test_sel_old_mp = {
	if = {
		limit = { is_ai = yes age < 70 is_alive = yes }
		if = { limit = { has_variable = wm_career_hopeful } %s }
		else = { %s }
	}
}""" % (log("RFT_PASS defeated_mp_back_on_ladder"), log("RFT_FAIL defeated_mp_back_on_ladder")))


def byelection():
    phase("byelection")
    new_hopeful("wm_test_hopeful2", "Test Activist Two")
    emit("%s = { set_variable = { name = wm_on_shortlist value = yes } }" % H2)
    emit("""title:e_united_kingdom = {
	random_in_de_jure_hierarchy = {
		limit = {
			tier = tier_county
			has_variable = wm_lean_lab
			var:wm_lean_lab >= 300
			NOT = { this = %s }
			NOT = { has_variable = wm_byelection_due }
			NOT = { has_variable_list = wm_sel_parties }
			NOT = { exists = var:wm_candidate_lab }
			holder ?= { var:wm_party ?= %s NOT = { wm_election_safe_seat_trigger = yes } is_ai = yes }
		}
		save_scope_as = wm_test_by_seat
	}
}
set_global_variable = { name = wm_test_by_seat value = scope:wm_test_by_seat }
set_global_variable = { name = wm_test_by_mp value = scope:wm_test_by_seat.holder }""" % (SEAT, LAB))
    show("byelection_seat", BYSEAT)
    emit("global_var:wm_test_by_mp = { death = natural }")
    check("byelection_called", "has_variable = wm_byelection_due", BYSEAT)
    check("byelection_selection_open", "has_variable_list = wm_sel_parties is_target_in_variable_list = { name = wm_sel_parties target = %s } "
          "has_variable = wm_sel_wait_lab" % LAB, BYSEAT)
    emit("%s = { if = { limit = { NOT = { has_variable = wm_career_applied } } %s = { save_scope_as = wm_sel_seat } "
         "wm_career_apply_effect = yes } }" % (H2, BYSEAT))
    check("hopeful2_applied", "var:wm_career_applied = %s" % BYSEAT, H2)
    emit("%s = { set_variable = { name = wm_standing value = 100 } set_variable = { name = wm_hustings_score value = 300 } }" % H2)
    emit("%s = { remove_variable = wm_sel_wait_lab wm_career_close_due_selections_effect = yes }" % BYSEAT)
    check("byelection_candidate_stored", "var:wm_candidate_lab ?= %s" % H2, BYSEAT)
    # Polling day now, with the seat leaning hard to Labour
    emit("%s = { set_variable = { name = wm_lean_lab value = 950 } remove_variable = wm_byelection_wait wm_byelection_hold_effect = yes }" % BYSEAT)
    check("byelection_held", "NOT = { has_variable = wm_byelection_due } has_variable = wm_seat_share", BYSEAT)
    show("byelection_winner", "%s.holder" % BYSEAT)
    check("byelection_candidate_is_mp", "holder ?= %s" % H2, BYSEAT)
    check("byelection_candidate_serves_leader", "liege ?= var:wm_party.holder", H2)
    check("byelection_candidate_campaign_wound_up", "is_landless_adventurer = no NOT = { has_variable = wm_career_hopeful }", H2)
    check("byelection_seat_candidate_cleared", "NOT = { exists = var:wm_candidate_lab }", BYSEAT)
    emit("remove_global_variable = wm_test_quiet")


jobs()
selection()
election()
byelection()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_career.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(blocks) + "\n\tdebug_log = \"RFT done\"\n}\nrf_test_effect_later = {\n\tdebug_log = \"RFT done\"\n}\n",
               encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
EVENTS.parent.mkdir(exist_ok=True)
EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
