#!/usr/bin/env python3
"""Westminster terminology pass: modern British-politics words for vanilla CK3's English UI.

    python3 westminster/tools/ui/build_terms.py [--game <path to CK3 game folder>] [--report]

Reads the installed game's English localization and writes overrides into
westminster/westminster/localization/english/replace/wm_terms_*.yml (files in a `replace` folder
override vanilla keys of the same name). Re-run it after a game update.

Four kinds of override:
  1. EXPLICIT: hand-written values for the most visible keys (concept names, HUD buttons,
     council positions, rewritten concept descriptions).
  1b. EDITS: long vanilla values with a phrase or two rewritten, then given the AUTO substitution.
  2. AUTO: every key of a whitelisted set of vanilla files (game concepts, core, the main windows,
     council, factions...) has its plain text run through the TERMS substitution table. Only plain
     text is touched: [data expressions], $KEY$ references, #format codes, @icons! and \\n are kept
     exactly, and the script checks that per key before writing.
  3. SKILLS: every other vanilla file (except events, names and debug text) is scanned for keys that name a
     skill or currency (SKILL_WORDS); those keys get the AUTO substitution too.

Keys that the mod already defines in another localization file are skipped (and listed with
--report), so this pass never fights a hand-written file.
"""
import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
MOD = HERE.parent.parent / "westminster"
LOC = MOD / "localization" / "english"
OUT = LOC / "replace"
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "common" / "tools"))
from ck3paths import GAME as DEFAULT_GAME  # noqa: E402  (CK3_GAME_DIR overrides the Steam default)
OUT_PREFIX = "wm_terms_"

