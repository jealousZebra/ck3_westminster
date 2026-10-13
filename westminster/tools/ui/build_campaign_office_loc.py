#!/usr/bin/env python3
"""Localization half of build_campaign_office.py: the adventurer camp in political words.

    .venv/bin/python westminster/tools/ui/build_campaign_office_loc.py      (also run by build_campaign_office.py)

Writes westminster/localization/english/replace/wm_campaign_office_l_english.yml:
  1. HAND: hand-written values (the concepts, the political focuses, the office facilities and staff, the jobs board).
  2. AUTO: every other camp-related vanilla key (camp buildings, camp officers, domicile and contract window strings,
     camp purposes, the camp concepts) gets build_terms.py's substitution table and then this file's CAMP_TERMS
     (camp -> campaign office, provisions -> campaign funds, followers -> team members ...). Only plain text changes:
     [data], $KEYS$, #formats and @icons! are kept exactly (checked per key).
Keys any other mod localization file defines (except build_terms.py's wm_terms_* output, which skips ours) are left
alone. Rerun build_terms.py after this when keys move here, so the two never define the same key.
"""
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_terms as bt  # noqa: E402  (tokenize, transform, parse_yml, load_vanilla, mod_keys)

MOD = HERE.parent.parent / "westminster"
OUT = MOD / "localization" / "english" / "replace" / "wm_campaign_office_l_english.yml"

# ------------------------------------------------------------------------------------------------ terms

CAMP_TERMS = [
    # protected (build_terms' words for religion and others that contain "camp")
    ("Political Camps", "Political Camps"), ("Political Camp", "Political Camp"),
    ("political camps", "political camps"), ("political camp", "political camp"),
    ("Campaign", "Campaign"), ("campaign", "campaign"), ("Campaigns", "Campaigns"), ("campaigns", "campaigns"),
    ("Vassal Contract", "Vassal Contract"), ("vassal contract", "vassal contract"),
    ("Backbencher Contract", "Backbencher Contract"),
    # the adventurer
    ("Landless Adventurers", "Campaigners"), ("Landless Adventurer", "Campaigner"),
    ("landless adventurers", "campaigners"), ("landless adventurer", "campaigner"),
    ("Adventurer Camps", "Campaign Offices"), ("Adventurer Camp", "Campaign Office"),
    ("Adventurers", "Campaigners"), ("Adventurer", "Campaigner"), ("adventurers", "campaigners"),
    ("adventurer", "campaigner"), ("Adventuring", "Campaigning"), ("adventuring", "campaigning"),
    # the camp
    ("Camp Purposes", "Political Focuses"), ("Camp Purpose", "Political Focus"),
    ("camp purposes", "political focuses"), ("camp purpose", "political focus"),
    ("Camp Temperament", "Team Morale"), ("camp temperament", "team morale"),
    ("Camp Officers", "Senior Staff"), ("Camp Officer", "Senior Staffer"),
    ("camp officers", "senior staff"), ("camp officer", "senior staffer"),
    ("Camp Upgrades", "Office Facilities"), ("Camp Upgrade", "Office Facility"),
    ("Camp Buildings", "Office Facilities"), ("Camp Building", "Office Facility"),
    ("camp upgrades", "office facilities"), ("camp upgrade", "office facility"),
    ("camp buildings", "office facilities"), ("camp building", "office facility"),
    ("Camps", "Campaign Offices"), ("Camp", "Campaign Office"), ("camps", "campaign offices"),
    ("camp", "campaign office"), ("Encampment", "Campaign Office"), ("encampment", "campaign office"),
    ("Followers", "Team Members"), ("Follower", "Team Member"), ("followers", "team members"),
    ("follower", "team member"),
    ("Officers", "Staffers"), ("Officer", "Staffer"), ("officers", "staffers"), ("officer", "staffer"),
    ("Provisions", "Campaign Funds"), ("provisions", "campaign funds"), ("Provision", "Campaign Fund"),
    ("Mutinous", "Demoralised"), ("Steadfast", "Fired-Up"),
    ("Tents", "Rooms"), ("Tent", "Room"), ("tents", "rooms"), ("tent", "room"),
    ("Pavilion", "Campaign HQ"), ("pavilion", "campaign HQ"),
    ("Domiciles", "Bases"), ("Domicile", "Base"), ("domiciles", "bases"), ("domicile", "base"),
    ("Task Contracts", "Jobs"), ("Task Contract", "Job"), ("task contracts", "jobs"), ("task contract", "job"),
    ("Contractors", "Employers"), ("Contractor", "Employer"), ("contractors", "employers"), ("contractor", "employer"),
    ("Contracts", "Jobs"), ("Contract", "Job"), ("contracts", "jobs"), ("contract", "job"),
    ("Sellswords", "Hired Guns"), ("sellswords", "hired guns"), ("Swords-for-Hire", "Campaign Consultants"),
    ("on the road", "on the campaign trail"), ("the open road", "the campaign trail"),
    ("coin", "money"),
]
_camp = dict(CAMP_TERMS)
_pattern = re.compile(r"(?<![A-Za-z0-9_\-])(" + "|".join(re.escape(k) for k in sorted(_camp, key=len, reverse=True))
                      + r")(?![A-Za-z0-9_\-])")


