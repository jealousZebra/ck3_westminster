# CK3 modding notes

What we've learned making mods for Crusader Kings III 1.20 (on macOS, but most of it applies everywhere). Most of these cost a debugging session, and many
fail silently. Read this before writing script or GUI for a new mod, and add to it when the game surprises you.

## Where things are (macOS; the tools take CK3_GAME_DIR and CK3_DOCS_DIR for other places)

| What | Path |
|---|---|
| Game files (vanilla script and GUI to copy from) | `~/Library/Application Support/Steam/steamapps/common/Crusader Kings III/game` |
| Game binary | `…/Crusader Kings III/binaries/ck3.app` |
| Error log | `~/Documents/Paradox Interactive/Crusader Kings III/logs/error.log` |
| Debug log (`debug_log` output) | `~/Documents/Paradox Interactive/Crusader Kings III/logs/debug.log` |
| Launcher mod files (`.mod`) | `~/Documents/Paradox Interactive/Crusader Kings III/mod/` |
| Enabled mods (the playset) | `~/Documents/Paradox Interactive/Crusader Kings III/dlc_load.json` |
| Game language | `language` in `~/Documents/Paradox Interactive/Crusader Kings III/pdx_settings.txt` |

Each mod has a `.mod` file in the launcher's `mod/` folder whose `path` points at the mod folder in this repo, for
for example `path="/path/to/repository/<mod>/<mod>"`. `python3 common/tools/install_mod.py <mod>` writes it
from the mod's template. Move the repo and you must run it again.

## Files and encoding

- Script (`.txt`), GUI (`.gui`) and localization (`.yml`) files need a **UTF-8 BOM**. Without it the game may skip the
  file or garble non-ASCII text. `common/tools/ck3_checks.py static <mod>` checks this.
- Prefix every file, variable, effect, trigger, scripted GUI and localization key with the mod's prefix (`wm_` for
  Westminster) so mods don't clash with each other or vanilla, and so error-log checks can find the mod's own errors.
- Localization files go in `localization/<language>/<name>_l_<language>.yml` and start with `l_<language>:`.
- Write symbols like "+" in GUI text with `raw_text`.

## Script

- `create_character` can't take both `location` and `employer`.
- `change_title_holder` refuses a county's capital barony: filter with `is_capital_barony = no`.
- **Creating titles:** use the character effect `get_title = <title>` to create an uncreated duchy, kingdom or
  empire. A `title_and_vassal_change` with `type = created` silently does nothing for uncreated titles.
- **The game destroys a duchy or kingdom given to someone who holds no county.** Give a new ruler land first, then
  the higher title.
- **Transfer type:** `usurped` causes legitimacy-loss toasts. `returned` and `revoked` wipe coronation modifiers
  (vanilla `title_on_actions.txt`, around line 2912). `granted` is the quiet one. A title created with `get_title`
  reports transfer type `granted` with no `scope:previous_holder`.
- `add_hook` always shows a toast.
- `every_in_de_jure_hierarchy` includes the title itself.
- `create_dynamic_title = { tier = hegemony name = KEY }` works and sets `scope:new_title`. The player can rename it
  with the feather. `set_de_jure_liege_title` puts an empire under it.
- Set `forbid_crypto_reconversion` on a county before `set_county_faith`, or you get crypto-religionists.
- **Saves keep the mod's variables.** State left on titles or characters from an old run (an old plan, say) comes
  back in the next one. Clear per-title state where you rebuild it, not only on the last list.
- **Performance:** moving about 1,000 counties and 5,000 baronies (organising all of Europe) is slow because the game
  runs `on_title_gain` (about 3,000 lines of vanilla script) for each title change. Doing each title's handover,
  liege change and barons in one `title_and_vassal_change` saved about 25%. Timings vary a lot with machine load,
  so compare A/B runs back to back.
