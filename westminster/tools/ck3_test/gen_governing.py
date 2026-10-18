#!/usr/bin/env python3
"""Engine tests for budgets, delivery, personal votes and parliamentary Brexit gates."""
from pathlib import Path
OUT=Path(__file__).parent/'harness/common/scripted_effects/rf_test_effects.txt'
steps=[]
def emit(s):steps.append(s)
def check(n,c):emit(f'if = {{ limit = {{ {c} }} debug_log = "RFT_PASS {n}" }} else = {{ debug_log = "RFT_FAIL {n}" }}')
emit('set_global_variable = { name = wm_test_quiet value = yes } remove_global_variable = wm_gov_reserve wm_governing_ensure_effect = yes')
check('budget_initialises','global_var:wm_gov_reserve = 60 global_var:wm_gov_debt = 0 global_var:wm_gov_services = 50')
emit('title:e_united_kingdom.holder = { wm_governing_delivery_effect = yes }')
check('plan_costs_fiscal_room','global_var:wm_gov_reserve = 50 global_var:wm_gov_delivery = 6')
emit('wm_governing_monthly_effect = yes')
check('delivery_improves_services','global_var:wm_gov_services = 51 global_var:wm_gov_delivery = 5')
emit('wm_governing_change_effect = { KEY = wm_gov_services AMOUNT = 1000 } wm_governing_change_effect = { KEY = wm_gov_reserve AMOUNT = -1000 }')
check('budget_bounds','global_var:wm_gov_services = 100 global_var:wm_gov_reserve = 0')
emit('set_global_variable = { name = wm_gov_debt value = 90 } wm_governing_monthly_effect = yes')
check('debt_has_consequences','global_var:wm_gov_economy = 49')
emit('title:e_united_kingdom.holder = { wm_career_surgery_effect = yes wm_career_project_effect = yes }')
check('constituency_work_builds_vote','title:e_united_kingdom.holder = { var:wm_personal_vote = 40 }')
emit('set_global_variable = { name = wm_brexit_phase value = 2 } set_global_variable = { name = wm_brexit_progress value = 96 } set_global_variable = { name = wm_brexit_approach value = 1 } wm_governing_monthly_effect = yes')
check('negotiations_reach_parliament','global_var:wm_brexit_phase = 3 global_var:wm_brexit_progress = 100')
emit('title:e_united_kingdom.holder = { wm_commons_introduce_bill_effect = { TYPE = 6 } }')
check('withdrawal_is_ordinary_bill','global_var:wm_commons_bill_type = 6 global_var:wm_commons_opp_base = 1 global_var:wm_commons_bill_controversy = 35')
emit('set_global_variable = { name = wm_commons_result value = 2 } set_global_variable = { name = wm_commons_margin value = -10 } title:e_united_kingdom.holder = { wm_commons_apply_result_effect = yes }')
check('defeat_blocks_withdrawal','global_var:wm_brexit_phase = 3')
emit('set_global_variable = { name = wm_commons_result value = 1 } title:e_united_kingdom.holder = { wm_commons_apply_result_effect = yes }')
check('passage_opens_transition','global_var:wm_brexit_phase = 4')
check('withdrawal_not_emergency_powers','title:e_united_kingdom.holder = { NOT = { has_character_modifier = wm_commons_emergency_powers_modifier } }')
emit('wm_governing_monthly_effect = yes')
check('transition_completes','global_var:wm_brexit_phase = 5')
emit('''title:e_united_kingdom.holder = { trigger_event = wm_governing.2 }
''')
OUT.write_text('rf_test_effect = {\ndebug_log = "RFT start"\n'+'\n'.join(steps)+'\ndebug_log = "RFT done"\n}\nrf_test_effect_later = {}\n',encoding='utf-8-sig')
print(OUT)
