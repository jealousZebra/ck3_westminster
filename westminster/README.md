# Westminster

A total-conversion CK3 mod about British politics. Rise from campaigner to Prime Minister on a map of the 650
Westminster constituencies. Play the 1979 or 2024 start; future releases will add more prime-ministerial eras and
deepen the House of Lords, mayors, councils and devolved politics.

| | |
|---|---|
| Status | 0.5.4 public beta on Steam Workshop. The 1979 and 2024 starts, the Commons, elections, campaigns, careers, parties and the newspaper interface are playable. In-game localization: English, French, German, Japanese, Korean, Polish, Russian, Simplified Chinese and Spanish. |
| Release | [workshop/PUBLISHING.md](workshop/PUBLISHING.md): Workshop page text, thumbnail, screenshots; `tools/release.sh <version>` checks and zips |
| Game | CK3 1.20 (any platform; the in-game test tools are macOS-only) |
| Prefix | `wm_` (files, variables, effects, localization keys) |
| Design | [PLAN.md](PLAN.md): decisions, how CK3 systems map to British politics, milestones |
| Credits | [westminster/CREDITS.txt](westminster/CREDITS.txt) (ships with the mod) and [NOTICE.md](../NOTICE.md) |

**Real names, fictional events.** Real politicians, other public figures and the royal family appear under their
real names. All events are generic and fictional, and nothing in the mod says or implies anything about any real
person. Some birth dates are approximate, and MPs' spouses and families are invented. The mod isn't affiliated with
Parliament, any political party or the Royal Household. Murder, abduction and seduction schemes are switched off
(`tools/data/build_safeguards.py`), so no real person can be their target.

For source changes, start with the [modding guide](../docs/modding.md) and [contribution workflow](../CONTRIBUTING.md).

## 18 October 2026 update: movement and historical eras

The 18 October upload adds the 1945 Attlee, 1997 Blair, 2010 Cameron coalition and 2016 May starts, alongside
1979 and 2024. The descriptor remains 0.5.4. Fresh-start smoke tests pass; longer campaign and Windows validation of the new content remain.

- Build Your Movement: membership drives, donors, national publicity, targeted local branches, candidate recruitment
  and an invitation to a disillusioned MP to defect. All six founded-party slots participate in elections, candidate
  selection, seat counts, government formation, results and the polls/chamber panel.
- Your Political Career: constituency surgeries and local projects build an incumbent's personal vote; a backbench
  public-service caucus changes rebellion pressure; ministers can publish delivery plans and face a six-month review.
- Press Desk: editorial relationships, interviews, endorsements, and a fictional leaked-draft event with public or private responses. Committee inquiries build standing and strengthen the public-service caucus.
- Government Programme: fiscal room, borrowing, debt pressure, public services, economic confidence and negotiated
  backbench concessions. The historical opening programmes go through an ordinary Public Services Bill.
- Brexit: a 2016 mandate, a choice between close alignment and regulatory independence, funded negotiating rounds,
  a parliamentary settlement, defeat/retry and transition. These are simplified gameplay outcomes, not economic forecasts.
- Era-specific likeness DNA and bookmark caches for the major historical politicians. Underlying faces remain stable
  across the new eras; the DNA is an approximation using CK3's portrait system.

Historical constituencies are mapped to the fixed modern map. The 1945 map has ten explicitly notional MPs, 1997
keeps nine real MPs unlanded, and the dated 2010/2016 snapshots each contain one notional map filler. Most minor
characters' birth dates remain approximate. English copy is used as a fallback for new content in the other eight
languages. These limitations remain in the published beta.

Checks: `python3 tools/data/test_eras.py` from this directory audits the map, featured portraits and history/DNA
references. Validation on 18 October 2026: the combined suite passed all 30 engine checks. Fresh campaigns in 1945, 1997, 2010 and 2016 passed all 26 opening assertions (prime minister, 650 seats, governing state, cabinet, polling anchor, monarch, coalition and Brexit mandate where applicable), with no failures or crashes observed. The existing 1979 start also loaded successfully. Eight historical/localization/portrait audits and eight stability tests pass; static validation covers 864 files in nine languages. These are opening smoke tests, not full campaign or Windows certification.