- The error log reports variables that are **set but never used** (or used but never set). Use in localization doesn't
  count, and neither does use in a scripted trigger or effect that nothing calls. If a variable is only shown in the
  UI, read it in a scripted GUI's `is_shown` or another live trigger.

## GUI

- Duplicate properties in a block make it fail, and the error log says so.
- `vbox` and `hbox` need `ignoreinvisible = yes`, or hidden children still take up space. This fails silently.
- Widgets placed below a window's edge let clicks fall through to the map.
- The window frame is drawn about 20px inside the window edge, so leave a margin of 40px or more.
- GUI `And(...)` doesn't short-circuit. `And( GetPlayer.IsValid, GetScriptedGui(...).IsShown(...) )` still runs the
  scripted GUI when there's no player and floods the log. Check `GetPlayer.MakeScope.Var('x').IsSet` instead.
- A script value read from the GUI as `Title.MakeScope.ScriptValue(...)` has the title as `root`, not the player.
  Getting this wrong once caused 49,000 errors a minute.
- Vanilla `button_tab` has `layoutpolicy_horizontal = expanding`, and its pressed state barely shows. Give selected
  radio buttons their own overlay.
- **Changing a vanilla window** means overriding its whole file (for example `gui/window_title.gui`). Only
  `type`/`template` definitions can be overridden on their own, and they rarely sit where you want to add things.
  Generate the override from the installed game's file with a script, and record the game version in it so a release
  check can catch a game update (see a local generator script). A whole-file override conflicts with any
  other mod that changes the same window.
- In debug mode (`-debug_mode`) the game reloads GUI files when they change. The test harness relies on this (see
  [ck3-testing.md](ck3-testing.md)).

- `gfx/interface/skinned/...` paths are resolved per culture skin: if `gfx/interface/skins/<skin>/...` has its own
  copy, that one is shown. Replacing a skinned texture means writing it into every skin that has one too.
- `modify_texture` with `blend_mode = overlay` is neutral at mid grey (128); `alphamultiply` uses the alpha channel.
  Neutralising the `component_overlay/` textures and flattening the grunge masks (`mask_clouds`, `mask_scratches`,
  `mask_rough_edges`) removes the aged-parchment look everywhere without touching GUI files.
- A council card's background can come from a scripted illustration (the chaplain's is
  `character_religion_interior`), and portraits there use the 3D `environment_council`, which has no backdrop.
- `add_title_law` checks the law's `can_have`; history `succession_laws` doesn't.
- Name formats put royal-family titles in `$TIER$` (`prince`, `princess`, `prince_<culture>`...): blank those keys
  rather than removing `$TIER$`, which also carries the rank.

- A `flowcontainer` with no fixed size placed straight in an expanding `vbox`/`hbox`, with `hbox` children, makes
  the layouts resize each other forever: the game crashes as soon as a game starts
  (`CPdxGuiFlowContainer::UpdateSizeInternalBottomUp` → `CPdxGuiWidget::Resize` → `CPdxGuiLayout::FilterEvent`).
  Give it `flowcontainer = { direction = horizontal }` children and put it inside a fixed-size `widget`.
- A tenet's `visible = no` (`common/religion/tenet_types`) doesn't keep it out of the faith window's tenet lists
  (Faith Details, "Unknown Tenets"). Westminster hides that group in the GUI by comparing
  `TenetGroupItem.GetGroupTitle` with `Localize( 'TENET_GROUP_ITEM_UNKNOWN' )` (`tools/ui/build_faith_view.py`).
- Rite creation and editing are gated by the scripted rules `can_create_rite` and `can_edit_rite`
  (`common/scripted_rules/00_rules.txt`). In debug mode, localization changes show without a restart too.
- A `textbox` with `multiline = yes` inside a vbox can still be cut to one line ("..."): keep it short, or give it a
  fixed size outside layouts.
- Data-bound colours exist for few objects. Westminster's seat chart is stacked progress bars (cumulative seats,
  largest party first) under a stencil texture with a transparent hole per seat.
