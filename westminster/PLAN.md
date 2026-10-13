# UK politics: plan (draft)

Name: **Westminster** (decided). A total-conversion CK3 mod about British politics. The player
**rises as one politician**: from candidate or backbencher, through ministerial office, to Prime Minister. They build a
political family along the way. The map is the UK's Westminster constituencies.

Status: **0.5.1 public beta**. The 1979 and 2024 bookmarks, nine in-game languages, dark modern interface, elections,
the Commons and landless political careers are playable; see README.md for the current feature list. Decisions
marked **(decided)** came from the owner. The rest are proposals to agree before building.

## Decisions so far

- **(decided)** Bookmarks: one per Prime Minister from Neville Chamberlain (1937) onwards. Start with **2024**
  (Starmer's first government) and work backwards later.
- **(decided)** Real people under their real names. Events are neutral: scandals, crimes, affairs and illness are
  generic random events, **never scripted against a named living person**. A real person only becomes involved if the
  game's randomness happens to pick them.
- **(decided)** A new map of the Westminster constituencies.
- **(decided)** The player rises as one politician. It plays as personal and dynastic CK3, not a management game.
- **(decided)** The title mappings below: parties as kingdom-tier titles, ideology as faith, the PM holding the UK
  title.
- **(decided)** The **House of Lords** is in the game.
- **(decided)** **Mayors** are in the game.
- **(decided)** **Every bookmark uses the 2024 map** of 650 seats. Older bookmarks put each historical MP in the
  nearest 2024 seat.
- **(decided)** **Unlanded roles are playable**: candidates, councillors, activists, party staff and more. They can
  aspire to become MPs or peers.
- **(decided)** **The devolved parliaments are in the game**: the Scottish Parliament, the Senedd and the Northern
  Ireland Assembly, each with its First Minister.
- **(decided)** **Councils have real control**: council elections, party control of each council, council leaders,
  and council powers.
- **(decided)** **About 100 peers** in the 2024 bookmark: the notable real ones plus invented ones.
- **(decided)** **Some satire**: gaffes, tabloid headlines, absurd honours. It's never aimed at a named living person.

## Core idea: what CK3 things become

CK3 is about people, families and titles. British politics is about people, parties and seats. These are the
proposed mappings.

| CK3 | Becomes | Why it fits |
|---|---|---|
| County (title) | **A constituency** (650 in 2024) | The holder is the **MP**. Losing an election means losing the title. |
| Barony / province | Areas within a constituency (towns, wards), drawn from real geography | Counties need baronies. They also give the map local texture. |
| Duchy | **County or city area** (Greater Manchester, Kent, Glasgow…) | Groups seats; the regional party machine; future **mayoralties**. |
| Kingdom | **England, Scotland, Wales, Northern Ireland** | The devolved governments (First Ministers) can be playable later. |
| Empire | **The United Kingdom**, held by the **Prime Minister** | Becoming PM means holding the top title: the end goal. |
| Monarch | **The Crown**: a landless kingdom-tier title (`k_wm_crown`), not the PM's. A figure who appoints the PM, grants peerages and opens Parliament, and very rarely speaks out (see [The Crown](#the-crown)) | Kept out of the hierarchy, like an officiant. |
| Landless titles (`landless = yes`; 1.20 noble-family titles are county-tier landless titles) | **Peerages**, **party titles**, **mayoralties** | They belong to no land, so a peer or mayor needn't be an MP. A hereditary peerage passes down; a life peerage is destroyed on the holder's death. |
| Landless adventurer government (1.20) | **Unlanded careers**: candidate, activist, councillor, party staffer, journalist, union official, lobbyist | Playable without land. The camp becomes an office or campaign, followers become the team, provisions become campaign funds, and task contracts become jobs (canvassing, speechwriting, fundraising, research). |
| Liege / vassal | **Party leader / MP**. MPs are vassals of their party leader, and party leaders sit under the PM. | Party discipline = vassal opinion; defection = changing liege. |
| Landless kingdom-tier titles | **Political parties** (Labour, Conservative, Lib Dem, SNP, Reform, Green, Plaid, DUP, Sinn Féin…) | The leader holds the party title. A **leadership election** is CK3's elective succession, with the party's MPs as electors. |
| Faith | **Ideology** (see "Ideology replaces religion") | Religions are political camps, faiths are ideologies, doctrines are policy positions, conversion is changing your mind. |
| Culture | **Nation and region** (Scottish, Welsh, Northern Irish, Northern English, Londoner…) | Drives regional voting and local candidates' appeal. |
| Dynasty / house | **Parties** (decided 2026-10-08): each party is a dynasty with one house, and its emblem is the house shield. The royal family stays a family. | Party membership shows everywhere a house does; crossing the floor is changing house, and a player can found a party. |
| Council | **Cabinet**: Chancellor, Foreign, Home, Defence… | Real offices the PM appoints, with skills that matter. |
| Court positions | **Junior ministers, whips, special advisers, PPS** | A ladder of small appointments for a rising MP. |
| Gold / prestige / piety | **Funds / Profile / Political Capital** | Profile is fame. Political Capital is credit with the party, spent on asks and favours. (Decided 2026-10-09.) |
| Renown / dread / stress / legitimacy | **Party Brand / Clout / Pressure / Mandate** | Renown is the party's reputation (parties are houses). (Decided 2026-10-09.) |
| Skills: diplomacy, stewardship, martial, intrigue, learning, prowess | **Charisma, Economy, Security, Spin, Policy, Stamina** | Each with its own modern icon. (Decided 2026-10-09.) |
| Legitimacy (1.20) | **Mandate** of the PM and government | Low mandate → leadership challenges and early elections. |
| Schemes | **Political schemes**: build a following, plot a leadership challenge, leak to the press, smear, court a donor | CK3's best feature for "rise as one politician". |
| Secrets and hooks | **Scandals and favours owed** | Expenses, affairs, leaks. Hooks = "you owe me". |
| Factions | **Rebellions and pressure groups**: backbench revolts, leadership challenges, splits | Vanilla factions, with the war part replaced. |
| Struggles / situations | **Big political arcs**: Brexit, Scottish independence, the Troubles, a cost-of-living crisis | Multi-phase situations with catalysts. Each bookmark gets its own. |
| Activities | **Party conference, PMQs, campaign tour, state visit, by-election campaign** | Vanilla activity system with new phases. |
| Lifestyles and perks | **Political careers**: Orator, Policy wonk, Whip, Fixer, Media darling | Reskinned focus trees. |
| Traits | Existing personality traits, plus new ones: Eurosceptic, Unionist, Media-savvy, Careerist, Gaffe-prone… | |
| Wars | **Not used.** Warfare is turned off (no casus belli). Real wars (WWII, the Falklands) become situations. | |
| Great projects | **Infrastructure and big policy**: HS2, NHS founding, North Sea oil | A long build with political payoff. |
| Diarchies / regencies (1.20) | **Coalitions and confidence-and-supply** (2010 coalition, 2017 DUP deal) | Two people sharing power. |

### House of Lords

**(decided)** The 2024 bookmark has about **100 peers**: the notable real ones (former PMs and ministers, the Lord
Speaker, leaders of the parties in the Lords, well-known crossbenchers) plus invented ones. Party balance and
crossbenchers are kept in proportion to the real House. Vote weights stand in for the full chamber of about 800.

- **Peers** hold a **peerage**: a landless, county-tier title such as "Baron Smith of Wigan".
  - **Life peers:** created through the PM's honours lists, resignation honours and dissolution honours. The title
    ends when the holder dies.
  - **Hereditary peers:** the title passes to the heir. Before 1999 they make up the whole House; afterwards, 92 stay.
    Their by-elections, with tiny electorates, are a satire opportunity.
  - **Lords Spiritual:** 26 bishops, appointed through the Church.
- **The House of Lords** is a landless title, held by the **Lord Speaker**. Peers are its members (tracked as a list)
  and sit on crossbenches or with their party.
- **What the Lords does:**
  - revises and delays bills from the Commons: it can send a bill back once, and the Parliament Acts limit it after
    that;
  - provides ministers: some Cabinet posts can go to peers;
  - gives patronage: a peerage is something to promise, and something to want.
- **Routes into the Lords:**
  - being an ex-MP or ex-minister;
  - party service;
  - being a donor ("cash for honours" is a scandal secret);
  - expertise: crossbenchers from science, the military or business.
- **Era rules:** each bookmark sets them (hereditary peers before 1999, life peers from 1958, bishops always).

### Devolved parliaments

| Parliament | Seats | Electoral system | Government |
|---|---|---|---|
| Scottish Parliament (Holyrood) | 129 MSPs | Additional member: 73 constituencies plus 56 regional list seats | The **First Minister** holds the Scotland kingdom-tier title |
| Senedd | 60 members in 2024 (96 from 2026, by closed list) | Era-dependent | The **First Minister of Wales** holds the Wales title |
| Northern Ireland Assembly (Stormont) | 90 MLAs | Single transferable vote | **Power-sharing**: a First Minister and deputy First Minister from the largest unionist and nationalist parties, modelled as a **diarchy** |

- **Who the members are:** notable real members, with generated ones filling the rest. Each character has a
  membership flag and a party. Seat counts per party are stored, so the elections don't need a title per seat.
- **Elections:** each parliament has its own cycle and electoral system. Results come from national and regional
  support, with a simplified proportional allocation.
- **First Ministers** are chosen by the parliament: the largest party or a coalition, and a vote if that's contested.
- **Situations:**
  - Scottish independence (referendum, then a second-referendum campaign);
  - Stormont suspension (the Assembly collapses until a deal is made);
  - Welsh devolution's growing powers.
- **England** has no devolved government. The England title is held by the PM, or by no one.
- **Older bookmarks:** devolution only exists from 1999. Before that, Stormont runs from 1921 to 1972; after that,
  Northern Ireland is under direct rule.
- **Careers:** a member of a devolved parliament can move to Westminster and back, or become a First Minister.

### Councils (real control)

- **About 360 councils** (2024): 317 in England, 32 in Scotland, 22 in Wales and 11 in Northern Ireland. Each is a
  **landless title** whose capital is its main town. Council areas don't line up with constituencies.
- **Composition:** each council stores its seat count per party, not 18,000 councillor characters. Only the **council
  leader**, the opposition leader and the playable or notable councillors are real characters.
- **Council elections:**
  - each council has its own cycle (all-out every 4 years, or by thirds, simplified);
  - results come from local party support, national mood (a mid-term protest vote against the government) and
    events;
  - **control** goes to the party with a majority. Otherwise there's no overall control, and the largest party or a
    coalition leads.
- **The council leader holds the council title.** Council leaders serve their party leader, like MPs and mayors do.
- **What councils do:** council tax, housing, planning, bins and potholes, social care, budget crises (a Section 114
  notice, effectively bankruptcy). These are decisions, events and a budget value. Control of councils feeds the
  party's local base: activists, candidate pipeline, poll effect.
- **Players as councillors:** a councillor is a character with a council seat (a flag plus the seat count). They can
  climb from councillor to council leader, then MP or mayor.

### Mayors

- **Mayoralties** are landless duchy-tier titles tied to their area's duchy. In 2024 these are the mayor of London
  and the combined-authority mayors: Greater Manchester, West Midlands, Liverpool City Region, West Yorkshire, and
  the others.
- They have **their own elections**, on their own cycle, worked out from the area's seats and the candidate. Mayors
  serve their party leader like MPs do.
- A mayor has powers over the area (transport, policing, development), modelled as decisions and great projects.
  They're a power base: a popular mayor is a leadership threat.
- Older bookmarks have the mayoralties that existed then: none before 2000 apart from ceremonial Lord Mayors, which
  could be satire flavour.

### Unlanded careers (the way in)

- **Playable starts:**
  - activist or local party member;
  - councillor: a council seat on the area that will become a mayoralty, or a simple office title;
  - parliamentary candidate;
  - special adviser or party staffer;
  - journalist;
  - union official;
  - think-tank wonk;
  - lobbyist;
  - donor.
- **Built on the 1.20 landless adventurer system.** The team (followers) and funds (provisions) carry over. Task
  contracts become jobs offered by MPs, parties and papers. Doing them earns profile, money, contacts (hooks) and
  Party Standing (`var:wm_standing`).
- **Ambitions** are career goals:
  - **become an MP:** get on a shortlist, win a selection, then win the seat at a general election or by-election;
  - **become a peer:** get on an honours list;
  - **become a mayor.**
- **Selection contests** are activities: the local party's members are the voters, rivals scheme against each other,
  and endorsements matter.
- **Falling back down:** an MP who loses their seat becomes unlanded again. Their career continues as a candidate,
  commentator, lobbyist or peer.

#### The ladder to an MP (first version, 2026-10-08)

Activist, then the approved list, then selected candidate for a seat, then MP at the next general election or
by-election.

- **Hopefuls** are party members (`var:wm_party`) with no seat, on global list `wm_career_hopefuls` with
  `var:wm_career_hopeful` and **standing** with their party, `var:wm_standing` (0 to 100).
  - A player hopeful is a landless adventurer whose camp is their **campaign team** (`var:wm_career_camp`).
  - AI hopefuls are ordinary characters: local activists found by selections, and defeated MPs.
- **Jobs** are task contracts (`common/task_contracts/wm_career_contracts.txt`). Each month the party's MPs offer a
  player hopeful a job (up to three on offer):
  - canvassing (diplomacy), a fundraising dinner (stewardship), speechwriting (learning), opposition research
    (intrigue);
  - the **candidate assessment** (charisma), offered from standing 25, which puts them on the party's **approved
    list** (`var:wm_on_shortlist`).
  - Three weeks after a job is taken a skill check settles it (30% plus 4% per skill point, at most 95%). Success
    pays standing, profile, money and campaign funds (provisions), the employer's good opinion, and the employer as a
    contact. Failure costs 3 standing and a little profile.
  - AI hopefuls gain standing slowly without jobs.
- **Selections.** A local party opens one in a seat:
  - **by-election:** when an MP dies, every party that took 15% there in 2024 selects, over a fortnight;
  - **target seat:** from the third year of a Parliament, or once it is dissolved, each party opens a selection each
    month in one seat it doesn't hold where the current swing gives it 25%. These run 30 days, or 14 during a
    campaign.
  - No selection opens where the party already has a living candidate.
- **Applying.** Hopefuls of the party on the approved list, or with standing of 30 or more, may apply:
  - players are invited (event `wm_career.20`), or take the "Apply for Selection" decision;
  - up to three AI hopefuls apply, local ones (the seat's culture) more often.
  - Each applicant gives a **hustings speech**. Players choose their pitch: the local area (diplomacy), a costed plan
    (learning) or their rivals' records (intrigue), as a skill duel (`wm_career.21`). The AI's speech is a diplomacy
    check.
- **The members' vote** when the selection closes: standing, plus the hustings result, half the selector's opinion of
  the applicant (the local MP if they're in the party, otherwise the party leader), 20 for local roots, and up to 20
  of luck. With fewer than two in the running the local party puts up a local activist, so every selection picks
  someone.
  - The winner is stored on the seat as `var:wm_candidate_<party key>` (for example `wm_candidate_lab`), and on the
    candidate as `var:wm_career_selected_seat`. They gain 10 standing and some profile; the others gain 2 and stay
    hopefuls.
- **Winning the seat.** When an election or by-election gives the seat to a party (`wm_election_new_mp_effect`, which
  the by-election uses too), its living candidate becomes the MP instead of a new character
  (`wm_career_find_candidate_effect`).
  - They serve the party leader like any MP.
  - Their campaign team is wound up (the adventurer title is destroyed, and the government becomes feudal) and they
    leave the ladder (`wm_career_took_seat_effect`).
  - A candidate whose party loses stays the candidate for next time.
- **Defeated MPs** (`var:wm_lost_seat`) under 70 come back as hopefuls: on the approved list, with at least 50
  standing. Players take "Back on the Campaign Trail" (a campaign team).
- **Bookmark:** Jess Okafor, a fictional 24-year-old Labour activist in Leeds, is playable in the 2024 bookmark as a
  `new_landless_adventurer` (generated by `tools/data/build_2024.py`). Her history sets `var:wm_standing`, which puts
  her on the ladder at game start.
- **Files:**
  - `scripted_effects/wm_career_effects.txt`, plus `wm_career_parties.txt` for the per-party calls (party key and
    title pairs, as in `wm_election_parties.txt`);
  - `scripted_triggers/wm_career_triggers.txt`, `script_values/wm_career_values.txt` (thresholds and chances),
    `opinion_modifiers/wm_career_opinions.txt`;
  - `on_action/wm_career_on_actions.txt`: game start, a monthly tick from the PM's quarterly pulse, and by-election
    selections on an MP's death;
  - `events/wm_career_events.txt`, `decisions/wm_career_decisions.txt`, `localization/english/wm_career_l_english.yml`;
  - tests in `tools/ck3_test/gen_career.py`.
- **Later:**
  - retiring MPs, whose seats open to their own party (the general election keeps a sitting MP of the winning party);
  - rivals scheming and endorsements, selections as activities, and deselection;
  - jobs from papers, unions and think tanks, and other playable starts (councillor, special adviser, journalist);
  - candidates' qualities counting at the election itself.

### Riots (first version, 2026-10-08)

**(decided)** Vanilla peasant and popular revolts become **rioters and protest marches**. Nobody raises an army.

- **Revolts are off.** The mod overrides vanilla `common/factions/00_peasant_faction_new.txt` and
  `00_populist_faction.txt` (copies with `always = no` added to the create/join triggers), so no county starts or
  joins a peasant or populist faction.
- **How a riot starts.** Each 1 January (`yearly_global_pulse`), there's a 75% chance of a riot in a random seat,
  most likely one whose people are unhappy with their MP (low county opinion). At most two riots run at once.
- **The riot.** The seat gets the *Rioting* modifier (less tax, lower opinion) and a **march organiser**, a new local
  activist. The riot's state is stored as variables on the seat.
  - Each riot has one **demand**: help with the cost of living, a minister's resignation, a general election, or a
    policy U-turn.
- **The march.**
  1. The **local MP** hears first and can try to talk the crowd down (a diplomacy duel), back the protesters (popular
     at home, but the party leader is annoyed), or keep their head down.
  2. After 10–20 days the march sets off for Westminster.
  3. After another 20–30 days it reaches Westminster with its demand.
- **The Prime Minister answers.**
  - **Concede:** costs prestige (profile) and some mandate (legitimacy), plus the demand itself:
    - cost of living: money, and a cost-of-living package that cuts income for 3 years;
    - resignation: a random cabinet minister is sacked, and resents it;
    - election: a promise of an early election (a flag for the election system to pick up);
    - U-turn: a U-turn modifier.

    The seat gets *Demands Met* (+opinion).
  - **Negotiate:** a diplomacy duel. Success means a smaller prestige cost and a compromise. Failure means the march
    comes back, bigger, 30 days later. After two failures, talking is no longer an option.
  - **Police it:** usually the crowd is cleared. That brings a general-opinion penalty for the PM, an opinion hit in
    the seat, and an annoyed local MP. Sometimes it turns violent: a large prestige loss, a bigger penalty, and the
    rioting spreads to a neighbouring seat.
- **Files:**
  - `events/wm_riot_events.txt`;
  - `common/scripted_effects/wm_riot_effects.txt`;
  - `common/on_action/wm_gameplay_on_actions.txt`;
  - tests in `tools/ck3_test/gen_gameplay.py`.
- **Later:** riots driven by the economy and polls rather than county opinion, a "join the march" option for players,
  and the election promise feeding real general elections.

### The Crown

**(decided)** The royal family is in the game, but not important.

- **The title.** **The Crown** is a landless kingdom-tier title, `k_wm_crown`. The monarch holds it; the Prime
  Minister holds the United Kingdom. The monarch has no seat and no vassals, and is in no one's realm.
- **Government.** The monarch has their own government, `wm_crown_government`. It has none of the feudal flags, so
  vanilla war and feudal content leaves them alone. Its rank names read **King/Queen** instead of the kingdom-tier
  "First Minister".
- **2024 bookmark.** King Charles III holds the Crown. Queen Camilla, the Prince and Princess of Wales and their three
  children are his courtiers (`history/characters/wm_royal_family.txt`). Succession is single heir with equal
  gender. They're flavour, and like every real person they're never the subject of scripted events.
- **Speak Out Against MP.** This is a monarch-only character interaction against anyone holding a seat.
  - **Cost:** **1,500 prestige**. Charles starts with about 2,500, so it's a once-a-reign act. It has a 10-year
    cooldown.
  - **Effects on the MP:** they lose 350 prestige and get *Rebuked by the Crown* for 5 years (−15 general opinion,
    prestige drain), and their seat gets −15 county opinion.
  - **Opinion effects:** the MP dislikes the monarch (−40), their party leader is embarrassed (−15), and the PM
    resents the meddling (−20).
  - **The MP's reply:** they get an event. They can bite their tongue, or hit back at the Palace: they win back some
    prestige, and the monarch loses some.
  - **AI:** an AI monarch considers it once a year, with a 3% chance. They need the prestige, and only target an MP
    they dislike (opinion −20 or below).
- **Later:** the monarch appointing the PM after an election, the King's Speech, honours lists, and royal events as
  generic random flavour.

### House of Commons (first version, 2026-10-08)

Milestone 4's Commons: government bills, the whips, divisions and confidence motions.

- **Introducing a bill.** The Prime Minister takes the decision **Introduce a Bill** (every 180 days at most; the AI
  sometimes does) and picks one:

  | Bill | Leans | Controversy | If it passes |
  |---|---|---|---|
  | Finance Bill (taxes up) | left | 10 | money, *Tax Rise* (income up, opinion down), polls −2 |
  | Public Services Bill (spending) | left | 0 | *Public Services Spending* (opinion up, income down), polls +3 |
  | Public Service Reform Bill | right | 30 | mandate (legitimacy), *Reformer* (prestige), polls −1 |
  | Emergency Powers Bill | neither | 10 | prestige, *Emergency Powers* (mandate); the opposition backs it 70% of the time |

- **Wings.** Each MP gets a wing of their own party the first time it matters (`var:wm_commons_wing`: −1 left, 0
  centre, 1 right; compassionate and generous MPs lean left, greedy and callous ones right). A bill that leans
  against an MP's wing makes them likelier to rebel; one that leans their way makes them loyal.
- **The Chief Whip's report.** The Prime Minister sees both sides' numbers and how many of their MPs might rebel,
  then chooses:
  - leave it to the whips;
  - a three-line whip (costs prestige);
  - calling the waverers in one by one (costs money);
  - concessions: fewer rebels, but the bill is watered down and does about half as much;
  - pulling the bill (small prestige loss).
- **The division,** a week later. Every seat's holder votes once, except the Speaker (flag `wm_speaker`). The vote is
  over the counties of `e_united_kingdom`, with the tallies in global variables (voters go on the global list
  `wm_commons_voters`, cleared at the start of each division, so nobody votes twice).
  - Government MPs follow the whip unless they rebel. Their chance (0–90%) is the bill's controversy minus 15
    (backbench loyalty), +15 if the bill offends their wing or −10 if it suits it, minus a fifth of their opinion of
    their party leader, minus the Prime Minister's authority (prestige and legitimacy levels × 2), minus the whips'
    operation (15 / 30 / 20), plus 5 for each earlier rebellion, plus traits. A rebel votes against (65%) or
    abstains (35%). An uncontroversial bill sees a handful of rebels; the Reform Bill a few dozen.
  - Opposition MPs follow their party's whip, usually against, and rarely defy it. Party leaders always vote with
    their party. Sinn Féin MPs abstain. Independents vote by wing and their opinion of the Prime Minister.
  - A player MP gets the **division bell** event: vote with the government, against it, or abstain.
  - A bill needs more ayes than noes.
- **The result** is a newspaper headline for every player ("GOVERNMENT DEFEATED", "COMFORTABLE MAJORITY",
  "KNIFE-EDGE: GOVERNMENT SCRAPES HOME"...) with the lobby numbers ("Ayes 352, Noes 258") and the number of
  rebels. A defeated bill costs the Prime Minister prestige and mandate, *Defeated in the Commons*, and polls −2.
- **Rebels.** The party leader takes note of each rebel (*Defied the whip*, −10, stacking). On a third rebellion the
  MP **loses the whip**: their `wm_party` is removed and they sit as an independent serving the Prime Minister,
  resenting their old leader (−40).
- **Confidence motions.** The **Leader of the Opposition** (the leader of the largest party outside the government)
  can **Table a Motion of No Confidence** (yearly at most; the AI rarely does, mostly against a thin majority).
  The Prime Minister's whips get the same choices. Government MPs rarely rebel on a confidence motion (controversy
  −25). A tie defeats the motion.
  - If the government **loses**, `global_var:wm_election_required` is set for the election system to act on. The
    Prime Minister loses mandate and prestige and gets *Lost the Confidence of the House*.
  - If it **survives**, the mover loses face and the Prime Minister resents them.
  - Neither decision is available while an election is required.
- **Polls.** The Commons touches the polls only through `wm_commons_poll_effect = { PARTY = <party title>
  AMOUNT = <n> }`. It adds to `global_var:wm_poll_mood_<party>` if the polls have created it.
- **Files:**
  - `common/decisions/wm_commons_decisions.txt`;
  - `events/wm_commons_events.txt`;
  - `common/scripted_effects/wm_commons_effects.txt`;
  - `common/script_values/wm_commons_values.txt`, which also documents the global variables;
  - `common/scripted_triggers/wm_commons_triggers.txt`;
  - `common/modifiers/wm_commons_modifiers.txt` and `common/opinion_modifiers/wm_commons_opinions.txt`;
  - `localization/english/wm_commons_l_english.yml`;
  - `common/on_action/wm_commons_on_actions.txt` (creates the `wm_poll_mood_<party>` variables at 0 at game start);
  - tests in `tools/ck3_test/gen_commons.py`.
- **Later:** more bills, and bills from the party's own programme; the Lords revising bills; the whip restored after
  good behaviour; coalition partners whipped with the government; a whips' office (court positions) that affects the
  numbers; and player party leaders choosing whether to withdraw the whip.

### Elections (first version, 2026-10-08)

- **Polls.** National vote share per party is a global variable, `global_var:wm_poll_<party>` in tenths of a percent
  (`lab`, `con`, `ld`, `ruk`, `grn`, `snp`, `pc`, `sf`, `dup`, `sdlp`, `apni`, `uup`, `tuv`, plus `oth`), adding up to
  1000. Polls start from the 2024 result and move once a month: a random walk (up to 5% of the party's share), a 5% pull
  back towards an anchor, then rescaling to 1000. The anchor is the 2024 share. For the PM's party it also includes the
  government's fortunes: the PM's prestige and legitimacy, riots policed, put down or conceded (the riot modifiers on
  the PM), an election promised and not yet called, active riots, and mid-term blues (years 1 to 4).
  `wm_polls_shift_effect = { P = con AMOUNT = -20 }` is the hook for scandals and other events. Regional parties poll
  UK-wide: their swing is scaled by the nation's share of the vote (SNP ×11.9, Plaid ×21.8, NI parties ×36.9).
- **Seat lean.** `wm_init_seat_leans_effect` (generated) stores each seat's 2024 shares on its title as
  `var:wm_lean_<party>`. A party's share in a seat is half uniform swing and half proportional swing from its 2024
  share. On top of that come ±1.5 points of local randomness and, for the party defending the seat, a 3-point incumbency
  bonus. An independent MP keeps their personal vote. Party leaders, the PM and the Speaker always keep their seats.
- **General elections.** Parliament is dissolved after 58 months, or earlier if the PM takes "Call a General Election"
  (after at least 6 months, with a 1-year cooldown). The AI calls one when well ahead in the polls, more readily late
  in the Parliament and after promising one to protesters, and never when behind. Polling day is 35 days later
  (`wm_election.1`).
  - Seats that change hands go to a new local character (the seat's culture, a generated surname) in one title and
    vassal change each. The new MP serves their party leader. Defeated MPs keep their party and become unlanded.
  - The leader of the largest party then becomes PM. They take `e_united_kingdom` and the nations, and the old PM and
    their non-party followers serve them. A hung parliament means the largest party governs; coalitions come later.
  - Finally every MP is put back under their party leader, and party leaders, independents and the Speaker under the
    PM. Other systems can call an election with `wm_election_schedule_effect` (for example after a lost confidence
    vote).
- **By-elections.** When an MP dies (`on_death`), or when `wm_byelection_call_effect` is called on a seat (resignation),
  the seat waits 4 weeks. It's then decided by the same model with no incumbency bonus, and the winner is always a new
  MP. If the PM died, the leader of the largest party takes over first.
- **Results.** Every player gets a front page with the headline chosen by result ("LABOUR LANDSLIDE", "TORIES SWEEP TO
  POWER", "HUNG PARLIAMENT", "... SCRAPE HOME", "... RE-ELECTED"), the seats per party with changes, and their own
  seat's share and majority. By-elections send a toast ("By-election: Reform Gain").
- **Files:**
  - `tools/data/build_seat_leans.py` generates the party-dependent parts: `wm_election_seat_leans.txt`,
    `wm_election_parties.txt`, `script_values/wm_polls_values.txt`, `events/wm_election_results_events.txt` and
    `wm_election_parties_l_english.yml`;
  - hand-written: `scripted_effects/wm_election_effects.txt`, `wm_polls_effects.txt` and `wm_byelection_effects.txt`;
    `script_values/wm_election_values.txt`; `scripted_triggers/wm_election_triggers.txt`;
    `on_action/wm_election_on_actions.txt`; `decisions/wm_election_decisions.txt`; `events/wm_election_events.txt`,
    `wm_polls_events.txt` and `wm_byelection_events.txt`; `localization/english/wm_election_l_english.yml`;
  - tests in `tools/ck3_test/gen_elections.py`.
- **Later:** regional polls, candidates' own qualities (skills, scandals), coalitions and confidence-and-supply, a polls
  window and results map, and leaders who can lose their seats. (Candidate selection: "Unlanded careers".)

### Campaigns (first version, 2026-10-08)

The five weeks between dissolution and polling day.

- **Starting.** The elections code has no hook, so a hidden **weekly watcher** (event `wm_campaign.100`) reads its
  state. It runs on the Prime Minister and reschedules itself every 7 days. The quarterly pulse and game start restart
  it if the chain is lost. When `global_var:wm_el_scheduled` and `wm_el_campaign` are set, a campaign starts
  (`global_var:wm_campaign_active`). Every party MP and leader gets the flag `wm_campaign_on_trail`, and week 1 runs at
  once. That is within a week of any dissolution: the decision, the five-year deadline or a lost confidence vote.
- **Each week** (`global_var:wm_campaign_week`, up to 5):
  - **AI party leaders** roll an automatic week: a good week (+0.8 points, likelier with diplomacy), a steady one
    (+0.3), or a gaffe (−0.8 and some prestige, likelier with low diplomacy).
  - **Player campaigners** get *On the Campaign Trail* (`wm_campaign.1`). They choose one of:
    - **A big rally** (diplomacy-weighted): +1.2 points and prestige for a leader. An MP gets +0.3 nationally and
      +0.5 in their own seat. It can also come out flat, or flop into a gaffe.
    - **The TV debate** (party leaders, once a campaign): a diplomacy duel, or a learning duel ("bury them in
      statistics"), against the rival leader. The PM's rival is the leader of the biggest other party; everyone
      else's is the PM. The winner gets +2 points and the loser −1.5, and the loser resents the winner.
    - **A policy launch** (leaders; stewardship and learning): +1.5 points, or the costings unravel (−1).
    - **Door-knocking** in their own seat: their party's share there (`var:wm_lean_<party>`, the lean that elections
      swing from) goes up by 0.8 to 1.5 points, capped at 85%. The seat also gets *Met Their MP on the Doorstep*.
    - **A quiet week** at campaign HQ.
  - **Gaffes** (`wm_campaign.2`): a 15% chance a week, or a failed rally. They're generic satire (an awkward
    sandwich, a hot mic, the price of milk, a cupboard, an upside-down leaflet). The player can laugh it off
    (diplomacy), blame a junior staffer, or do it again on purpose (a gamble that can go viral either way).
- **Polls.** Every move goes through `wm_polls_shift_effect` (`wm_campaign_own_poll_effect`). The amounts are in the
  party's own nation, so a regional party's shift is divided by its nation factor (SNP 11.9, Plaid 21.8, NI 36.9). Like
  any shift, it fades as polls drift back to their anchors, so the last weeks matter most.
- **Ending.** Once polling day has passed (`wm_el_scheduled` cleared), the watcher clears the campaign's state.
- **Files:**
  - `events/wm_campaign_events.txt`;
  - `common/scripted_effects/wm_campaign_effects.txt` (documents the state);
  - `common/script_values/wm_campaign_values.txt` (all the amounts; the conference ones too);
  - `common/scripted_triggers/wm_campaign_triggers.txt`;
  - `common/modifiers/wm_campaign_modifiers.txt`;
  - `common/on_action/wm_campaign_on_actions.txt`;
  - `localization/english/wm_campaign_l_english.yml`;
  - tests in `tools/ck3_test/gen_campaign.py`.
- **Later:**
  - campaign visits to target seats (the leader's choice of marginals);
  - manifestos and a launch event;
  - debates between more than two leaders;
  - candidates' quality and money in the seat result;
  - a campaign UI with the daily polls;
  - the press backing a party.

### Party conferences (first version, 2026-10-08)

- **When.** Each autumn the weekly watcher opens each major party's conference within a week of its date:

  | Party | Opens |
  |---|---|
  | Liberal Democrats | 14 September |
  | Reform | 18 September |
  | Labour | 22 September |
  | Conservatives | 29 September |
  | Greens | 3 October |
  | SNP | 10 October |

  `global_var:wm_conference_done_<party>` (300 days) stops a second conference. A conference that falls during an
  election campaign is held after polling day if that is still in October. `wm_conference_hold_all_effect` holds them
  all at once (tests, console).
- **The leader's speech.** A player leader gets `wm_conference.1`, then the papers' verdict (`wm_conference.2`). AI
  leaders roll the same outcomes.
  - **Speech as written:** weighted by diplomacy and stewardship. The outcome is one of:
    - a **triumphant speech**: +2 points, prestige, *Conference Triumph* for a year, and the MPs warm to their leader;
    - **solid**: +0.5 points, a little prestige;
    - a **cough-ridden disaster**: −1.5 points, a prestige loss, *Conference Disaster*, the MPs sour, and two plotters'
      worth of rumblings.
  - **Speak from the heart:** a bigger swing either way.
  - **A set-piece policy:** stewardship and learning. +2.5 points, or the policy sinks by lunchtime (−1 and a plotter).
- **MPs.** A player MP gets `wm_conference.10`:
  - a **fringe meeting**: prestige and +0.2 points, or remarks that go off-message and annoy the leader;
  - **plotting in the hotel bar**: one more plotter, and two disgruntled colleagues like you. There's a 30% chance
    the whips overhear, and the leader resents it (−25).
  - **working the receptions**: the three most sociable colleagues like you (+15);
  - **loud applause**: the leader likes you (+10).

  AI MPs who dislike their leader (opinion below −10) plot 25% of the time.
- **Leadership rumblings.** Three days on (`wm_conference.30`), if at least 3 MPs plotted
  (`var:wm_conference_rumblings` on the party title), the papers talk of a fresh start. A player leader
  (`wm_conference.20`) can face the plotters down (diplomacy), promise to listen (prestige for MPs' goodwill), or
  dismiss it as bubble chatter (−0.5 points). An AI leader takes a bad week (−0.8 points, prestige). Rumblings don't
  yet start a leadership challenge.
- **Files:**
  - `events/wm_conference_events.txt`;
  - `common/scripted_effects/wm_conference_effects.txt`;
  - `common/opinion_modifiers/wm_conference_opinions.txt`;
  - `localization/english/wm_conference_l_english.yml`;
  - the shared campaign files above;
  - tests in `tools/ck3_test/gen_campaign.py`.
- **Later:**
  - conferences as a CK3 activity, with the player attending as a guest;
  - motions and votes on party policy;
  - rumblings feeding a real leadership challenge;
  - the PM's party conference setting the year's bills;
  - smaller parties' conferences.

### Coalitions (first version, 2026-10-08)

Hung parliaments: coalitions, confidence-and-supply and minority government.

- **When.** After a general election, `wm_election_form_government_effect` makes the largest party's leader Prime
  Minister as before, then calls `wm_coalition_after_formation_effect`. If the PM's party has a working majority
  (`wm_coalition_majority_value`: half the MPs who vote, all but the Speaker, plus one: 325 of 650) it governs alone.
  Otherwise the PM looks for a partner. After a by-election the hook only keeps an existing deal in step (a new PM of
  the same party gets the same Deputy PM; a change of governing party ends the deal).
- **Choosing a partner.** Every other party with seats and a leader (not Sinn Féin, who don't take their seats) is
  scored (`common/script_values/wm_coalition_values.txt`):

  | | |
  |---|---|
  | base | 10 |
  | left-right distance | −6 per point (the table below) |
  | together they reach a majority | +20 |
  | small party (under 20 seats) holding the balance | +10 |
  | big party (150+ seats): the main opposition doesn't prop up its rival | −40 |
  | its leader's opinion of the PM | −12 to +12 |

  Left-right scores (−10 left to 10 right): Green −7, Sinn Féin −6, Plaid −5, SNP −4, Labour −3, SDLP −3, Lib Dem 0,
  Alliance 0, UUP 4, Conservative 5, DUP 6, TUV 8, Reform 9. The PM ranks partners by that score plus a little for
  size (seats ÷ 5, at most 15), so when nobody can make a majority the best available is chosen.
- **Offers.** A partner accepts when the score plus the terms reaches the threshold:
  - **coalition** (threshold 30): +10 per cabinet seat (1 or 2), +10 for one of its policies in the programme;
  - **confidence-and-supply** (threshold 15): +10 for the money for its priorities.

  So Labour and the Lib Dems (12 with a majority) agree a coalition with one seat and a policy, or
  confidence-and-supply; the Conservatives and the Lib Dems (0) only for two seats and a policy (2010); the
  Conservatives and the DUP (14, more with a majority) settle for confidence-and-supply (2017).
- **AI to AI.** The PM offers its top choice a coalition with one seat and a policy, then two seats, then
  confidence-and-supply; a small party is offered confidence-and-supply first. If nothing is accepted: minority
  government. A player partner is sent the AI's offer to accept or refuse (`wm_coalition.3`).
- **A player PM negotiates** (`wm_coalition.1`, `.2`, `.4`): picks one of the three best partners (with their seats),
  sees the arithmetic and their mood, and offers a coalition (one seat; one seat and a policy; two seats and a policy)
  or confidence-and-supply. Each option says whether their negotiators are signalling yes. A refusal lets them
  sweeten the offer, try another party, or govern alone.
- **A coalition:** the partner's leader becomes **Deputy Prime Minister**, a diarchy on the PM of the mod's own type
  `wm_coalition_deputyship` (started and ended only by script, with none of vanilla's diarch powers), and gets the
  *Deputy Prime Minister* modifier. A policy concession gives the PM *Coalition Compromise* (−0.5 prestige a month,
  5 years). The partner's MPs take the government whip on every vote, rebel like government MPs, and its leader is
  never Leader of the Opposition.
- **Confidence-and-supply:** the partner's MPs vote with the government on motions of no confidence and the Finance
  Bill only, and follow their own whip otherwise. The PM pays `medium_gold_value` to the partner's leader, who gets
  *Confidence-and-Supply Deal*. Both kinds give the two leaders *Coalition Partner* (+20) towards each other.
- **The Commons hook** (minimal edits, marked "Coalitions hook"): `wm_commons_is_government_mp_trigger` (the governing
  party or `global_var:wm_coalition_partner`) and `wm_commons_whipped_with_government_trigger` (also
  `global_var:wm_coalition_supply_partner` on bill types 1 and 5) in `wm_commons_triggers.txt`, used by the whip, the
  rebel count, the Chief Whip's forecast and the division bell.
- **Breakdown.** Each quarter (`quarterly_playable_pulse` on the PM) the junior partner may walk out:
  `wm_coalition_breakdown_chance_value`, 2% plus 4 if its poll has fallen 2 points since the deal (4 more at 4 points),
  4 for a Public Service Reform Bill, 3 for a tax rise, 4 for a defeat in the Commons, 6 for a lost confidence vote
  (the PM's modifiers), 3–8 if its leader dislikes the PM, minus 1 per cabinet seat and 1 for a policy win; at most
  30%. A player junior leader is asked first (`wm_coalition.20`) and can also take the decision **Leave the
  Government Deal**. Walking out ends the deal (and the diarchy); the PM resents the partner's leader (−30). Then an AI
  PM soldiers on (40%), calls an election (30%, `wm_election_schedule_effect`), or the Leader of the Opposition
  tables a motion of no confidence (30%); a player PM chooses (`wm_coalition.21`), including finding new partners.
- **Headlines** are toasts for every player: COALITION AGREED, DEAL DONE: GOVERNMENT PROPPED UP, MINORITY GOVERNMENT,
  COALITION COLLAPSES. (A majority needs none: the results front page covers it.)
- **State:** global variables, documented at the top of `wm_coalition_values.txt` (`wm_coalition_outcome`: 1 majority,
  2 minority, 3 coalition, 4 confidence-and-supply, 5 talks under way, 6 collapsed).
- **Files:**
  - `common/scripted_effects/wm_coalition_effects.txt`, `common/script_values/wm_coalition_values.txt`,
    `common/scripted_triggers/wm_coalition_triggers.txt`;
  - `events/wm_coalition_events.txt`, `common/decisions/wm_coalition_decisions.txt`,
    `common/on_action/wm_coalition_on_actions.txt`;
  - `common/diarchies/diarchy_types/wm_coalition_diarchies.txt`, `common/modifiers/wm_coalition_modifiers.txt`,
    `common/opinion_modifiers/wm_coalition_opinions.txt`;
  - `localization/english/wm_coalition_l_english.yml`;
  - tests in `tools/ck3_test/gen_coalitions.py`.
- **Later:** the old PM trying to stay on with a coalition of the second and third parties; cabinet seats as real
  council positions; policy concessions that change bills; a coalition of three or more parties; the junior partner
  voting against particular bills; and the Lords.

### Parties are houses (first version, 2026-10-08)

**(decided)** No dynasties: the house shield is the party. Families of politicians aren't modelled beyond fictional,
lowborn spouses for about two thirds of MPs (`tools/data/build_spouses.py`; never the real spouse) (the royal
family keeps its house).

- **Houses.** Each of the 13 parties is a dynasty with one house (`wm_dyn_party_<party>` / `wm_house_party_<party>`,
  named after the party), and every member is in it. Independents and the Speaker share the **Independent** house,
  so nobody is lowborn. The party leader heads the house (set at game start). The house knows its party
  (`var:wm_house_party` on the house); `wm_party_sync_house_effect` keeps a character's house in step with
  `var:wm_party` (called when an election or by-election makes a new MP, when a selection finds a new activist, and
  when an MP loses the whip, who moves to the Independent house).
- **Names.** A character's whole name is their first name ("Keir Starmer", a localization key per character), and
  the name formats don't show the house, dynasty or patronym (`localization/english/replace/wm_colleagues_l_english.yml`),
  so a party never appears as a surname. New characters get whole names from the cultures' name lists, which are
  overridden with the 2024 MPs' given names and common British surnames; nobody is named after a relative.
- **Emblems.** Each house's coat of arms is a simplified emblem inspired by the party's logo (Labour's rose,
  the Conservative oak, the Lib Dem bird, the SNP loop, Plaid's poppy, Reform's arrow, the Green sunflower, a
  triskele for Sinn Féin, a torch for the DUP, the SDLP rose, an Alliance chevron, the UUP's red hand on a roundel,
  a TUV megaphone, a rosette for independents). The party's dynasty and title share it.
- **Cross the Floor** (decision, players only, 100 prestige, yearly): pick a party from the list, or sit as an
  independent. The character takes its whip and house, an MP serves the new leader (or the PM), an unlanded member
  joins the new leader's court, and the old leader gets *Crossed the floor* (−30). A hopeful's standing resets.
- **Found a Party** (decision, MPs only, 500 prestige): six slots (`k_party_new_1`–`6`: Lantern, Bridge, Beacon,
  Kestrel, Compass, Hearth), each with a made-up emblem. The founder serves the PM, gets a new dynasty and house
  (`create_dynasty` with the slot's coat of arms) and the party title with an elected leadership; the old leader
  gets *Split the party* (−50). Other members can then cross the floor to it.
- **Colleagues.** The character window's Family tab is *Colleagues*: up to 42 living members of the character's
  party, with the party's size as the tab's count. House and Dynasty read *Party*.
- **Files:**
  - generated by `tools/data/build_2024.py`: `common/dynasties/wm_party_dynasties.txt`,
    `common/dynasty_houses/wm_party_houses.txt`, `common/culture/name_lists/wm_name_lists.txt`,
    `common/scripted_effects/wm_party_houses.txt`, `common/scripted_triggers/wm_party_houses.txt`,
    `common/decisions/wm_party_decisions.txt`, `localization/english/wm_names_l_english.yml` and
    `wm_party_houses_l_english.yml`;
  - by `tools/ui/build_party_arms.py`: `common/coat_of_arms/coat_of_arms/wm_party_arms.txt` and the emblems in
    `gfx/coat_of_arms/colored_emblems/` (pictograms from fal.ai, cached in `art/fal/arms_*.jpg`);
  - by `tools/ui/build_colleagues.py`: `gui/window_character.gui` and `localization/english/replace/wm_colleagues_l_english.yml`;
  - by hand: `common/scripted_effects/wm_party_effects.txt`, `common/on_action/wm_party_on_actions.txt`,
    `common/opinion_modifiers/wm_party_opinions.txt`;
  - tests in `tools/ck3_test/gen_parties.py` (needs a save made after this change: `tools/ck3_test/make_save.sh`).
- **Later:** founded parties in the polls and elections (for now their MPs have no national vote and lose their
  seats at the next election); the AI crossing the floor and splitting parties; defections in by-elections; a
  merged list of colleagues sorted by office.

### Satire

Some, not a lot. The aim is gentle political comedy.
- Gaffe events, and a **Gaffe-prone** trait.
- Tabloid **headline** pop-ups after events.
- Honours for cronies and donors.
- Hereditary-peer by-elections.
- The leadership-contest circus, and doomed relaunches.
- Satirical nicknames earned through play, such as "the Lettuce", from events and only for player-driven outcomes.
  Never pre-written about real people.

### New things to build

- **General elections.** Every 5 years at most, or earlier if the PM calls one or loses a confidence vote.
  - Each seat's result is worked out from:
    - national swing by party;
    - regional swing (culture);
    - the candidate (skills, profile, scandals);
    - incumbency;
    - the seat's lean (a stored variable).
  - The new MPs are then handed their seats using a bulk title-transfer approach.
- **Results night UI**: seat counts, swing, a map coloured by party (CK3's map modes can colour by liege).
- **Opinion polls**: national and regional support per party, moved by events, scandals and the economy. Shown in a
  new window.
- **By-elections** when an MP dies, resigns or is recalled.
- **House of Commons votes** on bills and confidence motions. MPs vote by party, whip, wing and opinion. The player
  can rebel or whip votes. A defeated bill or lost confidence vote has consequences.
- **Candidate selection**: a seat whose MP stands down picks a new candidate from local members. This is the
  player's way in.
- **Leadership elections** with rules per party (MPs only, members' ballot, etc.). CK3 elective succession with
  custom voters.
- **The economy** as a few national values (growth, inflation, unemployment, debt). Budgets and events move them, and
  they feed the polls.
- **Press**: newspapers as characters or titles with a stance, which make and break politicians (hooks, scandals).

## The map

A CK3 map is a set of images plus text files:
- `provinces.png`: one colour per province;
- `heightmap.png`;
- `rivers.png`;
- terrain masks;
- `definition.csv`;
- `default.map`;
- `positions.txt` (where names and units go).

Vanilla's is 9216×4608, with a heightmap twice that.

**Plan: generate the map from open data with scripts rather than drawing it.**

| Map layer | Source |
|---|---|
| Constituency boundaries, 2024 | ONS Open Geography Portal, "Westminster Parliamentary Constituencies (July 2024)", Open Government Licence |
| Areas inside seats (baronies) | Local-authority wards or built-up areas |
| Height | OS Terrain 50 or a public DEM. Gives the heightmap, then terrain masks (hills, moorland, farmland, urban) from land-cover data. |
| Rivers | OS Open Rivers |
| Coastline and sea | The boundary data |
| Neighbours | Ireland (non-playable or a wasteland) and Europe's coast as decoration |

- **Map scale:** the UK is about 1,000 km tall. On a 4,608px-high map that's roughly 4px per km. London seats are 3–5
  km across, about 12–20px, which is enough. Very small seats may need enlarged insets or a minimum size.
- **Risks:**
  - CK3 is picky about map files: province colour rules, adjacency, sea zones and pathfinding nodes.
  - The 3D terrain textures and map objects (trees, towns) are the biggest unknowns for a new map. A first version can
    use flat, simple terrain.

### Bookmarks and changing boundaries

Seats were redrawn in 1945, 1950, 1955, 1974, 1983, 1997, 2005/2010 and 2024, but CK3 can't redraw provinces during a
game. **(decided)** Every bookmark uses the 2024 seats:
- Historical MPs are placed in the nearest 2024 seat.
- Where two historical seats map to one, the winner of the larger one gets the seat.
- Seat names stay as they are in 2024.

This is approximate history, accepted for simplicity.

## Data

| What | Source |
|---|---|
| MPs (names, birth dates, party, seat, dates in office) | UK Parliament Members API (members-api.parliament.uk), Wikidata. Also covers historical MPs for the older bookmarks. |
| 2024 results and vote shares per seat | House of Commons Library results data. Gives each seat's lean. |
| Families (spouses, children, political dynasties) | Wikidata, where public. |
| Cabinet for each bookmark | Wikipedia lists of ministries. |
| Councils (list, areas, main towns) | ONS Local Authority Districts (2024), Open Government Licence |
| Council composition by party | Open Council Data UK, or council and Wikipedia results. **Check the licence before use.** |
| Members of the devolved parliaments | The Scottish Parliament, Senedd and NI Assembly websites and open data, plus Wikidata (notable members only; the rest generated) |
| Peers (about 100) | UK Parliament Members API (Lords), Wikidata |

Python scripts turn these into CK3 history files (characters, titles, dynasties). Each bookmark is a date plus a data
snapshot. Portraits are CK3's generated faces, except about 75 recognisable people (leaders, senior ministers, former PMs,
the royal family) who get fixed caricature likenesses (`tools/data/build_likenesses.py`). Age, sex, ethnicity and style can
be set.

## Removing the Middle Ages

A total conversion has to replace or turn off a lot of vanilla:
- history (all characters and titles);
- landed titles;
- religions and cultures (swapped for ideologies and regions);
- casus belli;
- most events and decisions;
- holdings and buildings (swapped for constituency features like industry, universities and ports);
- men-at-arms;
- travel and the court UI (reskinned).

Approach:
1. Start from a minimal working TC: one bookmark, the map, the titles, no war.
2. Turn off vanilla content in bulk: `replace_path` for history, events and on_actions that fire medieval content.
3. Bring back only what we've reskinned, then run the local test harness and checks.

## Ideology replaces religion (decided and built 2026-10-08)

CK3's faith system becomes political ideology. Religions are political camps, faiths are ideologies; every character
and every seat has one.

| Camp (religion) | Ideologies (faiths) |
|---|---|
| Left `wm_camp_left` | Socialist `wm_ideo_socialist`, Social Democrat `wm_ideo_social_democrat`, Green `wm_ideo_green` |
| Centre `wm_camp_centre` | Liberal `wm_ideo_liberal`, Centrist `wm_ideo_centrist`, Cross-community `wm_ideo_cross_community` |
| Right `wm_camp_right` | One Nation `wm_ideo_one_nation`, Free-market `wm_ideo_free_market`, National Conservative `wm_ideo_national_conservative`, Populist Right `wm_ideo_populist_right` |
| Nationalist `wm_camp_nationalist` | Scottish Nationalist `wm_ideo_scottish_nationalist`, Welsh Nationalist `wm_ideo_welsh_nationalist`, Irish Republican `wm_ideo_irish_republican`, Irish Nationalist `wm_ideo_irish_nationalist` (constitutional) |
| Unionist `wm_camp_unionist` | Unionist `wm_ideo_unionist` |

"Not Stated" (`wm_faith_not_stated`) stays for the royal family, spouses and others outside politics.

- **Doctrines** are policy positions (tax and spending, public ownership, immigration, Europe, devolution, civil
  liberties); **tenets** are signature causes. **Hostility** is ideological distance: same camp is mild, opposite
  camps (left and right, nationalist and unionist) strong. It feeds opinion, coalition talks, whip rebellions and
  the party wings. **Conversion** is changing your mind; a seat's ideology drifts with campaigns, riots and trust.
  **Fervour** is ideological energy (activists, turnout). The faith map mode is the political-lean map. No holy
  wars, no heresy imprisonment, no religious head.
- **Real MPs:** an MP gets their own ideology only where it's obvious from public record: membership of a
  self-declared caucus (e.g. the Socialist Campaign Group, the One Nation caucus, the European Research Group, the
  Common Sense Group). Otherwise they take their party's mainstream ideology, with a little seeded variation inside
  the party's range. The source of each assignment is kept in the generator.
- **Party wings follow ideology** (Socialist: Labour Left; Social Democrat: Soft Left; Centrist: Labour
  Centrists; One Nation; Free-market: Free-marketeers; National Conservative: Traditionalists), replacing the
  random assignment.
- **Seats** take the ideology of the party that won them in 2024, then drift.
- **Icons:** a modern flat badge per ideology and per camp (fal.ai), ink-on-paper style.

## Ideas from other mods (decided 2026-10-08)

Eight features drawn from other political mods and games. Ideas only: no code or art is copied. Sources are noted for
credit. **All eight are built (first version, 2026-10-08)**; see README.md "Gameplay so far" for how they play and
the tests that cover them (gen_politics.py: 1, 5, 6, 7; gen_leadership.py: 2; gen_majority.py: 4, 8; the seat chart,
3, is in tools/ui/build_polls_panel.py). Not yet done: the election model doesn't use expected turnout; a Yes vote in
a referendum doesn't lead to secession; balance over long games is untested.

1. **Campaign spending: propaganda and smears** (from CK3 Res Publica). Party leaders and MPs can pay money each
   month for a press campaign that moves their party's national poll share, or a smear campaign against a rival
   party. Smears risk backfiring (a scandal secret on the spender, a poll drop). A leader can spend political capital
   to get a hook on a rival party's leader. Never aimed at a named living person's private life: campaigns are about
   parties and policies.
2. **Shortlist ballots** (Res Publica). Leadership contests become two rounds: MPs nominate, the top candidates
   (threshold of MPs' nominations) go to a members' ballot decided by opinion, political capital and skills. The same
   mechanism elects the Speaker (all MPs, secret ballot) after a general election or a vacancy.
3. **The Commons seat chart** (Victoria 3 Parliament 2.0). A panel showing the Chamber as government and opposition
   benches facing each other, seats coloured by party, with the majority line, plus poll and seat history over the
   last week, three months and year (stored snapshots).
4. **Disputed results** (Victoria 3 Arbitrate the Election Results). A very close seat (under ~1% margin) can be
   challenged: accept, demand a recount (chance to overturn, costs money), or go to an election court (slow,
   expensive, can order a re-run by-election). Losing badly or contesting a landslide angers the public and can set
   off riots, which feed the existing riot marches.
5. **Public trust** (HOI4 UK Public Trust submod). One national 0-100 score of trust in politics, moved by U-turns,
   broken promises, riots, scandals, policed protests, passed popular bills and clean campaigns. Low trust raises
   riot chances, helps small and new parties in the polls and lowers turnout; high trust helps the government.
   Each bookmark starts at its era's level, with era set-piece events written generically.
6. **Party wings** (CK3 Golden Dominion). Each major party has wings (e.g. Labour: Left, Soft Left, Centrist; Tory:
   One Nation, Free-market, Traditionalist) as factions inside the party house. MPs belong to a wing; the leader must
   keep the wings' approval (cabinet places, bills that suit them) or face rebellions and leadership challenges.
7. **Devolution journals** (Victoria 3 British Flavour Pack). Flavour for Scotland, Wales and Northern Ireland:
   independence/union sentiment per nation, referendum demands, powers that can be devolved or clawed back, the
   Northern Ireland power-sharing collapse and restoration. Hooks into the devolved governments (`k_gov_*`).
8. **By-elections that can bring a government down** (board game *Westminster: The Election Game*, 1983). A
   government's majority is tracked live: losing by-elections and defections shrink it, and a government that loses
   its majority faces a confidence motion. A string of by-election losses also hurts the PM's standing and public
   trust.

## 0.4 design (shipped; retained as implementation history)

Defaults taken while the roadmap's open decisions wait: dark is the only look for now (no light companion mod yet);
the intrigue list below.

- **Stability first.** Boot with every DLC disabled; shrink the heaviest textures (terrain detail maps, interface
  skins) without visible loss; test the current CK3 version; spread the 650-seat weekly and monthly loops so no tick
  stalls the game.
- **Night edition.** The newspaper look turned dark: charcoal panels (around #1d1f22), off-white text (#ece7dc),
  muted greys for secondary text, the same red accent (#c8102e family) and the same typography. Paper textures become
  dark paper; ink rules become light rules; party colours stay. Generated by the existing UI tools (build_theme.py
  and friends), so a light look stays one palette switch away.
- **The unlanded start.** Contract schemes must run and travel to a contract must arrive. The adventurer camp is a
  campaign office; camp purposes become political focuses (Grassroots Organiser, Think-Tank Wonk, Party Fixer, Media
  Pundit); contracts and camp texts read as modern political jobs; new fal.ai pictures for each focus and the camp
  backdrop. No medieval words or art left on those screens.
- **Intrigue, political versions.** Back: Fabricate a Scandal (vanilla fabricate hook), Leak to the Press (expose a
  secret, blackmail), Plot to Oust (leadership plots built on depose/claim schemes), and an affair scheme (seduce)
  that only targets fictional or AI-generated characters, never the royal family or minors. Murder and abduction stay
  off. All scheme events stay generic and fictional.
- **Map icons.** Holding, building and map-mode icons redrawn as fal.ai badges matching the ideology and stat icons.
- **Spouse ranks.** The PM's and party leaders' spouses take no rank (no "Empress"): done.

## Milestones

| # | Milestone | Done when |
|---|---|---|
| 0 ✅ | **Technical spikes** (prove the risky parts), all on a small test map: (a) generate and load the map, e.g. 10 Scottish seats; (b) a party as a landless kingdom-tier title with a leadership election by its MPs; (c) a general election transferring 650 titles, with timing; (d) a peerage as a landless county-tier title held by a non-MP, life vs hereditary; (e) a mayoralty as a landless duchy-tier title held by a non-MP; (f) a reskinned landless adventurer (candidate) taking a selection contract; (g) a council as a landless title with stored party seat counts and a council election; (h) a devolved parliament: a kingdom-tier title held by its First Minister, plus Northern Ireland's First Minister/deputy diarchy | Each spike works in game, or we've changed the design |
| 1 ✅ | **Map**: all 650 seats from 2024 data, heightmap, rivers and terrain | Shipped |
| 2 ✅ | **2024 bookmark**: titles, parties, the 650 MPs elected in July 2024, the Starmer cabinet, the opposition | Shipped |
| 3 ✅ | **Core loop**: elections, polls, by-elections, candidate selection, leadership elections, the career ladder from unlanded activist to MP to PM | Shipped; balance continues |
| 4 | **Parliament**: Commons votes, whips, confidence motions, rebellions; the House of Lords (peerages, honours lists, revising bills); mayors and their elections; the devolved parliaments; councils and council elections | |
| 5 | **Content**: political schemes, scandals (secrets), press, activities (conference, PMQs, campaigning), events | It's fun |
| 6 ✅ | **Polish and release**: UI, nine languages, Workshop page | Public beta released; localization and dark interface followed in 0.4 |
| 7 ✅ | **1979 Thatcher bookmark**: reusable dated-snapshot generator; the 1979 Commons mapped to the 2024 constituencies; Thatcher's first ministry, opposition and election baseline; era rules; recognisable models for the significant figures | Shipped in 0.5: start as Thatcher, Callaghan or another 1979 MP and play a functioning Parliament |
| 8+ | **More bookmarks**, going back: Sunak 2022, Truss, Johnson, May, Cameron, Brown, Blair, Major, Callaghan, Wilson, Heath, Douglas-Home, Macmillan, Eden, Churchill 1951, Attlee, Churchill 1940, Chamberlain 1937 | |

## Open questions

None at the moment. Small design questions will come up during the spikes.
