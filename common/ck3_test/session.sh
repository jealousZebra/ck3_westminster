#!/bin/bash
# Interactive test session: start CK3 with only the given mods and leave it running, so menus can be driven step
# by step with click.swift and screenshots; then stop it and restore the launcher's playset.
#
#   MODS="mod/westminster.mod" common/ck3_test/session.sh start   # waits until the main menu has loaded
#   common/ck3_test/session.sh shot <file.png>                       # screenshot (1600px wide)
#   common/ck3_test/session.sh click <x fraction> <y fraction> [n]   # click (fractions of the screen), or scroll n
#   common/ck3_test/session.sh stop                                  # quit the game, restore the playset
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
DOCS="${CK3_DOCS_DIR:-$HOME/Documents/Paradox Interactive/Crusader Kings III}"	# the game's user folder
GAME="${CK3_GAME_DIR:-$HOME/Library/Application Support/Steam/steamapps/common/Crusader Kings III/game}"
BIN="$(dirname "$GAME")/binaries"
BAK="${TMPDIR:-/tmp}/ck3_session_dlc_load.json"
CLICK="${TMPDIR:-/tmp}/rf_click"
case "${1:-}" in
start)
	pgrep -qx ck3 && { echo "CK3 is already running"; exit 1; }
	[ -f "$BAK" ] && { echo "A session backup exists ($BAK): run stop first"; exit 1; }
	cp "$DOCS/dlc_load.json" "$BAK"
	python3 -c "import json,sys;p=sys.argv[1];d=json.load(open(p));d['enabled_mods']=sys.argv[2].split();json.dump(d,open(p,'w'))" "$DOCS/dlc_load.json" "${MODS?set MODS}"
	(cd "$BIN" && nohup ./ck3.app/Contents/MacOS/ck3 -debug_mode >/dev/null 2>&1 &)
	sleep 10
	for i in $(seq 1 90); do
		grep -q "Total startup duration" "$DOCS/logs/debug.log" 2>/dev/null && break
		pgrep -qx ck3 || { echo "CK3 exited"; exit 1; }
		sleep 2
	done
	sleep 3; open -a "$BIN/ck3.app"; echo "main menu loaded" ;;
shot)
	open -a "$BIN/ck3.app"; sleep 1
	screencapture -x "$2" && sips -Z 1600 "$2" --out "$2" >/dev/null && echo "$2" ;;
click)
	[ "$CLICK" -nt "$HERE/click.swift" ] || swiftc -O "$HERE/click.swift" -o "$CLICK" || exit 1
	open -a "$BIN/ck3.app"; sleep 0.5
	"$CLICK" "$2" "$3" ${4:-} ;;
stop)
	pkill -x ck3; for i in $(seq 1 20); do pgrep -qx ck3 || break; sleep 2; done
	pkill -9 -x ck3 2>/dev/null
	[ -f "$BAK" ] && cp "$BAK" "$DOCS/dlc_load.json" && rm -f "$BAK"
	echo "stopped; playset restored" ;;
*) sed -n 2,9p "$0"; exit 1 ;;
esac
