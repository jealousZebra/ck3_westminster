#!/usr/bin/env python3
"""Writes Westminster's tests for the working majority, by-elections that can bring a government down, disputed
results and the seat chart into the harness (harness/common/scripted_effects/rf_test_effects.txt), in the style of
gen_elections.py.

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3). Everything is checked at once (recounts and
petitions are settled by removing their timers and calling the effect the weekly watcher would), so the game
needn't be unpaused. The suite sets global_var:wm_test_quiet (no events or toasts; players act like the AI) and
global_var:wm_test_dispute_force to fix the outcome of each dispute:

    python3 westminster/tools/ck3_test/gen_majority.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/majority.log
    python3 common/ck3_test/report.py westminster/tools/test_out/majority.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  chart      the seat chart's layout: each side's seats add up (government + opposition + Speaker = 650), the rows
             of the government bench hold exactly Labour's seats, front rows fill first; the poll tracker's snapshots
             start at today's values and move on a week and four weeks later; the panel's seat count runs
  majority   the working majority is the government's MPs minus every other voting MP (not the Speaker or Sinn
             Féin); losing the whip costs the government 2; three by-election defeats in a row each cost 2, hurt the
             Prime Minister (By-election Blues after two, Losing Streak after three) and are counted as a run
  disputes   a close result is recorded for challenge; a recount that overturns it gives the seat to the runner-up
             (and another recount gives the defeated MP their seat back); an election court that finds against the
             result orders a by-election; a dismissed petition costs the petitioner; contesting a heavy defeat costs
             standing (and may bring a riot); refusing to concede a general election costs the leader dearly
  lose       enough Labour MPs lose the whip that the government has no majority: the Leader of the Opposition
             tables a motion of no confidence (the Commons' business is a type 5 motion, moved by them)
"""
import os
import sys
from pathlib import Path

