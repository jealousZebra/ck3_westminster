"""Where Crusader Kings III is installed, for every tool in the repo.

    from ck3paths import GAME, DOCS, game_version        # (add common/tools to sys.path first)

Set CK3_GAME_DIR to the game's "Crusader Kings III/game" folder and CK3_DOCS_DIR to the user folder
("Documents/Paradox Interactive/Crusader Kings III") if they aren't in the usual Steam places checked below.
"""
import json
import os
from pathlib import Path

GAME_GUESSES = [
    "~/Library/Application Support/Steam/steamapps/common/Crusader Kings III/game",     # macOS
    "C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game",            # Windows
    "~/.steam/steam/steamapps/common/Crusader Kings III/game",                          # Linux
    "~/.local/share/Steam/steamapps/common/Crusader Kings III/game",
]
DOCS_GUESSES = [
    "~/Documents/Paradox Interactive/Crusader Kings III",                               # macOS, Windows
    "~/.local/share/Paradox Interactive/Crusader Kings III",                            # Linux
]


def _find(env, guesses, marker):
    if os.environ.get(env):
        return Path(os.environ[env]).expanduser()
    for g in guesses:
        p = Path(g).expanduser()
        if (p / marker).exists():
            return p
    return Path(guesses[0]).expanduser()          # the tools report the missing file; set the variable to fix it


GAME = _find("CK3_GAME_DIR", GAME_GUESSES, "common")
DOCS = _find("CK3_DOCS_DIR", DOCS_GUESSES, "mod")


def game_version(game=None):
    """The installed game's version, e.g. '1.20.0.4', from the launcher settings next to the game folder."""
    game = Path(game) if game else GAME
    try:
        data = json.loads((game.parent / "launcher" / "launcher-settings.json").read_text(encoding="utf-8"))
        return data.get("rawVersion") or data.get("version", "unknown").split()[0]
    except (OSError, ValueError):
        return "unknown"


if __name__ == "__main__":                      # used by the shell tools: python3 ck3paths.py game|docs|version
    import sys
    what = sys.argv[1] if len(sys.argv) > 1 else "game"
    print({"game": GAME, "docs": DOCS, "version": game_version()}[what])
