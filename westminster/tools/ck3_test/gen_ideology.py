#!/usr/bin/env python3
"""Writes Westminster's ideology tests (religion is political ideology: tools/data/build_ideology.py) into the harness
(harness/common/scripted_effects/rf_test_effects.txt), in the style of gen_politics.py.

The save must be made after the ideologies were added to the bookmark (build_2024.py): run
tools/ck3_test/make_save.sh first. The suite sets global_var:wm_test_quiet and checks everything at once, so the
game can stay paused:

    python3 westminster/tools/ck3_test/gen_ideology.py
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 \\
      common/ck3_test/run_test.sh westminster/tools/test_out/ideology.log
    python3 common/ck3_test/report.py westminster/tools/test_out/ideology.log
    python3 common/tools/ck3_checks.py errorlog wm_

What it covers:
  caucus     MPs on a caucus list have its ideology (Socialist Campaign Group: Jeremy Corbyn, John McDonnell, Diane
             Abbott; One Nation: Tom Tugendhat; ERG: Mark Francois; Free Market Forum: Kemi Badenoch)
  fallback   party leaders and other MPs take their party's ideology (Starmer, Davey, Farage, Denyer, Flynn,
             Robinson, both Eastwoods, Saville Roberts, Maskey); every Labour, Conservative, Lib Dem and Reform MP is
             inside their party's range; independents by former party (Alex Easton: Unionist)
  apolitical the royal family, the Speaker and the MPs' spouses are Not Stated
  seats      seats take the 2024 winner's ideology (Aldershot, Richmond, Clacton, Islington North, Chorley, Belfast
             West, North Down); most Labour seats are Social Democrat
  hostility  same ideology 0, same camp 1, left/right 2, nationalist/unionist 3, Not Stated 0; no holy wars, no head
             of faith, pluralistic (no faith imprisonment)
  wings      each wing holds only its ideology, and each Labour/Conservative MP of a wing ideology is in that wing;
             changing ideology changes wing
  decision   Change Your Politics: a backbencher can take it (the Speaker can't); choosing Socialist converts them
             and moves their wing; a Conservative who joins Labour is moved to the nearest Labour ideology
  bills      a Finance Bill (taxes up) adds dissent for a low-tax ideology and less for a tax-and-spend one
  drift      a rioting, low-trust seat converts to its MP's ideology; Northern Ireland seats don't follow the
             national polls
"""
import os
from pathlib import Path

# RFT_OUT=<file> writes elsewhere (to look at the suite without touching the harness)
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


def f(k):
    return "faith:wm_ideo_" + k


def mp(seat):
    return "title:c_%s.holder" % seat


def in_range(ideos):
    return "OR = { %s }" % " ".join("faith = %s" % f(i) for i in ideos)


def setup():
    phase("setup")
    emit("set_global_variable = { name = wm_test_quiet value = yes }")
    check("pm_exists", "exists = %s" % PM)


def caucus():
    phase("caucus")
    for name, seat, ideo in [("corbyn_socialist", "islington_north", "socialist"),
                             ("mcdonnell_socialist", "hayes_and_harlington", "socialist"),
                             ("abbott_socialist", "hackney_north_and_stoke_newington", "socialist"),
                             ("tugendhat_one_nation", "tonbridge", "one_nation"),
                             ("francois_national_conservative", "rayleigh_and_wickford", "national_conservative"),
                             ("badenoch_free_market", "north_west_essex", "free_market")]:
        check(name, "faith = %s" % f(ideo), mp(seat))


