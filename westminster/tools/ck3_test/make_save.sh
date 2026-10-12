#!/bin/bash
# Makes a fresh test save for the spike tests: starts a new game on the 2024 test bookmark, lets it run to the
# first monthly autosave, and copies that to tools/ck3_test/saves/wm_2025.ck3. Re-run after changing titles or
# history (a save only has the titles that existed when it was made). Needs an unlocked screen: it clicks the menus.
# The click points are fractions of the screen, measured full-screen on a 2560x1664 display with the game's
# interface scale at 0.8: check them with common/ck3_test/session.sh on another screen.
# The game's autosave setting is switched to monthly for the run and put back afterwards.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
DOCS="${CK3_DOCS_DIR:-$HOME/Documents/Paradox Interactive/Crusader Kings III}"	# the game's user folder
S="$ROOT/common/ck3_test/session.sh"
SETTINGS="$DOCS/pdx_settings.txt"
cp "$SETTINGS" "${TMPDIR:-/tmp}/wm_pdx_settings.bak"
cp "$DOCS/continue_game.json" "${TMPDIR:-/tmp}/wm_continue_game.bak"
python3 - "$SETTINGS" <<'PY'
import re, sys
p = sys.argv[1]; s = open(p).read()
s = re.sub(r'("autosave"=\{\s*version=\d+\s*value=)"[A-Z_]+"', r'\1"MONTHLY"', s)
open(p, "w").write(s)
PY
finish() {
	"$S" stop >/dev/null
	cp "${TMPDIR:-/tmp}/wm_pdx_settings.bak" "$SETTINGS"
	cp "${TMPDIR:-/tmp}/wm_continue_game.bak" "$DOCS/continue_game.json"
	# The game rotates autosaves (autosave.ck3, autosave_1.ck3, ...): remove the ones this run made
	find "$DOCS/save games" -name 'autosave*.ck3' -newer "${TMPDIR:-/tmp}/wm_save_marker" -delete
}
trap finish EXIT
touch "${TMPDIR:-/tmp}/wm_save_marker"
MODS="mod/westminster.mod" "$S" start || exit 1
"$S" click 0.234 0.419; sleep 6        # New Game
"$S" click 0.244 0.410; sleep 3        # Keir Starmer's name banner (his place: tools/ui/build_bookmark_screen.py layout())
"$S" click 0.8825 0.768                # Start
for i in $(seq 1 60); do sleep 3; grep -q "Setup completion\|Game setup done" "$DOCS/logs/debug.log" && break; done
sleep 15
osascript -e 'tell application "System Events" to key code 49'     # unpause
osascript -e 'tell application "System Events" to keystroke "5"'   # top speed
for i in $(seq 1 100); do
	sleep 3
	[ "$DOCS/save games/autosave.ck3" -nt "${TMPDIR:-/tmp}/wm_save_marker" ] && break
	pgrep -qx ck3 || { echo "CK3 exited"; exit 1; }
done
sleep 3
mkdir -p "$HERE/saves"
cp "$DOCS/save games/autosave.ck3" "$HERE/saves/wm_2025.ck3" && echo "saved $HERE/saves/wm_2025.ck3"