def camp_sub(text):
    out, pos = [], 0
    for m in _pattern.finditer(text):
        old, new = m.group(1), _camp[m.group(1)]
        before = text[pos:m.start()]
        art = re.search(r"(?:^|(?<=[\s(]))([Aa]n?) $", before)
        if art and new != old and bt._vowel_sound(new) != bt._vowel_sound(old):
            a = art.group(1)
            before = before[:art.start(1)] + ((a[0] + "n") if bt._vowel_sound(new) else a[0]) + " "
        out += [before, new]
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def transform(value):
    v = bt.transform(value, Counter())
    return "".join(t if is_m else camp_sub(t) for is_m, t in bt.tokenize(v))


# ------------------------------------------------------------------------------------------------ hand-written

FOCUS = {
    # vanilla purpose: (name, job line, focus bonus line, flavour)
    "wanderers": ("Party Activist",
                  "Offered every kind of job, none more than another",
                  "May change to any other $camp_purpose$ without spending [prestige|E]",
                  "Leaflets in one pocket, a membership card in the other, and no idea yet where it all leads."),
    "explorers": ("Grassroots Organiser",
                  "Offered more canvassing, phone bank and get-out-the-vote jobs",
                  "Travels faster between doorsteps",
                  "Every street has a door that hasn't been knocked on yet."),
    "scholars": ("Think-Tank Wonk",
                 "Offered more policy papers, speechwriting and costing jobs",
                 "Learns faster from every job",
                 "There is a footnote for everything, and a chart for most of it."),
    "brigands": ("Media Pundit",
                 "Offered more media rounds and opposition research",
                 "Every job done well earns extra [prestige|E]: more airtime",
                 "Available for comment, any channel, any hour, any subject."),
    "mercenaries": ("Campaign Consultant",
                    "Offered more fundraising, phone bank and costing jobs",
                    "Every job done well earns extra [gold|E]: the invoice",
                    "Strategy, data and a day rate. Results not guaranteed; invoices are."),
    "legitimists": ("Party Fixer",
                    "Offered more of the party's inside jobs: speechwriting and research",
                    "Every job done well earns extra Party Standing",
                    "Somebody has to count the votes before the vote, and know who owes whom."),
}

