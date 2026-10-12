#!/bin/bash
# Screenshots of a mod's UI: starts CK3 on the last save with the harness, then for each
# step rewrites <harness>/gui/rf_test.gui (the game reloads it in debug mode, which runs
# scripted GUI rf_test_s<step>) and takes a screenshot. Needs an unlocked screen.
# FULL=1 keeps the screenshots at full screen resolution (for the Workshop page).
#
#   HARNESS=<mod>/tools/ck3_test/harness common/ck3_test/ui_walkthrough.sh <out dir> <steps>
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
DOCS="${CK3_DOCS_DIR:-$HOME/Documents/Paradox Interactive/Crusader Kings III}"	# the game's user folder
GAME="${CK3_GAME_DIR:-$HOME/Library/Application Support/Steam/steamapps/common/Crusader Kings III/game}"
BIN="$(dirname "$GAME")/binaries"
LOG="$DOCS/logs/debug.log"
HARNESS="${HARNESS:?set HARNESS to the test harness folder of the mod}"
HARNESS="$(cd "$HARNESS" && pwd)"
OUTDIR="${1:?output folder}"; STEPS="${2:-10}"
mkdir -p "$OUTDIR"
PARK="${TMPDIR:-/tmp}/rf_park_mouse"
[ -x "$PARK" ] || swiftc -O "$HERE/park_mouse.swift" -o "$PARK" || exit 1
widget() {	# the widget runs scripted GUI rf_test_s<step> when (re)created
	cat > "$HARNESS/gui/rf_test.gui" <<GUI
widget = {
	name = "rf_test_widget"
	size = { 10 10 }
	visible = "[GetPlayer.IsValid]"
	state = {
		name = rf_run
		trigger_on_create = yes
		on_start = "[GetScriptedGui('rf_test_s$1').Execute( GuiScope.SetRoot( GetPlayer.MakeScope ).End )]"
	}
}
GUI
}
pgrep -qx ck3 && { echo "CK3 is already running; close it first."; exit 1; }
BAK="${TMPDIR:-/tmp}/ck3_dlc_load.json.bak"
cp "$DOCS/dlc_load.json" "$BAK"
printf 'version="0.1"\nname="Test Harness"\nsupported_version="1.20.*"\npath="%s"\n' "$HARNESS" > "$DOCS/mod/rf_test.mod"
python3 -c "import json,sys;p=sys.argv[1];d=json.load(open(p));d['enabled_mods']+=['mod/rf_test.mod'] if 'mod/rf_test.mod' not in d['enabled_mods'] else [];json.dump(d,open(p,'w'))" "$DOCS/dlc_load.json"
restore() {
	pkill -x ck3; for i in $(seq 1 20); do pgrep -qx ck3 || break; sleep 2; done
	pkill -9 -x ck3 2>/dev/null
	cp "$BAK" "$DOCS/dlc_load.json"; rm -f "$DOCS/mod/rf_test.mod" "$BAK"
}
trap restore EXIT
widget 1
(cd "$BIN" && nohup ./ck3.app/Contents/MacOS/ck3 -debug_mode -continuelastsave >/dev/null 2>&1 &)
sleep 20
for i in $(seq 1 120); do grep -q "RFT done" "$LOG" 2>/dev/null && break; sleep 2; done
for step in $(seq 1 "$STEPS"); do
	if [ "$step" -gt 1 ]; then
		n=$(grep -c "RFT done" "$LOG")
		widget "$step"
		for i in $(seq 1 30); do [ "$(grep -c "RFT done" "$LOG")" -gt "$n" ] && break; sleep 1; done
	fi
	open -a "$BIN/ck3.app"	# bring the game to the front
	"$PARK"	# and move the mouse off the windows (no tooltips)
	sleep 4
	screencapture -x "$OUTDIR/step$step.png"
	[ -z "${FULL:-}" ] && sips -Z 1600 "$OUTDIR/step$step.png" --out "$OUTDIR/step$step.png" >/dev/null
	echo "step $step captured"
done
widget 1	# leave it starting at step 1
