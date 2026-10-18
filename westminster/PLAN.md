# Design notes

Westminster follows one politician from campaigner to MP, minister, party leader and Prime Minister.
The 650 modern constituencies are the shared map for every start. Release plans belong in [the roadmap](../ROADMAP.md);
implementation recipes are in [the modding guide](../docs/modding.md).

## CK3 systems

| CK3 | Westminster |
| --- | --- |
| County title | Constituency; its holder is the MP |
| Kingdom title `k_party_*` | Political party |
| Dynasty house | Party identity; synchronized with `var:wm_party` |
| Empire `e_united_kingdom` | UK government; its holder is PM |
| Faith, religion, doctrines | Ideology, political camp, policy attitudes |
| Council | Cabinet |
| Gold, prestige, piety | Funds, Profile, Political Capital |
| Legitimacy | Mandate |
| Diplomacy, stewardship, martial, intrigue, learning, prowess | Charisma, Economy, Security, Spin, Policy, Stamina |
| Hooks, schemes and factions | Favours, political manoeuvres and party pressure |

## State and scope

- Party membership is a **title reference** in the character's `wm_party` variable. Party houses alone do not drive elections.
- Constituency vote leans and candidate references live on county titles. Polls, election and parliamentary state use globals.
- Career standing/personal vote and press relationships belong to characters. Movement membership/donors belong to party titles.
- Bills move through the existing Commons whip/division process. A government programme uses the Public Services Bill;
  Brexit has its own bill type. Defeat must not apply passage rewards.
- Dated history defines the starting holders; on-actions initialize the cabinet, coalition and gameplay state.
- Generated scripts are committed so ordinary CK3 edits are reviewable. Builders remain the source of truth for their outputs.

## Historical starts

The 18 October 2026 upload contains 1945, 1979, 1997, 2010, 2016 and 2024 starts. Historical constituencies are approximated
on the modern map; snapshot files record notional seats and unlanded MPs. Most minor historical characters have
approximate birth dates. Keep those limits visible; do not describe the map as exact historical geography.

## Content boundaries

Real public figures use real names and approximate CK3 likenesses. Events are generic and fictional; no scripted
allegations against named living people. MP spouses/relatives are invented. Royal history is separately documented.
Ideology assignments and stats are gameplay abstractions, not factual judgements about a person's character.

Warfare, murder and abduction are disabled; political competition should resolve through elections, Parliament,
party contests and events. Keep vanilla startup safeguards and portrait caches: missing them caused real Windows crashes.

## Depth still to build

The current development model shares fiscal room, debt, services and economic confidence; it does not model a full
budget for every department. Committee inquiries are not a complete committee-chair career. Press relationships do
not yet provide a cast of independent newspaper owners. The Lords and local politics remain areas for expansion.
