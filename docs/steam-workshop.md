# Publishing to the Steam Workshop

> These notes started in the [ck3_realm_manager](https://github.com/jealousZebra/ck3_realm_manager) (formerly ck3mod) repo, which Westminster shared with
> another mod, Realm Forge. Examples that mention Realm Forge or `realm_forge/` refer to that repo; Westminster's own
> commands are in this repo's README.md.

General steps for every mod in this repo. Each mod's `workshop/PUBLISHING.md` has its own specifics: its item ID,
screenshot commands and so on.

## Uploading (by the mod owner)

The mod is uploaded with the **Paradox launcher**: Mods → Upload Mod → pick the mod → Steam Workshop. On Apple Silicon
the launcher needs Rosetta. The launcher takes the following from the mod folder's `descriptor.mod`:

- `name`, which becomes the **Workshop title**. Keep it the same as the English title, or an upload overwrites the
  title.
- `version`
- `tags`
- `supported_version`
- `picture`: `thumbnail.png`, the Workshop's main image. It must be square. The launcher crops it to a wide
  rectangle, so keep the important part in the middle band.

After the first upload, the launcher writes `remote_file_id` into `descriptor.mod`. Keep it, so updates go to the same
item. Don't put Steam passwords anywhere near the tooling: the owner signs in to Steam themselves.

The first upload should be **Hidden** or **Friends only**. Subscribe, check that the Workshop copy loads, and only then
make it public. Visibility is the owner's decision.

## Workshop page text, kept in the repo

Keep every piece of page text as files in the mod's `workshop/` folder: English at the top level, other languages in
`workshop/translations/<language>/`.

| File | Goes to |
|---|---|
| `title.txt` | Edit title & description → Title, per language |
| `description.bbcode.txt` | Edit title & description → Description, per language (Steam BBCode) |
| `short_description.txt` | Launcher upload dialog, if asked |
| `change_notes_<version>.txt` | Change notes for that version's upload, per language |
| `CHANGELOG.md` | Full history (English) |

### Limits and quirks

- The description limit is **8000 bytes**, and Steam counts each line break as 2 bytes (CRLF). The Russian
  description had to be trimmed to about 7,800 bytes of file size before it would save.
- The title limit is 128 characters.
- Steam's search matches **whole words**. Put the words players type into the title (for Realm Forge: take titles,
  organize, cheat, de jure, vassals), and use the US spelling "organize" as well as the British spelling used in the
  text.
- Steam CK3 tags are a fixed list (Gameplay, Utilities, Character Interactions, Interface, Translation, the language
  tags…). The launcher sets them from `descriptor.mod`. We haven't confirmed which ones it accepts, and a tag it
  doesn't accept may make an upload fail.

## Editing the page in the browser

These pages work in a browser signed in to the owner's Steam account. The field and function names are for
scripting the edits from the browser's developer console:

- **Title and description:** `https://steamcommunity.com/sharedfiles/itemedittext?id=<ID>&language=<N>`. Set
  `#title` / `#description`, then call `ValidateForm()`.
- **Change notes:** `https://steamcommunity.com/sharedfiles/editchangelogentry/<ID>/<entryId>/?language=<N>`. Set
  textarea `#change_description`, then call `SaveChanges()`. Each upload makes a new entry. Find the entry IDs on
  `/sharedfiles/filedetails/changelog/<ID>`. That page sometimes errors once; retry.
- **Screenshots:** `https://steamcommunity.com/sharedfiles/managepreviews?id=<ID>`. Uploading a file with the same
  name replaces the image. Finish with "Save and Continue".

**Language codes:**

| Code | Language |
|---|---|
| 0 | English |
| 1 | German |
| 2 | French |
| 5 | Spanish (Spain) |
| 27 | Spanish (Latin America): use the Spanish texts |
| 8 | Russian |
| 12 | Polish |
| 6 | Simplified Chinese |
| 4 | Korean |
| 10 | Japanese |

What works and what doesn't:

- Pasting with cmd+v into Steam's fields doesn't work.
- A local HTTP server to serve the text is blocked.
- **What works:** set the field's value from JavaScript with a `String.raw` template literal, check its length
  against the file (minus the trailing newline), then save. Use `sessionStorage` to carry long text across page loads
  in the same tab.
- **Wait for each save before going to the next language.** Saving navigates the page. If the next navigation starts
  too early, that save is lost or the script runs on the wrong page.
- Check the language select's value before writing.
- **Steam's limits are in bytes, not characters:** the title is 128 bytes and the description 8,000 bytes of UTF-8,
  with each line break sent as CRLF (2 bytes). Cyrillic takes 2 bytes a character and Chinese, Japanese and Korean 3,
  so translations hit the limit long before the English does. Over the limit, the save is silently dropped: the page
  reloads with no error and the old text. Westminster's `workshop/translations/check.py` checks both.
- **Faster than editing each page:** the edit form is a plain POST to `/sharedfiles/itemedittext/` with `id`,
  `sessionid` (read it from the edit page), `language`, `title` and `description`. Posting with `fetch` from a
  steamcommunity.com tab saves a language without loading the page; re-fetch the edit page to confirm.
- **Verify afterwards:** fetch each language's edit page, parse it with `DOMParser`, and compare the title and the
  description length with the files.

## Screenshots

Take them in the real game with the UI walkthrough ([ck3-testing.md](ck3-testing.md)) at full resolution (`FULL=1`).
Then crop them with a script, scaling from the 1600px-wide layout, so they can be remade after a UI change. Show other
languages too: a German and a Chinese shot show the mod is translated.
