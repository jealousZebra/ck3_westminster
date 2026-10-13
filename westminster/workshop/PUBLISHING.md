# Publishing Westminster to the Steam Workshop

- Workshop item: not uploaded yet. After the first upload, put its link here and in the root README.
- General steps, Steam's limits and how to edit the page in the browser:
  [docs/steam-workshop.md](../../docs/steam-workshop.md).

Commands below are run from the repo root.

## Before each release

1. Build the mod if anything changed (westminster/README.md, "Setup, install and test"). The interface textures,
   map images, terrain and flags aren't in git, but they must be in the mod folder: the launcher uploads what is on
   disk.
2. Add a `## <version>` entry to `workshop/CHANGELOG.md` and write `workshop/change_notes_<version>.txt`.
3. Run `westminster/tools/release.sh <version>` with CK3 closed and Steam running (`--no-game <version>` skips the
   in-game tests). It stops at the first failure. It:
   - checks the generated files are there and rebuilds `thumbnail.png` (`art/make_thumbnail.py`);
   - runs the static checks (braces, encoding, localization keys) with `common/tools/ck3_checks.py`;
   - runs every in-game test suite (`tools/run_spikes.sh`), which fails on any Westminster error in `error.log`;
   - sets the version in `westminster/descriptor.mod`, `westminster.mod` and the launcher's copy;
   - packages `dist/westminster_<version>.zip` (the whole mod folder; about 0.9 GB on disk).
4. If the title, tags or picture changed, run `python3 common/tools/install_mod.py westminster` so the launcher's
   copy of the `.mod` file matches the template.

## Uploading (by the mod owner)

1. Close CK3. Open the Paradox launcher.
2. Mods → Upload Mod → **Westminster - UK Politics Total Conversion (Modern Britain, Elections, Parliament, Prime
   Minister)** → Steam Workshop. The launcher uploads `westminster/westminster/` (the mod folder, with the generated
   textures) using `descriptor.mod` (name, version, tags, picture) and `thumbnail.png`.
3. **First upload:** set the item to **Hidden** or **Friends only**. Subscribe from a second machine or after
   disabling the local mod, start a new 2024 game from the Workshop copy, and check the map, the interface and a
   month or two of play. Only then make it Public (the owner's decision).
4. After the first upload the launcher writes `remote_file_id` into `westminster/descriptor.mod`. Copy that line into
   `westminster.mod` too and keep it, so later uploads update the same item.
5. Paste `workshop/title.txt` and `workshop/description.bbcode.txt` into Edit title & description (English), and add
   the screenshots below.
6. Each upload adds an empty change-notes entry. Fill it in from `change_notes_<version>.txt`.

To update: rebuild, add the changelog entry and change notes, run `release.sh <version>`, then Upload Mod again from
the launcher (it finds the item by `remote_file_id`).

The tags in `descriptor.mod` (Total Conversion, Map, Bookmarks, Gameplay, Historical) are from CK3's Workshop tag
list, but we haven't confirmed which ones the launcher accepts. If an upload fails on a tag, drop it.

## Page text

- English is in `workshop/`:
  - `title.txt`
  - `description.bbcode.txt` (about 5,700 bytes counting line breaks twice; Steam's limit is 8,000)
  - `short_description.txt`
  - `change_notes_<version>.txt`
- Translations of the page (title, description, short description, change notes) are in
  `workshop/translations/<language>/` for French, German, Spanish (also use it for Latin American Spanish), Russian,
  Polish, Simplified Chinese, Korean and Japanese. `python3 workshop/translations/check.py` checks them against the
  English. Paste each into the Workshop page's language selector (codes in docs/steam-workshop.md). The in-game mod includes English, French, German, Japanese, Korean, Polish, Russian, Simplified Chinese and Spanish localization. Workshop page translations are maintained separately.
- `title.txt` holds the words players search for (UK politics, total conversion, modern Britain, elections,
  Parliament, Prime Minister). It is also `name` in `westminster/descriptor.mod` and `westminster.mod`, so a launcher
  upload keeps the title. If you change one, change the other.
- Keep the claims factual: the description lists only what the mod does today (check westminster/README.md).

## Thumbnail

`westminster/thumbnail.png` (1024 × 1024, under 1 MB) is built by `.venv/bin/python westminster/art/make_thumbnail.py
[version]`: a newspaper front page with the masthead WESTMINSTER, a dateline with "BETA <version>" and a photo of the
Palace of Westminster at dusk. The masthead, dateline and photo are inside the middle band (y 256-768), which
survives the launcher's 2:1 crop; the folio line and the headline only show in Steam's square view. The photo is
AI-generated (fal.ai, FLUX.1 [dev]) and cached in `art/fal/thumb_westminster.jpg`; delete it to generate a new one.

## Screenshots

Not taken yet. Take them in the real game at full resolution (`FULL=1`, see
[docs/ck3-testing.md](../../docs/ck3-testing.md)), crop to 16:9, and save them here as `workshop/screenshots/<n>_<name>.jpg`:

| # | File | Screen | Caption |
|---|---|---|---|
| 1 | `1_map_2024.jpg` | The realm map zoomed to England and Wales with the party colours, a constituency's tooltip open | All 650 constituencies of 2024, held by the MPs who won them |
| 2 | `2_state_of_the_parties.jpg` | The State of the Parties panel: latest poll, trust, seat chart, poll tracker | The State of the Parties: polls, public trust and the Commons at a glance |
| 3 | `3_main_menu.jpg` | The main menu masthead over the Westminster photo, or the 2024 bookmark screen | A modern newspaper interface, from the main menu on |
| 4 | `4_election_result.jpg` | A general-election front page ("HUNG PARLIAMENT" or "LANDSLIDE") | Elections decided seat by seat from the 2024 result |
| 5 | `5_commons_vote.jpg` | A Commons bill event with the Chief Whip's forecast and the whipping options | Whip the Commons, face rebellions and confidence votes |
| 6 | `6_leadership_contest.jpg` | A leadership contest (nominations or the members' ballot), or Cross the Floor | Parties are houses: contests, defections and new parties |
| 7 | `7_cabinet_character.jpg` | The Prime Minister's character window with the Cabinet (modern skills and currencies) | Charisma, Spin, Political Capital: modern terms throughout |
| 8 | `8_riot_or_activist.jpg` | A riot marching on Westminster, or the activist's selection contest | Riots that march on Westminster; or start as an activist |

Use a start that shows real MPs with likenesses (Starmer, Sunak, Davey). Avoid shots that put words in a real
person's mouth: events are generic, and captions should describe the game, not the person.
