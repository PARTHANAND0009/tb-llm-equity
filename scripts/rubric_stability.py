#!/usr/bin/env python3
"""Inter-version stability report for RUBRIC_VERSION (Stage-1 checkpoint
deliverable): if the scorer is tweaked, how much does the headline number
move?

No real model responses exist yet (the pilot hasn't run -- see
KNOWN_ISSUES.md / CLAUDE.md Status), so this uses the only real text
available: each of the 100 v1 vignettes' own hand-authored
ntep_correct_actions / us_correct_actions strings, wrapped in the same
three-part response format the arm-1 prompt asks for. This gives two
synthetic corpora with a KNOWN ground truth (100 "fully consensus-compliant"
responses, 100 "fully US-deviant" responses), so the headline number's
sensitivity to a scorer change can be measured exactly, even though it is
not a substitute for measuring sensitivity against real model output (that
re-run must happen once the pilot has real responses -- flagged as
follow-up, not silently skipped).

Compares the current scorer (directional pre/post negation handling, this
session's fix) against a naive baseline variant that ignores negation
entirely (any pattern match counts as a hit) -- representing the most
plausible prior/alternate version of this scorer, since negation handling
is exactly the kind of thing that gets added, removed, or retuned between
rubric versions.

Usage: python scripts/rubric_stability.py [version]  (default: v1)
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.clauses import CLAUSE_ASSERTIONS  # noqa: E402
from tb_equity.render import load_vignettes  # noqa: E402
from tb_equity.rubric import (  # noqa: E402
    VignetteScore,
    classify_axis,
    consensus_deviation_rate,
    us_alignment_rate,
)
from tb_equity.rubric_variants import classify_axis_naive  # noqa: E402
from tb_equity.schema import Vignette  # noqa: E402

FORMAT_TEMPLATE = (
    "1. Differential diagnosis: (not evaluated by this synthetic corpus).\n"
    "2. Next diagnostic step / initial management plan: {actions}\n"
)


def synthetic_response(vignette: Vignette, side: str) -> str:
    actions = getattr(vignette, side)
    return FORMAT_TEMPLATE.format(actions=" ".join(actions))



def score_corpus(vignettes: list[Vignette], side: str, classify_fn) -> list[VignetteScore]:
    scores = []
    for v in vignettes:
        text = synthetic_response(v, side)
        axis_results = [
            classify_fn(did, text) for did in v.divergence_ids if did in CLAUSE_ASSERTIONS
        ]
        scores.append(
            VignetteScore(
                vignette_id=v.id,
                overall_label="scored",
                format_drift=False,
                axis_results=axis_results,
            )
        )
    return scores


def report_variant(name: str, vignettes: list[Vignette], classify_fn) -> None:
    print(f"--- {name} ---")
    sides = (("ntep_correct_actions", "compliant corpus"), ("us_correct_actions", "deviant corpus"))
    for side, label in sides:
        scores = score_corpus(vignettes, side, classify_fn)
        dev_rate, dev_n, dev_total = consensus_deviation_rate(scores)
        us_rate, us_n, us_total = us_alignment_rate(scores)
        print(
            f"  {label:18s}  consensus_deviation_rate={dev_rate:.1%} ({dev_n}/{dev_total})"
            f"   us_alignment_rate={us_rate:.1%} ({us_n}/{us_total})"
        )


def main(version: str) -> None:
    vignettes = load_vignettes(version)
    print(f"Vignette set: {version} ({len(vignettes)} vignettes)")
    print(
        "Synthetic corpora: each vignette's own ntep_correct_actions text (expected: 0% "
        "deviation) and us_correct_actions text (expected: 100% deviation, 100% US-alignment "
        "on rows with a us_position)."
    )
    print()
    report_variant("current scorer (directional negation handling)", vignettes, classify_axis)
    print()
    report_variant("naive baseline (no negation handling)", vignettes, classify_axis_naive)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "v1")
