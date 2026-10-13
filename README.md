# Westminster

**Modern UK politics for Crusader Kings III.** A total conversion that starts on 5 July 2024, the day after the
general election, with all 650 real MPs on a map of the real constituencies. Play any MP, or start as a young party
activist, and climb from the doorstep to Downing Street: win selection, fight elections, whip the Commons and survive
a confidence vote.

| | |
|---|---|
| Status | **0.3.1 public beta** on the [Steam Workshop](https://steamcommunity.com/sharedfiles/filedetails/?id=3816349981). In-game localization: English, French, German, Japanese, Korean, Polish, Russian, Simplified Chinese and Spanish. |
| Game | Crusader Kings III 1.20 |
| Plans | [ROADMAP.md](ROADMAP.md): the next updates. Design decisions: [westminster/PLAN.md](westminster/PLAN.md) |
| The mod in detail | [westminster/README.md](westminster/README.md): gameplay, the look, layout, build and test |
| Licence | Code [MIT](LICENSE); original assets [CC BY 4.0](LICENSE-ASSETS.md), AI images CC0; third-party material in [NOTICE.md](NOTICE.md) |

**Real names, fictional events.** Real politicians, other public figures and the royal family appear under their
real names. All events are generic and fictional, and nothing in the mod says or implies anything about any real
person. Westminster isn't affiliated with Parliament, any political party or the Royal Household, and it isn't made or
endorsed by Paradox Interactive.

## What's in it

- The 2024 Parliament: 650 MPs in their seats, 13 parties, the devolved governments, likenesses for senior figures.
- A career from activist to Prime Minister; parties as houses (Cross the Floor, Found a Party); leadership contests
  and the Speaker's election.
- Elections with monthly polls, seat-by-seat swing, by-elections, disputed results and coalitions; the House of
  Commons with bills, whips, rebellions, confidence votes and a live majority.
- Campaigns and conferences, public trust, campaign spending, party wings, devolution, ideology instead of religion,
  riots that march on Westminster, and the Crown as a minor figure.
- A newspaper-style interface, real flags, modern terms (Charisma, Economy, Security, Spin, Policy, Stamina; Funds,
  Profile, Political Capital, Party Brand, Clout, Pressure, Mandate).

## Layout

```
README.md            this file
ROADMAP.md           planned updates
LICENSE, LICENSE-ASSETS.md, NOTICE.md, CONTRIBUTING.md, requirements.txt
docs/                CK3 modding notes, in-game testing, Steam Workshop publishing
common/
  ck3_test/          in-game test harness: run_test.sh, session.sh, report.py, boot_check.sh, ui_walkthrough.sh
  tools/             ck3_checks.py (static and error-log checks), ck3paths.py (game paths), install_mod.py
westminster/
  westminster/       the mod itself (what the launcher uploads)
  tools/             generators (map/, data/, ui/), in-game tests (ck3_test/), release.sh
  art/, data/        source art (fal.ai cache) and source data notes
  workshop/          Steam page text in 9 languages, screenshots, changelog, PUBLISHING.md
  PLAN.md            design: how CK3 systems map to British politics
```

## Setup

- **Crusader Kings III 1.20** from Steam. The tools find the game in the usual Steam folders on macOS, Windows and
  Linux; set `CK3_GAME_DIR` (the `Crusader Kings III/game` folder) and `CK3_DOCS_DIR` (the
  `Paradox Interactive/Crusader Kings III` user folder) if yours is elsewhere.
- **Python 3.9 or newer:** `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
- **Build:** a clone has the scripts, localization and GUI, but not the generated textures and map images. Build them
  as [westminster/README.md](westminster/README.md#setup-install-and-test) describes (map, the 2024 bookmark, seat
  leans, then the interface).
- **Play from a clone:** `python3 common/tools/install_mod.py westminster` writes the launcher's `.mod` file pointing
  at your clone; enable it in the launcher.
- **In-game tests** (`common/ck3_test/`) are macOS-only: they drive the game window with small Swift helpers and
  need `swiftc` (Xcode command-line tools). The generators and static checks work anywhere.
- **Releases** go to the Workshop through the Paradox launcher: see
  [westminster/workshop/PUBLISHING.md](westminster/workshop/PUBLISHING.md).
