#!/bin/bash
# Checks and packages a Westminster release.
#
#   westminster/tools/release.sh 0.3              # full release: checks, in-game tests, set version, zip
#   westminster/tools/release.sh --no-game 0.3    # the same without the in-game tests (CK3 not started)
#   westminster/tools/release.sh --no-game        # checks only (no version change, no zip)
#
# Steps (stops at the first failure):
#   1. check the generated files are there: the interface textures, map images, terrain and flags aren't in git, so
#      a clone must be built first (westminster/README.md, "Setup, install and test"); rebuild the thumbnail
#   2. static checks (common/tools/ck3_checks.py): balanced braces and UTF-8 BOM in every script/GUI/localization
#      file, no missing or duplicate localization keys
#   3. run every in-game test suite (tools/run_spikes.sh), which fails on any FAIL or Westminster error in error.log
#   4. set the version in descriptor.mod, westminster.mod and the launcher's copy; require a CHANGELOG entry for it
#   5. zip westminster/ (the whole mod folder, generated files included) and westminster.mod into dist/
# The in-game tests need CK3 closed (they start it) and Steam running. Nothing here uploads: the owner uploads with
# the Paradox launcher (workshop/PUBLISHING.md).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"	# westminster/ (this mod's folder in the repo)
REPO="$ROOT/.."
COMMON="$REPO/common"	# tools shared by every mod in the repo
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY=python3
cd "$ROOT"
GAME=yes
[ "${1:-}" = "--no-game" ] && { GAME=no; shift; }
VERSION="${1:-}"
DOCS="${CK3_DOCS_DIR:-$HOME/Documents/Paradox Interactive/Crusader Kings III}"	# the game's user folder

step() { printf '\n== %s\n' "$*"; }

step "Generated files"
missing=0
for p in gfx/interface/skinned gfx/interface/frontend gfx/map/terrain/flat_maps gfx/map/water \
		gfx/coat_of_arms/textured_emblems map_data/provinces.png map_data/heightmap.png \
		gfx/map/terrain/snow_diffuse_for_combined_winter.dds; do
	[ -e "westminster/$p" ] || { echo "missing: westminster/$p"; missing=1; }
done
for kind in buildings activities combat siege special_building unit_stack_player_owned; do
	[ -f "westminster/gfx/map/map_object_data/wm_${kind}_locators.txt" ] || { echo "missing: $kind locators; boot Westminster, then run tools/map/build_map_support.py --import-locators"; missing=1; }
done
ls westminster/gfx/coat_of_arms/textured_emblems/wm_flag_*.dds >/dev/null 2>&1 || { echo "missing: flags (wm_flag_*.dds)"; missing=1; }
[ "$missing" = 0 ] || { echo "Build the mod first (westminster/README.md, \"Setup, install and test\")."; exit 1; }
"$PY" tools/ui/check_bookmark_assets.py
"$PY" art/make_thumbnail.py "${VERSION:-0.3}"

step "Static checks"
python3 "$COMMON/tools/ck3_checks.py" static westminster
"$PY" tools/data/test_stability.py

if [ "$GAME" = yes ]; then
	step "In-game tests"
	pgrep -qx ck3 && { echo "Close CK3 first: the tests start it."; exit 1; }
	tools/run_spikes.sh || { echo "In-game tests failed."; exit 1; }
fi

if [ -n "$VERSION" ]; then
	step "Version $VERSION"
	grep -Eq "^## $VERSION( |$)" workshop/CHANGELOG.md || { echo "Add a '## $VERSION' entry to workshop/CHANGELOG.md first."; exit 1; }
	[ -f "workshop/change_notes_$VERSION.txt" ] || { echo "Write workshop/change_notes_$VERSION.txt first."; exit 1; }
	for f in westminster/descriptor.mod westminster.mod "$DOCS/mod/westminster.mod"; do
		[ -f "$f" ] && sed -i '' "s/^version=\".*\"/version=\"$VERSION\"/" "$f"
	done
	step "Package"
	mkdir -p dist
	find westminster -name .DS_Store -delete
	rm -f "dist/westminster_$VERSION.zip"
	zip -rq "dist/westminster_$VERSION.zip" westminster westminster.mod
	ls -lh "dist/westminster_$VERSION.zip"
	du -sh westminster | awk '{print "mod folder on disk: " $1}'
	echo "Upload with the Paradox launcher (see workshop/PUBLISHING.md)."
fi
echo; echo "Release checks passed."
