#!/usr/bin/env python3
"""Writes Westminster's spike tests into the harness (harness/common/scripted_effects/rf_test_effects.txt).

Runs on the Westminster test save (tools/ck3_test/saves/wm_2025.ck3: the test bookmark, 1 Jan 2025, playing the
test PM who holds the United Kingdom, England and one seat). Each check logs RFT_PASS / RFT_FAIL to debug.log:

    python3 westminster/tools/ck3_test/gen_spikes.py <spike letters, e.g. degh; default b>
    HARNESS=westminster/tools/ck3_test/harness MODS="mod/westminster.mod" \\
      SAVE=westminster/tools/ck3_test/saves/wm_2025.ck3 UNPAUSE=1 common/ck3_test/run_test.sh westminster/tools/test_out/spikes.log
    python3 common/ck3_test/report.py westminster/tools/test_out/spikes.log
"""
import sys
from pathlib import Path

SPIKE = sys.argv[1] if len(sys.argv) > 1 else "b"

OUT = Path(__file__).resolve().parent / "harness/common/scripted_effects/rf_test_effects.txt"
blocks = []
later = []          # run by event rf_test.2, 40 days after setup (run_test.sh with UNPAUSE=1 lets time pass)


def emit(text):
    (later if LATER else blocks).append(text)


LATER = False


def log(msg):
    return 'debug_log = "%s"' % msg


def check(name, cond, scope=None):
    test = cond if scope is None else "%s = { %s }" % (scope, cond)
    emit("if = { limit = { %s } %s }\nelse = { %s }" % (test, log("RFT_PASS " + name), log("RFT_FAIL " + name)))


def show(label, scope):
    """Log a scope (debug_log_scopes prints it on the next line)."""
    emit("%s = { %s debug_log_scopes = yes }" % (scope, log("RFT_DETAIL " + label)))


def phase(name):
    emit(log("RFT_PHASE " + name))


def spike_b():
    global LATER
    SEATS = ["c_aldershot", "c_basingstoke", "c_bath", "c_bedford", "c_blackpool_south"]

    # ---------------------------------------------------------------- spike b: party leadership election
    # In the TUV (one MP, its leader), so five test MPs are the whole electorate and the favourite is clear
    phase("party_leadership")
    emit("title:k_party_tuv.holder = { save_scope_as = wm_leader }")
    check("party_title_held", "exists = holder", "title:k_party_tuv")
    check("party_has_election_law", "has_title_law = wm_party_succession_law", "title:k_party_tuv")
    for i, seat in enumerate(SEATS):
        emit("""create_character = {
    	name = "Test MP %d"
    	age = %d
    	gender = male
    	culture = culture:english
    	faith = faith:wm_faith_not_stated
    	location = root.capital_province
    	save_scope_as = wm_mp_%d
    }
    create_title_and_vassal_change = { type = granted save_scope_as = wm_change add_claim_on_loss = no }
    title:%s = { change_title_holder = { holder = scope:wm_mp_%d change = scope:wm_change } }
    scope:wm_mp_%d = { change_liege = { liege = scope:wm_leader change = scope:wm_change } }
    resolve_title_and_vassal_change = scope:wm_change
    scope:wm_mp_%d = { set_variable = { name = wm_party value = title:k_party_tuv } }""" % (i + 1, 40 + i * 3, i, seat, i, i, i))
    # Make MP 3 the obvious favourite: famous and liked by colleagues
    emit("scope:wm_mp_2 = { add_prestige = 2000 }")
    for i in (0, 1, 3, 4):
        emit("scope:wm_mp_%d = { add_opinion = { target = scope:wm_mp_2 modifier = friendliness_opinion opinion = 50 } }" % i)
    check("party_five_mps", "any_vassal = { count >= 5 has_variable = wm_party var:wm_party = title:k_party_tuv }", "scope:wm_leader")
    check("mp_holds_seat", "holder = scope:wm_mp_0", "title:c_aldershot")
    # Saved scopes don't survive until the later event, so keep what it needs in global variables
    emit("set_global_variable = { name = wm_test_old_leader value = scope:wm_leader }")
    emit("set_global_variable = { name = wm_test_favourite value = scope:wm_mp_2 }")
    # Let the election tally its votes, then the leader dies (the event fires for root, the player)
    LATER = True
    phase("party_leadership_after_40_days")
    check("party_has_electors", "any_elector = { count >= 5 }", "title:k_party_tuv")
    # AI votes otherwise update on the AI's own schedule (vanilla does the same after forcing a papal vote)
    emit("title:k_party_tuv = { every_elector = { recalculate_succession_election_vote = yes } }")
    emit("title:k_party_tuv = { every_elector = { %s debug_log_scopes = yes } }" % log("RFT_DETAIL elector"))
    emit("title:k_party_tuv = { every_title_heir = { %s debug_log_scopes = yes } }" % log("RFT_DETAIL title_heir"))
    emit("""title:k_party_tuv = { every_elector = { save_temporary_scope_as = wm_el
    	if = { limit = { global_var:wm_test_favourite = { has_election_vote_of = { who = scope:wm_el title = title:k_party_tuv } } } %s debug_log_scopes = yes }
    	else = { %s debug_log_scopes = yes }
    } }""" % (log("RFT_DETAIL votes_for_favourite"), log("RFT_DETAIL votes_elsewhere")))
    check("favourite_is_heir", "any_title_heir = { this = global_var:wm_test_favourite }", "title:k_party_tuv")
    emit("global_var:wm_test_old_leader = { death = natural }")
    check("old_leader_dead", "is_alive = no", "global_var:wm_test_old_leader")
    show("new_party_leader", "title:k_party_tuv.holder")
    check("new_leader_is_an_mp", "exists = holder holder = { is_alive = yes has_variable = wm_party var:wm_party = title:k_party_tuv }",
          "title:k_party_tuv")
    check("new_leader_is_favourite", "holder = global_var:wm_test_favourite", "title:k_party_tuv")
    show("new_uk_holder", "title:e_united_kingdom.holder")
    LATER = False



