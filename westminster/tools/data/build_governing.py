#!/usr/bin/env python3
"""Career actions, departmental delivery and a parliamentary Brexit settlement."""
from mod_files import LANGUAGES, generated_header, write_mod_file as write

HEADER = generated_header("build_governing.py")


def main():
    effects = (
        HEADER
        + """wm_governing_ensure_effect = {
    if = { limit = { NOT = { has_global_variable = wm_gov_reserve } }
        set_global_variable = { name = wm_gov_reserve value = 60 }
        set_global_variable = { name = wm_gov_debt value = 0 }
        set_global_variable = { name = wm_gov_services value = 50 }
        set_global_variable = { name = wm_gov_economy value = 50 }
        set_global_variable = { name = wm_gov_delivery value = 0 }
        set_global_variable = { name = wm_brexit_progress value = 0 }
        set_global_variable = { name = wm_brexit_approach value = 0 }
        set_global_variable = { name = wm_brexit_phase value = 0 }
        if = { limit = { game_start_date = 2016.7.14 } set_global_variable = { name = wm_brexit_phase value = 1 } }
        if = { limit = { game_start_date >= 2021.1.1 } set_global_variable = { name = wm_brexit_phase value = 5 } }
    }
}
# Bounded global changes keep long campaigns numerically stable.
wm_governing_change_effect = {
    set_global_variable = { name = $KEY$ value = { value = global_var:$KEY$ add = $AMOUNT$ min = 0 max = 100 } }
}
wm_governing_monthly_effect = {
    wm_governing_ensure_effect = yes
    # Delivery plans are promises, not permanent free bonuses. Ministers must renew them.
    if = { limit = { global_var:wm_gov_delivery > 0 }
        wm_governing_change_effect = { KEY = wm_gov_services AMOUNT = 1 }
        wm_governing_change_effect = { KEY = wm_gov_delivery AMOUNT = -1 }
    }
    if = { limit = { global_var:wm_gov_debt > 70 }
        wm_governing_change_effect = { KEY = wm_gov_economy AMOUNT = -1 }
        wm_trust_change_effect = { AMOUNT = -0.5 }
    }
    if = { limit = { global_var:wm_gov_services >= 70 } wm_trust_change_effect = { AMOUNT = 0.3 } }
    if = { limit = { global_var:wm_gov_services < 30 } wm_trust_change_effect = { AMOUNT = -0.5 } }
    if = { limit = { global_var:wm_brexit_phase = 2 }
        wm_governing_change_effect = { KEY = wm_brexit_progress AMOUNT = 4 }
        if = { limit = { global_var:wm_brexit_progress >= 100 } set_global_variable = { name = wm_brexit_phase value = 3 } }
    }
    if = { limit = { global_var:wm_brexit_phase = 4 }
        set_global_variable = { name = wm_brexit_phase value = 5 }
        if = { limit = { global_var:wm_brexit_approach = 1 }
            wm_governing_change_effect = { KEY = wm_gov_economy AMOUNT = -3 }
            wm_trust_change_effect = { AMOUNT = 3 }
        }
        else = {
            wm_governing_change_effect = { KEY = wm_gov_economy AMOUNT = -10 }
            wm_trust_change_effect = { AMOUNT = 1 }
        }
    }
}
# Character: current constituency work follows the MP, not their successor.
wm_career_surgery_effect = {
    if = { limit = { NOT = { has_variable = wm_personal_vote } } set_variable = { name = wm_personal_vote value = 0 } }
    set_variable = { name = wm_personal_vote value = { value = var:wm_personal_vote add = 10 max = 100 } }
    add_prestige = 10
}
wm_career_project_effect = {
    wm_career_surgery_effect = yes
    set_variable = { name = wm_personal_vote value = { value = var:wm_personal_vote add = 20 max = 100 } }
    wm_trust_change_effect = { AMOUNT = 1 }
}
wm_governing_delivery_effect = {
    wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = -10 }
    wm_governing_change_effect = { KEY = wm_gov_delivery AMOUNT = 6 }
    add_prestige = 30
    # A missed review damages the minister's standing, while successful delivery builds it.
    trigger_event = { id = wm_governing.3 months = 6 }
}
wm_era_programme_passed_effect = {
    if = { limit = { has_global_variable = wm_era_programme_pending global_var:wm_commons_bill_type = 2 }
        set_global_variable = { name = wm_era_programme_passed value = global_var:wm_era_programme_pending }
        remove_global_variable = wm_era_programme_pending
        wm_governing_change_effect = { KEY = wm_gov_services AMOUNT = 10 }
        wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = -15 }
        wm_trust_change_effect = { AMOUNT = 5 }
    }
}
wm_brexit_deal_passed_effect = {
    if = { limit = { global_var:wm_commons_bill_type = 6 }
        set_global_variable = { name = wm_brexit_phase value = 4 }
        add_prestige = 100
    }
}
"""
    )
    write("common/scripted_effects/wm_governing_effects.txt", effects)
    decisions = HEADER
    for name, shown, event in [
        ("career", "is_adult = yes NOT = { has_character_flag = wm_speaker }", "1"),
        ("government", "wm_commons_is_pm_trigger = yes", "2"),
    ]:
        decisions += f"""wm_{name}_desk_decision = {{
 picture = {{ reference = "gfx/interface/illustrations/loading_screens/wm_commons.dds" }}
 decision_group_type = major sort_order = 94 ai_check_interval = 0 cooldown = {{ months = 1 }}
 desc = wm_{name}_desk_decision_desc selection_tooltip = wm_{name}_desk_decision_tooltip confirm_text = wm_desk_open
 is_shown = {{ {shown} }}
 effect = {{ wm_governing_ensure_effect = yes trigger_event = wm_governing.{event} }}
 ai_potential = {{ always = no }} ai_will_do = {{ base = 0 }}
}}
"""
    write("common/decisions/wm_governing_decisions.txt", decisions)
    loc = {
        "wm_career_desk_decision": "Your Political Career",
        "wm_career_desk_decision_desc": "Find the next step in your career: build a local reputation, bargain in Parliament or deliver as a minister.",
        "wm_career_desk_decision_tooltip": "Review the opportunities available in your current role.",
        "wm_government_desk_decision": "The Government Programme",
        "wm_government_desk_decision_desc": "Allocate limited fiscal room, manage public services and debt, and steer the country through its political challenges.",
        "wm_government_desk_decision_tooltip": "Review public finances, delivery and the Brexit settlement.",
        "wm_desk_open": "Open the desk",
        "wm_governing.1.t": "Your Political Career",
        "wm_career.goal_pm": "#bold Next objective: govern successfully.#! Use the Government Programme to manage fiscal room, deliver public services and build support in Parliament.",
        "wm_career.goal_leader": "#bold Next objective: win a stronger parliamentary party.#! Recruit candidates and concentrate local branches in target seats. Keep enough standing to defend your leadership.",
        "wm_career.goal_minister": "#bold Next objective: build a record of delivery.#! A funded departmental plan faces a review in six months; successful delivery builds the standing needed for promotion.",
        "wm_career.goal_mp": "#bold Next objective: become indispensable.#! Strengthen your personal vote with constituency work, bargain for public-service concessions and build your standing for office.",
        "wm_career.goal_hopeful": "#bold Next objective: win selection and enter Parliament.#! Join a party, take political work to build standing, then apply for an open constituency selection.",
        "wm_governing.1.desc": "#bold Build your next opportunity#!\\nLocal work gives an MP a personal vote, worth up to ten percentage points while defending their seat. Party leaders can build an organisation and recruit candidates through Build Your Movement. Unlanded members should seek party work and selection.\\n\\nBackbenchers can demand public-service concessions before the next division. Ministers can spend ten points of national fiscal room on a six-month delivery plan. A review rewards successful delivery or damages your standing. Each action is available only when your role and resources allow it.",
        "wm_career.surgery": "Hold a constituency surgery (10 funds; +1% personal vote)",
        "wm_career.project": "Organise a local project (50 funds; +3% personal vote)",
        "wm_career.amendment": "Organise a public-services caucus (75 prestige)",
        "wm_career.delivery": "Publish a departmental delivery plan (10 fiscal room)",
        "wm_career.interview": "Give an interview about your work (25 prestige)",
        "wm_governing.close": "Return to Westminster",
        "wm_governing.2.t": "The Government Programme",
        "wm_governing.2.desc": "Fiscal room: [GetGlobalVariable('wm_gov_reserve').GetValue|0]/100\\nDebt pressure: [GetGlobalVariable('wm_gov_debt').GetValue|0]/100\\nPublic services: [GetGlobalVariable('wm_gov_services').GetValue|0]/100\\nEconomic confidence: [GetGlobalVariable('wm_gov_economy').GetValue|0]/100\\n\\nBrexit: [ROOT.Char.Custom('wm_brexit_status')]. Negotiation progress: [GetGlobalVariable('wm_brexit_progress').GetValue|0]/100.\\n\\nPublic-service investment uses fiscal room; borrowing restores it at the cost of debt pressure. High debt harms economic confidence and trust each month. The withdrawal settlement must pass an ordinary Commons division; defeat leaves negotiations open.",
        "wm_era.nhs": "Introduce a national health service programme (Public Services Bill)",
        "wm_era.new_labour": "Introduce the public-service investment programme (Public Services Bill)",
        "wm_era.coalition": "Put the coalition public-service settlement to Parliament",
        "wm_government.invest": "Invest in public services (20 fiscal room; +8 services)",
        "wm_government.borrow": "Authorise borrowing (+20 fiscal room; +15 debt pressure)",
        "wm_government.repay": "Reduce debt (20 fiscal room; -15 debt pressure)",
        "wm_government.cuts": "Reduce departmental budgets (+15 fiscal room; -8 services)",
        "wm_government.concede": "Accept the public-services caucus amendment (10 fiscal room)",
        "wm_brexit.soft": "Seek close economic alignment (12 fiscal room; faster negotiations)",
        "wm_brexit.hard": "Prioritise regulatory independence (8 fiscal room; slower negotiations)",
        "wm_brexit.negotiate": "Fund an additional negotiating round (8 fiscal room; +20 progress)",
        "wm_brexit.vote": "Bring the withdrawal settlement before Parliament",
        "wm_governing.3.t": "The Departmental Review",
        "wm_governing.3.desc": "Six months after your delivery plan, the department faces scrutiny. Strong public services build your standing; poor delivery means difficult questions.",
        "wm_review.success": "Delivery has strengthened our record.",
        "wm_review.failure": "We must answer for the shortfall.",
        "wm_brexit_bill_name": "Withdrawal Settlement Bill",
        "wm_brexit.phase_0": "No withdrawal mandate",
        "wm_brexit.phase_1": "Choose a withdrawal strategy",
        "wm_brexit.phase_2": "Negotiations under way",
        "wm_brexit.phase_3": "Settlement ready for Parliament",
        "wm_brexit.phase_4": "Preparing the transition",
        "wm_brexit.phase_5": "Withdrawal completed",
        "wm_commons_bill_6_name": "Withdrawal Settlement Bill",
        "wm_commons_bill_6_desc": "The government asks Parliament to approve the negotiated withdrawal settlement. A defeat leaves the settlement open for another attempt; passage begins the transition.",
    }

    def option(name, trigger, effect):
        return (
            f"option = {{ name = {name} "
            + (f"trigger = {{ {trigger} }} " if trigger else "")
            + effect
            + " }\n"
        )

    events = (
        HEADER
        + """namespace = wm_governing
wm_governing.1 = {
 type = character_event title = wm_governing.1.t
 desc = {
  first_valid = {
   triggered_desc = { trigger = { wm_commons_is_pm_trigger = yes } desc = wm_career.goal_pm }
   triggered_desc = { trigger = { wm_commons_is_party_leader_trigger = yes } desc = wm_career.goal_leader }
   triggered_desc = { trigger = { is_councillor = yes } desc = wm_career.goal_minister }
   triggered_desc = { trigger = { wm_is_mp_trigger = yes } desc = wm_career.goal_mp }
   desc = wm_career.goal_hopeful
  }
  desc = wm_governing.1.desc
 }
 theme = realm
 left_portrait = { character = root animation = personality_rational }
"""
    )
    events += option(
        "wm_career.surgery",
        "wm_is_mp_trigger = yes gold >= 10",
        "remove_short_term_gold = 10 wm_career_surgery_effect = yes",
    )
    events += option(
        "wm_career.project",
        "wm_is_mp_trigger = yes gold >= 50",
        "remove_short_term_gold = 50 wm_career_project_effect = yes",
    )
    events += option(
        "wm_career.amendment",
        "wm_is_mp_trigger = yes prestige >= 75 NOT = { wm_commons_is_party_leader_trigger = yes }",
        "add_prestige = -75 set_variable = { name = wm_public_services_caucus value = yes years = 1 }",
    )
    events += option(
        "wm_career.delivery",
        "is_councillor = yes global_var:wm_gov_reserve >= 10 NOT = { has_character_flag = wm_delivery_pending }",
        "add_character_flag = { flag = wm_delivery_pending months = 6 } wm_governing_delivery_effect = yes",
    )
    events += option(
        "wm_career.interview",
        "prestige >= 25",
        "add_prestige = -25 wm_trust_change_effect = { AMOUNT = 1 } if = { limit = { has_variable = wm_party } var:wm_party = { wm_movement_ensure_effect = yes set_variable = { name = wm_movement_reputation value = { value = var:wm_movement_reputation add = 2 max = 100 } } } }",
    )
    events += option("wm_governing.close", "", "") + "}\n"
    events += "wm_governing.2 = { type = character_event title = wm_governing.2.t desc = wm_governing.2.desc theme = realm\n"
    for name, trigger, effect in [
        (
            "wm_government.invest",
            "global_var:wm_gov_reserve >= 20",
            "wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = -20 } wm_governing_change_effect = { KEY = wm_gov_services AMOUNT = 8 }",
        ),
        (
            "wm_government.borrow",
            "global_var:wm_gov_debt <= 85 global_var:wm_gov_reserve <= 80",
            "wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = 20 } wm_governing_change_effect = { KEY = wm_gov_debt AMOUNT = 15 }",
        ),
        (
            "wm_government.repay",
            "global_var:wm_gov_reserve >= 20 global_var:wm_gov_debt >= 15",
            "wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = -20 } wm_governing_change_effect = { KEY = wm_gov_debt AMOUNT = -15 }",
        ),
        (
            "wm_government.cuts",
            "global_var:wm_gov_services >= 8 global_var:wm_gov_reserve <= 85",
            "wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = 15 } wm_governing_change_effect = { KEY = wm_gov_services AMOUNT = -8 } wm_trust_change_effect = { AMOUNT = -2 }",
        ),
        (
            "wm_government.concede",
            "global_var:wm_gov_reserve >= 10",
            "wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = -10 } wm_governing_change_effect = { KEY = wm_gov_services AMOUNT = 3 } set_global_variable = { name = wm_services_concession value = yes months = 6 }",
        ),
        (
            "wm_brexit.soft",
            "global_var:wm_brexit_phase = 1 global_var:wm_gov_reserve >= 12",
            "wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = -12 } set_global_variable = { name = wm_brexit_approach value = 1 } set_global_variable = { name = wm_brexit_progress value = 35 } set_global_variable = { name = wm_brexit_phase value = 2 }",
        ),
        (
            "wm_brexit.hard",
            "global_var:wm_brexit_phase = 1 global_var:wm_gov_reserve >= 8",
            "wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = -8 } set_global_variable = { name = wm_brexit_approach value = 2 } set_global_variable = { name = wm_brexit_progress value = 10 } set_global_variable = { name = wm_brexit_phase value = 2 }",
        ),
        (
            "wm_brexit.negotiate",
            "global_var:wm_brexit_phase = 2 global_var:wm_gov_reserve >= 8",
            "wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = -8 } wm_governing_change_effect = { KEY = wm_brexit_progress AMOUNT = 20 }",
        ),
        (
            "wm_brexit.vote",
            "global_var:wm_brexit_phase = 3 wm_commons_house_free_trigger = yes",
            "wm_commons_introduce_bill_effect = { TYPE = 6 } set_global_variable = { name = wm_commons_bill_lean value = 0 } set_global_variable = { name = wm_commons_bill_controversy value = 35 } trigger_event = wm_commons.2",
        ),
    ]:
        events += option(name, trigger, effect)
    for year, key in [(1945, "nhs"), (1997, "new_labour"), (2010, "coalition")]:
        from build_eras import ERAS

        events += option(
            "wm_era." + key,
            f'game_start_date = {ERAS[year]["date"]} wm_commons_house_free_trigger = yes global_var:wm_gov_reserve >= 15 NOT = {{ has_global_variable = wm_era_programme_passed }}',
            f"set_global_variable = {{ name = wm_era_programme_pending value = {year} }} wm_commons_introduce_bill_effect = {{ TYPE = 2 }} trigger_event = wm_commons.2",
        )
    events += option("wm_governing.close", "", "") + "}\n"
    events += """wm_governing.3 = {
 type = character_event title = wm_governing.3.t desc = wm_governing.3.desc theme = realm
 option = { name = wm_review.success trigger = { global_var:wm_gov_services >= 55 }
  add_prestige = 75 if = { limit = { NOT = { has_variable = wm_standing } } set_variable = { name = wm_standing value = 0 } } change_variable = { name = wm_standing add = 10 }
 }
 option = { name = wm_review.failure trigger = { global_var:wm_gov_services < 55 } add_prestige = -50 add_stress = 15 }
}
"""
    write("events/wm_governing_events.txt", events)
    write(
        "common/on_action/wm_governing_on_actions.txt",
        HEADER
        + """on_game_start_after_lobby = { on_actions = { wm_governing_start } }
wm_governing_start = { effect = { wm_governing_ensure_effect = yes } }
""",
    )
    write(
        "common/customizable_localization/wm_governing_loc.txt",
        HEADER
        + "wm_brexit_status = { type = character\n"
        + "".join(
            "text = { trigger = { global_var:wm_brexit_phase = %d } localization_key = wm_brexit.phase_%d }\n"
            % (i, i)
            for i in range(6)
        )
        + "}\n",
    )
    for lang in LANGUAGES:
        write(
            f"localization/{lang}/wm_governing_l_{lang}.yml",
            f"l_{lang}:\n # English fallback pending translation.\n"
            + "\n".join(f' {k}: "{v}"' for k, v in loc.items())
            + "\n",
        )


if __name__ == "__main__":
    main()