# ---------------------------------------------------------------------------------------------
# The substitution table for plain text. Matched case-sensitively as whole words, longest first,
# in a single pass (so a replacement is never replaced again). An entry mapping a phrase to itself
# protects it (e.g. "Ecumenical Council" keeps its "Council").
# ---------------------------------------------------------------------------------------------
TERMS = [
    # protected phrases (other DLC systems that share a word)
    ("Ecumenical Council", "Ecumenical Council"), ("ecumenical council", "ecumenical council"),
    ("Investiture Council", "Investiture Council"),
    ("Grand Chancellor", "Grand Chancellor"), ("Grand Marshal", "Grand Marshal"),
    ("Royal Court Language", "Office Language"),
    ("Court Language", "Office Language"),

    # currencies (PLAN.md, decided 2026-10-09): gold, prestige, piety, renown, dread, stress, legitimacy become
    # Funds, Profile, Political Capital, Party Brand (parties are houses), Clout, Pressure and Mandate
    ("Gold", "Funds"), ("gold", "funds"),
    ("Level of Fame", "Profile Level"), ("Levels of Fame", "Profile Levels"),
    ("Level of Devotion", "Political Capital Level"), ("Level(s) of Devotion", "Political Capital Level(s)"),
    ("Levels of Devotion", "Political Capital Levels"),
    ("Level of Splendor", "Party Brand Level"), ("Levels of Splendor", "Party Brand Levels"),
    ("Dynasty Prestige", "Party Brand"),
    ("Prestige", "Profile"), ("prestige", "profile"),
    ("Filial Piety", "Filial Piety"),
    ("Piety", "Political Capital"), ("piety", "political capital"),
    ("Devotion", "Loyalty"),
    ("Renown", "Party Brand"), ("renown", "party brand"),
    ("Dreadful", "Formidable"), ("Dreaded", "Formidable"), ("Dread", "Clout"),
    ("Existential Dread", "Existential Dread"),
    ("Stressed", "Under Pressure"),
    ("Stress", "Pressure"), ("stress", "pressure"),
    ("Legitimacy", "Mandate"), ("legitimacy", "mandate"),

    # the party machine (levies, men-at-arms, knights)
    ("Men-at-Arms Regiments", "Activist Groups"), ("Men-at-Arms Regiment", "Activist Group"),
    ("Men-at-Arms", "Activists"), ("men-at-arms", "activists"),
    ("Man-at-Arms", "Activist"), ("man-at-arms", "activist"),
    ("Levies", "Volunteers"), ("levies", "volunteers"), ("Levy", "Volunteer"),
    ("Acclaimed Knights", "Star Organisers"), ("Acclaimed Knight", "Star Organiser"),
    ("Knights", "Organisers"), ("Knight", "Organiser"), ("knights", "organisers"), ("knight", "organiser"),

    # hierarchy
    ("Top Lieges", "Prime Ministers"), ("Top Liege", "Prime Minister"),
    ("top lieges", "Prime Ministers"), ("top liege", "Prime Minister"),
    ("Lieges", "Party Leaders"), ("Liege", "Party Leader"),
    ("lieges", "party leaders"), ("liege", "party leader"),
    ("Vassals", "Backbenchers"), ("Vassal", "Backbencher"),
    ("vassals", "backbenchers"), ("vassal", "backbencher"),
    ("Realm Capitals", "Home Bases"), ("Realm Capital", "Home Base"), ("realm capital", "home base"),
    ("My Realm", "My Party"),
    ("Realms", "Parties"), ("Realm", "Party"), ("realms", "parties"), ("realm", "party"),
    ("Domains", "Portfolios"), ("Domain", "Portfolio"), ("domains", "portfolios"), ("domain", "portfolio"),

    # land tiers in running text (the rank and tier keys themselves are in wm_ranks_l_english.yml)
    ("Baronies", "Wards"), ("Barony", "Ward"), ("baronies", "wards"), ("barony", "ward"),
    ("Counties", "Constituencies"), ("County", "Constituency"),
    ("counties", "constituencies"), ("county", "constituency"),
    ("Duchies", "Regions"), ("Duchy", "Region"), ("duchies", "regions"), ("duchy", "region"),
    ("Kingdoms", "Nations"), ("Kingdom", "Nation"),

    # the office (court) and the Cabinet (council)
    ("Court Chaplains", "Leaders of the House"), ("Court Chaplain", "Leader of the House"),
    ("court chaplain", "Leader of the House"),
    ("Court Positions", "Appointments"), ("Court Position", "Appointment"),
    ("court positions", "appointments"), ("court position", "appointment"),
    ("Royal Courts", "Private Offices"), ("Royal Court", "Private Office"),
    ("royal court", "private office"),
    ("Hold Court", "Hold a Surgery"), ("Holding Court", "Holding a Surgery"),
    ("Courtiers", "Staff"), ("Courtier", "Staffer"), ("courtiers", "staff"), ("courtier", "staffer"),
    ("Courts", "Offices"), ("Court", "Office"),
    ("at court", "in the office"), ("the court", "the office"), ("your court", "your office"),
    ("their court", "their office"), ("his court", "his office"), ("her court", "her office"),
    ("a court", "an office"), ("my court", "my office"), ("own court", "own office"),
    ("Councillor Tasks", "Ministerial Tasks"), ("Councillor Task", "Ministerial Task"),
    ("councillor tasks", "ministerial tasks"), ("councillor task", "ministerial task"),
    ("Councillors", "Ministers"), ("Councillor", "Minister"),
    ("councillors", "ministers"), ("councillor", "minister"),
    ("Councils", "Cabinets"), ("Council", "Cabinet"), ("councils", "cabinets"), ("council", "cabinet"),
    ("Chancellors", "Foreign Secretaries"), ("Chancellor", "Foreign Secretary"),
    ("Stewards", "Chancellors of the Exchequer"), ("Steward", "Chancellor of the Exchequer"),
    ("Marshals", "Home Secretaries"), ("Marshal", "Home Secretary"),
    ("Spymasters", "Chief Whips"), ("Spymaster", "Chief Whip"),

    # skills (PLAN.md, decided 2026-10-09). Capitalised: as skill names; lower case only next to "skill" or
    # "lifestyle", since lower-case "learning", "intrigue" or "prowess" is often just English.
    ("Diplomacy", "Charisma"), ("Stewardship", "Economy"), ("Martial", "Security"),
    ("Intrigue", "Spin"), ("Learning", "Policy"), ("Prowess", "Stamina"),
    ("prowess skill", "stamina skill"), ("prowess checks", "stamina checks"),
    # "Learning" that is just the English word
    ("Learning to", "Learning to"), ("Learning a", "Learning a"), ("Learning the", "Learning the"),
    ("Learning Language", "Learning Language"), ("Learning Local", "Learning Local"),
    ("Love of Learning", "Love of Learning"), ("Beacon of Learning", "Beacon of Learning"),
    ("Religious Learning", "Religious Learning"), ("Gave Up Learning", "Gave Up Learning"),
    ("Extracurricular Learning", "Extracurricular Learning"), ("Learning Efforts", "Learning Efforts"),
    ("Take Stewardship", "Take Stewardship"), ("Backroom Diplomacy", "Backroom Diplomacy"),
    ("Schism Through Diplomacy", "Schism Through Diplomacy"), ("Martial Arts", "Martial Arts"),
    ("Martial Custom", "Martial Custom"), ("Martial Customs", "Martial Customs"),
    ("diplomacy skill", "charisma skill"), ("stewardship skill", "economy skill"), ("martial skill", "security skill"),
    ("intrigue skill", "spin skill"), ("learning skill", "policy skill"),
    ("diplomacy lifestyle", "charisma lifestyle"), ("stewardship lifestyle", "economy lifestyle"),
    ("martial lifestyle", "security lifestyle"), ("intrigue lifestyle", "spin lifestyle"),
    ("learning lifestyle", "policy lifestyle"),

    # religion is political ideology (tools/data/build_ideology.py): faiths are ideologies, religions are political
    # camps, doctrines policy positions, tenets causes, fervour conviction
    ("Holy War", "Holy War"), ("Holy Wars", "Holy Wars"), ("holy war", "holy war"), ("holy wars", "holy wars"),
    ("Great Holy War", "Great Holy War"), ("Great Holy Wars", "Great Holy Wars"),
    ("Heads of Faith", "Movement Leaders"), ("Head of Faith", "Movement Leader"),
    ("heads of faith", "movement leaders"), ("head of faith", "movement leader"),
    ("Religious Heads", "Movement Leaders"), ("Religious Head", "Movement Leader"),
    ("religious heads", "movement leaders"), ("religious head", "movement leader"),
    ("Faiths", "Ideologies"), ("Faith", "Ideology"), ("faiths", "ideologies"), ("faith", "ideology"),
    ("Religious Families", "Political Families"), ("Religious Family", "Political Family"),
    ("religious families", "political families"), ("religious family", "political family"),
    ("Religions", "Political Camps"), ("Religion", "Political Camp"),
    ("religions", "political camps"), ("religion", "political camp"),
    ("Holy Sites", "Heartlands"), ("Holy Site", "Heartland"), ("holy sites", "heartlands"), ("holy site", "heartland"),
    ("Heresies", "Splinter Groups"), ("Heresy", "Splintering"), ("heresies", "splinter groups"), ("heresy", "splintering"),
    ("Heretics", "Dissidents"), ("Heretic", "Dissident"), ("heretics", "dissidents"), ("heretic", "dissident"),
    ("Heretical", "Breakaway"), ("heretical", "breakaway"),
    ("Clergy", "Party Officials"), ("clergy", "party officials"),
    ("Fervor", "Conviction"), ("fervor", "conviction"),
    ("Convert to Faith", "Adopt This Ideology"), ("Convert to Rite", "Adopt This Ideology"),
    ("Convert Faith", "Change Ideology"), ("Convert Rite", "Change Ideology"),
    # rites: each ideology has exactly one, of the same name (build_ideology.py), so a rite is the ideology itself
    ("Mainline Rites", "Mainstream Ideologies"), ("Mainline Rite", "Mainstream Ideology"),
    ("mainline rites", "mainstream ideologies"), ("mainline rite", "mainstream ideology"),
    ("Branched Rites", "Offshoots"), ("Branched Rite", "Offshoot"), ("branched rites", "offshoots"), ("branched rite", "offshoot"),
    ("Heads of Rites", "Leading Voices"), ("Head of Rite", "Leading Voice"), ("head of rite", "leading voice"),
    ("Rites", "Ideologies"), ("Rite", "Ideology"), ("rites", "ideologies"), ("rite", "ideology"),
    ("Spiritual Fulfillment", "Personal Conviction"), ("spiritual fulfillment", "personal conviction"),
    ("Doctrines", "Policy Positions"), ("Doctrine", "Policy Position"),
    ("doctrines", "policy positions"), ("doctrine", "policy position"),
    ("Core Tenets", "Core Causes"), ("Tenets", "Causes"), ("Tenet", "Cause"), ("tenets", "causes"), ("tenet", "cause"),
    ("Heathens", "Opponents"), ("Heathen", "Opponent"), ("heathens", "opponents"), ("heathen", "opponent"),
    ("Infidels", "Opponents"), ("Infidel", "Opponent"), ("infidels", "opponents"), ("infidel", "opponent"),

    # popular revolts (Westminster replaces them with riots and protest marches)
    ("Peasant Factions", "Protest Movements"), ("Peasant Faction", "Protest Movement"),
    ("Populist Factions", "Populist Movements"), ("Populist Faction", "Populist Movement"),
    ("Peasant Revolts", "Protest Movements"), ("Peasant Revolt", "Protest Movement"),
    ("Peasant Rabble", "Protesters"),
    ("Peasant Uprising", "Riot"), ("Populist Uprising", "Populist Riot"),
]