BUILDINGS = {
    # name, description (the "Requires" line is added for upgrades)
    "camp_main_01": ("Campaign HQ", "The office itself: a rented room, then a shopfront on the high street, then a proper headquarters with a phone for every desk."),
    "supply_tent_01": ("Print Room", "Leaflets, posters, envelopes and the one printer everybody swears at. The campaign runs on paper."),
    "supply_tent_sutler": ("Bulk-Buy Suppliers", "A wholesaler who does a good price on A5 if you ask nicely and pay on time."),
    "supply_tent_mender": ("Second-Hand Kit", "Donated laptops and refurbished phones: not pretty, but they work."),
    "supply_tent_smithy": ("In-House Printer", "A proper press in the back room: no more waiting a week for the printers."),
    "supply_tent_arsenal": ("Leaflet Stockpile", "Boxes of every leaflet the campaign has ever designed, ready for any street at an hour's notice."),
    "supply_tent_reserve_provisions": ("Reserve Fund", "Money put aside for the last fortnight, when every pound counts double."),
    "supply_tent_reserve_water": ("Emergency Float", "A biscuit tin of petty cash for the things nobody budgeted for."),
    "supply_tent_climbing_gear": ("Ladders and Cable Ties", "Every lamp post in the constituency is a poster site if you can reach it."),
    "supply_tent_subdued_gear": ("Plain Clothes", "No rosettes, no lanyards: some work is better done without the colours on."),
    "barber_tent_01": ("Welfare Room", "A sofa, a kettle and a first aid kit: somewhere for volunteers to recover from the doorstep."),
    "barber_tent_surgeons_tools": ("First Aid Kit", "Plasters for letterbox fingers and ice packs for dog bites, properly stocked."),
    "barber_tent_dentists_tools": ("Occupational Health", "A nurse on call and a proper policy on breaks. Volunteers notice."),
    "barber_tent_torturers_tools": ("Mock Interview Room", "One chair, one bright lamp and a staffer who plays the hostile presenter far too well."),
    "barber_tent_reference_corpus": ("Reference Library", "Hansard, old manifestos and every select committee report worth having, on shelves and on file."),
    "barber_tent_morticians_tools": ("Post-Mortem Team", "After every election, somebody has to work out what went wrong, and what can be salvaged."),
    "baggage_train_01": ("Battle Bus", "A minibus, a sat nav and a boot full of leaflets: the campaign goes where the voters are."),
    "baggage_train_ample_steeds": ("Spare Minibuses", "When one breaks down on the bypass, the other is already on its way."),
    "baggage_train_porters": ("Removal Van", "Moving the whole office to a new town takes a weekend, not a month."),
    "baggage_train_trackers": ("Canvassing Data", "Every door knocked, every voter's intention: the campaign knows where to go next."),
    "baggage_train_kennel": ("Office Dog", "Good for morale, better for photo opportunities."),
    "baggage_train_siege_engineers": ("Digital Team", "Targeted adverts, email lists and a dashboard that refreshes every ten minutes."),
    "baggage_train_shrine": ("Quiet Room", "Somewhere to pray, think or simply be away from the phones for ten minutes."),
    "baggage_train_scribes": ("Press Officers", "Press releases, letters to the editor and statements drafted before anybody asks."),
    "baggage_train_bartering_grounds": ("Merch Stall", "Mugs, tote bags and badges: supporters pay to advertise you."),
    "baggage_train_proof_of_claims": ("Endorsement File", "Letters of support from councillors, union branches and the local great and good, ready to wave."),
    "baggage_train_ransom_cages": ("Holding Room", "Where awkward visitors wait while somebody senior is found to deal with them."),
    "baggage_train_negotiators": ("Reputation Managers", "A bad headline is a problem; a bad headline nobody answered is a crisis."),
    "baggage_train_ascetics": ("Policy Volunteers", "Retired civil servants and earnest students who will read the whole white paper so you don't have to."),
    "baggage_train_pleasure_tents": ("Private Offices", "A door that closes. Senior staff appreciate it more than a pay rise."),
    "mess_tent_01": ("Office Kitchen", "A tea urn, a fridge full of milk and somebody's birthday cake: the campaign marches on its stomach."),
    "mess_tent_herbalists": ("Healthy Snacks", "Fruit as well as biscuits. A small revolution."),
    "mess_tent_brewers": ("Coffee Machine", "A real one, with beans. Morning canvass turnout doubles."),
    "mess_tent_curers": ("Batch Cooking", "A freezer full of chilli for the long nights of the short campaign."),
    "mess_tent_bakers": ("Bacon Rolls", "Saturday morning, before the doorstep session. Nobody misses it."),
    "mess_tent_cooks": ("Volunteer Cooks", "Members who can't canvass but can feed thirty people on a budget."),
    "camp_fire_01": ("Team Meeting", "Monday night in the back room: who's doing what, who's annoyed with whom, and the biscuits."),
    "camp_fire_trailing_musicians": ("Office Playlist", "Somebody's speaker, somebody's playlist, and morale that holds through the envelope stuffing."),
    "camp_fire_wandering_poets": ("Wordsmiths", "People who can make a leaflet sing and a slogan stick."),
    "camp_fire_capering_fools": ("Office Comedians", "Every team needs someone who can make the bad polls funny."),
    "camp_fire_libations_for_the_lost": ("Drinks for the Defeated", "A pint for the ones who lost their seats, and a promise to win them back."),
    "camp_fire_local_hangers_on": ("Local Gossips", "The newsagent, the school-gate parents and the man in the pub who knows everything."),
    "camp_fire_future_dreams": ("Big Vision Sessions", "Away days with flip charts about the country the campaign is for."),
    "camp_fire_nightly_debates": ("Late-Night Debates", "Two wonks, one policy, five opinions and a closing time nobody keeps."),
    "camp_fire_juicy_rumors": ("Juicy Rumours", "Everything said off the record ends up somewhere. Better it ends up here."),
    "proving_grounds_01": ("Training Room", "Doorstep scripts, role-plays and how to answer the question you weren't asked."),
    "proving_grounds_horse_run": ("Cycle Canvass", "Bikes for the long roads and the estates the minibus can't reach."),
    "proving_grounds_camel_run": ("Rural Routes", "Villages, farms and lanes without street names: a canvass plan for the countryside."),
    "proving_grounds_elephantry_reserve": ("Celebrity Supporters", "An actor, a footballer and a TV cook who will turn up for the cameras."),
    "proving_grounds_nightly_barding_drills": ("Battle Bus Drills", "Load, drive, unload, canvass, repeat, until it runs like clockwork."),
    "proving_grounds_life_in_the_saddle": ("Life on the Road", "Some people only come alive in a different town every day."),
    "proving_grounds_the_stump": ("The Soapbox", "A crate in the market square and a lot of practice at being heckled."),
    "proving_grounds_personal_bouts": ("Debate Practice", "Mock hustings with a staffer playing your nastiest opponent."),
    "proving_grounds_training_circle": ("Role-Play Circle", "Angry voter, worried voter, voter who wants to talk about bins: everyone practises everything."),
    "proving_grounds_mock_battle_drills": ("Mock Polling Days", "A full rehearsal of polling day, from the first knock-up to the close of poll."),
    "proving_grounds_lockwagon": ("Shared Kitty", "Every donation goes into one pot, and the pot pays for everything. Mostly."),
    "proving_grounds_martial_study": ("Campaign Case Studies", "Every election has been fought before. Read how it was won."),
    "proving_grounds_the_stick_game": ("Office Sweepstake", "On the result, the turnout and which candidate cries first."),
    "proving_grounds_bodyguard_drills": ("Close Protection Drills", "A candidate in public needs someone watching the crowd."),
    "camp_perimeter_01": ("Front Desk", "Someone to answer the door, the phone and the angry constituent, in that order."),
    "camp_perimeter_good_siting": ("High Street Frontage", "Right by the bus stop and the supermarket: everyone walks past the window."),
    "camp_perimeter_fixed_layout": ("Hot-Desk Plan", "The same desks, the same rota, wherever the office moves. Everyone knows where everything is."),
    "camp_perimeter_extra_watch": ("Door Entry System", "A buzzer, a camera and a list of who's expected."),
    "camp_perimeter_palisade": ("Shutters", "Steel shutters after dark: the windows survive election night."),
    "camp_perimeter_ditch": ("Bollards", "Nobody parks a van across the office door twice."),
    "camp_perimeter_camp_hygiene": ("Cleaning Rota", "The fridge is cleared every Friday. It is the law."),
}

