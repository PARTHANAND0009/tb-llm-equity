#!/usr/bin/env python3
"""Pre-commit check for RULE 3 — ANONYMITY.

No school name, city, or state may appear in any file under data/ or
results/, or in any generated text. This script scans the given files for
case-insensitive substring matches against the blocklist in
config/blocklist.txt and fails (non-zero exit) if any are found.

Usage (via pre-commit, which passes staged file paths as argv):
    python scripts/check_anonymity.py [FILE ...]

Any argv entry that is a directory is expanded to every file under it
(recursively) -- this is what lets `python scripts/check_anonymity.py
data/prompts submission` used for a manual full-tree audit actually scan
files, rather than silently checking nothing (a plain `Path.is_file()`
guard on a directory argument is always False).

Separately from the blocklist, `check_provenance_scope_leak` enforces a
narrower, hard-coded rule: legitimate provenance strings that are meant to
appear ONLY in submission/ (e.g. a named clinician reviewer's name/
institution) must never leak into data/ or results/. These strings must
NOT be added to config/blocklist.txt, since the blocklist is enforced
everywhere including submission/ -- that would make the legitimate
provenance record itself a violation.

Uses only the standard library so it runs under "language: system" in
pre-commit without needing the project venv.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BLOCKLIST_PATH = REPO_ROOT / "config" / "blocklist.txt"

# Strings that are legitimate provenance ONLY inside submission/ (e.g. a
# named clinician reviewer recorded in METHODS_TRANSPARENCY.md) and must
# never leak into data/ or results/, where IRIS anonymous evaluation
# applies. Keep this in sync with provenance actually recorded in
# submission/ -- see submission/METHODS_TRANSPARENCY.md.
PROVENANCE_SCOPE_TERMS = [
    "Dr. Ojasvi Anand",
    "Ojasvi Anand",
    "SSR Medical College",
]
PROVENANCE_ALLOWED_PREFIX = "submission" + "/"


def _iter_files(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for arg in paths:
        p = Path(arg)
        if p.is_dir():
            files.extend(sorted(f for f in p.rglob("*") if f.is_file()))
        elif p.is_file():
            files.append(p)
    return files


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


def _relative_posix(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def check_provenance_scope_leak(files: list[Path]) -> list[tuple[Path, int, str, str]]:
    """Strings that are legitimate provenance only in submission/ must not

    appear anywhere else -- independent of (and not addable to) the
    blocklist. Returns (path, lineno, term, line) for every violation.
    """
    hits: list[tuple[Path, int, str, str]] = []
    for path in files:
        if _relative_posix(path).startswith(PROVENANCE_ALLOWED_PREFIX):
            continue
        for lineno, term, line in scan_file(path, PROVENANCE_SCOPE_TERMS):
            hits.append((path, lineno, term, line))
    return hits


def main(argv: list[str]) -> int:
    if not argv:
        print("check_anonymity: no files given, nothing to check.")
        return 0

    files = _iter_files(argv)

    terms = load_blocklist()
    failed = False

    if not terms:
        print(
            "check_anonymity: config/blocklist.txt has no entries yet -- "
            "nothing to check against the blocklist. Populate it before "
            "committing real data."
        )
    else:
        for path in files:
            hits = scan_file(path, terms)
            for lineno, term, line in hits:
                failed = True
                print(f"{path}:{lineno}: blocked identifier '{term}' found: {line}")

    scope_hits = check_provenance_scope_leak(files)
    for path, lineno, term, line in scope_hits:
        failed = True
        print(
            f"{path}:{lineno}: provenance string '{term}' found outside submission/ "
            f"(only allowed there): {line}"
        )

    if failed:
        print(
            "\nRULE 3 violation: identifying strings found. Remove them before committing."
        )
        return 1

    print(f"check_anonymity: scanned {len(files)} file(s), no violations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
