"""Deliberately-inferior scorer variants, kept only for sensitivity/stability

comparisons against the real RUBRIC_VERSION scorer in rubric.py -- never
used to compute a reported outcome. See RUBRIC_SPEC.md section 10 and
scripts/rubric_stability.py / scripts/analyze_results.py for how these are
used.
"""

from __future__ import annotations

import re

from tb_equity.clauses import CLAUSE_ASSERTIONS
from tb_equity.rubric import AxisResult


def classify_axis_naive(divergence_id: str, text: str) -> AxisResult:
    """Baseline variant: a bare regex search, no negation handling at all --
    what src/tb_equity/rubric.py's classify_axis effectively did before this
    project's directional pre/post negation fix (see clauses.py's
    affirmed_hits). Used only to measure how much the headline number would
    move under a plausible alternate scorer design -- never to score a real
    result."""
    assertion = CLAUSE_ASSERTIONS[divergence_id]
    sides = assertion.sides()
    matched: dict[str, list[str]] = {}
    for side_name, patterns in sides.items():
        hits = [pat for pat in patterns if re.search(pat, text, re.IGNORECASE)]
        if hits:
            matched[side_name] = hits
    if len(matched) == 0:
        label = "not_addressed"
    elif len(matched) == 1:
        label = next(iter(matched))
    else:
        label = "hedged"
    return AxisResult(
        divergence_id=divergence_id,
        label=label,
        matched=matched,
        is_critical=assertion.is_critical,
        divergence_class=assertion.divergence_class,
    )