OFFICERS = {
    "second": ("Deputy Campaign Manager", "The $second_camp_officer$ runs the office when the candidate is out on the doorstep, and keeps everyone else on task."),
    "quartermaster": ("Office Manager", "The $quartermaster_camp_officer$ keeps the campaign funds, the stationery cupboard and the rota in order."),
    "armorer": ("Materials Manager", "The $armorer_camp_officer$ makes sure every volunteer has a lanyard, a clipboard and leaflets that are actually up to date."),
    "chief_forager": ("Fundraising Lead", "The $chief_forager_camp_officer$ finds the money: raffles, dinners, standing orders and the occasional generous donor."),
    "master_thief": ("Opposition Researcher", "The $master_thief_camp_officer$ knows what the other side said in 2011, and where it was written down."),
    "head_porter": ("Logistics Coordinator", "The $head_porter_camp_officer$ gets the office, the boxes and the people to the next town in one piece."),
    "head_groom": ("Transport Manager", "The $head_groom_camp_officer$ looks after the minibuses, the fuel cards and the parking fines."),
    "huntperson": ("Outreach Organiser", "The $huntperson_camp_officer$ plans the days out: street stalls, community events and visits."),
    "kennelperson": ("Volunteer Coordinator", "The $kennelperson_camp_officer$ keeps the volunteers fed, thanked and pointed in the right direction."),
    "chief_engineer": ("Digital Director", "The $chief_engineer_camp_officer$ runs the data, the adverts and the machinery of a modern campaign."),
    "witness": ("Endorsements Officer", "The $witness_camp_officer$ collects every letter of support and makes sure everybody hears about them."),
    "person_haggler": ("Deal Broker", "The $person_haggler_camp_officer$ handles the awkward visitors and gets the best terms out of every favour."),
    "camp_cook": ("Chief Tea Maker", "The $camp_cook_camp_officer$ keeps the urn hot and the team fed through the long evenings."),
    "master_bard": ("Content Creator", "The $master_bard_camp_officer$ turns a day on the doorstep into a video, a post and, now and then, a viral moment."),
    "stooge": ("Intern", "The $stooge_camp_officer$ does the photocopying, the coffee run and every job nobody else wants. Morale improves, for everyone else."),
    "master_of_arms": ("Field Director", "The $master_of_arms_camp_officer$ runs the canvass teams: who knocks where, and when."),
    "light_cavalry_captain": ("Rapid Response Lead", "The $light_cavalry_captain_camp_officer$ gets a team anywhere in the area within the hour."),
    "camelry_captain": ("Rural Team Lead", "The $camelry_captain_camp_officer$ runs the canvass in the villages and the farms."),
    "elephantry_captain": ("Celebrity Liaison", "The $elephantry_captain_camp_officer$ looks after the famous supporters, their diaries and their egos."),
    "heavy_cavalry_captain": ("Battle Bus Captain", "The $heavy_cavalry_captain_camp_officer$ runs the bus tours: big visits, big crowds, big pictures."),
    "horse_archer_captain": ("Leaflet Run Lead", "The $horse_archer_captain_camp_officer$ organises the fast delivery rounds, street by street."),
    "archer_captain": ("Rebuttal Unit Lead", "The $archer_captain_camp_officer$ answers every attack before lunch."),
    "heavy_infantry_captain": ("Doorstep Team Lead", "The $heavy_infantry_captain_camp_officer$ leads the big Saturday canvass sessions."),
    "light_infantry_captain": ("Street Stall Lead", "The $light_infantry_captain_camp_officer$ runs the stalls in the market square and outside the station."),
    "pike_captain": ("Phone Bank Lead", "The $pike_captain_camp_officer$ runs the evening phone banks: scripts, lists and a steady line of calls."),
    "master_of_spoils": ("Treasurer", "The $master_of_spoils_camp_officer$ keeps the accounts, signs the cheques and files the returns with the Electoral Commission."),
    "laureate": ("Wordsmith", "The $laureate_camp_officer$ writes the lines people remember, and the ones they quote back at you."),
    "camp_priest": ("Welfare Officer", "The $camp_priest_camp_officer$ looks after the team: a listening ear, a quiet word and an eye on who is burning out."),
}

