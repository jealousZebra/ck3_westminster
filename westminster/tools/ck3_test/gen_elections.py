#!/usr/bin/env python3
"""Writes Westminster's election tests (polls, seat leans, general elections, by-elections, the early-election
decision) into the harness (harness/common/scripted_effects/rf_test_effects.txt), in the style of gen_gameplay.py.

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3). The save predates the election system, so
the suite runs wm_election_init_effect itself. It sets global_var:wm_test_quiet so no results event or toast opens
for the player while the clock has to run. The game must be unpaused: the by-election is checked 40 days
after the MP dies (event rf_test.2). Each check logs RFT_PASS / RFT_FAIL to debug.log:

    python3 westminster/tools/ck3_test/gen_elections.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 UNPAUSE=1 WAIT_LOOPS=120 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/elections.log
    python3 common/ck3_test/report.py westminster/tools/test_out/elections.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  polls      every party's poll exists, starts at its 2024 share, and the polls add up to about 100% before and
             after two years of monthly drift; the monthly tick advances Parliament's clock once per 20 days
  leans      each seat's 2024 shares are on its title (Labour in Holborn, Sinn Féin but no Labour in Belfast West,
             650 seats with data), and the seat counts match the save
  decision   "Call a General Election" can be taken by the Prime Minister and not by a backbencher; it dissolves
             Parliament
  election   a general election on unchanged polls fills all 650 seats, every MP serves their party leader, party
             leaders serve the PM, and the largest party's leader holds the United Kingdom; a second election
             after a Conservative poll surge changes the government (the Conservative leader takes the United
             Kingdom and the nations, the old PM serves the new one)
  byelection an MP dies; the seat waits for its by-election, which a new MP of some party wins within 40 days
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt"
blocks = []
later = []          # run by event rf_test.2, 40 days after setup
LATER = False

PM = "title:e_united_kingdom.holder"
POLLS = ["lab", "con", "ld", "ruk", "grn", "snp", "pc", "sf", "dup", "sdlp", "apni", "uup", "tuv", "oth"]
NATIONS = ["k_england", "k_scotland", "k_wales", "k_northern_ireland"]


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


SEATS_ALL = "title:e_united_kingdom"
NO_EMPTY_SEAT = "NOT = { any_in_de_jure_hierarchy = { tier = tier_county NOT = { exists = holder } } }"
# Every party MP who isn't the PM or their party's leader serves their party leader
MPS_SERVE_LEADER = ("NOT = { any_in_de_jure_hierarchy = { tier = tier_county exists = holder holder = { has_variable = wm_party "
                    "NOT = { this = %s } NOT = { this = var:wm_party.holder } NOT = { liege = var:wm_party.holder } } } }" % PM)
# Every party leader with a seat (other than the PM) serves the PM
LEADERS_SERVE_PM = ("NOT = { any_in_de_jure_hierarchy = { tier = tier_county exists = holder holder = { "
                    "var:wm_party.holder ?= this NOT = { this = %s } NOT = { liege = %s } } } }" % (PM, PM))
PARTIES_LED = ("NOT = { any_in_de_jure_hierarchy = { tier = tier_county exists = holder holder = { "
               "has_variable = wm_party NOT = { exists = var:wm_party.holder } } } }")


def polls():
    phase("polls")
    # No results front page or toasts for the player: an event window could stop the clock before the later stage
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    emit("wm_election_init_effect = yes")
    emit("set_global_variable = { name = wm_el_months value = 12 }")
    for p in POLLS:
        check("poll_exists_%s" % p, "has_global_variable = wm_poll_%s" % p)
    check("poll_lab_starts_at_2024", "global_var:wm_poll_lab = wm_polls_2024_lab")
    check("poll_snp_starts_at_2024", "global_var:wm_poll_snp = wm_polls_2024_snp")
    check("polls_sum_100", "wm_polls_total >= 995 wm_polls_total <= 1005")
    emit("while = { count = 24 wm_polls_drift_all_effect = yes }")
    check("polls_sum_100_after_drift", "wm_polls_total >= 990 wm_polls_total <= 1010")
    check("polls_positive_after_drift", " ".join("global_var:wm_poll_%s > 0" % p for p in POLLS))
    check("poll_lab_plausible_after_drift", "global_var:wm_poll_lab > 150 global_var:wm_poll_lab < 550")
    # The monthly tick: once, then not again within 20 days
    emit("remove_global_variable = wm_polls_ticked")
    emit("wm_polls_monthly_effect = yes")
    check("monthly_tick_advances_clock", "global_var:wm_el_months = 13")
    emit("wm_polls_monthly_effect = yes")
    check("monthly_tick_once_per_20_days", "global_var:wm_el_months = 13")
    check("government_lead_value", "wm_polls_government_lead > -1000 wm_polls_government_lead < 1000")


def leans():
    phase("leans")
    check("lean_holborn_labour", "has_variable = wm_lean_lab var:wm_lean_lab > 300", "title:c_holborn_and_st_pancras")
    check("lean_belfast_west_sf_no_labour", "has_variable = wm_lean_sf var:wm_lean_sf > 400 NOT = { has_variable = wm_lean_lab }",
          "title:c_belfast_west")
    check("lean_glasgow_snp", "has_variable = wm_lean_snp", "title:c_glasgow_north")
    check("lean_650_seats", "any_in_de_jure_hierarchy = { tier = tier_county OR = { has_variable = wm_lean_lab has_variable = wm_lean_grn "
          "has_variable = wm_lean_sf has_variable = wm_lean_dup } count >= 650 }", SEATS_ALL)
    check("lean_con_most_seats", "any_in_de_jure_hierarchy = { tier = tier_county has_variable = wm_lean_con count >= 600 }", SEATS_ALL)
    check("seat_counts_add_up", "wm_election_total_seats = 650")
    check("labour_largest_at_start", "global_var:wm_el_largest = title:k_party_labour global_var:wm_seats_lab >= 380")


def decision():
    phase("decision")
    check("pm_exists", "exists = %s" % PM)
    check("pm_can_call_election", "can_execute_decision = wm_election_call_decision", PM)
    emit("title:c_aldershot = { save_scope_as = wm_test_bb_seat }")
    check("backbencher_cannot_call_election", "NOT = { can_execute_decision = wm_election_call_decision }", "title:c_aldershot.holder")
    emit("wm_election_schedule_effect = yes")
    check("election_scheduled", "has_global_variable = wm_el_scheduled has_global_variable = wm_el_campaign")
    check("cannot_call_twice", "NOT = { can_execute_decision = wm_election_call_decision }", PM)


def general_election(run, setup, expect_party=None, expect_change=False):
    phase("general_election_%d" % run)
    if setup:
        emit(setup)
    emit("set_global_variable = { name = wm_test_old_pm_%d value = %s }" % (run, PM))
    emit(log("RFT_TIME election_%d_start" % run))
    emit("wm_election_general_effect = yes")
    emit(log("RFT_TIME election_%d_done" % run))
    check("election_%d_all_seats_have_mps" % run, NO_EMPTY_SEAT, SEATS_ALL)
    check("election_%d_mps_serve_their_leader" % run, MPS_SERVE_LEADER, SEATS_ALL)
    check("election_%d_leaders_serve_pm" % run, LEADERS_SERVE_PM, SEATS_ALL)
    check("election_%d_every_party_has_a_leader" % run, PARTIES_LED, SEATS_ALL)
    check("election_%d_650_seats_counted" % run, "wm_election_total_seats = 650")
    check("election_%d_largest_party_leader_is_pm" % run, "exists = global_var:wm_el_largest.holder global_var:wm_el_largest.holder = %s" % PM)
    check("election_%d_pm_independent" % run, "is_independent_ruler = yes", PM)
    emit("%s = { if = { limit = { is_independent_ruler = no } liege = { %s debug_log_scopes = yes } } }"
         % (PM, log("RFT_DETAIL election_%d_pm_liege" % run)))
    check("election_%d_clock_reset" % run, "global_var:wm_el_months = 0 NOT = { has_global_variable = wm_el_scheduled }")
    check("election_%d_pm_seat_result" % run, "any_held_title = { tier = tier_county has_variable = wm_seat_share has_variable = wm_seat_majority }", PM)
    show("election_%d_pm" % run, PM)
    show("election_%d_largest_party" % run, "global_var:wm_el_largest")
    for p in ("lab", "con", "ld", "ruk", "snp"):
        emit("if = { limit = { global_var:wm_seats_%s >= 300 } %s } else_if = { limit = { global_var:wm_seats_%s >= 100 } %s } "
             "else_if = { limit = { global_var:wm_seats_%s >= 10 } %s } else = { %s }"
             % (p, log("RFT_DETAIL election_%d_%s_300_plus" % (run, p)), p, log("RFT_DETAIL election_%d_%s_100_299" % (run, p)),
                p, log("RFT_DETAIL election_%d_%s_10_99" % (run, p)), log("RFT_DETAIL election_%d_%s_under_10" % (run, p))))
    if expect_party:
        check("election_%d_%s_largest" % (run, expect_party.split("_")[-1]), "global_var:wm_el_largest = title:%s" % expect_party)
    if expect_change:
        check("election_%d_government_changed" % run, "has_global_variable = wm_el_gov_changed NOT = { %s = global_var:wm_test_old_pm_%d }" % (PM, run))
        for n in NATIONS:
            check("election_%d_new_pm_holds_%s" % (run, n), "holder = %s" % PM, "title:" + n)
        check("election_%d_old_pm_serves_new_pm" % run, "liege = %s" % PM, "global_var:wm_test_old_pm_%d" % run)
        check("election_%d_old_pm_keeps_seat" % run, "wm_is_mp_trigger = yes", "global_var:wm_test_old_pm_%d" % run)
    else:
        check("election_%d_government_unchanged" % run, "%s = global_var:wm_test_old_pm_%d" % (PM, run))


def elections():
    # Unchanged polls: much like 2024 (incumbents have the edge)
    general_election(1, "wm_polls_init_effect = yes", "k_party_labour", False)
    # A Conservative surge: a change of government


def election_2():
    """Run after the by-election checks: once the government changes, the player is a backbencher and vanilla's
    cabinet offer letter pauses the game, which would stop the 40-day stage."""
    general_election(2, "wm_polls_init_effect = yes\n"
                        "set_global_variable = { name = wm_poll_con value = 450 }\n"
                        "set_global_variable = { name = wm_poll_lab value = 180 }\n"
                        "wm_polls_normalise_effect = yes", "k_party_conservative", True)


def byelection():
    global LATER
    phase("byelection")
    emit("""title:e_united_kingdom = {
	random_in_de_jure_hierarchy = {
		limit = {
			tier = tier_county
			NOT = { has_variable = wm_byelection_due }
			holder ?= { has_variable = wm_party NOT = { wm_election_safe_seat_trigger = yes } }
		}
		save_scope_as = wm_test_by_seat
	}
}
set_global_variable = { name = wm_test_by_seat value = scope:wm_test_by_seat }
set_global_variable = { name = wm_test_dead_mp value = scope:wm_test_by_seat.holder }""")
    show("byelection_seat", "global_var:wm_test_by_seat")
    emit("global_var:wm_test_dead_mp = { death = natural }")
    check("dead_mp_dead", "is_alive = no", "global_var:wm_test_dead_mp")
    check("byelection_called", "has_variable = wm_byelection_due has_variable = wm_byelection_wait has_variable = wm_byelection_party",
          "global_var:wm_test_by_seat")
    check("byelection_queued", "is_target_in_global_variable_list = { name = wm_byelection_queue target = global_var:wm_test_by_seat }")
    show("byelection_interim_holder", "global_var:wm_test_by_seat.holder")
    LATER = True
    phase("byelection_after_40_days")
    check("byelection_held", "NOT = { has_variable = wm_byelection_due }", "global_var:wm_test_by_seat")
    check("byelection_dequeued", "NOT = { is_target_in_global_variable_list = { name = wm_byelection_queue target = global_var:wm_test_by_seat } }")
    check("byelection_new_mp", "exists = holder holder = { is_alive = yes has_variable = wm_party NOT = { this = global_var:wm_test_dead_mp } }",
          "global_var:wm_test_by_seat")
    check("byelection_mp_serves_leader", "holder = { OR = { liege = var:wm_party.holder this = var:wm_party.holder } }",
          "global_var:wm_test_by_seat")
    check("byelection_result_recorded", "has_variable = wm_seat_share", "global_var:wm_test_by_seat")
    show("byelection_winner", "global_var:wm_test_by_seat.holder")
    election_2()
    emit("remove_global_variable = wm_test_quiet")
    LATER = False


polls()
leans()
decision()
elections()
byelection()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_elections.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(blocks) + ("\n\ttrigger_event = { id = rf_test.2 days = 40 }\n}\n" if later else "\n\tdebug_log = \"RFT done\"\n}\n")
               + "rf_test_effect_later = {\n" + "\n".join(later) + "\n\tdebug_log = \"RFT done\"\n}\n", encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
EVENTS.parent.mkdir(exist_ok=True)
EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