def spike_c():
    """A general election: every seat gets a winner (Labour or Conservative at random, keeping the incumbent
    where the party holds), the seat changes hands in one title change, and the MP becomes a vassal of their
    party's leader. Twice: first from the start (one PM holding everything), then a second election with
    incumbents. RFT_TIME lines time each part."""
    phase("general_election")
    emit("set_variable = { name = wm_party value = title:k_party_labour }")
    # The Conservative leader in the 2024 bookmark (Sunak, who sits for Richmond and Northallerton)
    emit("set_global_variable = { name = wm_tory_leader value = title:k_party_conservative.holder }")
    check("tory_leader_set", "holder = global_var:wm_tory_leader", "title:k_party_conservative")
    for run in (1, 2):
        emit(log("RFT_TIME election_%d_start" % run))
        emit("""title:e_united_kingdom = {
	every_in_de_jure_hierarchy = {
		limit = { tier = tier_county NOT = { this = title:c_holborn_and_st_pancras this = title:c_richmond_and_northallerton } }
		save_scope_as = wm_seat
		random_list = {
			50 = { title:k_party_labour = { save_scope_as = wm_winner } root = { save_scope_as = wm_leader } }
			50 = { title:k_party_conservative = { save_scope_as = wm_winner } global_var:wm_tory_leader = { save_scope_as = wm_leader } }
		}
		if = {
			limit = { exists = holder holder = { has_variable = wm_party var:wm_party = scope:wm_winner NOT = { this = root } } }
			holder = { save_scope_as = wm_mp }
		}
		else = {
			root = { create_character = { age = 45 gender_female_chance = 35 culture = culture:english faith = faith:wm_faith_not_stated
				location = root.capital_province save_scope_as = wm_mp } }
			scope:wm_mp = { set_variable = { name = wm_party value = scope:wm_winner } }
			create_title_and_vassal_change = { type = granted save_scope_as = wm_change add_claim_on_loss = no }
			change_title_holder = { holder = scope:wm_mp change = scope:wm_change }
			scope:wm_mp = { change_liege = { liege = scope:wm_leader change = scope:wm_change } }
			resolve_title_and_vassal_change = scope:wm_change
		}
	}
}""")
        emit(log("RFT_TIME election_%d_done" % run))
        check("election_%d_all_seats_have_mps" % run,
              "NOT = { any_in_de_jure_hierarchy = { tier = tier_county NOT = { exists = holder } } }", "title:e_united_kingdom")
        check("election_%d_mps_serve_their_leader" % run,
              "NOT = { any_in_de_jure_hierarchy = { tier = tier_county exists = holder holder = { has_variable = wm_party "
              "NOT = { this = root this = global_var:wm_tory_leader } NOT = { liege = var:wm_party.holder } } } }", "title:e_united_kingdom")
        emit("""title:e_united_kingdom = {
	every_in_de_jure_hierarchy = { limit = { tier = tier_county holder ?= { var:wm_party ?= title:k_party_labour } } add_to_temporary_list = wm_lab_%d }
	every_in_de_jure_hierarchy = { limit = { tier = tier_county holder ?= { var:wm_party ?= title:k_party_conservative } } add_to_temporary_list = wm_con_%d }
}
root = { set_variable = { name = wm_lab_seats value = 0 } set_variable = { name = wm_con_seats value = 0 } }
every_in_list = { list = wm_lab_%d root = { change_variable = { name = wm_lab_seats add = 1 } } }
every_in_list = { list = wm_con_%d root = { change_variable = { name = wm_con_seats add = 1 } } }""" % (run, run, run, run))
        check("election_%d_both_parties_win_200_plus" % run, "var:wm_lab_seats >= 200 var:wm_con_seats >= 200")
        emit("root = { set_variable = { name = wm_total_seats value = var:wm_lab_seats } change_variable = { name = wm_total_seats add = var:wm_con_seats } }")
        check("election_%d_650_party_seats" % run, "var:wm_total_seats = 650")



