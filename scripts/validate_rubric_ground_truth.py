#!/usr/bin/env python3
"""Report the rubric's self-consistency accuracy against the real v1
vignette set's own hand-authored ntep/who/us_correct_actions text (see
src/tb_equity/rubric_validation.py for what this checks and why).

Usage: python scripts/validate_rubric_ground_truth.py [version]  (default: v1)
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.render import load_vignettes  # noqa: E402
from tb_equity.rubric_validation import validate_against_ground_truth  # noqa: E402


def main(version: str) -> None:
    vignettes = load_vignettes(version)
    report = validate_against_ground_truth(vignettes)

    print(f"Vignette set: {version} ({len(vignettes)} vignettes)")
    print(f"Total (vignette, divergence_id, side) instances checked: {report.total_checked}")
    print(f"Correct: {report.total_correct}  ({report.accuracy:.1%})")
    print(f"Skipped (no us_position exists for this row): {report.skipped_no_us_side}")
    print()
    print("Per divergence_id accuracy:")
    for did in sorted(report.per_divergence_id, key=lambda x: int(x.split("-")[1])):
        c, t = report.per_divergence_id[did]
        flag = "  <-- below 90%" if t and c / t < 0.9 else ""
        print(f"  {did}: {c}/{t} ({c / t:.0%}){flag}")

    if report.mismatches:
        print()
        print(f"{len(report.mismatches)} mismatches (for hand inspection):")
        for m in report.mismatches:
            print(
                f"  [{m.vignette_id} / {m.divergence_id} / {m.side}] "
                f"expected={m.expected!r} got={m.got!r}"
            )
            print(f"    text: {m.text!r}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v1")
