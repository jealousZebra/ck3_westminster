# Publishing Westminster to the Steam Workshop

- Workshop item: [Westminster: UK Politics 1979–2024 | CK3 Total Conversion](https://steamcommunity.com/sharedfiles/filedetails/?id=3816349981).
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
2. Mods → Upload Mod → **Westminster: UK Politics 1979–2024 | CK3 Total Conversion** → Steam Workshop. The launcher
   uploads `westminster/westminster/` (the mod folder, with the generated
   textures) using `descriptor.mod` (name, version, tags, picture) and `thumbnail.png`.
3. For a new Workshop item, begin as **Hidden** or **Friends only**. Subscribe from a second machine or after
   disabling the local mod, start both bookmarks from the Workshop copy, and check the map, interface and a month or
   two of play before making it public.
4. Keep `remote_file_id="3816349981"` in both descriptors so uploads update the existing item.
5. Paste `workshop/title.txt` and `workshop/description.bbcode.txt` into Edit title & description (English), and add
   the screenshots below.
6. Each upload adds an empty change-notes entry. Fill it in from `change_notes_<version>.txt`.

To update: rebuild, add the changelog entry and change notes, run `release.sh <version>`, then Upload Mod again from
the launcher (it finds the item by `remote_file_id`).

The current tags are Total Conversion, Gameplay, Historical, Character Focuses and Interface. Keep
`westminster.mod` and `westminster/descriptor.mod` in sync because the launcher can overwrite Workshop metadata.

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

`westminster/thumbnail.png` (1024 × 1024, under 1 MB) is built by
`.venv/bin/python westminster/art/make_thumbnail.py`. The approved source is
`art/thumbnail_westminster_v3.png`: Thatcher and Starmer flank Parliament, with the title and date range inside the
middle band that survives the launcher's centred 2:1 crop.

## Screenshots

Current screenshots are in `workshop/screenshots/`. Replace them after visible UI or bookmark changes by capturing
the real game at full resolution (`FULL=1`, see [docs/ck3-testing.md](../../docs/ck3-testing.md)) and cropping to
16:9. The current set covers:

| # | File | Screen |
|---|---|---|
| 1 | `1_main_menu.jpg` | Westminster main menu |
| 2 | `2_election_map_2024.jpg` | 2024 election map and constituencies |
| 3 | `3_choose_your_mp.jpg` | 2024 bookmark character selection |
| 4 | `4_prime_minister_and_cabinet.jpg` | Prime Minister and Cabinet |
| 5 | `5_london_seats_and_flags.jpg` | London constituencies and modern flags |
| 6 | `6_scotland_snp.jpg` | Scottish constituencies and the SNP |

Use a start that shows real MPs with likenesses (Starmer, Sunak, Davey). Avoid shots that put words in a real
person's mouth: events are generic, and captions should describe the game, not the person.
