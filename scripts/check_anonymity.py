#!/usr/bin/env python3
"""Pre-commit check for RULE 3 — ANONYMITY.

No school name, city, or state may appear in any file under data/ or
results/, or in any generated text. This script scans the given files for
case-insensitive substring matches against the blocklist in
config/blocklist.txt and fails (non-zero exit) if any are found.

Usage (via pre-commit, which passes staged file paths as argv):
    python scripts/check_anonymity.py [FILE ...]

Uses only the standard library so it runs under "language: system" in
pre-commit without needing the project venv.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BLOCKLIST_PATH = REPO_ROOT / "config" / "blocklist.txt"


def load_blocklist(path: Path = BLOCKLIST_PATH) -> list[str]:
    if not path.exists():
        return []
    terms = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        terms.append(stripped)
    return terms


def scan_file(path: Path, terms: list[str]) -> list[tuple[int, str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    hits = []
    lower_terms = [(t, t.lower()) for t in terms]
    for lineno, line in enumerate(text.splitlines(), start=1):
        lower_line = line.lower()
        for original, lowered in lower_terms:
            if lowered in lower_line:
                hits.append((lineno, original, line.strip()))
    return hits


def main(argv: list[str]) -> int:
    terms = load_blocklist()
    if not terms:
        print(
            "check_anonymity: config/blocklist.txt has no entries yet -- "
            "nothing to check. Populate it before committing real data."
        )
        return 0

    if not argv:
        print("check_anonymity: no files given, nothing to check.")
        return 0

    failed = False
    for arg in argv:
        path = Path(arg)
        if not path.is_file():
            continue
        hits = scan_file(path, terms)
        for lineno, term, line in hits:
            failed = True
            print(f"{path}:{lineno}: blocked identifier '{term}' found: {line}")

    if failed:
        print(
            "\nRULE 3 violation: identifying strings found (see config/blocklist.txt). "
            "Remove them before committing."
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
