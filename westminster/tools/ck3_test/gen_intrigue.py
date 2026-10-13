#!/usr/bin/env python3
"""Writes Westminster's intrigue tests (Fabricate a Scandal, Leak to the Press, Plot to Oust, an affair, and the
real-people safeguards) into the harness (harness/common/scripted_effects/rf_test_effects.txt), in the style of
gen_politics.py.

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3). The outcome rolls are forced with
global_var:wm_intrigue_force (1 success, 2 failure discovered), so everything is checked at once and the game can stay
paused. The suite sets global_var:wm_test_quiet (no pop-ups):

    python3 westminster/tools/ck3_test/gen_intrigue.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/intrigue.log
    python3 common/ck3_test/report.py westminster/tools/test_out/intrigue.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  real      MPs, royals (the King, the Prince of Wales, the royal children) and other real figures are real people
            (flagged, and in the fallback list for old saves); a generated spouse and new characters are fictional;
            the royal children and anyone under 18 can never be affair targets
  banned    murder and abduction can't be started
  affair    a fictional AI can start an affair with a fictional adult, but not with a real MP, a royal or a
            16-year-old; a real AI MP can't start one even with a fictional target; success makes them lovers (and
            a lover secret when one is married) and ends the scheme; a discovered failure leaves the cooldown
  scandal   an AI MP can start Fabricate a Scandal on a rival party's leader (no perk needed); success gives a hook
            and a story secret the schemer knows; a discovered failure leaves the target resentful
  leak      the story is leakable; leaking it costs the target Profile, their party's poll and public trust, and
            the target resents the leaker; a smear-campaign secret leaks without a second poll hit
  oust      a Conservative MP can plot against their leader, not against another MP; success opens a leadership
            challenge (kind 2) with the plotter on the ballot and the leader as incumbent; a discovered failure on
            the Lib Dems leaves the leader resentful and no contest
  flow      the moment to act: an AI scheme's completed phase either waits (marked ready) or resolves
"""
import os
from pathlib import Path

