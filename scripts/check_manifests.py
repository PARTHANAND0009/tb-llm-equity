#!/usr/bin/env python3
"""Validate results/manifests/*.json against RULE 1's required fields.

Backs the `make manifest-check` target. Exits non-zero if any manifest file
is invalid JSON or is missing a required field. Succeeds trivially (with a
notice) if no manifests exist yet.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = REPO_ROOT / "results" / "manifests"

sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.manifest import validate_manifest  # noqa: E402


def main() -> int:
    manifest_files = sorted(MANIFEST_DIR.glob("*.json"))
    if not manifest_files:
        print("check_manifests: no manifests found yet -- nothing to check.")
        return 0

    failed = False
    for path in manifest_files:
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failed = True
            print(f"{path}: invalid JSON ({exc})")
            continue
        problems = validate_manifest(manifest)
        for problem in problems:
            failed = True
            print(f"{path}: {problem}")

    if failed:
        print("\nRULE 1 violation: one or more manifests are incomplete.")
        return 1

    print(f"check_manifests: {len(manifest_files)} manifest(s) OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
