#!/usr/bin/env python3
"""Install a mod from this repo into the Paradox launcher's mod list.

    python3 common/tools/install_mod.py westminster
    python3 common/tools/install_mod.py westminster

Writes <CK3 user folder>/mod/<mod>.mod from the repo's template (<mod>/<mod>.mod), with `path` pointing at
<repo>/<mod>/<mod>, so the launcher loads the mod straight from your clone. Re-run it whenever the template
changes (Westminster's replace_path lines live there). A remote_file_id already in the installed file is kept.
The user folder is found by common/tools/ck3paths.py; set CK3_DOCS_DIR if it isn't in the usual place.
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ck3paths import DOCS  # noqa: E402


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    mod = sys.argv[1].strip("/")
    template = REPO / mod / (mod + ".mod")
    content = REPO / mod / mod
    if not template.is_file() or not (content / "descriptor.mod").is_file():
        sys.exit("No mod called %r here: expected %s and %s/descriptor.mod" % (mod, template, content))
    text = template.read_text(encoding="utf-8")
    text = "".join(ln for ln in text.splitlines(True) if not ln.startswith("# Placeholder path"))
    line = 'path="%s"' % content.as_posix()
    text, n = re.subn(r'^path=".*"$', lambda m: line, text, flags=re.M)
    if n != 1:
        sys.exit("%s should have exactly one path=\"...\" line" % template)
    out = DOCS / "mod" / (mod + ".mod")
    if out.is_file():
        old = re.search(r'^remote_file_id=".*"$', out.read_text(encoding="utf-8"), re.M)
        if old and "remote_file_id" not in text:
            text = text.rstrip("\n") + "\n" + old.group(0) + "\n"
    if not out.parent.is_dir():
        sys.exit("%s does not exist. Start CK3's launcher once, or set CK3_DOCS_DIR." % out.parent)
    out.write_text(text, encoding="utf-8")
    print("wrote %s (path=%s)" % (out, content))


if __name__ == "__main__":
    main()