# ---------------------------------------------------------------------------------------------
# Whitelisted vanilla files (relative to localization/english) whose keys all get the AUTO pass.
# ---------------------------------------------------------------------------------------------
AUTO_FILES = {
    "concepts": ["game_concepts_l_english.yml", "dlc/**/*game_concepts*_l_english.yml"],
    "ui": [
        "core_l_english.yml", "my_realm_window_l_english.yml",
        "gui/ingame_main_l_english.yml", "gui/realm_window_l_english.yml",
        "gui/council_window_l_english.yml", "gui/court_window_l_english.yml",
        "gui/character_window_l_english.yml", "gui/militaryview_l_english.yml",
        "gui/armyview_l_english.yml", "gui/levyview_l_english.yml",
        "gui/factions_view_l_english.yml", "gui/decisionsview_l_english.yml",
        "gui/schemewindow_l_english.yml", "gui/character_list_l_english.yml",
        "gui/characterinteractionwindow_l_english.yml", "gui/encyclopedia_l_english.yml",
        "gui/outliner_l_english.yml", "important_actions_l_english.yml", "messages_l_english.yml",
    ],
    "council": [
        "council_l_english.yml", "council_tasks_l_english.yml",
        "modifiers/council_modifiers_l_english.yml",
    ],
    "factions": ["factions_l_english.yml"],
    "religion": [
        "gui/faith_view_l_english.yml", "gui/holy_site_window_l_english.yml", "gui/personal_beliefs_window_l_english.yml",
        "gui/rite_creation_window_l_english.yml",
        "religion/religion_l_english.yml", "religion/doctrine_category_types_l_english.yml",
    ],
    "character": [
        "focuses_l_english.yml", "knight_culture_l_english.yml",
        "modifiers/modifiers_l_english.yml", "opinions/general_opinions_l_english.yml",
        "interactions_l_english.yml", "laws_l_english.yml",
    ],
}

# ---------------------------------------------------------------------------------------------
# The SKILLS pass: skills and currencies appear all over vanilla (traits, perks, schemes, modifiers,
# tooltips), not only in AUTO_FILES. Every other vanilla file except the ones below is scanned, and a key whose
# plain text names a skill or currency gets the full TERMS substitution (into wm_terms_skills_l_english.yml).
# ---------------------------------------------------------------------------------------------
SKILL_WORDS = re.compile(
    r"(?<![A-Za-z0-9_\-])(Diplomacy|Stewardship|Martial|Intrigue|Learning|Prowess|prowess|Piety|piety|"
    r"Prestige|prestige|Renown|renown|Dread|Dreadful|Dreaded|dread|Stress|Stressed|stress|stressed|"
    r"Legitimacy|legitimacy|Devotion|Splendor|(?:diplomacy|stewardship|martial|intrigue|learning) (?:skill|lifestyle))"
    r"(?![A-Za-z0-9_\-])")
SKILL_SCAN_SKIP = re.compile(r"event|debug|tutorial|achievement|credits|^names/|^dynasties/|^titles|^cultures?/name")