def fallback():
    phase("fallback")
    for name, seat, ideo in [("starmer_social_democrat", "holborn_and_st_pancras", "social_democrat"),
                             ("davey_liberal", "kingston_and_surbiton", "liberal"),
                             ("farage_populist_right", "clacton", "populist_right"),
                             ("denyer_green", "bristol_central", "green"),
                             ("flynn_scottish_nationalist", "aberdeen_south", "scottish_nationalist"),
                             ("robinson_unionist", "belfast_east", "unionist"),
                             ("colum_eastwood_irish_nationalist", "foyle", "irish_nationalist"),
                             ("sorcha_eastwood_cross_community", "lagan_valley", "cross_community"),
                             ("saville_roberts_welsh_nationalist", "dwyfor_meirionnydd", "welsh_nationalist"),
                             ("maskey_irish_republican", "belfast_west", "irish_republican"),
                             ("easton_independent_unionist", "north_down", "unionist")]:
        check(name, "faith = %s" % f(ideo), mp(seat))
    for party, ideos in [("labour", ["social_democrat", "socialist", "centrist"]),
                         ("conservative", ["one_nation", "free_market", "national_conservative"]),
                         ("lib_dem", ["liberal", "centrist"]), ("reform", ["populist_right"])]:
        check("%s_mps_in_range" % party, "NOT = { any_living_character = { var:wm_party ?= title:k_party_%s "
              "wm_is_mp_trigger = yes NOT = { %s } } }" % (party, in_range(ideos)))
    check("labour_mostly_social_democrat", "any_living_character = { var:wm_party ?= title:k_party_labour "
          "wm_is_mp_trigger = yes faith = %s count >= 250 }" % f("social_democrat"))
    check("conservatives_spread", " ".join("any_living_character = { var:wm_party ?= title:k_party_conservative "
                                          "faith = %s count >= 10 }" % f(i)
                                          for i in ("one_nation", "free_market", "national_conservative")))


def apolitical():
    phase("apolitical")
    check("monarch_not_stated", "faith = faith:wm_faith_not_stated", "title:k_wm_crown.holder")
    check("royal_family_not_stated", "NOT = { any_living_character = { dynasty ?= dynasty:wm_dyn_royal_windsor "
          "NOT = { faith = faith:wm_faith_not_stated } } }")
    check("speaker_not_stated", "faith = faith:wm_faith_not_stated", mp("chorley"))
    check("spouses_not_stated", "any_living_character = { wm_is_mp_trigger = yes any_spouse = { faith = faith:wm_faith_not_stated } "
          "count >= 300 }")
    check("nobody_catholic", "NOT = { any_living_character = { faith = faith:catholic } }")


def seats():
    phase("seats")
    for seat, ideo in [("aldershot", "social_democrat"), ("richmond_and_northallerton", "one_nation"),
                       ("clacton", "populist_right"), ("islington_north", "socialist"),
                       ("belfast_west", "irish_republican"), ("north_down", "unionist")]:
        check("seat_%s_%s" % (seat, ideo), "faith = %s" % f(ideo), "title:c_" + seat)
    check("seat_chorley_not_stated", "faith = faith:wm_faith_not_stated", "title:c_chorley")
    check("labour_seats_social_democrat", "%s = { any_in_de_jure_hierarchy = { tier = tier_county "
          "faith = %s count >= 380 } }" % (SEATS, f("social_democrat")))
    check("no_catholic_seat", "NOT = { %s = { any_in_de_jure_hierarchy = { tier = tier_county faith = faith:catholic } } }" % SEATS)


