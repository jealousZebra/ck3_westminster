#!/bin/bash
# Builds Westminster's whole newspaper UI, in the order the steps depend on (each overwrites parts of the last).
set -e
cd "$(dirname "$0")/../../.."
PY=.venv/bin/python
$PY westminster/tools/ui/build_theme.py          # fonts, text colours, skin, chrome, glow-free GUI files
$PY westminster/tools/ui/build_frontend.py       # main menu (starts from build_theme's frontend_main.gui)
$PY westminster/tools/ui/fal_images.py           # pictures and tab icons (cached in westminster/art/fal)
$PY westminster/tools/ui/build_illustrations.py  # scene lists and loading screens
$PY westminster/tools/ui/build_bookmark_screen.py # new-game screen: election map, character places and portraits, paper chrome (after fal_images and build_theme)
$PY westminster/tools/ui/build_portraits.py      # no crowns, hats or cloaks
$PY westminster/tools/ui/build_event_backgrounds.py   # event window backdrops
$PY westminster/tools/ui/build_terms.py              # modern terminology (localization/english/replace/wm_terms_*)
$PY westminster/tools/ui/build_polls_panel.py          # the Latest Poll panel
$PY westminster/tools/ui/build_ranks.py                # rank and tier names for every culture
$PY westminster/tools/ui/build_party_arms.py            # party emblems and coats of arms (cached in westminster/art/fal)
$PY westminster/tools/ui/build_colleagues.py            # Family tab -> Colleagues, names without the house (after build_theme)
$PY westminster/tools/ui/build_faith_view.py           # ideology (faith) view without its medieval parts (after build_theme)
$PY westminster/tools/ui/build_cabinet.py              # Cabinet: party colleagues only, office backgrounds
$PY westminster/tools/ui/build_coa_frames.py            # coats of arms shown as flags: masks, ink rules, no crowns
$PY westminster/tools/ui/build_flags.py                 # every title's flag (real ones from Wikimedia Commons, cached)
$PY westminster/tools/data/build_credits.py               # CREDITS.txt: data, font, picture and flag attribution (after build_flags)
$PY westminster/tools/ui/build_ideology_icons.py         # ideology and camp badges (faith icons; cached in westminster/art/fal)
$PY westminster/tools/ui/build_stat_icons.py            # skill and currency icons (cached in westminster/art/fal)