HAND = {
    # concepts
    "game_concept_camp": "Campaign Office", "game_concept_camps": "Campaign Offices",
    "game_concept_adventurer_camp": "Campaign Office", "game_concept_adventurer_camps": "Campaign Offices",
    "game_concept_camp_desc": "A $game_concept_camp$ is a campaigner's base: a rented room, a shopfront or a regional headquarters, its staff and volunteers, and the battle bus that takes it from town to town.\n\nEvery [GetGovernment( 'landless_adventurer_government' ).GetName] has a $game_concept_camp$ [domicile|E] that moves across the map with them.\n\n[camp_buildings|E] can be added, which give the $game_concept_camp$ and its campaigner lasting bonuses.",
    "game_concept_adventurer": "Campaigner", "game_concept_adventurers": "Campaigners",
    "game_concept_adventurer_possessive": "Campaigner's", "game_concept_adventurers_possessive": "Campaigners'",
    "game_concept_adventurer_desc": "A $game_concept_adventurer$ is a politician without a seat: an activist, a candidate or a former MP, leading a [camp|E].\n\nThey have no constituency and no income of their own: they take [task_contracts|E] from their party's MPs to earn money, profile and Party Standing, and call in favours from their [contact_list|E].\n\nA $game_concept_adventurer$ can move their office anywhere. The goal is a seat: get on the approved list, win a selection, then win the election.",
    "landless_adventurer_government": "Campaigner", "landless_adventurer_government_adjective": "Campaigning",
    "landless_adventurer_government_realm": "Campaign Office",
    "game_concept_camp_purpose": "Political Focus", "game_concept_camp_purposes": "Political Focuses",
    "game_concept_camp_purpose_purpose": "Focus", "game_concept_camp_purpose_purposes": "Focuses",
    "game_concept_camp_purpose_desc": "A $game_concept_camp_purpose$ is what a campaigner is known for: the kind of politician they are becoming.\n\nIt decides which [task_contracts|E] their party offers them most, gives a bonus of its own, and unlocks some [camp_buildings|E]. A $game_concept_camp_purpose_purpose$ can be changed, but changing from one to another costs [prestige|E]; a Party Activist may pick any for free.",
    "camp_purpose": "Political Focus",
    "camp_purpose_pass_phrase": "Become a [Law.GetNameNoTooltip]",
    "camp_purpose_confirmation_button_text": "Change Focus",
    "game_concept_camp_temperament": "Team Morale",
    "game_concept_camp_building": "Office Facility", "game_concept_camp_buildings": "Office Facilities",
    "game_concept_camp_building_desc": "$game_concept_camp_buildings$ are improvements to a [camp|E]: rooms, equipment, people and habits.\n\nMechanically, they are [domicile_buildings|E]. They can:\n$EFFECT_LIST_BULLET$ Unlock new [officers|E]\n$EFFECT_LIST_BULLET$ Give bonuses to the campaigner and the team\n$EFFECT_LIST_BULLET$ Improve [task_contract|E] rewards",
    "game_concept_follower": "Team Member", "game_concept_followers": "Team Members",
    "game_concept_follower_desc": "A $game_concept_follower$ is a volunteer or staffer who works for a [adventurer|E] without a seat.\n\nMechanically, they are like [courtiers|E], but they owe less and leave sooner if they dislike their boss.\n\nThe collective [opinion|E] of the $game_concept_followers$ sets the [camp_temperament|E].",
    "game_concept_officer": "Senior Staffer", "game_concept_officers": "Senior Staff",
    "game_concept_officer_desc": "$game_concept_officers$ are the jobs [followers|E] can be given to run the [camp|E]: office manager, field director, treasurer and so on.\n\nThey work like [court_positions|E]: what they bring depends on the holder's [aptitude|E] for the job.",
    "game_concept_provisions": "Campaign Funds", "game_concept_provision": "Campaign Fund",
    "game_concept_provisions_desc": "$game_concept_provisions$ are the office's running budget: rent, fuel, print and food for the volunteers.\n\nA [camp|E] spends $game_concept_provisions$ while it moves to a new [location|E]; how much depends on the size of the team, the distance and the [officers|E] it has.\n\nRunning out means unpaid bills and an unhappy team. Jobs done well, and some [camp_buildings|E], bring more in.",
    "game_concept_task_contract": "Job", "game_concept_task_contracts": "Jobs",
    "game_concept_task_contract_possessive": "Job's", "game_concept_task_contracts_possessive": "Jobs'",
    "game_concept_task_contract_desc": "$game_concept_task_contracts$ are work a [adventurer|E] does for the party's MPs: canvassing, fundraising, speechwriting, research, phone banks, policy papers and media rounds.\n\nEach takes three weeks and is settled by a skill check. Doing it well earns [gold|E], [prestige|E], [provisions|E], Party Standing and the MP as a contact; doing it badly costs a little standing.\n\nThe party's candidate assessment is a $game_concept_task_contract$ too: pass it to join the approved candidates list.",
    "game_concept_contractor": "Employer", "game_concept_contractors": "Employers",
    "game_concept_contractor_possessive": "Employer's", "game_concept_contractors_possessive": "Employers'",
    "game_concept_contractor_desc": "The $game_concept_contractor$ is the MP or party leader offering a [task_contract|E]. They pay for it, and remember how well it was done.",
    "game_concept_task_contract_tier": "Job Grade",
    "game_concept_domicile": "Base", "game_concept_domiciles": "Bases",
    "TASK_CONTRACT_CONTRACT": "Job", "TASK_CONTRACT_CONTRACT_PLURAL": "Jobs",
    "TASK_CONTRACT_CONTRACT_POSSESSIVE": "Job's", "TASK_CONTRACT_CONTRACT_POSSESSIVE_PLURAL": "Jobs'",
    "TASK_CONTRACT_DECLINE": "Not Now",
    "TASK_CONTRACT_DEFAULT_DESC_TITLE": "To whom it may concern,",
    "camp_domicile_type_possessive": "Campaign Office's",
    "domicile_temperament_low": "Demoralised Team", "domicile_temperament_high": "Fired-Up Team",
    "domicile_temperament_neutral": "Steady Team",
    "camp_move_desc": "Moving your [camp|E] to another town brings new [task_contracts|E] and new doors to knock on.\n\n#weak Moving far puts you out of reach of your [contact_list_contacts|E], so call in any favours first.#!\n\n#P Click to move your Campaign Office#!",
    "ep3_can_have_legitimists_camp_purpose_trigger.tt.explanation": "You must have a Party Standing of at least 40",
}