def hostility():
    phase("hostility")
    for a, b, level in [("social_democrat", "social_democrat", 0), ("social_democrat", "socialist", 1),
                        ("social_democrat", "liberal", 1), ("social_democrat", "one_nation", 2),
                        ("socialist", "populist_right", 2), ("liberal", "free_market", 1),
                        ("scottish_nationalist", "social_democrat", 1), ("scottish_nationalist", "one_nation", 2),
                        ("unionist", "irish_republican", 3), ("irish_nationalist", "unionist", 3),
                        ("unionist", "one_nation", 1), ("cross_community", "unionist", 1)]:
        check("hostility_%s_%s_%d" % (a, b, level), "faith_hostility_level = { target = %s value = %d }" % (f(b), level), f(a))
    check("not_stated_to_unionist_0", "faith_hostility_level = { target = %s value = 0 }" % f("unionist"),
          "faith:wm_faith_not_stated")
    check("unionist_to_not_stated_0", "faith_hostility_level = { target = faith:wm_faith_not_stated value = 0 }", f("unionist"))
    check("no_holy_wars", "faith = { has_doctrine_parameter = holy_wars_forbidden }", PM)
    check("no_holy_wars_right", "faith = { has_doctrine_parameter = holy_wars_forbidden }", mp("rayleigh_and_wickford"))
    check("no_holy_wars_not_stated", "has_doctrine_parameter = holy_wars_forbidden", "faith:wm_faith_not_stated")
    check("no_head_of_faith", "NOT = { exists = religious_head }", f("social_democrat"))
    check("pluralistic", "has_doctrine = doctrine_pluralism_pluralistic", f("national_conservative"))
    check("policy_doctrine", "has_doctrine = wm_ideo_doc_low_tax", f("free_market"))
    check("corbyn_francois_opposed", "faith_hostility_level = { target = %s.faith value >= 2 }" % mp("rayleigh_and_wickford"),
          mp("islington_north") + ".faith")


def wings():
    phase("wings")
    for wid, ideo in [(1, "socialist"), (2, "social_democrat"), (3, "centrist"), (4, "one_nation"),
                      (5, "free_market"), (6, "national_conservative")]:
        check("wing_%d_is_%s" % (wid, ideo), "NOT = { any_living_character = { var:wm_wing ?= %d NOT = { faith = %s } } }"
              % (wid, f(ideo)))
        party = "labour" if wid <= 3 else "conservative"
        check("%s_mps_in_wing_%d" % (ideo, wid), "NOT = { any_living_character = { var:wm_party ?= title:k_party_%s "
              "wm_is_mp_trigger = yes faith = %s NOT = { this = title:k_party_%s.holder } NOT = { var:wm_wing ?= %d } } }"
              % (party, f(ideo), party, wid))
    check("socialist_wing_size", "any_living_character = { var:wm_wing ?= 1 count >= 20 }")
    check("corbyn_no_wing", "NOT = { has_variable = wm_wing }", mp("islington_north"))


def decision():
    phase("decision")
    emit("""%s = {
	random_in_de_jure_hierarchy = {
		limit = {
			tier = tier_county
			holder ?= {
				var:wm_party ?= title:k_party_labour
				NOT = { this = title:k_party_labour.holder }
				faith = %s
				var:wm_wing ?= 2
			}
		}
		holder = { save_scope_as = wm_test_convert }
	}
}""" % (SEATS, f("social_democrat")))
    check("found_backbencher", "exists = scope:wm_test_convert")
    emit("scope:wm_test_convert = { add_prestige = 2000 add_piety = 1000 }")
    check("backbencher_can_change_politics", "can_execute_decision = wm_ideo_change_decision", "scope:wm_test_convert")
    check("speaker_cannot_change_politics", "NOT = { can_execute_decision = wm_ideo_change_decision }", mp("chorley"))
    emit("scope:wm_test_convert = { save_scope_value_as = { name = wm_ideo_pick_socialist value = yes } "
         "wm_ideo_change_chosen_effect = yes }")
    check("converted_to_socialist", "faith = %s" % f("socialist"), "scope:wm_test_convert")
    check("moved_to_labour_left", "var:wm_wing ?= 1 var:wm_commons_wing ?= -1 has_character_modifier = wm_wing_badge_1 "
          "NOT = { has_character_modifier = wm_wing_badge_2 }", "scope:wm_test_convert")
    # A Conservative who joins Labour is fitted to the nearest Labour ideology (One Nation -> Centrist)
    emit("""%s = {
	random_in_de_jure_hierarchy = {
		limit = {
			tier = tier_county
			holder ?= {
				var:wm_party ?= title:k_party_conservative
				NOT = { this = title:k_party_conservative.holder }
				faith = %s
			}
		}
		holder = { save_scope_as = wm_test_crosser }
	}
}""" % (SEATS, f("one_nation")))
    emit("scope:wm_test_crosser = { set_variable = { name = wm_party value = title:k_party_labour } wm_ideo_fit_party_effect = yes }")
    check("crosser_fitted_to_labour", "faith = %s" % f("centrist"), "scope:wm_test_crosser")
    check("crosser_wing_follows", "var:wm_wing ?= 3", "scope:wm_test_crosser")
    emit("scope:wm_test_crosser = { set_variable = { name = wm_party value = title:k_party_conservative } }")


