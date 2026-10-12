#!/bin/bash
# Starts CK3 with only the given mods enabled (no save loaded), waits, takes screenshots, keeps the logs, then
# closes the game and restores the launcher's playset. For checking that a mod (a total conversion especially)
# gets the game to the main menu, and what the error log says on the way.
#
#   MODS="mod/westminster.mod" common/ck3_test/boot_check.sh <out dir> [seconds to wait, default 150]
#
# Writes <out dir>/boot_<n>.png every 30 seconds, plus error.log and debug.log copies. Needs an unlocked screen
# for the screenshots. See docs/ck3-testing.md.
set -u
DOCS="${CK3_DOCS_DIR:-$HOME/Documents/Paradox Interactive/Crusader Kings III}"	# the game's user folder
GAME="${CK3_GAME_DIR:-$HOME/Library/Application Support/Steam/steamapps/common/Crusader Kings III/game}"
BIN="$(dirname "$GAME")/binaries"
MODS="${MODS?set MODS to the .mod files to enable (empty for vanilla), e.g. mod/westminster.mod}"
OUTDIR="${1:?output folder}"; WAIT="${2:-150}"
mkdir -p "$OUTDIR"

pgrep -qx ck3 && { echo "CK3 is already running; close it first."; exit 1; }
BAK="${TMPDIR:-/tmp}/ck3_dlc_load.json.bak"
cp "$DOCS/dlc_load.json" "$BAK"
python3 -c "import json,sys;p=sys.argv[1];d=json.load(open(p));d['enabled_mods']=sys.argv[2].split();json.dump(d,open(p,'w'))" "$DOCS/dlc_load.json" "$MODS"
restore() {
	pkill -x ck3; for i in $(seq 1 20); do pgrep -qx ck3 || break; sleep 2; done
	pkill -9 -x ck3 2>/dev/null
	cp "$BAK" "$DOCS/dlc_load.json"; rm -f "$BAK"
}
trap restore EXIT
(cd "$BIN" && nohup ./ck3.app/Contents/MacOS/ck3 -debug_mode >/dev/null 2>&1 &)
n=0
for t in $(seq 30 30 "$WAIT"); do
	sleep 30
	pgrep -qx ck3 || { echo "CK3 exited after about ${t}s"; break; }
	n=$((n + 1))
	open -a "$BIN/ck3.app"
	sleep 2
	screencapture -x "$OUTDIR/boot_$n.png" && sips -Z 1600 "$OUTDIR/boot_$n.png" --out "$OUTDIR/boot_$n.png" >/dev/null
done
cp "$DOCS/logs/error.log" "$OUTDIR/error.log" 2>/dev/null
cp "$DOCS/logs/debug.log" "$OUTDIR/debug.log" 2>/dev/null
[ -f "$DOCS/crashes" ] || true
echo "Screenshots and logs in $OUTDIR ($(grep -c '\[E\]' "$OUTDIR/error.log" 2>/dev/null || echo 0) error lines)"