def focus_effects(law, vanilla):
    """The camp purpose's effects text: its job and bonus lines, then vanilla's unlocked buildings and officers."""
    name, jobs, bonus, flavour = FOCUS[law]
    v = vanilla.get("camp_purpose_%s_effects" % law, ("", ""))[1]
    keep = ""
    i = v.find("$EFFECT_LIST_BULLET$Unlocks")
    if i >= 0:
        keep = v[i:]
        j = keep.find("\\n\\n#WEAK")
        keep = keep[:j] if j >= 0 else keep
        keep = "\\n" + transform(keep)
    return "$EFFECT_LIST_BULLET$%s\\n$EFFECT_LIST_BULLET$%s%s\\n\\n#WEAK %s#!" % (jobs, bonus, keep, flavour)


def hand_entries(vanilla):
    h = dict(HAND)
    for law, (name, *_rest) in FOCUS.items():
        h["camp_purpose_%s" % law] = name
        h["camp_purpose_%s_effects" % law] = focus_effects(law, vanilla)
    for key, (name, desc) in BUILDINGS.items():
        h["%s_domicile_building" % key] = name
        old = vanilla.get("%s_domicile_building_desc" % key, ("", ""))[1]
        m = re.match(r"(#weak \(Requires [^#]*\)#!(?:\\n)?)", old)
        h["%s_domicile_building_desc" % key] = (m.group(1) if m else "") + desc
    for key, (name, desc) in OFFICERS.items():
        h["%s_camp_officer" % key] = name
        h["%s_camp_officer_desc" % key] = desc
    return h