def bills():
    phase("bills")
    emit("set_global_variable = { name = wm_commons_bill_type value = 1 }")
    check("finance_bill_angers_low_tax", "wm_ideo_bill_clash_value = 8", mp("rayleigh_and_wickford"))
    check("finance_bill_suits_tax_and_spend", "wm_ideo_bill_clash_value = -4", PM)
    emit("set_global_variable = { name = wm_commons_bill_type value = 4 }")
    check("emergency_powers_anger_liberals", "wm_ideo_bill_clash_value = 8", mp("kingston_and_surbiton"))
    emit("remove_global_variable = wm_commons_bill_type")


def drift():
    phase("drift")
    emit("""%s = {
	random_in_de_jure_hierarchy = {
		limit = {
			tier = tier_county
			faith = %s
			holder ?= {
				var:wm_party ?= title:k_party_labour
				faith = %s
				NOT = { this = title:k_party_labour.holder }
				NOT = { this = scope:wm_test_convert }
			}
		}
		save_scope_as = wm_test_seat
	}
}""" % (SEATS, f("social_democrat"), f("social_democrat")))
    check("found_seat", "exists = scope:wm_test_seat")
    emit("scope:wm_test_seat.holder = { wm_ideo_set_faith_effect = { FAITH = %s } }" % f("centrist"))
    emit("scope:wm_test_seat = { add_county_modifier = { modifier = wm_riot_county_modifier days = 30 } }")
    emit("set_global_variable = { name = wm_test_trust value = global_var:wm_public_trust }")
    emit("set_global_variable = { name = wm_public_trust value = 10 }")
    check("riot_low_trust_faster", "wm_ideo_seat_drift_mp_chance_value >= 5", "scope:wm_test_seat")
    emit("set_global_variable = { name = wm_public_trust value = 60 }")
    check("calm_seat_slow", "wm_ideo_seat_drift_mp_chance_value = 4", "scope:wm_test_seat")
    emit("set_global_variable = { name = wm_public_trust value = 10 }")
    emit("while = { limit = { scope:wm_test_seat = { NOT = { faith = %s } } } wm_ideo_monthly_effect = yes }" % f("centrist"))
    check("seat_follows_mp", "faith = %s" % f("centrist"), "scope:wm_test_seat")
    check("national_lead_known", "exists = global_var:wm_ideo_national_faith")
    check("ni_seat_not_pulled_by_polls", "faith = %s" % f("irish_republican"), "title:c_belfast_west")
    check("speaker_seat_not_pulled", "faith = faith:wm_faith_not_stated", "title:c_chorley")
    emit("set_global_variable = { name = wm_public_trust value = global_var:wm_test_trust }")
    emit("remove_global_variable = wm_test_trust")
    emit("remove_global_variable = wm_test_quiet")


setup()
caucus()
fallback()
apolitical()
seats()
hostility()
wings()
decision()
bills()
drift()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_ideology.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n"
               + "\n".join(b for b in blocks if b) + "\n\tdebug_log = \"RFT done\"\n}\nrf_test_effect_later = {\n}\n", encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
if not os.environ.get("RFT_OUT"):
    EVENTS.parent.mkdir(exist_ok=True)
    EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
