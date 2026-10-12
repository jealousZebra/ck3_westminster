#!/bin/bash
# Screenshots of the polls panel's three tabs (tools/ck3_test/gen_seatchart.py) on the Westminster test save, with
# only Westminster enabled. The playset and the last save are put back afterwards. Needs an unlocked screen.
#
#   westminster/tools/ck3_test/shoot_seatchart.sh <out dir>
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../../.." && pwd)"
DOCS="$HOME/Documents/Paradox Interactive/Crusader Kings III"
OUTDIR="${1:?output folder}"
cp "$DOCS/dlc_load.json" "${TMPDIR:-/tmp}/wm_shot_dlc.bak"
cp "$DOCS/continue_game.json" "${TMPDIR:-/tmp}/wm_shot_continue.bak"
restore() {
	cp "${TMPDIR:-/tmp}/wm_shot_dlc.bak" "$DOCS/dlc_load.json"
	cp "${TMPDIR:-/tmp}/wm_shot_continue.bak" "$DOCS/continue_game.json"
	rm -f "$DOCS/save games/zz_wm_seatchart.ck3"
}
trap restore EXIT
printf '{"enabled_mods": ["mod/westminster.mod"], "disabled_dlcs": []}' > "$DOCS/dlc_load.json"
cp "$HERE/saves/wm_2025.ck3" "$DOCS/save games/zz_wm_seatchart.ck3"
printf '{\n\t"title":\t"zz_wm_seatchart",\n\t"desc":\t"test save",\n\t"date":\t"%s",\n\t"rawGameVersion":\t"1.20.0.4"\n}\n' "$(date '+%Y-%m-%d %H:%M:%S')" > "$DOCS/continue_game.json"
python3 "$HERE/gen_seatchart.py" >/dev/null
HARNESS="$HERE/harness" "$ROOT/common/ck3_test/ui_walkthrough.sh" "$OUTDIR" 3