The combined 30-check in-game suite is `tools/ck3_test/gen_expansion.py`; its components are `gen_movement.py` and `gen_governing.py`. Fresh-start checks are in `gen_eras.py` (the last
requires a fresh campaign in each new start). Generated map/interface textures are ignored; source art and exported bookmark portraits are committed. Historical bookmark portrait caches now come from CK3 exports, including engine entity/tags data; the generator rejects missing exports instead of inventing incomplete caches. Attlee uses the moustache accessory.

Build order after regenerating the 2024 data: `build_1979.py`, `build_eras.py`, `build_movement.py`,
`build_governing.py`, `build_press.py`, `build_seat_leans.py`, then `build_likenesses.py`. Run `tools/ui/build_ui.sh` to rebuild the
bookmark maps/caches and the polls UI. All data generators live in `tools/data/`.

## Foundations (the technical spikes)

These were the first experiments, proving that CK3 can model each piece. `tools/run_spikes.sh` still tests every one
in the game (`tools/ck3_test/gen_spikes.py`).

| Spike | Result |
|---|---|
| a. Map | The 650 seats from ONS 2024 boundaries, 60 sea zones, at 160 m per pixel (6144 × 8192). Both bookmarks load and the realm map shows the UK. |
| b. Parties | A party is a landless kingdom-tier title. When the leader dies, the party's MPs elect the next one with a custom election (`wm_party_leadership`). They vote for the colleague they like and rate. |
| c. General election | All 650 seats re-elected in one go, each MP serving their party leader. About 2 seconds; the second election, with incumbents, under 1 second. |
| d. Peerages | Landless county-tier titles held by people with no seat. A life peerage ends with the holder; a hereditary one passes to the heir. |
| e. Mayors | A mayoralty is a landless duchy-tier title. A mayor needs no seat and serves their party leader. |
| f. Unlanded careers | A hopeful plays as a landless adventurer (camp = campaign team) and takes a party's "seek selection" task contract. Finishing it puts them on the shortlist. |
| g. Councils | A council is a landless title storing seats per party. A council election sets control: a majority, otherwise no overall control. |
| h. Devolved governments | A First Minister holds a landless kingdom-tier title (the Scottish Government). Northern Ireland's First Minister and deputy share power as a co-rulership diarchy. |

## The map

Built by `tools/map/build_map.py` in about a minute: 1,597 town baronies in the 650 seats, the 46 ITL2 areas as
duchies, Ireland, the Isle of Man, the Channel Islands and the near Continent as scenery, 60 named sea zones,
Copernicus terrain, and generated terrain materials, colour map, paper map and water colour. 6144 x 8192 pixels at
160 m each.

## The 2024 bookmark

`tools/data/build_2024.py` builds the start on 5 July 2024 from UK Parliament and Wikidata data (sources and
licences in [data/README.md](data/README.md)):

- **The 650 MPs** elected on 4 July 2024 (`history/characters/wm_2024_mps.txt`, ids `wm_mp_<seat>`), each in their
  party's house (parties are houses, and names are whole names: see PLAN.md), a culture by nation, and their party as `var:wm_party` (set by a history
  `effect` on the start date). The Speaker has the flag `wm_speaker` and no party.
- **13 parties** that won seats (`common/landed_titles/10_wm_parties.txt`), each held by the leader of its MPs at
  Westminster and elected by them (`wm_party_succession_law`). Sinn Féin's is held by Mary Lou McDonald, who isn't an
  MP. Party leaders, independents and the Speaker serve the Prime Minister; every other MP serves their party leader.
- **Keir Starmer** holds the United Kingdom, its four nations, the Labour Party and Holborn and St Pancras. The
  devolved governments go to John Swinney, Michelle O'Neill and Vaughan Gething (`k_gov_wales`, new in
  `31_wm_wales_gov.txt`).
