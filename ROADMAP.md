# Westminster roadmap

What's planned after the 0.3 beta (released 2026-10-09; 0.3.1 switched achievements off). Written 2026-10-12 from
the Workshop comments and the owner's own play, and reviewed with the owner. Design detail for each item goes into
[westminster/PLAN.md](westminster/PLAN.md) before it's built; UX changes are agreed before they're built.

## What players said (Workshop comments, 44 so far)

| Theme | How many | Example |
|---|---|---|
| Crashes on start-up or while loading | 5, plus 1 stutter | "crashes before I get to the main menu" |
| Interface too bright | 6 | "The white UI is burning my eyes"; "can we have a dark mode?" |
| The unlanded start is broken | 1 | contract schemes don't run; travelling to accept a contract loops forever |
| Stutter every minute or so | 1 | probably a weekly or monthly loop over all 650 seats |
| Chinese translation | about 8 | "Could you localize the English parts into Chinese?" |
| Schemes back | 1 | "politicians absolutely seduce each other" |
| Extreme or fringe parties | 1 | play hard-line parties and "really reshape politics" |
| A Victoria 2-style interface | 1 | |

## 0.4: stability, a darker look and a proper unlanded start

In this order.

### 1. Crashes and stutter (first)
- Boot-test with every DLC switched off in the launcher: some of the copied vanilla interface files may assume content
  that players without DLC don't have.
- Make the mod smaller and lighter to load: the two terrain detail maps are 192 MB each and the mod is about 900 MB
  on disk. Halve or compress textures where nobody can see the difference.
- Check whether CK3 has been patched since 1.20.0.4, and test on the current version.
- Ask on the Workshop page for `error.log` and the DLC list from anyone who crashes (a pinned comment).
- Find the once-a-minute stutter: profile the weekly majority watcher and the monthly poll, trust and devolution ticks,
  which loop over all 650 seats, and spread or cache the work.

### 2. A darker interface
- A "night edition" of the newspaper look as the default: charcoal panels, off-white text, the same red accent and
  typography. Every hand-tuned colour (text formats, paper tints, overlays, the seat chart, the bookmark map) moves to
  the dark palette in `tools/ui/build_theme.py` and friends.
- Open decision: whether to also offer the current light look as an optional companion mod.

### 3. The unlanded start, fixed and themed
- Fix the contract schemes that never run and the endless travel loop.
- Theme the whole adventurer flow: the camp becomes a campaign office, camp purposes become political focuses (for
  example Grassroots Organiser, Think-Tank Wonk, Party Fixer, Media Pundit), contracts read as modern jobs, and no
  medieval wording or art is left on those screens.
- New fal.ai pictures for each focus and the camp backdrops, politics-specific.

### 4. Intrigue options back (political versions only)
- Bring back schemes in political dress, for example: Fabricate a Scandal (hooks), Leak to the Press (exposing
  secrets, blackmail), Plot to Oust (leadership plots), and an affair scheme limited to fictional or AI characters.
- Murder and abduction stay off. Events stay generic and fictional; nothing is scripted against a named real person.
- Open decision: the exact list.

### 5. New map icons
- Replace the icons shown on the map (holdings, buildings, map-mode buttons) with fal.ai icons in the same badge style
  as the ideology and stat icons: a constituency office, a town hall, a party headquarters and so on.

### Also in 0.4
- The "Empress" label on the Prime Minister's spouse (the fix is written and was held back from 0.3.1).

## 0.5: Margaret Thatcher, 4 May 1979

The first historical bookmark and the template for every bookmark that follows.

- Refactor the 2024-only generator into reusable dated snapshots for MPs, parties, governments, opposition and
  election results.
- Start on **4 May 1979**, with Margaret Thatcher as Prime Minister, James Callaghan leading Labour, David Steel
  leading the Liberals, Elizabeth II as monarch, and the first Thatcher ministry.
- Map the 1979 Commons onto the existing 2024 constituencies using the historical-seat rules in `PLAN.md`, and use
  the 1979 result rather than 2024 vote shares as the election and polling baseline.
- Apply era rules: no devolved parliaments or modern mayoralties, the pre-1999 House of Lords, period parties and
  offices, and period-appropriate terminology and presentation.
- Add a focused early-Thatcher situation around inflation, industrial relations and the government's Commons
  majority. Reuse generic political systems elsewhere so the bookmark remains a manageable vertical slice.
- Create recognisable CK3 character models for the party leaders, Cabinet and other significant figures of 1979.
- Done when a player can start as Thatcher, Callaghan or another 1979 MP, play a functioning Parliament and reach
  the next election using 1979 data.

## 0.6: newspapers

- **Legends become press coverage:** a legend becomes a running story (a scandal, a comeback, a landmark bill) that
  spreads across seats like a legend and moves Profile and public trust.
- **Papers with leanings:** a handful of fictional papers, for example *The Clarion* (left), *The Ledger* (centre,
  financial), *The Sentinel* (right), *The Daily Bulletin* (populist tabloid) and *The Caledonian* (Scottish). The
  same story is framed differently by each.
- **Editors as characters:** each paper has an unlanded editor to court, feud with or be endorsed by; election-night
  front pages come from the paper that backs you.
- Open decisions: fictional papers (recommended: real titles bring trademark and defamation risk) or real ones; and
  what "unlanded nobles as editors" should build on (CK3's landless characters and guests, or new landless titles
  like the parties).

## Later

- **Chinese translation** of the in-game text (about 2,000 interface strings plus Westminster's own events), with
  volunteer reviewers from the comments; other languages after it.
- **Fringe parties:** made-up fringe parties a player can found, very hard to play; never real far-right parties.
  Open decision.
- More bookmarks, using the 1979 pipeline and working back through every Prime Minister to Chamberlain (see PLAN.md
  milestones).
- The House of Lords, mayors and councils as full systems (now only early technical tests).
- Balance over long games, and AI behaviour after a decade or more.
- Modern clothing for portraits.

## Open decisions for the owner

1. A light look as an optional companion mod, or dark only?
2. Which schemes come back, under which names?
3. Fictional or real newspapers?
4. What "unlanded nobles as editors" builds on?
5. Fringe parties: yes (made-up only) or no?
