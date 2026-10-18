# Westminster

**Modern UK politics for Crusader Kings III.** A total conversion with six playable starts across 1945–2024, with historical MPs mapped onto 650 modern constituencies. Lead Margaret Thatcher's first government, govern
after the 2024 election, play another MP, or begin as a campaigner and climb from the doorstep to Downing Street.

| | |
|---|---|
| Source | **0.5.5**, prepared for the next upload; version identification update, no gameplay changes. |
| Workshop | [Public beta](https://steamcommunity.com/sharedfiles/filedetails/?id=3816349981): six-start build uploaded 18 October 2026 as **0.5.4**. |
| Game | Crusader Kings III 1.20 |
| Modding | [Character/DNA/policy guide](docs/modding.md), [contributing via PR](CONTRIBUTING.md) |
| Plans | [Roadmap](ROADMAP.md), [design notes](westminster/PLAN.md) |
| Forks | Welcome; see [branding and credit](BRANDING.md) |
| The mod in detail | [westminster/README.md](westminster/README.md): gameplay, the look, layout, build and test |
| Licence | Code [MIT](LICENSE); original assets [CC BY 4.0](LICENSE-ASSETS.md), AI images CC0; third-party material in [NOTICE.md](NOTICE.md) |

**Real names, fictional events.** Real politicians, other public figures and the royal family appear under their
real names. All events are generic and fictional, and nothing in the mod says or implies anything about any real
person. Westminster isn't affiliated with Parliament, any political party or the Royal Household, and it isn't made or
endorsed by Paradox Interactive.

The 18 October 2026 upload adds 1945, 1997, 2010 and 2016 starts, movement building, government/Brexit and press gameplay.
The source now uses 0.5.5 to distinguish that build from older uploads sharing 0.5.4. See [the changelog](westminster/workshop/CHANGELOG.md).

## What's in it

- Six starts: Attlee 1945, Thatcher 1979, Blair 1997, Cameron 2010, May 2016 and Starmer 2024.
- A career from activist to Prime Minister; parties as houses (Cross the Floor, Found a Party); leadership contests
  and the Speaker's election.
- Elections with monthly polls, seat-by-seat swing, by-elections, disputed results and coalitions; the House of
  Commons with bills, whips, rebellions, confidence votes and a live majority.
- Campaigns and conferences, public trust, campaign spending, party wings, devolution, ideology instead of religion,
  riots that march on Westminster, and the Crown as a minor figure.
- Playable landless campaigners, including Just Stop Oil, Extinction Rebellion and Amnesty International, who can
  organize, form a party and contest elections.
- A dark modern political interface, real flags, modern terms (Charisma, Economy, Security, Spin, Policy, Stamina;
  Funds, Profile, Political Capital, Party Brand, Clout, Pressure, Mandate).

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
  PLAN.md            design notes: how CK3 systems map to British politics
```

## Setup

- **Crusader Kings III 1.20** from Steam. The tools find the game in the usual Steam folders on macOS, Windows and
  Linux; set `CK3_GAME_DIR` (the `Crusader Kings III/game` folder) and `CK3_DOCS_DIR` (the
  `Paradox Interactive/Crusader Kings III` user folder) if yours is elsewhere.
- **Python:** 3.11 recommended. Source checks need only Python; builders need `requirements.txt`.
  macOS/Linux: `python3 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt`.
  Windows: `py -3.11 -m venv .venv`, then `.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **Build:** a clone has the scripts, localization and GUI, but not the generated textures and map images. Build them
  as [westminster/README.md](westminster/README.md#setup-install-and-test) describes (map, character histories, all bookmarks,
  seat leans, then the interface).
- **Play from a clone:** `python3 common/tools/install_mod.py westminster` writes the launcher's `.mod` file pointing
  at your clone; enable it in the launcher.
- **Source checks:** run the commands below from a clone; no CK3 installation, downloaded data or generated art needed.
  Manual in-game testing works on all platforms; window-driving helpers require macOS and `swiftc`. See [testing](docs/ck3-testing.md).
- **Releases** go to the Workshop through the Paradox launcher: see
  [westminster/workshop/PUBLISHING.md](westminster/workshop/PUBLISHING.md).

```sh
python3 common/tools/ck3_checks.py static westminster/westminster
python3 -m unittest discover -s westminster/tools/data -p 'test_*.py'
python3 westminster/workshop/translations/check.py
```

On Windows use `py` in place of `python3`. Two checks against installed vanilla files skip when CK3 is absent.
To play immediately, subscribe on Steam; the source ZIP is not a ready-to-play package.
For script-only local testing, see [reusing generated assets](docs/modding.md#local-playtesting).

## Making changes

Start with [the modding guide](docs/modding.md): it lists the source for each common edit and its rebuild command.
Character overrides are in `westminster/data/character_overrides.json`; no map or art rebuild is needed for stats.
Send changes as a [pull request](CONTRIBUTING.md). Please retain [credit when forking](BRANDING.md).

Before publishing source, run `python3 common/tools/check_secrets.py --history`. It scans tracked/unignored files
and locally reachable Git history without printing matched values; heuristic scanning cannot prove the absence of secrets.