# ---------------------------------------------------------------------------------------------
# Hand-written values. These win over the AUTO pass. Keys must exist in vanilla.
# ---------------------------------------------------------------------------------------------
EXPLICIT = {
    # ---- leftovers: a Cabinet member is a Minister (a "Councillor" is the local-council rank); parties are dynasties
    "COUNCILLOR_LIEGE_MODIFIERS_BONUS": "Minister's [liege|E] [modifiers|E]",
    "HOUSE_VIEW_PART_OF_DYNASTY": "[Dynasty.GetBaseNameNoTooltip]",
    "HOUSE_DYNASTY_TAB_BUTTON": "Party",
    "DYNASTY_VIEW_HEADING": "[Dynasty.GetBaseNameNoTooltip] Legacies",
    "game_concept_dynasty_perks": "Party Legacies",
    "MAX_MILITARY_STRENGTH_TRIGGER": "Maximum Strength: $VALUE|+0=$",
    # ---- resources
    "game_concept_gold": "Funds",
    "game_concept_gold_desc": "Funds are a politician's money: donations, membership subscriptions and campaign war chests. They pay for staff, offices, leaflets and campaigns.",
    "game_concept_prestige": "Profile",
    "game_concept_prestige_desc": "$game_concept_prestige$ is a politician's public fame: name recognition, column inches and airtime.\n\nIt is spent on public moves, depending on the [government_form|E].\n\nEvery time a Character gains Profile, they also progress toward the next [prestige_level|E].",
    "game_concept_prestige_experience": "Fame",
    "game_concept_prestige_level": "Profile Level",
    "game_concept_prestige_levels": "Profile Levels",
    "game_concept_prestige_level_impact": "Profile Level Impact",
    "game_concept_piety": "Political Capital",
    "game_concept_piety_desc": "$game_concept_piety$ is a politician's credit with their party and the establishment: loyalty shown, favours done, the right causes backed.\n\nIt is spent on asking things of the party and the establishment, depending on the [government_form|E].\n\nEach time a Character gains Political Capital, they also progress towards the next [piety_level|E].",
    "game_concept_piety_experience": "Loyalty",
    "game_concept_piety_experience_desc": "Each point of Loyalty a character gets increases their progress towards the next [piety_level|E]. When a character gains [piety|E] they also gain an equal amount of Loyalty.",
    "game_concept_piety_level": "Political Capital Level",
    "game_concept_piety_levels": "Political Capital Level(s)",
    "game_concept_maximum_piety_level": "Maximum Political Capital Level",
    "game_concept_piety_level_impact": "Political Capital Level Impact",
    # the levels themselves (vanilla: Sinner ... Religious Icon; 6-8 are the mandala government's)
    "piety_level_0": "Discredited",
    "piety_level_1": "Loyal",
    "piety_level_2": "Trusted",
    "piety_level_3": "Party Stalwart",
    "piety_level_4": "Party Grandee",
    "piety_level_5": "Party Icon",
    "game_concept_dynasty_prestige": "Party Brand",
    "game_concept_dynasty_prestige_level": "Party Brand Level",
    "DYNASTY_SPLENDOR": "Party Brand Level:",
    "game_concept_dynasty_prestige_desc": "$game_concept_dynasty_prestige$ is a party's reputation as a whole: what voters think its name stands for, and the doors it opens for its members.\n\nA [dynasty|E] gains $game_concept_dynasty_prestige$ from its living members, from the members who hold office, and from members married to other office-holders.\n\nIt counts towards the party's [dynasty_prestige_level|E], and the party's leader can spend it on [dynasty_perks|E].",

    # ---- the party machine
    "game_concept_levies": "Volunteers",
    "game_concept_levy": "Volunteer",
    "game_concept_men_at_arms": "Activists",
    "game_concept_knight": "Organiser",
    "game_concept_knights": "Organisers",
    "game_concept_knights_possessive": "Organiser's",

    # ---- hierarchy
    "game_concept_vassal": "Backbencher",
    "game_concept_vassals": "Backbenchers",
    "game_concept_vassal_possessive": "Backbencher's",
    "game_concept_vassals_possessive": "Backbenchers'",
    "game_concept_vassal_desc": "A $game_concept_vassal$ is a politician who answers to another: an MP to their [liege|E], a party leader to the Prime Minister.\n\nBackbenchers give their Party Leader [levies|E] and [taxes|E] — their [obligations|E] — in return for the whip and support.\n\nIf a $game_concept_vassal$'s [opinion|E] of their Party Leader is low, they may join [factions|E], or [scheme|E] to replace them.",
    "game_concept_liege": "Party Leader",
    "game_concept_lieges": "Party Leaders",
    "game_concept_liege_possessive": "Party Leader's",
    "game_concept_liege_desc": "A $game_concept_liege$ is a politician with at least one [vassal|E] answering to them. Party Leaders themselves answer to the Prime Minister.",
    "game_concept_realm": "Party",
    "game_concept_realms": "Parties",
    "game_concept_realm_possessive": "Party's",
    "game_concept_realm_desc": "A $game_concept_realm$ is everyone and everything a politician leads, directly or through their [vassals|E] (unlike a [domain|E], which is only what they hold themselves).",
    "game_concept_domain": "Portfolio",
    "game_concept_domains": "Portfolios",
    "game_concept_domain_desc": "A politician's $game_concept_domain$ is everything they hold personally: their seat and its wards.\n\nThe [domain_limit|E] means that a leader has to rely on [vassals|E] to lead more than a handful of seats.",
    "game_concept_barony": "Ward",
    "game_concept_baronies": "Wards",
    "game_concept_county": "Constituency",
    "game_concept_counties": "Constituencies",
    "game_concept_duchy": "Region",
    "game_concept_duchies": "Regions",
    "game_concept_kingdom": "Nation",
    "game_concept_kingdoms": "Nations",
    "game_concept_empire": "United Kingdom",
    "game_concept_empires": "Unions",

    # ---- office and Cabinet
    "game_concept_court": "Office",
    "game_concept_courts": "Offices",
    "game_concept_court_desc": "Every politician has an $game_concept_court$: the [unlanded|E] people who work for them.\n\nThese [courtiers|E] are their family, advisers, researchers and hangers-on.",
    "game_concept_courtier": "Staffer",
    "game_concept_courtiers": "Staff",
    "game_concept_council": "Cabinet",
    "game_concept_council_desc": "The $game_concept_council$ is the leader's top team of [councillors|E], each running a department. They can be given important [councillor_tasks|E].",
    "game_concept_councillor": "Minister",
    "game_concept_councillors": "Ministers",
    "game_concept_chancellor": "Foreign Secretary",
    "game_concept_chancellors": "Foreign Secretaries",
    "game_concept_chancellor_desc": "The $game_concept_chancellor$ is the [councillor|E] in charge of diplomacy, abroad and with the rest of the [realm|E].",
    "game_concept_steward": "Chancellor of the Exchequer",
    "game_concept_stewards": "Chancellors of the Exchequer",
    "game_concept_steward_desc": "The $game_concept_steward$ is the [councillor|E] in charge of the economy and the [domain|E]: [taxation|E], spending and [development|E].",
    "game_concept_marshal": "Home Secretary",
    "game_concept_marshals": "Home Secretaries",
    "game_concept_marshal_desc": "The $game_concept_marshal$ is the [councillor|E] in charge of security: the police, borders and keeping order.",
    "game_concept_spymaster": "Chief Whip",
    "game_concept_spymaster_desc": "The $game_concept_spymaster$ is the [councillor|E] who keeps the party in line and knows everyone's secrets. Beware a disloyal Chief Whip: they can easily hide, or join, a plot against you.",
    "game_concept_court_chaplain": "Leader of the House",
    "game_concept_court_chaplains": "Leaders of the House",
    "game_concept_court_chaplain_possessive": "Leader of the House's",
    "game_concept_court_chaplains_possessive": "Leaders of the House's",
    "councillor_chancellor": "Foreign Secretary",
    "councillor_chancellor_possessive": "Foreign Secretary's",
    "councillor_steward": "Chancellor of the Exchequer",
    "councillor_steward_possessive": "Chancellor of the Exchequer's",
    "councillor_marshal": "Home Secretary",
    "councillor_marshal_possessive": "Home Secretary's",
    "councillor_spymaster": "Chief Whip",
    "councillor_spymaster_possessive": "Chief Whip's",
    "councillor_court_chaplain": "Leader of the House",
    "councillor_court_chaplain_possessive": "Leader of the House's",
    # Catholic characters (all of Westminster's) get the bishop-title variant of the learning seat.
    "councillor_actual_bishop_title": "Leader of the House",
    "councillor_actual_bishop_title_possessive": "Leader of the House's",
    "COUNCIL_WINDOW_TITLE_GENERIC": "cabinet",
    "court": "office",
    "courtier": "staffer",

    # ---- HUD buttons and window titles
    "MY_REALM_BUTTON": "#T Party#!",
    "MY_REALM": "My Party",
    "MY_REALM_WINDOW_TITLE": "My Party",
    "MILITARY_BUTTON": "#T Security#!",
    "MILITARY": "Security",
    "MILITARY_VIEW": "Security",
    "INTRIGUE_BUTTON": "#T Scandals & Leaks#!",
    "INTRIGUE_VIEW": "Scandals & Leaks",
    "FACTION_BUTTON": "#T Rebellions#!",
    "FACTIONS_WINDOW": "Rebellions",
    "COURT_BUTTON": "#T [SelectLocalization( IsLandlessAdventurer( GetPlayer ), 'Campaign Team', 'Staff')]#!",

    # ---- skills and lifestyles (PLAN.md, decided 2026-10-09)
    "diplomacy": "Charisma",
    "martial": "Security",
    "stewardship": "Economy",
    "intrigue": "Spin",
    "learning": "Policy",
    "prowess": "Stamina",
    "interaction_category_diplomacy": "Negotiation",   # the interaction menu's category, not the skill
    "game_concept_diplomacy": "Charisma",
    "game_concept_diplomacy_skill": "Charisma Skill",
    "game_concept_diplomacy_skill_desc": "$game_concept_diplomacy$ is a [skill|E] for charm, persuasion and deal-making: working a room, winning colleagues round and getting a deal over the line.\n\nIt directly affects the [opinions|E] other characters have of you, and furthers Charisma [schemes|E].\n\nThe corresponding [lifestyle|E] is the [diplomacy_lifestyle|E].",
    "game_concept_intrigue": "Spin",
    "game_concept_intrigue_skill": "Spin Skill",
    "game_concept_intrigue_skill_desc": "$game_concept_intrigue$ is a [skill|E] for working the media and reading people: the briefing, the leak, the story placed in a friendly paper, the plot kept quiet.\n\nIt is mainly used to further, and defend against, Spin [schemes|E].\n\nThe corresponding [lifestyle|E] is the [intrigue_lifestyle|E].",
    "game_concept_prowess": "Stamina",
    "game_concept_prowess_skill": "Stamina Skill",
    "game_concept_martial": "Security",
    "game_concept_martial_skill": "Security Skill",
    "game_concept_martial_skill_desc": "$game_concept_martial$ is a [skill|E] for law and order, defence and crisis management: keeping the streets and the country safe.\n\nThe corresponding [lifestyle|E] is the [martial_lifestyle|E].",
    "game_concept_stewardship": "Economy",
    "game_concept_stewardship_skill": "Economy Skill",
    "game_concept_stewardship_skill_desc": "$game_concept_stewardship$ is a [skill|E] for budgets, the economy and running things. It directly increases [taxation|E], so every leader wants it.\n\nThe corresponding [lifestyle|E] is the [stewardship_lifestyle|E].",
    "game_concept_learning": "Policy",
    "game_concept_learning_skill": "Policy Skill",
    "game_concept_learning_skill_desc": "$game_concept_learning$ is a [skill|E] for ideas and detail: briefs read, bills drafted, select committees survived. It also brings in [piety|E] every month.\n\nThe corresponding [lifestyle|E] is the [learning_lifestyle|E].",
    "diplomacy_lifestyle_name": "Charisma",
    "martial_lifestyle_name": "Security",
    "stewardship_lifestyle_name": "Economy",
    "intrigue_lifestyle_name": "Spin",
    "learning_lifestyle_name": "Policy",

    # ---- clout (dread), pressure (stress), mandate (legitimacy)
    "game_concept_dread": "Clout",
    "DREAD": "Clout",
    "game_concept_stress": "Pressure",
    "STRESS": "Pressure",
    "game_concept_stress_desc": "Characters come under $game_concept_stress$ when they act against their [personality_traits|E]: the loyal backbencher voting against the whip, the honest minister made to defend a bad line.\n\nCharacters under enough Pressure gain a [stress_level|E], with effects on their health that last until they bring it down again.\n\nTime away from Westminster and [activities|E] relieve it.",
    "game_concept_legitimacy": "Mandate",
    # Mandate levels (vanilla: Illegitimate ... Eternal; 6-8 are the mandala government's): the _name keys are
    # customizable localization, the _flavor keys the HUD's
    "legitimacy_level_0_name": "No Mandate",
    "legitimacy_level_1_name": "Shaky",
    "legitimacy_level_2_name": "Accepted",
    "legitimacy_level_3_name": "Secure",
    "legitimacy_level_4_name": "Strong",
    "legitimacy_level_5_name": "Commanding",
    "legitimacy_level_6_name": "Landslide",
    "legitimacy_level_7_name": "Historic",
    "legitimacy_level_8_name": "Unassailable",
    "default_legitimacy_level_0_flavor": "No Mandate",
    "default_legitimacy_level_1_flavor": "Shaky",
    "default_legitimacy_level_2_flavor": "Accepted",
    "default_legitimacy_level_3_flavor": "Secure",
    "default_legitimacy_level_4_flavor": "Strong",
    "default_legitimacy_level_5_flavor": "Commanding",
    "default_legitimacy_level_6_flavor": "Landslide",
    "default_legitimacy_level_7_flavor": "Historic",
    "default_legitimacy_level_8_flavor": "Unassailable",
    "default_legitimacy_level_0": "No [legitimacy|E]",

    # ---- popular revolts
    "peasant_faction": "Protest Movement",
    "populist_faction": "Populist Movement",
    "FACTION_PEASANT_TITLE_NAME": "Protest Movement",
    "FACTION_PEASANT_REVOLT": "Protest Movement",
    "FACTION_POPULIST_REVOLT_TITLE_NAME": "the Populist Movement",
    "peasant_faction_event_troops": "Rioters",
    "populist_faction_event_troops": "Populist Rioters",

    # ---- money text
    "GOLD_TEXT": "£$VALUE|0$",

    # ---- ideology (religion): tools/data/build_ideology.py
    "game_concept_faith": "Ideology",
    "game_concept_faiths": "Ideologies",
    "game_concept_faithpossessive": "Ideology's",
    "game_concept_faith_desc": "An $game_concept_faith$ is a politician's political creed, within a larger [religion|E]. Every character and [county|E] has one: a constituency's Ideology is the lean of its voters, and it drifts towards its MP's.\n\nAn Ideology's [doctrines|E] are its policy positions and its [core_tenets|E] its signature causes. Its [fervor|E] is how fired up its activists are.\n\nPoliticians of different Ideologies like each other less, the more so the further apart their camps are. Anyone can change their mind (the decision Change Your Politics), at a price.",
    "game_concept_religion": "Political Camp",
    "game_concept_religions": "Political Camps",
    "game_concept_religion_desc": "A $game_concept_religion$ groups related [faiths|E]: the Left, the Centre, the Right, the Nationalists and the Unionists. Ideologies of the same or a neighbouring camp are Divergent; left and right are Opposed; nationalists and unionists are Irreconcilable.",
    "game_concept_faith_hostility": "Ideological Distance",
    "game_concept_faith_righteous": "Like-minded",
    "game_concept_faith_righteous_desc": "This [rite|E] shares your politics.\n\n#S Effects:\n#![GetHostilityDescription( '(int32)0' )]",
    "game_concept_faith_astray": "Divergent",
    "game_concept_faith_astray_desc": "This [rite|E] is in your political camp or a neighbouring one: you disagree on details.\n\n#S Effects:\n#![GetHostilityDescription( '(int32)1' )]",
    "game_concept_faith_hostile": "Opposed",
    "game_concept_faith_hostile_desc": "This [rite|E] is across the main political divide, left against right.\n\n#S Effects:\n#![GetHostilityDescription( '(int32)2' )]",
    "game_concept_faith_evil": "Irreconcilable",
    "game_concept_faith_evil_desc": "This [rite|E] wants the opposite constitutional future: nationalist against unionist.\n\n#S Effects:\n#![GetHostilityDescription( '(int32)3' )]",
    "game_concept_rite_desc": "In Westminster every [faith|E] has a single $game_concept_rite$ of the same name: the ideology itself, with its [core_tenets|E] and [doctrines|E]. They are fixed: politicians change their minds, not their ideology's.",
    "game_concept_faith_hostility_desc": "All [faiths|E] have a relation towards each other that is determined by how far apart their politics are.\n\nIdeologies of the same or a neighbouring [religion|E] disagree on details; left and right are opposed; nationalists and unionists are irreconcilable.\n\nThe following relations exist: [faith_righteous|L], [faith_astray|L], [faith_hostile|L], and [faith_evil|L].",
    "faith_conversion_recently_converted": "You recently changed your [faith|E] and cannot change it again yet",
    # the ideology map mode and its tooltip
    "MAPMODE_RELIGIONS": "#T Ideologies\n#!Shows the [faith|E] of each [county|E] on the map: the lean of its voters.\n\nIn striped areas the Constituency and the [top_liege|E] have different Ideologies.",
    "FAITHS_MAP_MODE_TOOLTIP": "#T Constituency's Ideology: [ROOT.Province.GetCounty.GetRite.GetNameNoTooltip]#!\n\nMP's Ideology: #high [ROOT.Province.GetCounty.GetTitle.GetHolder.GetRite.GetNameNoTooltip]#![ROOT.Province.Custom('GetTopLiegeRiteLine')][AddLocalizationIf( Not( EqualTo_string( ROOT.Province.GetCounty.GetTitle.GetHolder.GetFaith.GetNameNoTooltip, ROOT.Province.GetCounty.GetRite.GetFaith.GetNameNoTooltip ) ), 'FAITHS_MAP_MODE_TOOLTIP_FAITH_MISMATCH' )][ROOT.Province.GetBeingConvertedInClericalRegionText]",
    "FAITHS_MAP_MODE_TOOLTIP_TOP_LIEGE_RITE": "\nPrime Minister's Ideology: #high [county_top_liege.GetRite.GetNameNoTooltip]#!",
    "FAITHS_MAP_MODE_TOOLTIP_FAITH_MISMATCH": "\n\n@alert_icon! #alert_trial The MP's Ideology differs from the constituency's#!",
    "MAP_COUNTY_HOLDER_RIGHT_CLICK": "#I Right-click to select the constituency's MP#!",
    "faiths_MAP_MODE_TOOLTIP_CLICK_TO_SELECT": "\n#I Click to select [PROVINCE.GetCounty.GetRite.GetNameNoTooltip]#!",
    "game_concept_tenet_knowledge": "Policy Knowledge",
    "game_concept_tenet_knowledge_desc": "Politicians don't know every other ideology's thinking in detail.\n\nKnowing all the $game_concept_core_tenets$ and $game_concept_doctrines$ of an $game_concept_rite$ makes changing your mind to it easier.\n\nAll [core_tenets|E] and [doctrines|E] of your own [faith|E] are known to you. More can be learnt from [spouses|E], [friends|E] and [activities|E].",
    "game_concept_mainline_rite": "Ideology",       # "Liberal Ideology" (every ideology is its own mainline rite)
    "game_concept_mainline_rites": "Ideologies",
    "game_concept_head_of_rite": "Leading Voice",
    "game_concept_head_of_rite_desc": "The leading [character|E] of an [rite|E]: the politician who leads the most of its [counties|E].",
    "game_concept_spiritual_fulfillment": "Personal Conviction",
    "game_concept_spiritual_fulfillment_desc": "$game_concept_spiritual_fulfillment$ is how at ease a [character|E] is with their own politics. It rises and falls with their [traits|E] and with how they act.",
    "game_concept_spiritual_fulfillment_level": "Conviction Level",
    "game_concept_spiritual_fulfillment_levels": "Conviction Levels",
    "game_concept_spiritual_fulfillment_level_desc": "A [character_possessive|E] [spiritual_fulfillment|E] is divided into $game_concept_spiritual_fulfillment_levels$, each with its own effects.",
    "default_fulfillment_level_0": "Disillusioned",
    "default_fulfillment_level_1": "Wavering",
    "default_fulfillment_level_2": "Committed",
    "default_fulfillment_level_3": "Dedicated",
    "default_fulfillment_level_4": "True Believer",
    "FERVOR_TT": "#T Conviction: [Faith.GetFervor|2]%\n#!#weak How fired up the [faithpossessive|E] activists and voters are. Constituencies of an Ideology with high [fervor|E] care more about their MP's politics.#!\n\n[Faith.GetYearlyFervorChangeDesc]\n\n[Faith.GetFervorChangelog]",
    "FAITH_VIEW_OTHER_RITES_TITLE": "Other Ideologies",
    "FAITH_VIEW_OTHER_RITES_TT": "#T Other Ideologies#!\n\n#I Click to view other [faiths|E]#!",
    "FAITH_VIEW_FAITH_DETAILS_TT": "#T Compare Ideologies#!\n\n#I Click to view other [faiths|e], their [core_tenets|E] and their [doctrines|E]#!",
    "faith_find_adherent": "Find a Sympathiser",
    "game_concept_fervor": "Conviction",
    "game_concept_fervor_desc": "The $game_concept_fervor$ of an [faith|E] ranges from #V 0#! to #V 100%#!. It measures how fired up its activists and voters are: turnout, volunteers and noise.\n\nHigh $game_concept_fervor$ makes constituencies of the Ideology care more about their MP's politics.",
    "game_concept_doctrine": "Policy Position",
    "game_concept_doctrines": "Policy Positions",
    "game_concept_doctrines_desc": "Policy positions are what an [faith|E] stands for: tax and spending, ownership, immigration, Europe, the Union and civil liberties. Bills that clash with an MP's policy positions make a rebellion likelier.",
}