- Vanilla's start-up script (`common/on_action/game_start.txt`) is thousands of lines aimed at historical characters
  and titles; a total conversion should replace it (Westminster: `tools/data/build_game_start.py`). Its dynamic
  coats of arms (`coat_of_arms/dynamic_definitions/`) and `set_coa` calls also swap titles' arms.

## Localization and translation

- Take terms from the game's own localization (`game/localization/<language>/`) so the mod matches the game's UI in
  every language.
- Keep `[data expressions]`, `$KEY$` references, `#format` codes and `\n` exactly as in the English. a translation-check script can verify this.
- The game ships 9 languages: English, French, German, Spanish, Russian, Polish, Simplified Chinese, Korean and
  Japanese.

## Total conversions and new maps

What it took to get a brand-new map loading (Westminster, 2026-10-08). Each item cost a crash or a hang.

- **The game reads `replace_path` from the launcher's `.mod` file** in `Documents/.../mod/`, not from the mod
  folder's `descriptor.mod`. Keep both the same; the mod's `<mod>.mod` template in the repo should contain them, and
  `common/tools/install_mod.py <mod>` must be rerun after changing them.
- `replace_path` doesn't cover subfolders: `history/titles` needs `history/titles/ce3` too.
- **Replace all of `map_data`** (`replace_path="map_data"`), or vanilla `nodes.dat`, `positions.txt` and the region
  files load against your provinces.
- **`adjacencies.csv` must end with the line `-1;-1;;-1;-1;-1;-1;-1;`**. Without it the game loops forever on
  "Initializing Game" (it keeps reading the file).
- **There must be at least one province mapping** (`history/province_mapping`). With none, the game crashes reading
  province history: `CHistoryDatabase::ReadProvince` reads the first element of the empty mapping list. Map one sea
  zone onto another.
- **Every land province needs a visual ("graphical") region** in `map_data/geographical_regions`
  (`graphical_western = { graphical = yes duchies = { ... } }`). Empty regions also crashed
  `CGeographicalRegion::PostSetup`.
- Province history keys are `culture`, `faith`, `rite` and `holding`. Files are named after kingdoms
  (`history/provinces/k_<kingdom>.txt`), as in vanilla.
- Replace `common/province_terrain/00_province_terrain.txt` (and `01_province_properties.txt`), or the vanilla
  terrain for province ids up to about 14,000 floods the log.
- Map size comes from `NJominiMap` `WORLD_EXTENTS_X/Z` (width and height minus 1) in `common/defines`. The camera's
  start point and panning size come from `NCamera` in `common/defines/graphic`.
