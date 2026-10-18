#!/usr/bin/env python3
"""A small fictional press network and a committee route for backbenchers."""
from mod_files import LANGUAGES, generated_header, write_mod_file as write

HEADER = generated_header("build_press.py")
from build_seat_leans import PARTIES


def main():
    effect = (
        HEADER
        + """wm_press_ensure_effect = {
 if = { limit = { NOT = { has_variable = wm_press_relationship } } set_variable = { name = wm_press_relationship value = 0 } }
}
wm_press_relationship_effect = {
 wm_press_ensure_effect = yes
 set_variable = { name = wm_press_relationship value = { value = var:wm_press_relationship add = $AMOUNT$ min = 0 max = 100 } }
}
wm_press_poll_effect = {
"""
    )
    for k, _, title, *_ in PARTIES:
        effect += f" if = {{ limit = {{ var:wm_party ?= title:{title} }} if = {{ limit = {{ NOT = {{ has_global_variable = wm_poll_{k} }} }} set_global_variable = {{ name = wm_poll_{k} value = 0 }} }} wm_polls_shift_effect = {{ P = {k} AMOUNT = $AMOUNT$ }} }}\n"
    effect += " wm_polls_normalise_effect = yes\n}\n"
    effect += """wm_press_endorsement_effect = {
 wm_press_relationship_effect = { AMOUNT = -25 }
 wm_press_poll_effect = { AMOUNT = 20 }
 if = { limit = { wm_is_mp_trigger = yes } wm_career_surgery_effect = yes }
}
wm_committee_report_effect = {
 if = { limit = { NOT = { has_variable = wm_standing } } set_variable = { name = wm_standing value = 0 } }
 set_variable = { name = wm_standing value = { value = var:wm_standing add = 10 max = 100 } }
 add_prestige = 30
 wm_trust_change_effect = { AMOUNT = 1 }
 set_variable = { name = wm_public_services_caucus value = yes years = 1 }
}
"""
    write("common/scripted_effects/wm_press_effects.txt", effect)
    write(
        "common/decisions/wm_press_decisions.txt",
        HEADER
        + """wm_press_desk_decision = {
 picture = { reference = "gfx/interface/illustrations/loading_screens/wm_commons.dds" }
 decision_group_type = major sort_order = 92 ai_check_interval = 0 cooldown = { months = 2 }
 desc = wm_press_desk_decision_desc selection_tooltip = wm_press_desk_decision_tooltip confirm_text = wm_press_open
 is_shown = { is_adult = yes has_variable = wm_party }
 effect = { wm_press_ensure_effect = yes trigger_event = wm_press.1 }
 ai_potential = { always = no } ai_will_do = { base = 0 }
}
wm_committee_work_decision = {
 picture = { reference = "gfx/interface/illustrations/loading_screens/wm_commons.dds" }
 decision_group_type = major sort_order = 91 ai_check_interval = 0 cooldown = { months = 6 }
 desc = wm_committee_work_decision_desc selection_tooltip = wm_committee_work_decision_tooltip confirm_text = wm_committee_confirm
 is_shown = { wm_is_mp_trigger = yes NOT = { has_character_flag = wm_speaker } NOT = { wm_commons_is_party_leader_trigger = yes } }
 is_valid = { is_imprisoned = no }
 cost = { gold = 20 }
 effect = { wm_committee_report_effect = yes }
 ai_potential = { always = no } ai_will_do = { base = 0 }
}
""",
    )
    write(
        "events/wm_press_events.txt",
        HEADER
        + """namespace = wm_press
wm_press.1 = {
 type = character_event title = wm_press.1.t desc = wm_press.1.desc theme = realm
 option = { name = wm_press.interview trigger = { prestige >= 25 } add_prestige = -25 wm_press_relationship_effect = { AMOUNT = 8 } wm_press_poll_effect = { AMOUNT = 3 } }
 option = { name = wm_press.brief trigger = { gold >= 20 } remove_short_term_gold = 20 wm_press_relationship_effect = { AMOUNT = 15 } }
 option = { name = wm_press.endorse trigger = { var:wm_press_relationship >= 40 prestige >= 50 } add_prestige = -50 wm_press_endorsement_effect = yes }
 option = { name = wm_press.close }
}
wm_press.2 = {
 type = character_event title = wm_press.2.t desc = wm_press.2.desc theme = realm
 immediate = { wm_press_ensure_effect = yes }
 option = { name = wm_press.explain add_prestige = -25 wm_trust_change_effect = { AMOUNT = 1 } wm_press_relationship_effect = { AMOUNT = 5 } }
 option = { name = wm_press.context trigger = { var:wm_press_relationship >= 30 } wm_press_relationship_effect = { AMOUNT = -30 } }
 option = { name = wm_press.deny
  random_list = {
   50 = { add_prestige = 10 }
   50 = { add_prestige = -75 wm_trust_change_effect = { AMOUNT = -2 } wm_press_poll_effect = { AMOUNT = -10 } }
  }
 }
}
""",
    )
    write(
        "common/on_action/wm_press_on_actions.txt",
        HEADER
        + """yearly_playable_pulse = { on_actions = { wm_press_yearly } }
wm_press_yearly = {
 trigger = { is_ai = no is_adult = yes has_variable = wm_party }
 effect = { random = { chance = 20 trigger_event = wm_press.2 } }
}
""",
    )
    loc = {
        "wm_press_desk_decision": "The Press Desk",
        "wm_press_desk_decision_desc": "Build relationships with editors, make your case in interviews and seek an endorsement when an election approaches.",
        "wm_press_desk_decision_tooltip": "Work with a fictional press network.",
        "wm_press_open": "Open the press desk",
        "wm_press.1.t": "Your Press Network",
        "wm_press.1.desc": "Editorial relationships: [ROOT.Char.MakeScope.Var('wm_press_relationship').GetValue|0]/100.\\n\\nBriefings and interviews build access. With a relationship of at least 40, you can seek an endorsement: it improves your party’s current national polling by two points before normalisation, then uses 25 points of goodwill. Your relationships may also help when a draft policy leaks. These are fictional political stories.",
        "wm_press.interview": "Give an interview (25 prestige; +8 relationship; modest poll boost)",
        "wm_press.brief": "Brief an editor (20 funds; +15 relationship)",
        "wm_press.endorse": "Seek an endorsement (50 prestige; uses 25 relationship)",
        "wm_press.close": "Back to Westminster",
        "wm_press.2.t": "A Draft Reaches the Press",
        "wm_press.2.desc": "An unfinished policy paper has reached a fictional political newsletter. Its editor wants a comment before publication. You can explain the draft, draw on a trusted relationship to provide context, or deny that it represents your position.",
        "wm_press.explain": "Explain the unfinished proposal openly.",
        "wm_press.context": "Give the editor context in private (uses 30 relationship).",
        "wm_press.deny": "Distance yourself from the draft (a 50% risk of a worse story).",
        "wm_committee_work_decision": "Conduct a Committee Inquiry",
        "wm_committee_work_decision_desc": "Spend time on a public-service inquiry and publish recommendations. Gain 10 party standing, 30 prestige and a point of public trust. Your recommendations strengthen the public-service caucus for a year, increasing pressure on the government to offer concessions.",
        "wm_committee_work_decision_tooltip": "Build a backbench record through scrutiny.",
        "wm_committee_confirm": "Begin the inquiry",
    }
    for lang in LANGUAGES:
        write(
            f"localization/{lang}/wm_press_l_{lang}.yml",
            f"l_{lang}:\n # English fallback pending translation.\n"
            + "\n".join(f' {k}: "{v}"' for k, v in loc.items())
            + "\n",
        )


if __name__ == "__main__":
    main()