# Edits to long vanilla values: each (old, new) pair is applied to the vanilla text (the old text must be there),
# then the AUTO substitution runs over the result. For descriptions that need a modern sentence or two but keep
# vanilla's data expressions.
EDITS = {
    "game_concept_dread_desc": [
        ("is a measure of how feared a [ruler|E] is.", "is how much a [ruler|E] is feared: the leader who sacks ministers without blinking, the whip who never forgets a rebellion."),
        ("Rulers increase $game_concept_dread$ by performing cruel and heinous acts such as torturing and executing [prisoners|E].",
         "Politicians gain $game_concept_dread$ by ruthless acts: sackings, purges and making examples of rebels or [prisoners|E]."),
        ("makes it viable to play as a [tyrant|E]", "makes it possible to lead like a [tyrant|E]"),
    ],
    "game_concept_legitimacy_desc": [
        ("is the representation of the right to reign of a [ruler|E].", "is a leader's right to govern in the eyes of the party and the country: the election won, the leadership contest carried, the confidence of the House. A [ruler|E] without one is living on borrowed time."),
    ],
    "game_concept_prowess_skill_desc": [
        ("reflects the Character's aptitude in personal combat.", "reflects a Character's physical and mental endurance: eighteen-hour days, all-night sittings and the campaign trail."),
    ],
    "game_concept_piety_level_desc": [
        ("is a measure of how virtuous and devout they are, as well as their standing with other members of their [faith|E].",
         "is a measure of how much credit they have banked with their party and the establishment, and of their standing with others of their [faith|E]."),
    ],
}