# ------------------------------------------------------------------------------------------------ the AUTO set

AUTO_KEY = re.compile(
    r"^(camp_|supply_tent_|barber_tent_|baggage_train_|mess_tent_|proving_grounds_|camp_perimeter_|camp_fire_|"
    r"domicile_building_parameter_camp|laamp_building|DOMICILE_|TASK_CONTRACT_|game_concept_(camp|adventurer|follower|"
    r"officer|provision|task_contract|contractor|contract_scheme|domicile)|landless_adventurer_government)"
    r"|_camp_officer|camp_with_following_buildings_tt")
AUTO_FILES = {"domiciles/domicile_buildings_l_english.yml", "domiciles/domicile_types_l_english.yml",
              "court_positions_l_english.yml", "laws_l_english.yml", "game_concepts_l_english.yml",
              "dlc/ep3/dlc_ep3_game_concepts_l_english.yml",
              "contracts/task_contracts_l_english.yml", "core_l_english.yml", "important_actions_l_english.yml",
              "effects_l_english.yml", "triggers/domicile_triggers_l_english.yml", "modifiers/modifiers_l_english.yml"}
# window files whose every key is camp-related (or harmless to re-term)
ALL_KEYS_FILES = {"gui/domicile_window_l_english.yml", "gui/contract_window_l_english.yml",
                  "gui/travel_planner_window_l_english.yml"}
