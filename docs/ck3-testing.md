# Testing mods in the real game

Mods are tested by running CK3 itself, not by asking someone to click through and send screenshots. The repository-level
tools are in `common/ck3_test/`. The mod keeps its own tests and test harness.

The test tools are macOS-only (they use `osascript`, `screencapture`, `sips` and two small Swift helpers built with
`swiftc`); the mods themselves aren't. Steam must be running. The tools look for the game and its user folder in the
macOS Steam defaults; set `CK3_GAME_DIR` (the `Crusader Kings III/game` folder) and `CK3_DOCS_DIR` (the
`Paradox Interactive/Crusader Kings III` user folder) to override them. Install the mod under test into the launcher
first with `python3 common/tools/install_mod.py <mod>`.

**The tools change your real game settings while they run** and put them back afterwards: `dlc_load.json` (the
playset), `continue_game.json` (when a run passes `SAVE=`), `pdx_settings.txt` (`make_save.sh` sets monthly
autosaves) and a temporary `mod/rf_test.mod`. Backups go to `$TMPDIR` (`ck3_dlc_load.json.bak`,
`ck3_continue_game_bak.json`, `wm_pdx_settings.bak`, `wm_continue_game.bak`). A trap restores them when the script
exits; if the shell itself is killed, copy them back by hand.

## How it works

`common/ck3_test/run_test.sh` does the following:

1. It adds a temporary **test harness** mod (the mod's `tools/ck3_test/harness/` folder) to the launcher's playset
   (`dlc_load.json`, backed up first). With `SAVE=<file.ck3>` it also points `continue_game.json` at that save,
   with the game version read from the installed game's `launcher/launcher-settings.json`.
2. It starts CK3 in debug mode on the last save: `ck3 -debug_mode -continuelastsave`.
3. A widget in the harness (`gui/rf_test.gui`, with `trigger_on_create = yes`) runs scripted GUI `rf_test_s1` once
   the save has loaded. That runs the effect `rf_test_effect`, which is the test suite.
4. The suite writes results with `debug_log`. `RFT start`, `RFT_PHASE`, `RFT_PASS`, `RFT_FAIL`, `RFT_DETAIL` and
   `RFT_TIME` lines go to `logs/debug.log`, and the run ends with `RFT done`.
5. It copies the log from `RFT start` onwards into the output file, closes the game **without saving**, and restores
   the playset.

Then `python3 common/ck3_test/report.py <log>` prints the pass/fail summary. `debug_log_scopes = yes` after an
`RFT_DETAIL` line prints the offending scope.

```sh
python3 westminster/tools/ck3_test/gen_gameplay.py   # writes the suite into the harness
HARNESS=westminster/tools/ck3_test/harness common/ck3_test/run_test.sh westminster/tools/ck3_test/gameplay.log
python3 common/ck3_test/report.py westminster/tools/ck3_test/gameplay.log
python3 common/tools/ck3_checks.py errorlog wm_           # any errors from the mod's own files?
```

The mod under test must already be enabled in the playset. A mod's release script runs all of this, for example
`westminster/tools/release.sh`.

## Writing tests

Write the suite with a Python generator (Westminster: `tools/ck3_test/gen_gameplay.py`) rather than by hand. Each check
is a trigger, and the generator wraps it in `if/else` with `debug_log = "RFT_PASS name"` or `"RFT_FAIL name"`. A test
sets up its own scenario on the save (for example, start an election and check its results) and checks the results.

- The save is whatever CK3 loaded last (unless the run passes `SAVE=`), so tests mustn't depend on the player's own
  campaign.
- Saved temporary scopes inside loops can be stale when they're logged.
- Close the game promptly: the tools close it themselves. Don't leave CK3 running.

## UI walkthrough screenshots

`HARNESS=… common/ck3_test/ui_walkthrough.sh <out dir> <steps>` takes one screenshot per step:

- For each step it rewrites `<harness>/gui/rf_test.gui` to run `rf_test_s<step>`. The game reloads the GUI in debug
  mode, which runs that step.
- Before each capture it brings the game to the front and moves the mouse out of the way (`park_mouse.swift`,
  compiled to `$TMPDIR/rf_park_mouse`), so no tooltips appear.
- `FULL=1` keeps full screen resolution, for the Workshop page.

The generator for the steps chooses what each step shows using a global test-step variable.

- The screen must be unlocked, or the captures come out black.
- **Other languages:** change `language="l_english"` to `l_<language>` in `pdx_settings.txt`, take the screenshots, then
  put it back. Back up the file first.
- Find the game process with `pgrep -x ck3`. `pgrep -f MacOS/ck3` matches the calling shell's own command line.

## Booting a mod and driving the menus

For a total conversion (or any test without a save to load):

- `MODS="mod/<mod>.mod" common/ck3_test/boot_check.sh <out dir> [seconds]` starts the game with only those mods
  enabled, takes a screenshot every 30 seconds, keeps `error.log` and `debug.log`, then closes the game and
  restores the playset. "Total startup duration" in `debug.log` means the main menu loaded. "End loading of
  history" means history loaded too.
- `common/ck3_test/session.sh start | shot <png> | click <x> <y> [scroll] | stop` keeps the game running for a
  step-by-step session. `click.swift` clicks (or scrolls) at a point given as fractions of the screen, so
  coordinates read off a 1600px screenshot work at any resolution. Starting a new game: New Game, click the
  bookmark character, then Start. Space unpauses and `5` sets top speed (send them with `osascript` System Events
  keystrokes). The game autosaves on the 1st of each month, which gives `-continuelastsave` a save for the
  harness.

## Harness folder contents

The local harness is in `westminster/tools/ck3_test/harness/`. A new mod can use the same structure:

- `descriptor.mod`
- `gui/rf_test.gui` (rewritten by `ui_walkthrough.sh`)
- `gui/scripted_widgets/rf_test_widgets.txt`
- `common/scripted_guis/rf_test_guis.txt` (`rf_test_s1` … `rf_test_s<N>`)
- `common/scripted_effects/rf_test_effects.txt` (written by the generator; not in git, so run a generator before
  the first test)

Optionally add `on_action` hooks that log events the tests want to see.

## Looking at portraits

For portrait work, a temporary test mod with a HUD widget can show a page of portraits with names. In debug mode,
the GUI can be reloaded while the game runs.