# Explicit keys whose markup intentionally differs from vanilla (checked by hand).
MARKUP_CHANGE_OK = {
    "game_concept_gold_desc", "game_concept_prestige_desc", "game_concept_piety_desc",
    "game_concept_dynasty_prestige_desc", "game_concept_vassal_desc", "game_concept_liege_desc",
    "game_concept_realm_desc", "game_concept_domain_desc", "game_concept_court_desc",
    "game_concept_council_desc", "game_concept_chancellor_desc", "game_concept_steward_desc",
    "game_concept_marshal_desc", "game_concept_spymaster_desc", "game_concept_martial_skill_desc",
    "game_concept_stewardship_skill_desc", "game_concept_learning_skill_desc",
    "game_concept_diplomacy_skill_desc", "game_concept_intrigue_skill_desc", "game_concept_stress_desc",
    "councillor_actual_bishop_title", "councillor_actual_bishop_title_possessive", "default_legitimacy_level_0",
    "COUNCIL_WINDOW_TITLE_GENERIC",
    "game_concept_faith_desc", "game_concept_religion_desc", "game_concept_fervor_desc", "game_concept_doctrines_desc",
    "game_concept_faith_righteous_desc", "game_concept_faith_astray_desc", "game_concept_faith_hostile_desc",
    "game_concept_faith_evil_desc",
    "game_concept_rite_desc", "game_concept_head_of_rite_desc", "game_concept_faith_hostility_desc",
    "faith_conversion_recently_converted", "game_concept_tenet_knowledge_desc", "MAPMODE_RELIGIONS", "FAITHS_MAP_MODE_TOOLTIP", "faiths_MAP_MODE_TOOLTIP_CLICK_TO_SELECT", "game_concept_spiritual_fulfillment_desc",
    "game_concept_spiritual_fulfillment_level_desc", "FERVOR_TT", "FAITH_VIEW_OTHER_RITES_TT",
    "FAITH_VIEW_FAITH_DETAILS_TT",
}