# RFT_OUT=<file> writes elsewhere (to look at the suite without touching the shared harness)
OUT = Path(os.environ.get("RFT_OUT") or Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt")
blocks = []
PM = "title:e_united_kingdom.holder"
CON = "title:k_party_conservative"
LD = "title:k_party_lib_dem"


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


def person(scope, name, age, gender, extra=""):
    emit("""create_character = { name = "%s" age = %d gender = %s culture = culture:english faith = faith:wm_faith_not_stated
	location = root.capital_province save_scope_as = %s }
scope:%s = { set_sexuality = heterosexual %s }""" % (name, age, gender, scope, scope, extra))


def resolve(owner, kind, target):
    emit("scope:%s = { random_scheme = { limit = { scheme_type = %s scheme_target_character = scope:%s } "
         "wm_intrigue_resolve_effect = yes } }" % (owner, kind, target))


def can_start(owner, kind, target):
    return "scope:%s = { can_start_scheme = { type = %s target_character = scope:%s } }" % (owner, kind, target)


def setup():
    phase("setup")
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    emit("wm_election_init_effect = yes")
    for v in ("wm_el_scheduled", "wm_el_campaign", "wm_election_required"):
        emit("remove_global_variable = %s" % v)
    emit("wm_trust_ensure_effect = yes")
    gvar("wm_public_trust", 40)
    emit("wm_intrigue_init_effect = yes")	# the save predates the flags
    check("real_people_marked", "has_global_variable = wm_intrigue_real_marked")
    check("force_hook_reset", "global_var:wm_intrigue_force = 0")
    # Fictional people for the affair tests
    person("wm_t_rake", "Test Rake", 40, "male")
    person("wm_t_crush", "Test Crush", 35, "female")
    person("wm_t_teen", "Test Teen", 16, "female")
    person("wm_t_spouse", "Test Spouse", 38, "female")
    person("wm_t_flirt", "Test Flirt", 33, "male")
    person("wm_t_aide", "Test Aide", 30, "female")
    emit("scope:wm_t_rake = { marry = scope:wm_t_spouse }")
    # A real Labour MP (AI), the Conservative and Lib Dem leaders, a Conservative and a Lib Dem MP (AI)
    emit("%s = { random_vassal = { limit = { is_ai = yes wm_is_mp_trigger = yes has_character_flag = wm_real_person "
         "NOT = { has_character_flag = wm_speaker } } save_scope_as = wm_t_lab_mp } }" % PM)
    emit("%s.holder = { save_scope_as = wm_t_con_leader }" % CON)
    emit("%s.holder = { save_scope_as = wm_t_ld_leader }" % LD)
    emit("scope:wm_t_con_leader = { random_vassal = { limit = { is_ai = yes wm_is_mp_trigger = yes var:wm_party ?= %s } "
         "save_scope_as = wm_t_con_mp } }" % CON)
    emit("scope:wm_t_con_leader = { random_vassal = { limit = { is_ai = yes wm_is_mp_trigger = yes var:wm_party ?= %s "
         "NOT = { this = scope:wm_t_con_mp } } save_scope_as = wm_t_con_mp2 } }" % CON)
    emit("scope:wm_t_ld_leader = { random_vassal = { limit = { is_ai = yes wm_is_mp_trigger = yes var:wm_party ?= %s } "
         "save_scope_as = wm_t_ld_mp } }" % LD)
    for s in ("wm_t_lab_mp", "wm_t_con_leader", "wm_t_ld_leader", "wm_t_con_mp", "wm_t_con_mp2", "wm_t_ld_mp"):
        check("found_" + s[5:], "exists = scope:%s" % s)


def real():
    phase("real")
    for cid in ("wm_mp_aldershot", "wm_royal_charles", "wm_royal_william", "wm_char_john_major"):
        check("real_" + cid[3:], "wm_intrigue_is_real_person_trigger = yes", "character:" + cid)
        check("list_" + cid[3:], "wm_intrigue_real_list_trigger = yes", "character:" + cid)
        check("no_affair_" + cid[3:], "wm_intrigue_affair_target_trigger = no", "character:" + cid)
    for cid in ("wm_royal_george", "wm_royal_charlotte", "wm_royal_louis", "wm_royal_archie", "wm_royal_lilibet"):
        check("royal_child_" + cid[10:], "wm_intrigue_is_royal_trigger = yes wm_intrigue_affair_target_trigger = no",
              "character:" + cid)
    check("royal_spouse_is_royal", "wm_intrigue_is_royal_trigger = yes", "character:wm_royal_catherine")
    check("spouse_is_fictional", "wm_intrigue_is_real_person_trigger = no wm_intrigue_real_list_trigger = no",
          "character:wm_sp_aldershot")
    check("spouse_can_be_affair_target", "wm_intrigue_affair_target_trigger = yes", "character:wm_sp_aldershot")
    check("new_character_fictional", "wm_intrigue_is_real_person_trigger = no wm_intrigue_affair_target_trigger = yes",
          "scope:wm_t_crush")
    check("under_18_never", "wm_intrigue_affair_target_trigger = no", "scope:wm_t_teen")
    # An old save (no flags yet): the list still catches real people
    emit("remove_global_variable = wm_intrigue_real_marked")
    emit("character:wm_mp_aldershot = { remove_character_flag = wm_real_person }")
    check("old_save_still_real", "wm_intrigue_is_real_person_trigger = yes", "character:wm_mp_aldershot")
    check("old_save_spouse_fictional", "wm_intrigue_is_real_person_trigger = no", "character:wm_sp_aldershot")
    emit("character:wm_mp_aldershot = { add_character_flag = wm_real_person }")
    gvar("wm_intrigue_real_marked", "yes")


def banned():
    phase("banned")
    check("no_murder", "NOT = { %s }" % can_start("wm_t_lab_mp", "murder", "wm_t_con_leader"))
    check("no_abduct", "NOT = { %s }" % can_start("wm_t_lab_mp", "abduct", "wm_t_con_leader"))


def affair():
    phase("affair")
    check("affair_fictional_ok", can_start("wm_t_flirt", "seduce", "wm_t_crush"))
    check("affair_not_real_mp", "NOT = { %s }" % can_start("wm_t_flirt", "seduce", "wm_t_lab_mp"))
    emit("character:wm_royal_catherine = { save_scope_as = wm_t_royal }")
    check("affair_not_royal", "NOT = { %s }" % can_start("wm_t_flirt", "seduce", "wm_t_royal"))
    check("affair_not_minor", "NOT = { %s }" % can_start("wm_t_flirt", "seduce", "wm_t_teen"))
    check("affair_not_by_real_ai", "NOT = { %s }" % can_start("wm_t_lab_mp", "seduce", "wm_t_aide"))
    # Success: lovers, and a lover secret (the rake is married)
    emit("scope:wm_t_rake = { start_scheme = { type = seduce target_character = scope:wm_t_crush } }")
    check("affair_started", "any_scheme = { scheme_type = seduce }", "scope:wm_t_rake")
    gvar("wm_intrigue_force", 1)
    resolve("wm_t_rake", "seduce", "wm_t_crush")
    check("affair_lovers", "has_relation_lover = scope:wm_t_crush", "scope:wm_t_rake")
    check("affair_secret", "any_secret = { secret_type = secret_lover }", "scope:wm_t_rake")
    check("affair_scheme_ended", "NOT = { any_scheme = { scheme_type = seduce } }", "scope:wm_t_rake")
    check("affair_outcome_success", "var:wm_intrigue_last_outcome = 1", "scope:wm_t_rake")
    # A discovered failure: rebuffed, with a cooldown
    emit("scope:wm_t_flirt = { start_scheme = { type = seduce target_character = scope:wm_t_aide } }")
    gvar("wm_intrigue_force", 2)
    resolve("wm_t_flirt", "seduce", "wm_t_aide")
    check("affair_rebuffed", "has_opinion_modifier = { target = scope:wm_t_flirt modifier = seduce_regular_cooldown_opinion }",
          "scope:wm_t_aide")
    check("affair_not_lovers", "NOT = { has_relation_lover = scope:wm_t_aide }", "scope:wm_t_flirt")
    check("affair_outcome_caught", "var:wm_intrigue_last_outcome = 2", "scope:wm_t_flirt")


def scandal():
    phase("scandal")
    check("scandal_can_start", can_start("wm_t_lab_mp", "fabricate_hook", "wm_t_con_leader"))
    emit("scope:wm_t_lab_mp = { start_scheme = { type = fabricate_hook target_character = scope:wm_t_con_leader } }")
    check("scandal_started", "any_scheme = { scheme_type = fabricate_hook }", "scope:wm_t_lab_mp")
    gvar("wm_intrigue_force", 1)
    resolve("wm_t_lab_mp", "fabricate_hook", "wm_t_con_leader")
    check("scandal_hook", "has_hook = scope:wm_t_con_leader", "scope:wm_t_lab_mp")
    check("scandal_story", "any_secret = { secret_type = wm_secret_intrigue_story is_known_by = scope:wm_t_lab_mp }",
          "scope:wm_t_con_leader")
    check("scandal_scheme_ended", "NOT = { any_scheme = { scheme_type = fabricate_hook } }", "scope:wm_t_lab_mp")
    # A discovered failure (a Lib Dem MP digging into the Conservative leader)
    emit("scope:wm_t_ld_mp = { start_scheme = { type = fabricate_hook target_character = scope:wm_t_con_leader } }")
    gvar("wm_intrigue_force", 2)
    resolve("wm_t_ld_mp", "fabricate_hook", "wm_t_con_leader")
    check("scandal_caught", "has_opinion_modifier = { target = scope:wm_t_ld_mp modifier = wm_intrigue_caught_digging_opinion }",
          "scope:wm_t_con_leader")
    check("scandal_caught_no_hook", "NOT = { has_hook = scope:wm_t_con_leader }", "scope:wm_t_ld_mp")


def leak():
    phase("leak")
    emit("scope:wm_t_con_leader = { random_secret = { limit = { secret_type = wm_secret_intrigue_story "
         "is_known_by = scope:wm_t_lab_mp } save_scope_as = target } }")
    check("story_leakable", "wm_intrigue_leakable_secret_trigger = yes", "scope:target")
    gvar("wm_test_poll", "global_var:wm_poll_con")
    gvar("wm_test_trust", "global_var:wm_public_trust")
    gvar("wm_test_prestige", "scope:wm_t_con_leader.prestige")
    emit("scope:wm_t_con_leader = { save_scope_as = recipient }")
    emit("scope:wm_t_lab_mp = { save_scope_as = puppet_or_actor }")
    emit("wm_intrigue_leak_effect = yes")
    emit("scope:target = { expose_secret = scope:puppet_or_actor }")
    check("leak_poll_down", "global_var:wm_poll_con < global_var:wm_test_poll")
    check("leak_trust_down", "global_var:wm_public_trust < global_var:wm_test_trust")
    check("leak_profile_down", "prestige < global_var:wm_test_prestige", "scope:wm_t_con_leader")
    check("leak_resented", "has_opinion_modifier = { target = scope:wm_t_lab_mp modifier = wm_intrigue_leaked_opinion }",
          "scope:wm_t_con_leader")
    check("leak_story_spent", "NOT = { any_secret = { secret_type = wm_secret_intrigue_story is_known_by = scope:wm_t_lab_mp } }",
          "scope:wm_t_con_leader")
    # A smear-campaign secret: leakable, but its own exposure already costs the party (no second poll hit here)
    emit("scope:wm_t_ld_leader = { add_secret = { type = wm_secret_smear_campaign } "
         "random_secret = { type = wm_secret_smear_campaign save_scope_as = target } }")
    check("smear_leakable", "wm_intrigue_leakable_secret_trigger = yes", "scope:target")
    gvar("wm_test_poll", "global_var:wm_poll_ld")
    emit("scope:wm_t_ld_leader = { save_scope_as = recipient }")
    emit("wm_intrigue_leak_effect = yes")
    check("smear_no_double_hit", "global_var:wm_poll_ld = global_var:wm_test_poll")
    emit("clear_saved_scope = target")


def oust():
    phase("oust")
    emit("%s = { remove_variable = wm_lead_state }" % CON)
    check("oust_can_start", can_start("wm_t_con_mp", "wm_intrigue_oust", "wm_t_con_leader"))
    check("oust_not_other_mp", "NOT = { %s }" % can_start("wm_t_con_mp", "wm_intrigue_oust", "wm_t_con_mp2"))
    check("oust_not_other_party", "NOT = { %s }" % can_start("wm_t_lab_mp", "wm_intrigue_oust", "wm_t_con_leader"))
    emit("scope:wm_t_con_mp = { start_scheme = { type = wm_intrigue_oust target_character = scope:wm_t_con_leader } }")
    check("oust_started", "any_scheme = { scheme_type = wm_intrigue_oust }", "scope:wm_t_con_mp")
    gvar("wm_intrigue_force", 1)
    resolve("wm_t_con_mp", "wm_intrigue_oust", "wm_t_con_leader")
    check("oust_opens_challenge", "var:wm_lead_state = 1 var:wm_lead_kind = 2 var:wm_lead_incumbent = scope:wm_t_con_leader", CON)
    check("oust_plotter_on_ballot", "is_target_in_variable_list = { name = wm_lead_candidates target = scope:wm_t_con_mp }", CON)
    check("oust_leader_still_leads", "holder = scope:wm_t_con_leader", CON)
    check("oust_scheme_ended", "NOT = { any_scheme = { scheme_type = wm_intrigue_oust } }", "scope:wm_t_con_mp")
    check("oust_blocked_during_contest", "NOT = { %s }" % can_start("wm_t_con_mp2", "wm_intrigue_oust", "wm_t_con_leader"))
    # A discovered failure (Lib Dems): resentment, no contest
    emit("%s = { remove_variable = wm_lead_state }" % LD)
    emit("scope:wm_t_ld_mp = { start_scheme = { type = wm_intrigue_oust target_character = scope:wm_t_ld_leader } }")
    gvar("wm_intrigue_force", 2)
    resolve("wm_t_ld_mp", "wm_intrigue_oust", "wm_t_ld_leader")
    check("oust_caught", "has_opinion_modifier = { target = scope:wm_t_ld_mp modifier = wm_intrigue_caught_plotting_opinion }",
          "scope:wm_t_ld_leader")
    check("oust_caught_no_contest", "NOT = { has_variable = wm_lead_state }", LD)


def flow():
    phase("flow")
    gvar("wm_intrigue_force", 0)
    emit("scope:wm_t_flirt = { remove_variable = wm_intrigue_last_outcome }")
    emit("scope:wm_t_flirt = { start_scheme = { type = seduce target_character = scope:wm_t_crush } }")
    emit("scope:wm_t_flirt = { random_scheme = { limit = { scheme_type = seduce } wm_intrigue_phase_effect = yes } }")
    check("phase_waits_or_resolves", "OR = { any_scheme = { scheme_type = seduce has_variable = wm_intrigue_ready } "
          "has_variable = wm_intrigue_last_outcome }", "scope:wm_t_flirt")
    emit("scope:wm_t_flirt = { every_scheme = { end_scheme = yes } }")
    emit("remove_global_variable = wm_test_quiet")


setup()
real()
banned()
affair()
scandal()
leak()
oust()
flow()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_intrigue.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(b for b in blocks if b) + "\n\tdebug_log = \"RFT done\"\n}\nrf_test_effect_later = {\n}\n", encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
if not os.environ.get("RFT_OUT"):
    EVENTS.parent.mkdir(exist_ok=True)
    EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