def new_char(scope, name, age=50, extra=""):
    emit("""create_character = { name = "%s" age = %d gender = male culture = culture:english faith = faith:wm_faith_not_stated
	location = root.capital_province %s save_scope_as = %s }""" % (name, age, extra, scope))


NO_LAND = "NOT = { any_held_title = { is_landless_type_title = no } }"


def spike_d():
    """Peerages: landless county-tier titles held by people with no seat. Life peerages end with the holder;
    hereditary ones pass to the heir."""
    phase("peerages")
    new_char("wm_life_peer", "Test Life Peer", 70)
    emit("scope:wm_life_peer = { get_title = title:c_peerage_life_test }")
    check("life_peer_holds_peerage", "holder = scope:wm_life_peer", "title:c_peerage_life_test")
    check("life_peer_has_no_land", NO_LAND, "scope:wm_life_peer")
    show("life_peer_liege", "scope:wm_life_peer.liege")
    new_char("wm_earl", "Test Earl", 60)
    new_char("wm_earl_son", "Test Earl's Son", 30)
    emit("scope:wm_earl_son = { set_father = scope:wm_earl }")
    emit("scope:wm_earl = { get_title = title:c_peerage_hereditary_test }")
    check("earl_holds_peerage", "holder = scope:wm_earl", "title:c_peerage_hereditary_test")
    emit("scope:wm_life_peer = { death = natural }")
    check("life_peerage_ends_with_holder", "NOT = { exists = holder }", "title:c_peerage_life_test")
    emit("scope:wm_earl = { death = natural }")
    check("hereditary_peerage_passes_to_son", "holder = scope:wm_earl_son", "title:c_peerage_hereditary_test")
    check("son_has_no_land", NO_LAND, "scope:wm_earl_son")


def spike_e():
    """A mayoralty: a landless duchy-tier title held by someone with no seat, serving their party leader."""
    phase("mayor")
    new_char("wm_mayor", "Test Mayor", 55)
    emit("scope:wm_mayor = { get_title = title:d_mayor_greater_manchester }")
    check("mayor_holds_office", "holder = scope:wm_mayor", "title:d_mayor_greater_manchester")
    check("mayor_has_no_land", NO_LAND, "scope:wm_mayor")
    emit("""create_title_and_vassal_change = { type = swear_fealty save_scope_as = wm_change add_claim_on_loss = no }
scope:wm_mayor = { change_liege = { liege = root change = scope:wm_change } }
resolve_title_and_vassal_change = scope:wm_change""")
    check("mayor_serves_party_leader", "liege = root", "scope:wm_mayor")
    check("mayor_keeps_office_as_vassal", "holder = scope:wm_mayor", "title:d_mayor_greater_manchester")


def spike_g():
    """A council: a landless title whose seats per party are stored on the title, with an election that sets
    party control (majority, otherwise no overall control)."""
    phase("council")
    new_char("wm_council_leader", "Test Council Leader", 50)
    emit("scope:wm_council_leader = { get_title = title:c_council_test set_variable = { name = wm_party value = title:k_party_labour } }")
    check("council_leader_holds_council", "holder = scope:wm_council_leader", "title:c_council_test")
    emit("""title:c_council_test = {
	set_variable = { name = wm_seats_total value = 75 }
	set_variable = { name = wm_seats_lab value = 0 }
	set_variable = { name = wm_seats_con value = 0 }
	set_variable = { name = wm_seats_other value = 0 }
	# Council election: each seat goes Labour 50%, Conservative 30%, other 20%
	while = {
		count = 75
		random_list = {
			50 = { change_variable = { name = wm_seats_lab add = 1 } }
			30 = { change_variable = { name = wm_seats_con add = 1 } }
			20 = { change_variable = { name = wm_seats_other add = 1 } }
		}
	}
	if = { limit = { var:wm_seats_lab >= 38 } set_variable = { name = wm_control value = title:k_party_labour } }
	else_if = { limit = { var:wm_seats_con >= 38 } set_variable = { name = wm_control value = title:k_party_conservative } }
	else = { remove_variable = wm_control }
	set_variable = { name = wm_seats_sum value = var:wm_seats_lab }
	change_variable = { name = wm_seats_sum add = var:wm_seats_con }
	change_variable = { name = wm_seats_sum add = var:wm_seats_other }
}""")
    check("council_seats_add_up", "var:wm_seats_sum = 75", "title:c_council_test")
    check("council_control_matches_majority",
          "OR = { AND = { var:wm_seats_lab >= 38 var:wm_control = title:k_party_labour } "
          "AND = { var:wm_seats_con >= 38 var:wm_control = title:k_party_conservative } "
          "AND = { var:wm_seats_lab < 38 var:wm_seats_con < 38 NOT = { has_variable = wm_control } } }", "title:c_council_test")


