#!/usr/bin/env python3
"""Check publishable files and, with --history, reachable Git blobs. Never print values.

This is a small heuristic check, not a guarantee. It ignores local build caches via
Git's ignore rules; ignored files are not part of an open-source source checkout.
"""
import argparse
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PATTERNS = {
    "private key": rb"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----",
    "GitHub token": rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})",
    "AWS access key": rb"(?:AKIA|ASIA)[A-Z0-9]{16}",
    "OpenAI-style token": rb"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}",
    "Slack token": rb"xox[baprs]-[A-Za-z0-9-]{20,}",
    "API credential": rb"""(?i)(?:api[_-]?key|fal_key|access[_-]?token|client[_-]?secret|password)["']?\s*[=:]\s*["'][A-Za-z0-9_+/.:-]{20,}["']""",
    "authenticated URL": rb"https?://[^\s/:]+:[^\s/@]+@",
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def findings(data):
    return [label for label, pattern in PATTERNS.items() if re.search(pattern, data)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--history",
        action="store_true",
        help="also scan all locally reachable Git blobs",
    )
    args = parser.parse_args()
    failed = False
    paths = git("ls-files", "--cached", "--others", "--exclude-standard", "-z").split(
        b"\0"
    )
    count = 0
    for raw in sorted(set(paths) - {b""}):
        path = ROOT / raw.decode("utf-8")
        if not path.is_file():
            continue
        count += 1
        for label in findings(path.read_bytes()):
            print(f"CHECK {raw.decode('utf-8')}: {label} (value hidden)")
            failed = True
    print(f"Scanned {count} tracked/unignored working files")
    if args.history:
        # Batch mode reads each unique blob once, including deleted files. No diff or secret is printed.
        objects = git("rev-list", "--objects", "--all").splitlines()
        proc = subprocess.Popen(
            ["git", "cat-file", "--batch"],
            cwd=ROOT,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        blobs = 0
        try:
            for obj in objects:
                oid = obj.split(b" ", 1)[0]
                proc.stdin.write(oid + b"\n")
                proc.stdin.flush()
                header = proc.stdout.readline().split()
                if len(header) != 3:
                    raise RuntimeError("Could not read Git object")
                data = proc.stdout.read(int(header[2]))
                proc.stdout.read(1)
                if header[1] != b"blob":
                    continue
                blobs += 1
                for label in findings(data):
                    print(f"CHECK Git blob {oid.decode()}: {label} (value hidden)")
                    failed = True
        finally:
            proc.stdin.close()
            proc.stdout.close()
            proc.wait()
        print(f"Scanned {blobs} reachable historical blobs")
    if not failed:
        print(
            "No credential patterns found. Review third-party rights separately in NOTICE.md."
        )
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
