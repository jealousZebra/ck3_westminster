#!/usr/bin/env python3
"""Compose the movement/governing suites and exercise press/committee effects."""
import runpy
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/'harness/common/scripted_effects/rf_test_effects.txt'
parts=[]
for suite in ['gen_movement.py','gen_governing.py']:
 runpy.run_path(str(HERE/suite),run_name='__main__')
 text=OUT.read_text(encoding='utf-8-sig')
 body=text.split('rf_test_effect = {',1)[1].split('\nrf_test_effect_later',1)[0].rstrip()[:-1]
 parts.append(body.replace('debug_log = "RFT start"','').replace('debug_log = "RFT done"',''))
extra=[]
def emit(s):extra.append(s)
def check(n,c):emit(f'if = {{ limit = {{ {c} }} debug_log = "RFT_PASS {n}" }} else = {{ debug_log = "RFT_FAIL {n}" }}')
emit('title:e_united_kingdom.holder = { wm_press_ensure_effect = yes }')
check('press_network_initialises','title:e_united_kingdom.holder = { var:wm_press_relationship = 0 }')
emit('title:e_united_kingdom.holder = { wm_press_relationship_effect = { AMOUNT = 1000 } }')
check('press_relationship_capped','title:e_united_kingdom.holder = { var:wm_press_relationship = 100 }')
emit('wm_polls_normalise_effect = yes set_global_variable = { name = wm_test_press_before value = global_var:wm_poll_lab } title:e_united_kingdom.holder = { wm_press_endorsement_effect = yes }')
check('endorsement_uses_goodwill','title:e_united_kingdom.holder = { var:wm_press_relationship = 75 }')
check('endorsement_moves_real_polls','global_var:wm_poll_lab > global_var:wm_test_press_before')
emit('scope:wm_founder = { set_variable = { name = wm_standing value = 20 } wm_committee_report_effect = yes }')
check('committee_work_builds_standing','scope:wm_founder = { var:wm_standing = 30 has_variable = wm_public_services_caucus }')
emit('title:e_united_kingdom.holder = { trigger_event = wm_press.1 var:wm_party = { wm_movement_ensure_effect = yes } wm_movement_target_effect = yes trigger_event = wm_movement.1 }')
# Test the historical programme hook independently of the calendar-selected UI option.
emit('set_global_variable = { name = wm_era_programme_pending value = 1945 } set_global_variable = { name = wm_commons_bill_type value = 2 } title:e_united_kingdom.holder = { wm_era_programme_passed_effect = yes }')
check('historical_programme_enacted','global_var:wm_era_programme_passed = 1945 NOT = { has_global_variable = wm_era_programme_pending }')
OUT.write_text('rf_test_effect = {\ndebug_log = "RFT start"\n'+'\n'.join(parts+extra)+'\ndebug_log = "RFT done"\n}\nrf_test_effect_later = {}\n',encoding='utf-8-sig')
print('Expansion suite:',OUT)