def spike_h():
    """Devolved governments: a First Minister holding a landless kingdom-tier title, and Northern Ireland's
    First Minister and deputy First Minister sharing power as a diarchy."""
    phase("devolved")
    new_char("wm_fm_scotland", "Test First Minister", 50)
    emit("scope:wm_fm_scotland = { get_title = title:k_gov_scotland }")
    check("scottish_fm_holds_government", "holder = scope:wm_fm_scotland", "title:k_gov_scotland")
    check("scottish_fm_has_no_land", NO_LAND, "scope:wm_fm_scotland")
    new_char("wm_fm_ni", "Test NI First Minister", 50)
    new_char("wm_dfm_ni", "Test NI deputy First Minister", 48)
    emit("scope:wm_fm_ni = { get_title = title:k_gov_northern_ireland }")
    check("ni_fm_holds_executive", "holder = scope:wm_fm_ni", "title:k_gov_northern_ireland")
    emit("scope:wm_fm_ni = { try_start_diarchy = co_emperorship set_diarch = scope:wm_dfm_ni }")
    check("ni_power_sharing_diarchy", "is_diarch_of_target = scope:wm_fm_ni", "scope:wm_dfm_ni")
    show("ni_fm_diarch", "scope:wm_fm_ni.diarch")


def spike_f():
    """An unlanded hopeful as a landless adventurer (camp = campaign team) who takes a party's "seek selection"
    contract and completes it."""
    phase("unlanded_candidate")
    new_char("wm_cand", "Test Hopeful", 32)
    emit("create_adventurer_title = { name = wm_campaign_title_name holder = scope:wm_cand save_scope_as = wm_camp }")
    check("hopeful_is_landless_adventurer", "is_landless_adventurer = yes", "scope:wm_cand")
    check("hopeful_has_no_land", NO_LAND, "scope:wm_cand")
    # The character running create_task_contract owns the contract (it's offered to them)
    emit("""scope:wm_cand = { create_task_contract = {
	task_contract_employer = root
	task_contract_type = wm_selection_contract
	task_contract_tier = 1
	location = root.capital_province
	save_scope_as = wm_contract
} }""")
    check("contract_created", "exists = scope:wm_contract")
    emit("scope:wm_cand = { accept_task_contract = scope:wm_contract }")
    check("contract_taken_by_hopeful", "task_contract_taker ?= scope:wm_cand", "scope:wm_contract")
    emit("scope:wm_contract = { task_contract_taker ?= { %s debug_log_scopes = yes } }" % log("RFT_DETAIL taker"))
    emit("scope:wm_contract = { %s debug_log_scopes = yes }" % log("RFT_DETAIL contract"))
    check("contract_accepted", "has_variable = wm_seeking_selection", "scope:wm_cand")
    emit("scope:wm_contract = { complete_task_contract = success_standard }")
    check("contract_completed_shortlisted", "has_variable = wm_on_shortlist NOT = { has_variable = wm_seeking_selection }", "scope:wm_cand")

SPIKES = {"f": spike_f, "b": spike_b, "c": spike_c, "d": spike_d, "e": spike_e, "g": spike_g, "h": spike_h}
for letter in SPIKE:          # e.g. "degh" runs several in one go
    SPIKES[letter]()

OUT.write_text("# Generated by westminster/tools/ck3_test/gen_spikes.py - edit there.\nrf_test_effect = {\n\tdebug_log = \"RFT start\"\n\tset_global_variable = { name = wm_test_quiet value = yes }\t# no player pop-ups (they pause the game)\n"
               + "\n".join(blocks) + ("\n\ttrigger_event = { id = rf_test.2 days = 40 }\n}\n" if later else "\n\tdebug_log = \"RFT done\"\n}\n")
               + "rf_test_effect_later = {\n" + "\n".join(later) + "\n\tdebug_log = \"RFT done\"\n}\n", encoding="utf-8-sig")
EVENTS = OUT.parent.parent.parent / "events" / "rf_test_events.txt"
EVENTS.parent.mkdir(exist_ok=True)
EVENTS.write_text("namespace = rf_test\nrf_test.2 = {\n\thidden = yes\n\timmediate = { rf_test_effect_later = yes }\n}\n", encoding="utf-8-sig")
print("wrote", OUT)