REALM_KEYS = re.compile(r"ADVENTURER|CAMP|LAAMP", re.I)
SKIP_KEY = re.compile(r"estate|yurt|_asian|chinese|ecclesiastic|herd|horde|nomad|mandala|lease|_ISSUE|SETTLEMENT|"
                      r"MANDALA|campaign_|camp_party|game_concept_(vassal|tributary|lease|mercenary)_contract")


def main():
    root, vanilla = bt.load_vanilla(bt.DEFAULT_GAME)
    taken = {k: f for k, f in bt.mod_keys().items() if not f.endswith(OUT.name)}
    out, problems = {}, []
    for key, (rel, old) in vanilla.items():
        wanted = ((rel in AUTO_FILES and AUTO_KEY.search(key)) or rel in ALL_KEYS_FILES
                  or (rel == "gui/realm_window_l_english.yml" and REALM_KEYS.search(key)))
        if not wanted or SKIP_KEY.search(key):
            continue
        new = transform(old)
        if new != old:
            out[key] = new
    hand = hand_entries(vanilla)
    out.update(hand)
    lines, skipped = [], []
    for key in sorted(out):
        if key in taken:
            skipped.append(key)
            continue
        val = out[key]
        if key in vanilla and key not in hand and bt.markup(val) != bt.markup(vanilla[key][1]):
            problems.append(key)
            continue
        lines.append(' %s: "%s"' % (key, val))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("l_english:\n # Westminster: the adventurer camp as a campaign office. Generated by "
                   "westminster/tools/ui/build_campaign_office_loc.py - edit there.\n" + "\n".join(lines) + "\n",
                   encoding="utf-8-sig")
    print("campaign office loc: %d keys written, %d left to other files, %d markup problems" %
          (len(lines), len(skipped), len(problems)))
    for k in problems:
        print("  markup changed:", k)
    if "--report" in sys.argv:
        for k in skipped:
            print("  defined in %s: %s" % (taken[k], k))


if __name__ == "__main__":
    main()