- `NGame END_DATE` must be after the bookmarks (vanilla's is 1453).
- **The packed heightmap** (`packed_heightmap.png`, `indirection_heightmap.png`, `heightmap.heightmap`) can be
  written directly, without the game's map editor. The format is documented in
  `westminster/tools/map/heightmap_pack.py`, which decodes vanilla's own files to within 0.15%.
- The game generates missing map object locators (buildings, units) itself and logs "Copy that file ... to
  game/gfx/map/map_object_data".
- Import the generated locators into the mod's `gfx/map/map_object_data`: generating them on every first launch
  also logs missing transforms. Westminster's importer is `tools/map/build_map_support.py --import-locators`.
- `gfx/map/terrain/snow_diffuse_for_combined_winter.dds` must be map width/64 by map height/64, in uncompressed
  **BGRA8** (`B8G8R8A8_UNORM`). The winter code rejects DXT5 even though other map textures accept it.
- Replace `history/struggles` and `history/situations` too: otherwise vanilla starts the Dynastic Cycle, Silk Road
  and other situations against missing provinces and titles, including when optional DLCs are enabled.
- Existing Workshop subscribers can retain an older launcher `.mod` even after the downloaded `descriptor.mod`
  updates. Westminster also ships comment-only overrides at every vanilla situation/struggle history filename,
  generated by `tools/data/build_stability.py`, so these protections work without the newer `replace_path` lines.
  Regenerate after a CK3 update; `tools/data/test_stability.py` checks coverage against the installed game.
- Startup filtering must remove named historical characters as well as numeric ones, and all literal vanilla
  province scopes: a reused province id still refers to a different place on the new map.
- The rivers map is 8-bit indexed with vanilla's palette: 255 = land, 254 = water, lower values = rivers.
- Terrain masks (`gfx/map/terrain/masks/*_mask.png`) are map-sized 8-bit greyscale PNGs. `colormap.dds`,
  `flatmap.dds` and `detail_index.tga` are map-sized too. Vanilla's are stretched over a map of another size.

### Debugging crashes

- The game's crash reporter writes `Documents/.../crashes/<date>/exception.txt` (stack only). The crashed
  thread's registers and the signal are in the raw report, `~/Library/Caches/com.plausiblelabs.crashreporter.data/
  live_report.plcrash` (protobuf). A small decoder printed `pc`, `lr` and `x0`-`x28` and showed the NULL read.
- `lldb --batch -o "disassemble -n 'Class::Method(args)'" <ck3 binary>` works without running the game (the binary
  has symbols). **Don't run the game under lldb**: it needs Developer Tools access and puts up a macOS password
  prompt. Paradox's CrashReporter also asks for that access after each crash and waits on the same prompt, so the
  user must click Cancel. Kill leftover `crash_reporter/binaries/CrashReporter` processes after crash testing.

## Script lessons from Westminster's gameplay (2026-10-08)

- `run_interaction` applies an interaction's effects but **not its cost**. Charge the cost yourself, after it has
  run: before, the actor may no longer afford it, and the game refuses ("Interaction cannot be sent").
- Inside a scripted effect, `root` is still the original root (the event's or caller's), not the scope the effect was
  called in. Use `this` for the current scope.
- Variables and flags set in history files (`2024.7.5 = { effect = { set_variable = ... } }`) don't count for the
  "set but never used" / "used but never set" check. Setting them again in script (an `on_game_start` effect)
  silences it.
- Saved scopes don't survive into a later event. Pass what it needs in global variables.
- Election votes are recalculated on the AI's own schedule; `recalculate_succession_election_vote = yes` on each
  elector forces it.
- A total conversion should drop vanilla events (`replace_path` for **every** `events/` subfolder: 92 in 1.20).
  Otherwise medieval events (homage, feasts...) fire and pause the game for the player. Vanilla scripts that call
  them only log errors.

- Inside a script value, a bare reference to another script value (`x = other_value`) evaluated to 0; write
  `x = { value = other_value }`.
- A global variable named `wm_trust` read wrongly inside script-value blocks (40 read as 10); renaming it
  (`wm_public_trust`) fixed it. If a variable reads oddly, try a longer, unambiguous name.
- Use `?=` when the left side may not exist (`scope:x.var:y ?= z`).
- Copy a global list to a temporary list before running effects that remove items from it, and remember temporary
  lists last the whole script run (filter them when reused).
- **Faiths in 1.20 take their own doctrines in a `doctrines = { ... }` block** (`common/religion/faith_types/`).
  `doctrine = x` lines work in a religion (`religion_types/`), but inside a faith they're silently ignored. The
  doctrines are copied into the faith's main rite when a game starts, so a save made before a change keeps the old
  ones: make a new save.
- Faith hostility can be scripted without vanilla's families: give each religion a hidden "marker" doctrine and each
  faith a hostility doctrine whose `hostility_level_override = { <marker> = hostile ... }` sets the level towards
  faiths carrying that marker (Westminster: `tools/data/build_ideology.py`). `NReligion HOSTILITY_OPINION_EFFECTS`
  sets the opinion per level. A doctrine with the parameter `holy_wars_forbidden` switches off every religious CB.
- Shared test harness files must only be written while holding the game lock: a generator writing the harness while
  another suite was loading corrupted that run.

## Portraits and likenesses (Westminster, 2026-10-08)

- A fixed face is `dna = <key>` in history, with the key's `portrait_info = { genes = { ... } }` in
  `common/dna_data`. Morph genes are 0-255 with 128 neutral; colours are palette coordinates (`hair_color={ x y x y }`,
  see `gfx/portraits/*_palette.dds`). Westminster's `tools/data/build_likenesses.py` rolls a face from the game's
  ethnicities and lays described features on top.
- **Hairstyles and beards are chosen by portrait modifiers in play**, so DNA alone doesn't fix them. Give each
  character a modifier keyed on `this = character:<id>` (as vanilla's `02_all_historical_characters.txt`).
- In a portrait modifier, `mode = add` **adds** an accessory on top of the DNA's: adding `no_beard` doesn't remove a
  beard the DNA has. Set the DNA's own gene too.
- A woman's specific hairstyle needs `type = female` in the accessory block, or the log says "Can't find accessory ...
  in gene template".
- Baldness: stage 1 once age/100 >= the `gene_baldness` value, stage 2 once age/200 >= it (`05_hair_situational.txt`).
  Both stages swap the hairstyle for its `baldness_1`/`baldness_2` entity; a hairstyle without one shows no hair.
- `special_headgear_spectacles` in DNA isn't shown; a portrait modifier on that gene is. Vanilla's only glasses are
  round medieval pince-nez.
- A GUI test page of portraits: `portrait_shoulders` with `blockoverride "portrait_size"` renders; a bare
  `portrait_button` with `portrait_texture` crashed the game (no `using = portrait_base`) or stayed blank.
- A history character's `name = "Harry"` needs a localization key `Harry`, or the log reports missing loc.

## The bookmark (new-game) screen (Westminster, 2026-10-09)

- The background (`gfx/interface/bookmarks/<bookmark>.dds`, 1920 × 1080) is shown in a 1920 × 1080 frame inside a
  1920 × 1200 widget scaled to fit the screen. A character's `position = { x y }` is in the 1920 × 1200 widget: it
  is the top-left of the portrait, so background pixel (x, y) is position (x, y + 60). Below the portrait (about
  127 px tall) come the name banner (to about y + 175, 262 px wide) and two centred lines (subheading, difficulty).
- The line under the name is `<character name>_subheading` (vanilla: `$BOOKMARK_SUBHEADING_DEFAULT$`, "<tier> of
  <title>"); write your own text there rather than fighting the tier names.
- Missing files the error log names: the "location image" `gfx/interface/bookmarks/<bookmark>_<character name>.dds`
  (laid over the background, pulsing, when the character is selected; at 0.3 alpha on hover),
  `dynasty_splendor_level`, and the portrait. The Start button is `gfx/interface/bookmarks/start_buttons/<bookmark>.dds`
  and the date list's button `gfx/interface/icons/bookmark_buttons/<bookmark>.dds`.
- **Portraits** are `common/bookmark_portraits/<character name>.txt`, matched by name. Their `entity` and `tags` are
  hashes, so don't write them by hand: start a game on the bookmark's date in debug mode and run the console command
  `dump_bookmark_portraits` (or `dump_bookmark_portrait_for <history ids>`); the files land in the user folder's
  `common/bookmark_portraits/`. Gene lines (clothes, for one) can then be edited. The console opens with the key left
  of 1 (`osascript ... key code 10` on a Mac ISO keyboard). In debug mode the screen picks up changed portrait files
  and textures without a restart.
- `replace_path="common/bookmark_portraits"` drops vanilla's, which name portrait modifiers a total conversion may
  have replaced (they log "Unknown portrait modifier").
- Clothing colours follow the character, not the gene value: the same clothes gene came out blue on one character
  and black on another.