# Which output file an explicit key goes to, when its vanilla file isn't in AUTO_FILES.
EXPLICIT_CATEGORY = {"councillor_actual_bishop_title": "council",
                     "councillor_actual_bishop_title_possessive": "council",
                     "court": "ui", "courtier": "ui", "COUNCIL_WINDOW_TITLE_GENERIC": "ui"}

# ---------------------------------------------------------------------------------------------

LINE = re.compile(r'^\s*([A-Za-z0-9_.\-\']+):\d*\s*"(.*)"\s*(#.*)?$')


def parse_yml(path):
    """Yields (key, value) from a CK3 localization file."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith("l_"):
            continue
        # value = from the first quote after the colon to the last quote on the line
        m = re.match(r'^\s*([A-Za-z0-9_.\-\']+):\d*\s*"', line)
        if not m:
            continue
        rest = line[m.end():]
        end = rest.rfind('"')
        if end < 0:
            continue
        yield m.group(1), rest[:end]


def tokenize(s):
    """Splits a value into (is_markup, text) segments."""
    out, buf, i, n = [], [], 0, len(s)

    def flush():
        if buf:
            out.append((False, "".join(buf)))
            buf.clear()

    while i < n:
        c = s[i]
        j = None
        if c == "[":
            depth, j = 0, i
            while j < n:
                if s[j] == "[":
                    depth += 1
                elif s[j] == "]":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            j = min(j + 1, n)
        elif c == "$":
            k = s.find("$", i + 1)
            j = k + 1 if k > 0 else None
        elif c == "@":
            m = re.match(r"@[A-Za-z0-9_]+!", s[i:])
            j = i + m.end() if m else None
        elif c == "\\" and i + 1 < n:
            j = i + 2
        elif c == "#":
            if s[i + 1:i + 2] == "!":
                j = i + 2
            else:
                m = re.match(r"#[A-Za-z][A-Za-z0-9_;:]*", s[i:])
                if m:
                    j = i + m.end()
                    if s[j:j + 1] == "{":  # #color:{...}
                        depth, k = 0, j
                        while k < n:
                            if s[k] == "{":
                                depth += 1
                            elif s[k] == "}":
                                depth -= 1
                                if depth == 0:
                                    break
                            k += 1
                        j = min(k + 1, n)
        if j is None:
            buf.append(c)
            i += 1
        else:
            flush()
            out.append((True, s[i:j]))
            i = j
    flush()
    return out


def markup(s):
    return [t for is_m, t in tokenize(s) if is_m]


_terms = dict(TERMS)
_pattern = re.compile(
    r"(?<![A-Za-z0-9_\-])(" + "|".join(re.escape(k) for k in sorted(_terms, key=len, reverse=True))
    + r")(?![A-Za-z0-9_\-])")


def _vowel_sound(word):
    return word[:1] in "AEIOaeio" or (word[:1] in "Uu" and not word.lower().startswith(("uni", "us", "eu")))


def substitute(text, hits):
    """Replaces TERMS in plain text, fixing the article in front ("a Knight" -> "an Organiser")."""
    out, pos = [], 0
    for m in _pattern.finditer(text):
        old = m.group(1)
        new = _terms[old]
        before = text[pos:m.start()]
        if new != old:
            hits[old] += 1
            art = re.search(r"(?:^|(?<=[\s(]))([Aa]n?) $", before)
            if art and _vowel_sound(new) != _vowel_sound(old):
                a = art.group(1)
                fixed = (a[0] + "n") if _vowel_sound(new) else a[0]
                before = before[:art.start(1)] + fixed + " "
        out.append(before)
        out.append(new)
        pos = m.end()
    out.append(text[pos:])
    return "".join(out)


def transform(value, hits):
    return "".join(t if is_m else substitute(t, hits) for is_m, t in tokenize(value))


def load_vanilla(game):
    root = game / "localization" / "english"
    keys = {}  # key -> (relpath, value); first definition wins
    for p in sorted(root.rglob("*.yml")):
        rel = p.relative_to(root).as_posix()
        for k, v in parse_yml(p):
            keys.setdefault(k, (rel, v))
    return root, keys


def mod_keys():
    keys = {}
    for p in sorted((MOD / "localization").rglob("*.yml")):
        if p.name.startswith(OUT_PREFIX):
            continue
        for k, _ in parse_yml(p):
            keys.setdefault(k, p.relative_to(MOD).as_posix())
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", type=Path, default=DEFAULT_GAME)
    ap.add_argument("--report", action="store_true", help="list skipped keys and term counts")
    args = ap.parse_args()

    root, vanilla = load_vanilla(args.game)
    taken = mod_keys()
    problems, skipped = [], []
    files = defaultdict(dict)   # category -> key -> (new, old)
    hits = Counter()
    file_cat = {}
    for cat, globs in AUTO_FILES.items():
        for g in globs:
            matched = sorted(root.glob(g))
            if not matched:
                problems.append("AUTO_FILES: nothing matches %s" % g)
            for p in matched:
                file_cat.setdefault(p.relative_to(root).as_posix(), cat)

    # AUTO pass
    for key, (rel, old) in vanilla.items():
        cat = file_cat.get(rel)
        if cat is None or key in EXPLICIT or key in EDITS:
            continue
        new = transform(old, hits)
        if new == old:
            continue
        if key in taken:
            skipped.append((key, taken[key]))
            continue
        if markup(new) != markup(old):
            problems.append("%s: markup changed by the AUTO pass" % key)
            continue
        files[cat][key] = (new, old)

    # SKILLS pass over the rest of vanilla
    for key, (rel, old) in vanilla.items():
        if rel in file_cat or key in EXPLICIT or key in EDITS or SKILL_SCAN_SKIP.search(rel):
            continue
        if not any(not is_m and SKILL_WORDS.search(t) for is_m, t in tokenize(old)):
            continue
        new = transform(old, hits)
        if new == old:
            continue
        if key in taken:
            skipped.append((key, taken[key]))
            continue
        if markup(new) != markup(old):
            problems.append("%s: markup changed by the SKILLS pass" % key)
            continue
        files["skills"][key] = (new, old)

    # EDITS: vanilla text with a few phrases rewritten, then the AUTO substitution
    for key, pairs in EDITS.items():
        if key not in vanilla:
            problems.append("%s: EDITS key not in vanilla" % key)
            continue
        if key in taken:
            skipped.append((key, taken[key]))
            continue
        rel, old = vanilla[key]
        new = old
        for a, b in pairs:
            if a not in new:
                problems.append("%s: EDITS text not found: %s" % (key, a))
            new = new.replace(a, b)
        new = transform(new, hits)
        if markup(new) != markup(old):
            problems.append("%s: markup changed by EDITS" % key)
            continue
        files[file_cat.get(rel) or "ui"][key] = (new, old)

    # EXPLICIT values
    for key, new in EXPLICIT.items():
        new = new.replace("\n", "\\n")	# a line break in the Python source is a \n in the localization
        if key not in vanilla:
            problems.append("%s: EXPLICIT key not in vanilla" % key)
            continue
        if key in taken:
            skipped.append((key, taken[key]))
            continue
        rel, old = vanilla[key]
        if key not in MARKUP_CHANGE_OK and key != "COURT_BUTTON" and markup(new) != markup(old):
            problems.append("%s: markup differs from vanilla: %s vs %s" % (key, markup(new), markup(old)))
        if key == "COURT_BUTTON" and len(markup(new)) != len(markup(old)):
            problems.append("COURT_BUTTON: markup differs")
        # every [concept|E] must be a real concept
        for c in re.findall(r"\[([a-z_]+)\|E\]", new):
            if "game_concept_" + c not in vanilla:
                problems.append("%s: unknown concept [%s|E]" % (key, c))
        for ref in re.findall(r"\$([A-Za-z0-9_]+)\$", new):
            if ref not in vanilla and not ref.isupper():
                problems.append("%s: unknown reference $%s$" % (key, ref))
        cat = EXPLICIT_CATEGORY.get(key) or file_cat.get(rel) or "ui"
        files[cat][key] = (new, old)

    for cat in files:
        for key, (new, old) in files[cat].items():
            if new.count('"') != old.count('"'):
                problems.append("%s: contains a double quote" % key)

    if problems:
        print("\n".join(problems))
        sys.exit(1)

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob(OUT_PREFIX + "*_l_english.yml"):
        old.unlink()
    total = 0
    for cat in sorted(files):
        lines = ["l_english:",
                 " # Generated by westminster/tools/ui/build_terms.py from the installed game's English "
                 "localization. Don't edit: change the script and re-run it."]
        for key in sorted(files[cat]):
            lines.append(' %s: "%s"' % (key, files[cat][key][0]))
        path = OUT / ("%s%s_l_english.yml" % (OUT_PREFIX, cat))
        path.write_text("﻿" + "\n".join(lines) + "\n", encoding="utf-8")
        total += len(files[cat])
        print("%-45s %5d keys" % (path.relative_to(MOD).as_posix(), len(files[cat])))
    print("total %d keys, %d explicit; %d skipped (defined by the mod)" % (total, len(EXPLICIT), len(skipped)))
    if args.report:
        for key, where in sorted(skipped):
            print("skipped %s (in %s)" % (key, where))
        for term, n in hits.most_common():
            print("%6d  %s -> %s" % (n, term, _terms[term]))


if __name__ == "__main__":
    main()
