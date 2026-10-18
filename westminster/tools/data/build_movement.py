#!/usr/bin/env python3
"""Build the movement's playable organisation and election integration.

Local organisation is party-specific and capped at 45 percentage points. National
support is capped at 12 points; concentrating on constituencies matters more than
repeated national publicity. All state belongs to the party, surviving succession.
"""
from mod_files import LANGUAGES, generated_header, write_mod_file as write

HEADER = generated_header("build_movement.py")


def main():
    effects = [
        HEADER,
        """# Party title: initialize old saves without resetting established organisations.
wm_movement_ensure_effect = {
    if = { limit = { NOT = { has_variable = wm_movement_members } }
        set_variable = { name = wm_movement_members value = 100 }
        set_variable = { name = wm_movement_donors value = 0 }
        set_variable = { name = wm_movement_reputation value = 0 }
    }
}
# Character: choose an opposition-held constituency; the target stays until deliberately changed.
wm_movement_target_effect = {
    save_scope_as = wm_organiser
    title:e_united_kingdom = {
        random_in_de_jure_hierarchy = {
            limit = { tier = tier_county exists = holder
                NOT = { holder = { var:wm_party ?= scope:wm_organiser.var:wm_party } }
            }
            save_scope_as = wm_movement_seat
            scope:wm_organiser = { set_variable = { name = wm_movement_target value = scope:wm_movement_seat } }
        }
    }
}
wm_movement_recruit_members_effect = {
    var:wm_party = {
        wm_movement_ensure_effect = yes
        set_variable = { name = wm_movement_members value = { value = var:wm_movement_members add = 250 max = 20000 } }
    }
}
wm_movement_fundraise_effect = {
    var:wm_party = {
        wm_movement_ensure_effect = yes
        set_variable = { name = wm_movement_donors value = { value = var:wm_movement_donors add = 10 max = 500 } }
    }
    add_gold = 20
}
wm_movement_press_effect = {
    var:wm_party = {
        wm_movement_ensure_effect = yes
        set_variable = { name = wm_movement_reputation value = { value = var:wm_movement_reputation add = 5 max = 100 } }
    }
    add_prestige = 25
}
""",
    ]
    branch_calls = []
    candidate_calls = []
    for i in range(1, 7):
        k = f"new_{i}"
        branch_calls.append(
            f"if = {{ limit = {{ var:wm_party ?= title:k_party_{k} }} wm_movement_build_branch_party_effect = {{ P = {k} }} }}"
        )
        candidate_calls.append(
            f"if = {{ limit = {{ var:wm_party ?= title:k_party_{k} }} wm_movement_recruit_candidate_party_effect = {{ P = {k} }} }}"
        )
    effects += [
        "wm_movement_build_branch_effect = {\n" + "\n".join(branch_calls) + "\n}",
        "wm_movement_recruit_candidate_effect = {\n"
        + "\n".join(candidate_calls)
        + "\n}",
        """# A branch gives 6 percentage points locally, with diminishing returns at the cap.
wm_movement_build_branch_party_effect = {
    var:wm_movement_target = {
        if = { limit = { NOT = { has_variable = wm_lean_$P$ } } set_variable = { name = wm_lean_$P$ value = 0 } }
        set_variable = { name = wm_lean_$P$ value = { value = var:wm_lean_$P$ add = 60 max = 450 } }
    }
}
wm_movement_recruit_candidate_party_effect = {
    save_scope_as = wm_organiser
    var:wm_movement_target = { save_scope_as = wm_movement_seat }
    if = {
        limit = { NOT = { scope:wm_movement_seat.var:wm_candidate_$P$ ?= { wm_career_can_take_seat_trigger = { PARTY = k_party_$P$ } } } }
        create_character = {
            age = { 25 60 }
            gender_female_chance = 50
            culture = scope:wm_movement_seat.culture
            faith = scope:wm_organiser.faith
            dynasty = generate
            location = scope:wm_movement_seat.title_province
            save_scope_as = wm_movement_candidate
        }
        scope:wm_movement_candidate = {
            set_variable = { name = wm_party value = scope:wm_organiser.var:wm_party }
            set_variable = { name = wm_career_hopeful value = yes }
            set_variable = { name = wm_career_selected_seat value = scope:wm_movement_seat }
            wm_party_sync_house_effect = yes
        }
        scope:wm_movement_seat = { set_variable = { name = wm_candidate_$P$ value = scope:wm_movement_candidate } }
        add_courtier = scope:wm_movement_candidate
        wm_movement_build_branch_party_effect = { P = $P$ }
    }
}
""",
    ]
    write("common/scripted_effects/wm_movement_effects.txt", "\n".join(effects))
    write(
        "common/script_values/wm_movement_values.txt",
        HEADER
        + """# Party title; national vote share in tenths of a percent.
wm_movement_national_support = {
    value = 1
    if = { limit = { has_variable = wm_movement_members } add = { value = var:wm_movement_members divide = 250 } }
    if = { limit = { has_variable = wm_movement_donors } add = { value = var:wm_movement_donors divide = 10 } }
    if = { limit = { has_variable = wm_movement_reputation } add = { value = var:wm_movement_reputation divide = 2 } }
    max = 120
}
""",
    )
    loc = {
        "wm_movement_decision": "Build Your Movement",
        "wm_movement_decision_desc": "Turn your party into an organisation that can win seats. Recruit members, find donors and establish local branches before polling day.",
        "wm_movement_decision_tooltip": "Review your organisation and choose the next step.",
        "wm_movement_decision_confirm": "Open the campaign desk",
        "wm_movement.1.t": "Build Your Movement",
        "wm_movement.1.desc": "Members: [ROOT.Char.MakeScope.Var('wm_party').Title.MakeScope.Var('wm_movement_members').GetValue|0]\\nDonors: [ROOT.Char.MakeScope.Var('wm_party').Title.MakeScope.Var('wm_movement_donors').GetValue|0]\\nPublic profile: [ROOT.Char.MakeScope.Var('wm_party').Title.MakeScope.Var('wm_movement_reputation').GetValue|0]/100\\n\\nTarget seat: [ROOT.Char.MakeScope.Var('wm_movement_target').Title.GetNameNoTier]\\n\\n#bold Your next steps#!\\nBuild a branch and recruit a candidate in your target seat. Branches add six percentage points of local support, up to 45. Your selected candidate takes the seat if the party wins it. Switch targets to spread your organisation. Members, donors and publicity raise your national poll anchor, up to 12%.",
        "wm_movement.members": "Hold a membership drive (50 prestige; +250 members)",
        "wm_movement.donors": "Meet potential donors (25 prestige; +10 donors and 20 funds)",
        "wm_movement.branch": "Build the target-seat branch (20 funds; +6% local support)",
        "wm_movement.candidate": "Recruit a candidate (30 funds; +6% local support)",
        "wm_movement.press": "Give a national interview (40 prestige; +5 public profile)",
        "wm_movement.target": "Look for another target seat",
        "wm_movement.close": "Back to Westminster",
    }
    shown = (
        "is_adult = yes is_imprisoned = no var:wm_party.holder ?= this OR = { "
        + " ".join(f"var:wm_party ?= title:k_party_new_{i}" for i in range(1, 7))
        + " }"
    )
    write(
        "common/decisions/wm_movement_decisions.txt",
        HEADER
        + f"""wm_movement_decision = {{
    picture = {{ reference = "gfx/interface/illustrations/loading_screens/wm_commons.dds" }}
    decision_group_type = major
    sort_order = 95
    ai_check_interval = 0
    cooldown = {{ months = 1 }}
    desc = wm_movement_decision_desc
    selection_tooltip = wm_movement_decision_tooltip
    confirm_text = wm_movement_decision_confirm
    is_shown = {{ {shown} }}
    effect = {{
        var:wm_party = {{ wm_movement_ensure_effect = yes }}
        if = {{ limit = {{ NOT = {{ exists = var:wm_movement_target }} }} wm_movement_target_effect = yes }}
        trigger_event = wm_movement.1
    }}
    ai_potential = {{ always = no }}
    ai_will_do = {{ base = 0 }}
}}
""",
    )
    options = [
        (
            "members",
            "prestige >= 50",
            "add_prestige = -50 wm_movement_recruit_members_effect = yes",
        ),
        (
            "donors",
            "prestige >= 25",
            "add_prestige = -25 wm_movement_fundraise_effect = yes",
        ),
        (
            "branch",
            "gold >= 20 exists = var:wm_movement_target",
            "remove_short_term_gold = 20 wm_movement_build_branch_effect = yes",
        ),
        (
            "candidate",
            "gold >= 30 exists = var:wm_movement_target",
            "remove_short_term_gold = 30 wm_movement_recruit_candidate_effect = yes",
        ),
        (
            "press",
            "prestige >= 40",
            "add_prestige = -40 wm_movement_press_effect = yes",
        ),
        ("target", "", "wm_movement_target_effect = yes"),
        ("close", "", ""),
    ]
    event = (
        HEADER
        + """namespace = wm_movement
wm_movement.1 = {
    type = character_event
    title = wm_movement.1.t
    desc = wm_movement.1.desc
    theme = realm
    left_portrait = { character = root animation = personality_rational }
"""
    )
    for key, trigger, effect in options:
        event += (
            f"    option = {{ name = wm_movement.{key} "
            + (f"trigger = {{ {trigger} }} " if trigger else "")
            + effect
            + " }\n"
        )
    write("events/wm_movement_events.txt", event + "}\n")
    loc.update(
        {
            "wm_invite_defection_interaction": "Invite to Cross the Floor",
            "wm_invite_defection_interaction_desc": "Invite a disillusioned MP into your party. They must like you (40 opinion), dislike their current leader (-20 opinion), and be free to accept. Costs 250 prestige; once a year for each target.",
        }
    )
    write(
        "common/character_interactions/wm_movement_interactions.txt",
        HEADER
        + """wm_invite_defection_interaction = {
 category = interaction_category_friendly common_interaction = no interface_priority = 60
 desc = wm_invite_defection_interaction_desc
 is_shown = {
  scope:actor = { var:wm_party.holder ?= this }
  scope:recipient = {
   wm_is_mp_trigger = yes NOT = { has_character_flag = wm_speaker }
   exists = var:wm_party.holder NOT = { var:wm_party.holder ?= this }
   NOT = { var:wm_party ?= scope:actor.var:wm_party }
  }
 }
 is_valid_showing_failures_only = {
  scope:recipient = {
   is_imprisoned = no
   opinion = { target = scope:actor value >= 40 }
   opinion = { target = var:wm_party.holder value <= -20 }
  }
 }
 cooldown = { years = 1 }
 cost = { prestige = 250 }
 auto_accept = { scope:recipient = { is_ai = yes } }
 on_accept = { scope:recipient = { wm_party_join_effect = { PARTY = scope:actor.var:wm_party } } }
 ai_frequency = 0 ai_will_do = { base = 0 }
}
""",
    )
    for language in LANGUAGES:
        write(
            f"localization/{language}/wm_movement_l_{language}.yml",
            f"l_{language}:\n # English fallback pending translation.\n"
            + "\n".join(f' {k}: "{v}"' for k, v in loc.items())
            + "\n",
        )


if __name__ == "__main__":
    main()
