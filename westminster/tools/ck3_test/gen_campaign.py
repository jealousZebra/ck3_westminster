#!/usr/bin/env python3
"""Writes Westminster's campaign and conference tests into the harness
(harness/common/scripted_effects/rf_test_effects.txt), in the style of gen_elections.py.

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3). The save predates the election system, so the
suite runs wm_election_init_effect itself. It sets global_var:wm_test_quiet so players get the automatic (AI)
version of campaign and conference moves and no event window opens. Everything is checked at once (no waiting), so
the game can stay paused. Each check logs RFT_PASS / RFT_FAIL to debug.log:

    python3 westminster/tools/ck3_test/gen_campaign.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/campaign.log
    python3 common/ck3_test/report.py westminster/tools/test_out/campaign.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  start       calling a general election (wm_election_schedule_effect) and the weekly watcher start a campaign:
              week 1, every party leader (and MPs) on the campaign trail; the watcher runs once a week, and the
              next week advances the campaign; the watcher can be (re)started
  polls       campaign moves shift polls: a Conservative rally up, a Labour policy flop down, a TV debate (Labour
              up, Conservatives down), an SNP rally up by less than a point UK-wide (regional scaling), and an AI
              leader's automatic week moves their party
  door        door-knocking raises the player's party's share (var:wm_lean_<party>) in their own seat by 0.8 to 1.5
              points and gives the seat the doorstep modifier (the PM's seat if the player has none)
  conference  every major party's conference (forced: wm_conference_hold_all_effect) is marked held, its leader
              speaks (a result is recorded), the party's poll and the leader's prestige change, and Labour's MPs
              react to a triumph or disaster; the dated autumn check doesn't hold a second conference that year
  end         once polling day has passed, the watcher ends the campaign
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt"
blocks = []

PM = "title:e_united_kingdom.holder"
# Major parties with a conference: key, title
CONF = [("ld", "k_party_lib_dem"), ("ruk", "k_party_reform"), ("lab", "k_party_labour"), ("con", "k_party_conservative"),
        ("grn", "k_party_green"), ("snp", "k_party_snp")]


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


def setup():
    phase("setup")
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    emit("wm_election_init_effect = yes")
    for v in ("wm_el_scheduled", "wm_el_campaign", "wm_campaign_active", "wm_campaign_week", "wm_campaign_ticked"):
        emit("remove_global_variable = %s" % v)
    check("pm_exists", "exists = %s" % PM)
    check("pm_is_labour_leader", "var:wm_party ?= title:k_party_labour has_title = title:k_party_labour", PM)
    check("con_leader_exists", "exists = title:k_party_conservative.holder")
    check("no_campaign_before_election", "NOT = { has_global_variable = wm_campaign_active }")


def start():
    phase("start")
    emit("wm_election_schedule_effect = yes")
    emit("wm_campaign_watch_effect = yes")
    check("campaign_started", "has_global_variable = wm_campaign_active global_var:wm_campaign_week = 1")
    check("pm_on_campaign_trail", "has_character_flag = wm_campaign_on_trail", PM)
    check("con_leader_on_campaign_trail", "has_character_flag = wm_campaign_on_trail", "title:k_party_conservative.holder")
    check("every_party_leader_on_campaign_trail",
          "NOT = { any_living_character = { exists = var:wm_party has_title = var:wm_party wm_is_mp_trigger = yes "
          "NOT = { has_character_flag = wm_campaign_on_trail } } }")
    check("backbencher_on_campaign_trail", "has_character_flag = wm_campaign_on_trail", "title:c_aldershot.holder")
    emit("wm_campaign_watch_effect = yes")
    check("watcher_once_a_week", "global_var:wm_campaign_week = 1")
    emit("remove_global_variable = wm_campaign_ticked")
    emit("wm_campaign_watch_effect = yes")
    check("next_week_advances_campaign", "global_var:wm_campaign_week = 2 has_global_variable = wm_campaign_active")
    emit("remove_global_variable = wm_campaign_watch_alive")
    emit("%s = { wm_campaign_ensure_watch_effect = yes }" % PM)
    check("watcher_restarts", "has_global_variable = wm_campaign_watch_alive")


def poll_test(name, party, effect_scope, effect, direction, extra=None):
    emit("set_global_variable = { name = wm_test_poll_before value = global_var:wm_poll_%s }" % party)
    emit("%s = { %s }" % (effect_scope, effect))
    op = ">" if direction > 0 else "<"
    check(name, "global_var:wm_poll_%s %s global_var:wm_test_poll_before" % (party, op))
    if extra:
        extra()


def polls():
    phase("polls")
    poll_test("rally_raises_con_poll", "con", "title:k_party_conservative.holder", "wm_campaign_rally_success_effect = yes", 1)
    poll_test("policy_flop_lowers_lab_poll", "lab", PM, "wm_campaign_policy_flop_effect = yes", -1)
    emit("set_global_variable = { name = wm_test_con_before value = global_var:wm_poll_con }")
    poll_test("debate_win_raises_lab_poll", "lab", PM,
              "wm_campaign_debate_win_effect = { RIVAL = title:k_party_conservative.holder }", 1)
    check("debate_loss_lowers_con_poll", "global_var:wm_poll_con < global_var:wm_test_con_before")
    check("debate_loser_resents_winner",
          "has_opinion_modifier = { target = %s modifier = wm_campaign_debate_humiliated_opinion }" % PM,
          "title:k_party_conservative.holder")
    # Regional scaling: 1.2 points in Scotland is about 0.1 UK-wide
    emit("set_global_variable = { name = wm_test_snp_cap value = { value = global_var:wm_poll_snp add = 2 } }")
    poll_test("rally_raises_snp_poll", "snp", "title:k_party_snp.holder", "wm_campaign_rally_success_effect = yes", 1)
    check("snp_shift_scaled_to_uk", "global_var:wm_poll_snp < global_var:wm_test_snp_cap")
    emit("set_global_variable = { name = wm_test_poll_before value = global_var:wm_poll_ld }")
    emit("title:k_party_lib_dem.holder = { wm_campaign_ai_week_effect = yes }")
    check("ai_week_moves_ld_poll", "NOT = { global_var:wm_poll_ld = global_var:wm_test_poll_before }")


def door():
    phase("door_knocking")
    # The player if they have a seat and a party, otherwise the Prime Minister
    emit("if = { limit = { wm_is_mp_trigger = yes exists = var:wm_party } set_global_variable = { name = wm_test_knocker value = this } }\n"
         "else = { set_global_variable = { name = wm_test_knocker value = %s } }" % PM)
    show("door_knocker", "global_var:wm_test_knocker")
    emit("global_var:wm_test_knocker = { random_held_title = { limit = { tier = tier_county is_landless_type_title = no } "
         "save_scope_as = wm_test_seat } }")
    emit("set_global_variable = { name = wm_test_seat value = scope:wm_test_seat }")
    emit("global_var:wm_test_seat = { remove_county_modifier = wm_campaign_doorstep_county_modifier "
         "set_variable = { name = wm_test_lean_before value = wm_campaign_own_lean_value } "
         "set_variable = { name = wm_test_lean_cap value = { value = wm_campaign_own_lean_value add = 15 } } }")
    show("door_knock_seat", "global_var:wm_test_seat")
    check("seat_has_lean", "wm_campaign_own_lean_value > 0", "global_var:wm_test_seat")
    emit("global_var:wm_test_knocker = { wm_campaign_door_knock_effect = yes }")
    check("door_knock_raises_seat_lean", "wm_campaign_own_lean_value > var:wm_test_lean_before", "global_var:wm_test_seat")
    check("door_knock_raise_at_most_1_5_points", "wm_campaign_own_lean_value <= var:wm_test_lean_cap", "global_var:wm_test_seat")
    check("door_knock_doorstep_modifier", "has_county_modifier = wm_campaign_doorstep_county_modifier", "global_var:wm_test_seat")


def conference():
    phase("conference")
    for p, t in CONF:
        emit("remove_global_variable = wm_conference_done_%s" % p)
        emit("set_global_variable = { name = wm_test_cpoll_%s value = global_var:wm_poll_%s }" % (p, p))
        emit("title:%s.holder ?= { remove_variable = wm_conference_result set_variable = { name = wm_test_prestige value = prestige } }" % t)
    emit("wm_conference_hold_all_effect = yes")
    for p, t in CONF:
        leader = "title:%s.holder" % t
        check("conference_%s_leader_exists" % p, "exists = %s" % leader)
        check("conference_%s_held" % p, "has_global_variable = wm_conference_done_%s" % p)
        check("conference_%s_leader_spoke" % p, "has_character_flag = wm_conference_leader has_variable = wm_conference_result", leader)
        check("conference_%s_poll_changed" % p, "NOT = { global_var:wm_poll_%s = global_var:wm_test_cpoll_%s }" % (p, p))
        check("conference_%s_prestige_changed" % p, "NOT = { prestige = var:wm_test_prestige }", leader)
        emit("%s = { if = { limit = { var:wm_conference_result ?= 1 } %s } else_if = { limit = { var:wm_conference_result ?= 3 } %s } "
             "else = { %s } }" % (leader, log("RFT_DETAIL conference_%s_triumph" % p), log("RFT_DETAIL conference_%s_disaster" % p),
                                  log("RFT_DETAIL conference_%s_solid" % p)))
    emit("title:k_party_labour.holder = { save_scope_as = wm_test_lab_leader }")
    check("conference_lab_mps_react",
          "OR = { var:wm_conference_result = 2 "
          "any_vassal = { has_opinion_modifier = { target = scope:wm_test_lab_leader modifier = wm_conference_triumph_opinion } } "
          "any_vassal = { has_opinion_modifier = { target = scope:wm_test_lab_leader modifier = wm_conference_disaster_opinion } } }",
          "title:k_party_labour.holder")
    # The dated check doesn't hold a second conference this year
    for p, _ in CONF:
        emit("set_global_variable = { name = wm_test_cpoll_%s value = global_var:wm_poll_%s }" % (p, p))
    emit("wm_conference_autumn_effect = yes")
    check("conference_once_a_year", " ".join("global_var:wm_poll_%s = global_var:wm_test_cpoll_%s" % (p, p) for p, _ in CONF))


def end():
    phase("end")
    # Polling day has passed (and the election event, which needs wm_el_scheduled, won't fire)
    emit("remove_global_variable = wm_el_scheduled")
    emit("remove_global_variable = wm_el_campaign")
    emit("remove_global_variable = wm_campaign_ticked")
    emit("wm_campaign_watch_effect = yes")
    check("campaign_ends_after_polling_day", "NOT = { has_global_variable = wm_campaign_active } NOT = { has_global_variable = wm_campaign_week }")
    emit("remove_global_variable = wm_test_quiet")


setup()
start()
polls()
door()
conference()
end()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_campaign.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(blocks) + "\n\tdebug_log = \"RFT done\"\n}\nrf_test_effect_later = {\n}\n", encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
EVENTS.parent.mkdir(exist_ok=True)
EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