- The bookmark features Starmer, Rishi Sunak, Ed Davey and Sam Carling, the youngest new MP. The new-game screen
  shows them by their seats on a newspaper election map of the 2024 result, with portraits from their likenesses
  (`tools/ui/build_bookmark_screen.py`).

## The 1979 bookmark

`tools/data/build_1979.py` builds the start on 4 May 1979 using the same 650-seat map:

- Margaret Thatcher holds the United Kingdom and leads her first Cabinet; James Callaghan leads Labour and David
  Steel leads the Liberals, with Elizabeth II holding the Crown.
- The historical Commons is mapped to the closest appropriate modern constituencies, with every starting seat kept
  inside the United Kingdom.
- The 1979 result supplies the opening election and polling baseline.
- Thatcher, Callaghan, Steel, Michael Foot, Geoffrey Howe and other significant figures have recognisable CK3
  character models and dedicated bookmark presentation.

## Gameplay so far

- **Parties are houses:** the 13 parties that won seats in 2024 are landless titles, and each is also a house with
  an emblem inspired by its real symbol. Cross the Floor to another party, or Found a Party (six spare slots with
  made-up emblems). The Family tab lists your colleagues.
- **Leadership contests (shortlist ballots):** MPs nominate (15% of the party's MPs; 20% for a challenger), then the
  members vote between the top two. Contests follow a leader's death, a heavy election defeat, an AI challenge or a
  player's "Challenge for the Leadership".
- **The Speaker** is elected by all MPs in an exhaustive secret ballot after a general election at which the Speaker
  stands down, or when the chair is empty. The Speaker leaves their party.
- **Party wings:** Labour (Left, Soft Left, Centrists) and the Conservatives (One Nation, Free-marketeers,
  Traditionalists). Keep each wing's approval with cabinet places and policy, or face resentment, rebellions and,
  in the end, a leadership challenge. Real MPs' wings follow their ideology.
- **The Cabinet** is drawn from the PM's party (or coalition partner); ministers from other parties are dismissed
  and empty posts filled with the best-qualified colleague.
- **Riots** (replacing vanilla's peasant and popular revolts, whose factions are switched off):
  - a riot breaks out in a seat, most often where people are unhappy, and makes a demand: the cost of living, a
    minister's resignation, an election or a U-turn;
  - the local MP can talk the crowd down, back them or keep quiet;
  - the protesters then march on Westminster, where the Prime Minister can concede, negotiate or send in the police.
- **The Crown:** the monarch holds a ceremonial title (`k_wm_crown`) outside the PM's realm, and the royal family is
  flavour. "Speak Out Against MP" costs 1,500 prestige and has a 10-year cooldown, so it's rare. It damages the MP,
  annoys their party leader and the PM, and the MP can bite their tongue or hit back.
- **Elections:**
  - polls for 13 parties drift monthly, pulled by the PM's standing, riots and mid-term blues;
  - Parliament is dissolved after 58 months, or early when the PM calls an election (the AI does when ahead);
  - each seat is decided by swing from its 2024 result, so a new party leader becomes PM if their party is largest;
  - by-elections follow an MP's death, and every player gets a front-page result ("LABOUR LANDSLIDE", "HUNG
    PARLIAMENT");
  - **disputed results:** a seat won by under one point can go to a recount (it may be overturned) or an election
    court (it may order a by-election); contesting a clear defeat costs profile and political capital and can start riots, and a PM can
    even refuse to concede;
  - **the working majority** is tracked live: by-election losses, defections and lost whips shrink it, a run of
    by-election defeats hurts the PM, and losing the majority brings a motion of no confidence.
- **The House of Commons:**
  - the PM introduces bills (finance, public services, reform, emergency powers);
  - the Chief Whip forecasts the vote, and the PM can whip hard or concede;
  - MPs vote by party, wing and loyalty; three rebellions lose an MP the whip;
  - the Leader of the Opposition can table a motion of no confidence, and losing it forces an election.
- **Coalitions:**
  - in a hung parliament the largest party negotiates;
  - partners are scored by seats and left-right distance (the 2010 Con-LD and 2017 Con-DUP deals come out as
    history had them);
  - a coalition makes the junior leader Deputy PM (a diarchy), and their MPs take the government whip;
  - confidence-and-supply partners back only the budget and confidence votes;
  - deals can collapse.
- **Campaigns and conferences:**
  - weekly campaign choices: a rally, a TV debate, a policy launch, door-knocking, and generic gaffes;
  - each party's autumn conference: the leader's speech, fringe meetings, plotting and leadership rumblings.
- **The career ladder** for characters without a seat:
  - jobs (canvassing, fundraising, speechwriting, research) build Party Standing;
  - the candidate assessment leads to the approved list, then a selection contest (hustings and the members'
    vote);
  - the selected candidate becomes the MP if their party wins the seat at a general election or by-election;
  - the 2024 bookmark has a playable young activist, Jess Okafor (fictional).
- **Public trust** (0-100): riots, U-turns, broken promises, scandals and dirty campaigns wear it down; popular
  bills, kept promises and clean campaigns build it up. Low trust means more riots, lower turnout and gains for small
  parties; high trust helps the government.
- **Campaign spending:** pay monthly for a press campaign for your party, or a smear campaign against a rival party
  that can backfire into a scandal; party leaders can call in a favour from a rival leader.
- **Devolution:** independence support and devolved powers for Scotland, Wales and Northern Ireland, referendum
  requests, devolving or clawing back powers, and Stormont's collapse and restoration.
- **The State of the Parties panel** (newspaper button on the left): the latest poll and public trust, the Commons
  seat chart (government and opposition benches facing each other, with the majority line) and a poll tracker.
- **Ideology replaces religion:** political camps (Left, Centre, Right, Nationalist, Unionist) hold 15 ideologies,
  with policy positions as doctrines and signature causes as tenets. Ideologies of the same or a neighbouring camp
  are mildly at odds, left and right are opposed, and nationalists and unionists are irreconcilable. Real MPs take
  an ideology of their own only where a self-declared caucus list shows it (the Socialist Campaign Group, the One
  Nation caucus, the ERG, the Common Sense Group, the New Conservatives, the Free Market Forum); otherwise their
  party's, with a little variation (`tools/data/build_ideology.py`, `build_2024.py`). The royal family, spouses and
  the Speaker are "Not Stated". Seats start with the 2024 winner's ideology and drift towards their MP's (faster with
  low trust and riots). "Change Your Politics" converts you, at a price. There are no holy wars, heresy trials,
  religious heads or pilgrimages. Vanilla's murder, abduction and seduction schemes are switched off, so no real
  person can be targeted.
- **Wording:** 2,109 interface strings use modern terms (`tools/ui/build_terms.py`): Funds, Profile, Political Capital,
  Party Brand, Clout, Pressure and Mandate for the currencies; Charisma, Economy, Security, Spin, Policy and Stamina
  for the skills; Backbenchers, Party Leader, and the Cabinet with a Foreign Secretary, Chancellor of the Exchequer,
  Home Secretary and Chief Whip. A hopeful's standing with their party (`var:wm_standing`) is shown as Party Standing.
- **Vanilla events are removed** (every `events/` folder is replaced), so no medieval events pause the game.

All in-game tests run from `tools/run_spikes.sh`: the spikes (`tools/ck3_test/gen_spikes.py`) and the gameplay
suites `gen_gameplay.py` (riots and the Crown), `gen_commons.py`, `gen_elections.py`, `gen_coalitions.py`,
`gen_campaign.py`, `gen_career.py`, `gen_parties.py`, `gen_politics.py` (trust, campaign spending, wings,
devolution, faith), `gen_leadership.py` (leadership contests and the Speaker), `gen_majority.py` (disputed results
and the working majority) and `gen_ideology.py` (ideologies, hostility, wings, seats, Change Your Politics, drift). See "Setup, install and test" below.

## The look: a modern newspaper

- **Fonts:** Playfair Display for headlines and Source Serif 4 for text. They replace the medieval fonts at vanilla's
  paths.
- **Colours:** dark ink on newsprint, with one red accent and no text glows (`gui/preload/textformatting.gui`).
- **Interface textures** (`tools/ui/build_theme.py`):
  - the UI skin (`gfx/interface/skinned` and every culture's skin) redrawn as newsprint, with ornaments turned into
    plain rules;
  - buttons, HUD, tooltips and frames recoloured as a "newsprint negative".
- **Main menu** (`tools/ui/build_frontend.py`): a masthead panel over a photo of Westminster; the 3D medieval
  portraits are hidden.
- **Pictures** (`tools/ui/fal_images.py`): AI-generated press-photo style images (FLUX.1 [dev] through fal.ai)
  replace the main menu backdrop, the loading and pause screens, the council, decisions, faction and campaign
  scenes. The prompts are in `art/fal/prompts.json` and the generated images are cached in
  `art/fal/`, so a build needs no network. Only a new or changed prompt calls fal.ai, with the API key from `$FAL_KEY`
  or `~/.config/fal/key` (never in the repo). `tools/ui/build_party_arms.py` works the same way for the party
  emblems.
- **Flags** (`tools/ui/build_flags.py`): real flags from Wikimedia Commons for the nations, counties and cities that
  have one (cached in `data/raw/flags/`, credited in `westminster/CREDITS.txt`), and a unique generated flag for every
  other title. `tools/ui/build_coa_frames.py` shows coats of arms as flags.
- **New-game screen** (`tools/ui/build_bookmark_screen.py`): the 2024 bookmark's background is an election map
  drawn from the seat boundaries and results (London and Shetland insets, a legend); each featured character stands
  by their seat, and selecting one lights up their party's seats; the bars, buttons and name plates are paper and ink.
- **Elsewhere:** no crowns or cloaks on portraits (`build_portraits.py`), modern event backdrops
  (`build_event_backgrounds.py`), scene lists and loading screens (`build_illustrations.py`), rank names
  (`build_ranks.py`), the Colleagues tab (`build_colleagues.py`), the Cabinet (`build_cabinet.py`) and the Latest
  Poll panel (`build_polls_panel.py`).

`tools/ui/build_ui.sh` runs all of these in the order they depend on, then writes the credits.

## Layout

```
westminster/
  PLAN.md              the design
  westminster/         the mod (generated textures and map images are not in git: build them, see below)
    CREDITS.txt        attribution for data, fonts, pictures and flags (generated by tools/data/build_credits.py)
  westminster.mod      launcher .mod file template; it holds the replace_path lines the game actually reads
  data/                source data: README.md (sources, licences, download commands), ge2024_results.csv,
                       raw/ (downloads, not in git)
  art/fal/             AI-generated source images and their prompts (prompts.json), the cache for the UI tools
  tools/map/           build_map.py (the map and its titles), geo.py, terrain.py, heightmap_pack.py (CK3's packed
                       heightmap format)
  tools/data/          build_1979.py and build_2024.py (the bookmarks, MPs, parties and seats),
                       build_seat_leans.py (party-dependent election and poll script from the 2024 results),
                       build_likenesses.py (portraits of recognisable people), build_game_start.py (vanilla's start-up
                       script without the Middle Ages), build_safeguards.py (schemes switched off),
                       build_credits.py (CREDITS.txt), pdx_script.py (a small Paradox script reader)
  tools/ui/            the interface: build_ui.sh runs every step (see "The look" above)
  tools/ck3_test/      gen_*.py (the in-game test suites), make_save.sh (fresh test save), harness/,
                       saves/ (not in git)
  tools/run_spikes.sh  runs every in-game test suite
  tools/release.sh     release checks, version, dist/westminster_<version>.zip
  art/make_thumbnail.py  thumbnail.png (the Workshop image)
  workshop/            Steam page text, CHANGELOG.md, change notes, PUBLISHING.md
  dist/                release zips (not in git)
```

## Setup, install and test

Everything runs from the repo root. Setup (CK3, Python and `requirements.txt`, `CK3_GAME_DIR`/`CK3_DOCS_DIR`) is in
the [root README](../README.md#setup). The generated files that are in git (script, localization, GUI) are
up to date, but the textures and map images aren't in git, so a clone must be built before it can be played.

```sh
# 1. Download the source data into westminster/data/raw/ (commands in data/README.md)
# 2. Build, in this order (each step reads what the one before wrote)
.venv/bin/python westminster/tools/map/build_map.py          # map_data, titles, province history, localization
.venv/bin/python westminster/tools/data/build_2024.py        # the 2024 bookmark (needs the map's titles)
.venv/bin/python westminster/tools/data/build_1979.py        # the 1979 bookmark and election baseline
.venv/bin/python westminster/tools/data/build_eras.py        # the four new dated starts (after 2024/1979)
.venv/bin/python westminster/tools/data/build_movement.py    # movement script/localization
.venv/bin/python westminster/tools/data/build_governing.py   # career, government programme, Brexit
.venv/bin/python westminster/tools/data/build_press.py       # press and committee script/localization
.venv/bin/python westminster/tools/data/build_seat_leans.py  # election and poll script (needs ge2024_results.csv)
westminster/tools/ui/build_ui.sh                             # the whole interface, flags and CREDITS.txt
# 3. Then, only when their inputs change (each writes its own files)
.venv/bin/python westminster/tools/data/build_likenesses.py  # portraits (rerun build_2024.py after adding people)
.venv/bin/python westminster/tools/data/build_game_start.py  # after a CK3 patch
.venv/bin/python westminster/tools/data/build_safeguards.py  # after a CK3 patch
.venv/bin/python westminster/tools/data/build_stability.py  # map-compatible character pools and legacy tracks
# 4. Install into the launcher (writes the .mod file with your clone's path) and enable it there
python3 common/tools/install_mod.py westminster
# 5. Check
python3 common/tools/ck3_checks.py static westminster/westminster
```

After rebuilding the map, boot Westminster once and run
`.venv/bin/python westminster/tools/map/build_map_support.py --import-locators` to save CK3's generated building,
army and activity anchors into the mod. The map builder writes the map-sized BGRA winter lookup; release checks
require both it and the locators. `tools/data/test_stability.py` checks regressions in startup filtering and
localization validation. The mod replaces `history/struggles` and `history/situations` so vanilla's medieval and
Asian situations cannot start against Westminster's provinces. The stability generator also retains vanilla's
cached bookmark portrait data, which Windows streams behind the photo menu even when the portrait widgets are
hidden. Keep `common/bookmark_portraits/wm_vanilla_frontend_portraits.txt` in releases and regenerate it after a
game update; this also works with older launcher replacement settings.

Copies of the game's own files (GUI layouts, council positions, event backgrounds, portrait modifiers, the start-up
script, schemes) are made from your installed game by the scripts above, so rerun them after a CK3 patch. Their
first line names the game file and the script.

In-game tests (macOS; CK3 closed, Steam running; see [docs/ck3-testing.md](../docs/ck3-testing.md)):

```sh
westminster/tools/ck3_test/make_save.sh    # a fresh 2025 test save, after changing titles or history
westminster/tools/run_spikes.sh            # every suite, then the error-log check
```

`make_save.sh` starts a new game by clicking the main menu at fixed points given as fractions of the screen. They
were measured full-screen on a 2560 × 1664 MacBook display with the game's interface scale at 0.8, so check them
(with `common/ck3_test/session.sh`) on any other screen. To run one suite, run its generator and `run_test.sh` as each `gen_*.py` docstring shows, e.g.
`gen_parties.py`.

New-map lessons (crashes, hangs and their fixes) are in [docs/ck3-modding-notes.md](../docs/ck3-modding-notes.md).