SUITES = sys.argv[1] if len(sys.argv) > 1 else "cmdl"
# RFT_OUT=<file> writes elsewhere (to look at the suite without touching the shared harness)
OUT = Path(os.environ.get("RFT_OUT") or Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt")
blocks = []

PM = "title:e_united_kingdom.holder"
SEATS = "title:e_united_kingdom"
CON = "title:k_party_conservative"
LAB = "title:k_party_labour"


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


def number(label, value, steps=(-100, -10, 0, 10, 50, 100, 150, 200, 250, 300)):
    chain = []
    for i, s in enumerate(reversed(steps)):
        kw = "if" if i == 0 else "else_if"
        chain.append("%s = { limit = { %s >= %d } %s }" % (kw, value, s, log("RFT_DETAIL %s>=%d" % (label, s))))
    chain.append("else = { %s }" % log("RFT_DETAIL %s<%d" % (label, steps[0])))
    emit("\n".join(chain))


def pick_labour_seat(var):
    """A Labour backbencher's seat (not the PM's or a leader's) into global_var:<var>."""
    emit("""title:e_united_kingdom = {
	random_in_de_jure_hierarchy = {
		limit = {
			tier = tier_county
			NOT = { has_variable = wm_byelection_due }
			NOT = { has_variable = wm_dispute_state }
			holder ?= { var:wm_party ?= title:k_party_labour NOT = { wm_election_safe_seat_trigger = yes } }
		}
		save_scope_as = wm_test_pick
	}
}
set_global_variable = { name = %s value = scope:wm_test_pick }""" % var)


def setup():
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    emit("wm_election_init_effect = yes")
    emit("wm_majority_reset_effect = yes")


def chart():
    phase("seatchart")
    emit("wm_seatchart_compute_effect = yes")
    check("chart_gov_side_is_labour", "global_var:wm_sc_gov_total = global_var:wm_seats_lab")
    check("chart_sides_add_up", "global_var:wm_sc_gov_total > 0 wm_election_total_seats >= { value = global_var:wm_sc_gov_total "
          "add = global_var:wm_sc_opp_total add = global_var:wm_seats_spk } wm_election_total_seats <= { value = global_var:wm_sc_gov_total "
          "add = global_var:wm_sc_opp_total add = global_var:wm_seats_spk }")
    emit("set_global_variable = { name = wm_test_rows value = 0 }")
    for r in range(5):
        emit("change_global_variable = { name = wm_test_rows add = wm_sc_row_g_%d_0 }" % r)
    check("chart_labour_rows_hold_its_seats", "global_var:wm_test_rows = global_var:wm_seats_lab")
    emit("set_global_variable = { name = wm_test_rows value = 0 }")
    for r in range(5):
        emit("change_global_variable = { name = wm_test_rows add = wm_sc_row_o_%d_13 }" % r)
    check("chart_opposition_rows_hold_its_seats", "global_var:wm_test_rows = global_var:wm_sc_opp_total")
    check("chart_front_row_first", "wm_sc_row_g_0_0 >= wm_sc_row_g_4_0 wm_sc_row_g_0_0 <= { value = wm_sc_row_g_4_0 add = 1 }")
    check("chart_conservatives_lead_opposition_bench", "wm_sc_row_o_0_0 = 0 wm_sc_row_o_0_1 > 0")
    number("chart_majority", "global_var:wm_majority")
    # The tracker
    emit("remove_global_variable = wm_sc_init")
    emit("remove_global_variable = wm_sc_month_timer")
    emit("set_global_variable = { name = wm_test_poll_lab value = global_var:wm_poll_lab }")
    emit("wm_seatchart_weekly_effect = yes")
    check("tracker_starts_today", "global_var:wm_sc_m13_p_lab = global_var:wm_poll_lab global_var:wm_sc_m0_s_lab = global_var:wm_seats_lab "
          "global_var:wm_sc_wk_maj = global_var:wm_majority has_global_variable = wm_sc_month_timer")
    emit("change_global_variable = { name = wm_poll_lab add = 50 }")
    emit("wm_seatchart_weekly_effect = yes")
    check("tracker_month_waits", "global_var:wm_sc_m0_p_lab = global_var:wm_test_poll_lab")
    check("tracker_week_ago", "global_var:wm_sc_wk_p_lab = global_var:wm_test_poll_lab "
          "global_var:wm_sc_wk0_p_lab = global_var:wm_poll_lab")
    emit("remove_global_variable = wm_sc_month_timer")
    emit("wm_seatchart_weekly_effect = yes")
    check("tracker_month_moves_on", "global_var:wm_sc_m0_p_lab = global_var:wm_poll_lab global_var:wm_sc_m1_p_lab = global_var:wm_test_poll_lab")
    check("tracker_cells", "wm_sc_cell_now_p_lab >= { value = global_var:wm_poll_lab divide = 10 } wm_sc_cell_now_p_lab <= { value = global_var:wm_poll_lab divide = 10 } "
          "wm_sc_cell_m1_p_lab >= { value = global_var:wm_test_poll_lab divide = 10 } wm_sc_cell_m1_p_lab <= { value = global_var:wm_test_poll_lab divide = 10 } wm_sc_cell_now_s_lab = global_var:wm_seats_lab")
    emit("set_global_variable = { name = wm_poll_lab value = global_var:wm_test_poll_lab }")
    emit("wm_ui_count_seats_effect = yes")
    check("panel_seats", "wm_ui_seats_lab = global_var:wm_seats_lab wm_ui_seats_spk = 1")


def majority():
    phase("majority")
    check("majority_formula", "global_var:wm_majority >= { value = global_var:wm_majority_gov_seats multiply = 2 "
          "subtract = global_var:wm_majority_voting } global_var:wm_majority <= { value = global_var:wm_majority_gov_seats multiply = 2 "
          "subtract = global_var:wm_majority_voting } global_var:wm_majority_voting >= { value = wm_election_total_seats "
          "subtract = global_var:wm_seats_spk subtract = global_var:wm_seats_sf } global_var:wm_majority_voting <= { value = wm_election_total_seats "
          "subtract = global_var:wm_seats_spk subtract = global_var:wm_seats_sf }")
    check("majority_government_is_labour", "global_var:wm_majority_gov_seats = global_var:wm_seats_lab")
    check("majority_held", "has_global_variable = wm_majority_held global_var:wm_majority > 100")
    number("majority_start", "global_var:wm_majority")
    # Losing the whip
    pick_labour_seat("wm_test_whip_seat")
    emit("set_global_variable = { name = wm_test_maj value = global_var:wm_majority }")
    emit("global_var:wm_test_whip_seat.holder = { wm_commons_withdraw_whip_effect = yes }")
    check("whip_costs_two", "global_var:wm_majority >= { value = global_var:wm_test_maj subtract = 2 } global_var:wm_majority <= { value = global_var:wm_test_maj subtract = 2 }")
    # Three by-election defeats in a row
    emit("set_global_variable = { name = wm_poll_lab value = 40 }\nset_global_variable = { name = wm_poll_con value = 500 }\n"
         "set_global_variable = { name = wm_poll_ruk value = 300 }\nwm_polls_normalise_effect = yes")
    emit("%s = { set_variable = { name = wm_test_prestige value = prestige } }" % PM)
    for i in (1, 2, 3):
        pick_labour_seat("wm_test_by_%d" % i)
        emit("set_global_variable = { name = wm_test_maj value = global_var:wm_majority }")
        emit("global_var:wm_test_by_%d.holder = { death = natural }" % i)
        check("by%d_called" % i, "has_variable = wm_byelection_due", "global_var:wm_test_by_%d" % i)
        emit("global_var:wm_test_by_%d = { remove_variable = wm_byelection_wait }" % i)
        emit("wm_byelection_process_due_effect = yes")
        check("by%d_lost" % i, "NOT = { has_variable = wm_byelection_due } holder = { is_alive = yes NOT = { var:wm_party ?= title:k_party_labour } }",
              "global_var:wm_test_by_%d" % i)
        check("by%d_costs_two" % i, "global_var:wm_majority >= { value = global_var:wm_test_maj subtract = 2 } global_var:wm_majority <= { value = global_var:wm_test_maj subtract = 2 }")
        check("by%d_run" % i, "global_var:wm_majority_loss_run = %d has_global_variable = wm_majority_loss_recent" % i)
        if i == 2:
            check("by2_blues", "has_character_modifier = wm_majority_byelection_blues_modifier", PM)
    check("by3_losing_streak", "has_character_modifier = wm_majority_losing_streak_modifier "
          "NOT = { has_character_modifier = wm_majority_byelection_blues_modifier }", PM)
    check("by3_pm_standing_hurt", "prestige < var:wm_test_prestige", PM)
    check("by3_majority_still_held", "has_global_variable = wm_majority_held")
    emit("wm_polls_init_effect = yes")


def disputes():
    phase("disputes")
    emit("set_global_variable = { name = wm_test_dispute_force value = 1 }")
    emit("%s = { add_gold = 2000 add_prestige = 3000 }" % (CON + ".holder"))
    # A close result is recorded
    pick_labour_seat("wm_test_seat_a")
    emit("""global_var:wm_test_seat_a = {
	set_variable = { name = wm_el_runner value = title:k_party_conservative }
	set_variable = { name = wm_seat_majority value = 4 }
	clear_saved_scope = wm_el_loser
	wm_dispute_record_effect = yes
	remove_variable = wm_el_runner
}""")
    check("dispute_recorded", "var:wm_dispute_runner = title:k_party_conservative var:wm_dispute_margin = 4 has_variable = wm_dispute_window",
          "global_var:wm_test_seat_a")
    check("dispute_open_list", "is_target_in_global_variable_list = { name = wm_dispute_open target = global_var:wm_test_seat_a }")
    # A recount by the Conservatives overturns it
    emit("set_global_variable = { name = wm_test_old_mp value = global_var:wm_test_seat_a.holder }")
    emit("set_global_variable = { name = wm_test_maj value = global_var:wm_majority }")
    emit("%s.holder = { set_variable = { name = wm_test_gold value = gold } save_scope_as = wm_dispute_by }" % CON)
    emit("global_var:wm_test_seat_a = { wm_dispute_start_effect = { KIND = 1 } }")
    check("recount_under_way", "var:wm_dispute_state = 1 has_variable = wm_dispute_timer NOT = { has_variable = wm_dispute_window }",
          "global_var:wm_test_seat_a")
    check("recount_pending", "is_target_in_global_variable_list = { name = wm_dispute_pending target = global_var:wm_test_seat_a } "
          "NOT = { is_target_in_global_variable_list = { name = wm_dispute_open target = global_var:wm_test_seat_a } }")
    check("recount_paid", "gold < var:wm_test_gold", CON + ".holder")
    emit("global_var:wm_test_seat_a = { remove_variable = wm_dispute_timer }")
    emit("wm_dispute_process_due_effect = yes")
    check("recount_overturned", "holder.var:wm_party = title:k_party_conservative NOT = { holder = global_var:wm_test_old_mp } "
          "has_variable = wm_dispute_done NOT = { has_variable = wm_dispute_state } var:wm_seat_majority = 1", "global_var:wm_test_seat_a")
    check("recount_loser_unseated", "var:wm_lost_seat = global_var:wm_test_seat_a NOT = { wm_is_mp_trigger = yes }", "global_var:wm_test_old_mp")
    check("recount_new_mp_serves_leader", "holder = { liege = title:k_party_conservative.holder }", "global_var:wm_test_seat_a")
    check("recount_majority_down_two", "global_var:wm_majority >= { value = global_var:wm_test_maj subtract = 2 } global_var:wm_majority <= { value = global_var:wm_test_maj subtract = 2 }")
    check("recount_no_longer_pending", "NOT = { is_target_in_global_variable_list = { name = wm_dispute_pending target = global_var:wm_test_seat_a } }")
    show("recount_new_mp", "global_var:wm_test_seat_a.holder")
    # The defeated Labour MP fights back: another recount gives them their seat back
    emit("set_global_variable = { name = wm_test_con_mp value = global_var:wm_test_seat_a.holder }")
    emit("""global_var:wm_test_old_mp = { add_gold = 1000 save_scope_as = wm_dispute_by }
global_var:wm_test_seat_a = {
	set_variable = { name = wm_dispute_runner value = title:k_party_labour }
	set_variable = { name = wm_dispute_loser value = global_var:wm_test_old_mp }
	set_variable = { name = wm_dispute_margin value = 1 }
	wm_dispute_start_effect = { KIND = 1 }
	remove_variable = wm_dispute_timer
}
wm_dispute_process_due_effect = yes""")
    check("recount_restores_loser", "holder = global_var:wm_test_old_mp", "global_var:wm_test_seat_a")
    check("restored_mp_serves_leader", "liege = title:k_party_labour.holder NOT = { has_variable = wm_lost_seat }", "global_var:wm_test_old_mp")
    check("restored_seat_loser", "var:wm_lost_seat = global_var:wm_test_seat_a", "global_var:wm_test_con_mp")
    # The election court voids a result: a by-election
    pick_labour_seat("wm_test_seat_c")
    emit("""%s.holder = { save_scope_as = wm_dispute_by }
global_var:wm_test_seat_c = {
	set_variable = { name = wm_seat_majority value = 3 }
	wm_dispute_start_effect = { KIND = 2 }
}""" % CON)
    check("court_under_way", "var:wm_dispute_state = 2 var:wm_dispute_runner = title:k_party_conservative", "global_var:wm_test_seat_c")
    emit("global_var:wm_test_seat_c = { remove_variable = wm_dispute_timer }\nwm_dispute_process_due_effect = yes")
    check("court_orders_byelection", "has_variable = wm_byelection_due var:wm_byelection_party = title:k_party_labour "
          "holder.var:wm_party = title:k_party_labour", "global_var:wm_test_seat_c")
    check("court_byelection_queued", "is_target_in_global_variable_list = { name = wm_byelection_queue target = global_var:wm_test_seat_c }")
    # A dismissed petition costs the petitioner
    emit("set_global_variable = { name = wm_test_dispute_force value = 2 }")
    pick_labour_seat("wm_test_seat_d")
    emit("""%s.holder = { save_scope_as = wm_dispute_by }
global_var:wm_test_seat_d = {
	set_variable = { name = wm_seat_majority value = 6 }
	wm_dispute_start_effect = { KIND = 2 }
	remove_variable = wm_dispute_timer
}
scope:wm_dispute_by = { set_variable = { name = wm_test_prestige value = prestige } }
set_global_variable = { name = wm_test_d_mp value = global_var:wm_test_seat_d.holder }
wm_dispute_process_due_effect = yes""" % CON)
    check("petition_dismissed", "holder = global_var:wm_test_d_mp has_variable = wm_dispute_done NOT = { has_variable = wm_byelection_due }",
          "global_var:wm_test_seat_d")
    check("petition_costs", "prestige < var:wm_test_prestige", CON + ".holder")
    # Contesting a heavy defeat
    pick_labour_seat("wm_test_seat_e")
    emit("""%s.holder = { save_scope_as = wm_dispute_by set_variable = { name = wm_test_prestige value = prestige } }
global_var:wm_test_seat_e = {
	set_variable = { name = wm_seat_majority value = 150 }
	wm_dispute_start_effect = { KIND = 1 }
}""" % CON)
    check("bad_loser_standing", "prestige < var:wm_test_prestige has_character_modifier = wm_dispute_bad_loser_modifier", CON + ".holder")
    emit("if = { limit = { global_var:wm_test_seat_e = { wm_riot_is_active_trigger = yes } } %s } else = { %s }"
         % (log("RFT_DETAIL bad_loser_riot_started"), log("RFT_DETAIL bad_loser_no_riot")))
    emit("global_var:wm_test_seat_e = { remove_variable = wm_dispute_timer }\nwm_dispute_process_due_effect = yes")
    check("bad_loser_recount_upheld", "holder.var:wm_party = title:k_party_labour has_variable = wm_dispute_done", "global_var:wm_test_seat_e")
    # Refusing to concede
    emit("%s.holder = { set_variable = { name = wm_test_prestige value = prestige } wm_dispute_national_effect = yes }" % CON)
    check("refuse_to_concede", "has_character_modifier = wm_dispute_sore_loser_modifier has_variable = wm_dispute_refused "
          "prestige < var:wm_test_prestige", CON + ".holder")
    check("refuse_pm_minds", "has_opinion_modifier = { modifier = wm_dispute_sore_loser_opinion target = %s.holder }" % CON, PM)
    emit("remove_global_variable = wm_test_dispute_force")


def lose():
    phase("lose_majority")
    emit("set_global_variable = { name = wm_test_whips value = 0 }")
    emit("""while = {
	limit = {
		global_var:wm_majority > 0
		global_var:wm_test_whips < 200
	}
	change_global_variable = { name = wm_test_whips add = 1 }
	title:e_united_kingdom = {
		random_in_de_jure_hierarchy = {
			limit = {
				tier = tier_county
				holder ?= { var:wm_party ?= title:k_party_labour NOT = { wm_election_safe_seat_trigger = yes } }
			}
			holder = { wm_commons_withdraw_whip_effect = yes }
		}
	}
}""")
    check("majority_gone", "global_var:wm_majority <= 0 NOT = { has_global_variable = wm_majority_held }")
    number("majority_after_whips", "global_var:wm_majority")
    check("motion_tabled", "has_global_variable = wm_commons_pending global_var:wm_commons_bill_type = 5 "
          "NOT = { has_global_variable = wm_majority_motion_due }")
    check("motion_moved_by_opposition_leader", "global_var:wm_commons_mover = %s.holder" % CON)
    emit("wm_majority_update_effect = yes")
    check("motion_not_repeated", "NOT = { has_global_variable = wm_majority_motion_due }")


setup()
for letter in SUITES:
    {"c": chart, "m": majority, "d": disputes, "l": lose}[letter]()
emit("remove_global_variable = wm_test_quiet")

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_majority.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(blocks) + "\n\tdebug_log = \"RFT done\"\n}\nrf_test_effect_later = {\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
