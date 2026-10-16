# Westminster changelog

## 0.5.4 — Windows Startup Fix

- Retained the vanilla portrait-cache data used behind the main menu, fixing a reproduced Windows startup crash.
- Added file-level overrides for vanilla situation and struggle history, so the startup protections also work when the launcher retains older mod metadata.
- Added regression checks for portrait-cache coverage, regeneration and history overrides.

Windows CK3 1.20.1.1 testing passed fresh 1979 and 2024 campaigns with both current and outdated launcher metadata.
Existing vanilla script warnings remain; Linux and long campaigns are not verified. Start a fresh campaign when testing this update.

## 0.5.3 — Startup & Stability

- Corrected duplicate main-menu visibility settings and invalid startup/event script syntax.
- Excluded vanilla struggle and situation history that referenced provinces and titles outside Westminster's map.
- Added map locators and a correctly sized BGRA winter lookup texture.
- Fixed local-flavour character generation and guarded real-person setup for unborn or deceased characters, including the 1979 cast.
- Gave distinct IDs to the two pairs of same-name 1979 MPs and corrected historical cabinet initialization and election baselines.
- Repaired campaign-office localization formatting in all nine languages and restored translated trait labels.
- Removed vanilla historical battlefield travel destinations that referenced the wrong map.
- Added release checks for localization regressions and required map assets.

Start a new campaign for the corrected 1979 history and startup changes. Tested on macOS with CK3 1.20.1;
Windows/Linux crash reports still need verification on affected machines.

## 0.5.1 — Polish & Improvements

- Refined presentation throughout Westminster.
- Added quality-of-life and usability improvements.
- Made small fixes and adjustments across the mod.

## 0.5 — Thatcher, 1979

- Added a new 4 May 1979 start, the 1979 Commons, Thatcher's first Cabinet and key political figures.
- Added the 1979 election baseline, opening government situation and full bookmark artwork.
- Added recognisable character models for leading figures and fixed the main-menu and bookmark presentation.
- Kept all starting constituencies within the UK while preserving independence gameplay.

## 0.4 (beta)
- Added French, German, Japanese, Korean, Polish, Russian, Simplified Chinese and Spanish localization.
- Added playable campaigners from Just Stop Oil, Extinction Rebellion and Amnesty International, with paths to
  form a party, stand for election and enter Parliament.
- Redesigned the dark interface with clearer alerts and new modern political artwork for the HUD, lifestyles,
  perks and personality traits.
- Improved landless campaign contracts and corrected titles for the spouses of party leaders and the Prime Minister.

## 0.3.1 (beta)
- Achievements are switched off while Westminster is active (every vanilla achievement is made impossible;
  tools/data/build_safeguards.py).

## 0.3 (beta)
First public release, on the Steam Workshop. CK3 1.20, English only.
- The map: the 650 Westminster constituencies from the July 2024 boundaries, the nations and ITL2 areas, real terrain.
- The 2024 bookmark (5 July 2024): the 650 MPs elected on 4 July 2024 in their seats, the 13 parties that won seats,
  Keir Starmer's government, the devolved governments, and a playable young activist (fictional).
- Careers: party jobs build Party Standing; the candidate assessment, the approved list and a selection contest lead
  to a seat at the next election or by-election.
- Parties are houses: Cross the Floor, Found a Party; leadership contests (nominations, then the members' vote) and
  challenges; the Speaker's election.
- Elections: monthly polls, dissolution after 58 months or an early election, seat-by-seat swing from 2024,
  by-elections, front-page results, recounts and election courts, and a PM who can refuse to concede.
- Coalitions and confidence-and-supply deals in a hung parliament, with a Deputy PM; deals can collapse.
- The House of Commons: government bills, the Chief Whip's forecast, whipping, rebellions and losing the whip,
  motions of no confidence, and a live working majority.
- Weekly campaign choices and party conferences.
- Public trust, campaign spending (press and smear campaigns), party wings, and devolution (independence support,
  referendums, powers, Stormont).
- Ideology instead of religion: five camps and 15 ideologies; "Change Your Politics".
- Riots that make demands and march on Westminster.
- The Crown as a ceremonial title outside the PM's realm.
- The State of the Parties panel: latest poll, public trust, the Commons seat chart and a poll tracker.
- A newspaper-style interface: newsprint skin, Playfair Display and Source Serif 4, AI-generated press-photo pictures,
  real flags for the nations and for the counties and cities that have one, recognisable portraits for senior
  figures, and modern names for skills, currencies, ranks and the Cabinet.
- Vanilla's medieval events and decisions are removed; murder, abduction and seduction schemes are switched off.

Known issues: AI balance over long games is untested; portraits still wear medieval clothing; some vanilla screens
still look medieval; only the 2024 bookmark.
