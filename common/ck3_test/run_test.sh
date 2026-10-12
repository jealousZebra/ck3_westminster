#!/bin/bash
# Runs a mod's in-game tests: starts CK3 in debug mode on the last save with a temporary
# test mod (the harness folder) whose widget runs rf_test_effect once the save has loaded.
# The mod's own test generator writes that effect into the harness.
# Results are debug_log lines starting with "RFT" in logs/debug.log. The game is closed
# without saving and the launcher's mod list is restored afterwards.
#
#   HARNESS=<mod>/tools/ck3_test/harness common/ck3_test/run_test.sh <out.log>
#
# MODS="mod/a.mod mod/b.mod" enables exactly those mods (plus the harness) instead of the current playset.
# SAVE=<file.ck3> loads that save instead of the last one. Both are put back afterwards.
# UNPAUSE=1 unpauses at top speed once "RFT start" is logged, for tests that check things after time passes
# (the suite schedules a later event that logs the rest and "RFT done"). See docs/ck3-testing.md.
# CK3_GAME_DIR / CK3_DOCS_DIR override the game and user folders (macOS Steam defaults below).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
DOCS="${CK3_DOCS_DIR:-$HOME/Documents/Paradox Interactive/Crusader Kings III}"	# the game's user folder
GAME="${CK3_GAME_DIR:-$HOME/Library/Application Support/Steam/steamapps/common/Crusader Kings III/game}"
BIN="$(dirname "$GAME")/binaries"
LOG="$DOCS/logs/debug.log"
HARNESS="${HARNESS:?set HARNESS to the test harness folder of the mod}"
HARNESS="$(cd "$HARNESS" && pwd)"
OUT="${1:-$HARNESS/../last_run.log}"

pgrep -qx ck3 && { echo "CK3 is already running; close it first."; exit 1; }
BAK="${TMPDIR:-/tmp}/ck3_dlc_load.json.bak"
cp "$DOCS/dlc_load.json" "$BAK"
printf 'version="0.1"\nname="Test Harness"\nsupported_version="1.20.*"\npath="%s"\n' "$HARNESS" > "$DOCS/mod/rf_test.mod"
python3 - "$DOCS/dlc_load.json" "${MODS-__keep__}" <<'PY'
import json,sys
p=sys.argv[1]; d=json.load(open(p))
if sys.argv[2] != "__keep__": d["enabled_mods"] = sys.argv[2].split()
if "mod/rf_test.mod" not in d["enabled_mods"]: d["enabled_mods"].append("mod/rf_test.mod")
json.dump(d,open(p,"w"))
PY
# -continuelastsave loads "save games/<title>.ck3", where <title> comes from continue_game.json
SAVEBAK="${TMPDIR:-/tmp}/ck3_continue_game_bak.json"
SAVENAME="zz_test_harness_save"
if [ -n "${SAVE:-}" ]; then
	cp "$DOCS/continue_game.json" "$SAVEBAK"
	cp "$SAVE" "$DOCS/save games/$SAVENAME.ck3"
	VERSION="$(CK3_GAME_DIR="$GAME" python3 "$HERE/../tools/ck3paths.py" version)"	# from the launcher's settings
	printf '{\n\t"title":\t"%s",\n\t"desc":\t"test save",\n\t"date":\t"%s",\n\t"rawGameVersion":\t"%s"\n}\n' "$SAVENAME" "$(date '+%Y-%m-%d %H:%M:%S')" "$VERSION" > "$DOCS/continue_game.json"
fi
restore() {
	pkill -x ck3; for i in $(seq 1 20); do pgrep -qx ck3 || break; sleep 2; done
	pkill -9 -x ck3 2>/dev/null
	cp "$BAK" "$DOCS/dlc_load.json"; rm -f "$DOCS/mod/rf_test.mod" "$BAK"
	if [ -n "${SAVE:-}" ] && [ -f "$SAVEBAK" ]; then cp "$SAVEBAK" "$DOCS/continue_game.json"; rm -f "$SAVEBAK" "$DOCS/save games/$SAVENAME.ck3"; fi
}
trap restore EXIT
(cd "$BIN" && nohup ./ck3.app/Contents/MacOS/ck3 -debug_mode -continuelastsave >/dev/null 2>&1 &)
sleep 20
UNPAUSED=""
for i in $(seq 1 ${WAIT_LOOPS:-120}); do
	grep -q "RFT done" "$LOG" 2>/dev/null && break
	if [ -n "${UNPAUSE:-}" ] && [ -z "$UNPAUSED" ] && grep -q "RFT start" "$LOG" 2>/dev/null; then
		open -a "$BIN/ck3.app"; sleep 2
		osascript -e 'tell application "System Events" to key code 49' -e 'tell application "System Events" to keystroke "5"'
		UNPAUSED=1
	fi
	pgrep -qx ck3 || { echo "CK3 exited before the test finished"; break; }
	sleep 3
done
if [ -n "${SHOT:-}" ]; then sleep 6; screencapture -x "$SHOT"; fi
awk '/RFT start/{f=1} f' "$LOG" > "$OUT"
echo "Test log: $OUT ($(grep -c RFT "$OUT") RFT lines)"
[ -n "${PREFIX:-}" ] && grep -n "$PREFIX" "$DOCS/logs/error.log" | head -20
true
