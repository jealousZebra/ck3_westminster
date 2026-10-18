#!/usr/bin/env python3
"""Exercise a founded party from organisation to a winning candidate in the CK3 engine."""
from pathlib import Path
OUT=Path(__file__).parent/'harness/common/scripted_effects/rf_test_effects.txt'
steps=[]
def emit(s): steps.append(s)
def check(name,condition):
    emit(f'if = {{ limit = {{ {condition} }} debug_log = "RFT_PASS {name}" }} else = {{ debug_log = "RFT_FAIL {name}" }}')
emit('set_global_variable = { name = wm_test_quiet value = yes }')
emit('''title:e_united_kingdom = { random_in_de_jure_hierarchy = {
limit = { tier = tier_county holder ?= { var:wm_party ?= title:k_party_labour is_house_head = no is_dynast = no } }
holder = { save_scope_as = wm_founder wm_party_found_in_slot_effect = { SLOT = new_1 } }
} }
scope:wm_founder = { wm_movement_target_effect = yes var:wm_party = { wm_movement_ensure_effect = yes } }
''')
check('party_founded','scope:wm_founder = { var:wm_party ?= title:k_party_new_1 }')
check('target_exists','scope:wm_founder = { exists = var:wm_movement_target }')
emit('scope:wm_founder = { wm_movement_recruit_members_effect = yes wm_movement_fundraise_effect = yes wm_movement_press_effect = yes wm_movement_build_branch_effect = yes wm_movement_recruit_candidate_effect = yes }')
check('members_grow','title:k_party_new_1 = { var:wm_movement_members = 350 var:wm_movement_donors = 10 var:wm_movement_reputation = 5 }')
check('local_branch_and_candidate','scope:wm_founder.var:wm_movement_target = { var:wm_lean_new_1 = 120 var:wm_candidate_new_1 ?= { is_alive = yes var:wm_party ?= title:k_party_new_1 } }')
emit('''scope:wm_founder = { wm_movement_recruit_candidate_effect = yes }
''')
check('duplicate_candidate_no_extra_support','scope:wm_founder.var:wm_movement_target = { var:wm_lean_new_1 = 120 }')
emit('wm_polls_init_effect = yes wm_polls_drift_all_effect = yes')
check('active_party_in_polls','global_var:wm_poll_new_1 > 0')
check('vacant_party_no_phantom_support','global_var:wm_poll_new_6 = 0')
# Use overwhelming support to prove candidate and title transfer, independent of random noise.
emit('''scope:wm_founder.var:wm_movement_target = {
 set_variable = { name = wm_lean_new_1 value = 950 }
 save_scope_as = wm_target
}
set_global_variable = { name = wm_poll_new_1 value = 500 }
scope:wm_target = { wm_election_general_seat_effect = yes }
wm_election_count_seats_effect = yes
''')
check('movement_wins_seat','scope:wm_target.holder = { var:wm_party ?= title:k_party_new_1 }')
check('selected_candidate_elected','scope:wm_target.holder = scope:wm_movement_candidate')
check('seats_counted','global_var:wm_seats_new_1 >= 2')
check('seat_total_preserved','wm_election_total_seats = 650')
emit('scope:wm_founder = { var:wm_party = { set_variable = { name = wm_movement_members value = 20000 } set_variable = { name = wm_movement_donors value = 500 } set_variable = { name = wm_movement_reputation value = 100 } } }')
check('national_support_cap','title:k_party_new_1 = { wm_movement_national_support = 120 }')
OUT.write_text('rf_test_effect = {\ndebug_log = "RFT start"\n'+'\n'.join(steps)+'\ndebug_log = "RFT done"\n}\nrf_test_effect_later = {}\n',encoding='utf-8-sig')
print(OUT)
