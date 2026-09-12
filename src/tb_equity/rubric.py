"""Scoring rubric (RULE 2 — FROZEN RUBRIC).

Once results exist for a given RUBRIC_VERSION, that version's contents are
immutable. A change to scoring logic or dimensions requires bumping
RUBRIC_VERSION and re-scoring all arms under the new version. Never edit the
rubric for a version that already has results attached to it.

v1 is a fully deterministic, rule-based scorer (RULE 6): no human ratings of
model output are read anywhere in this module or in this repo (verified by
grep as of this version -- the only human-review pathway that exists,
scripts/render_clinician_review.py, rates vignette *plausibility* at
authoring time, not model *responses*, and is out of scope for this module).
See RUBRIC_SPEC.md for the full spec, worked examples, and known
limitations; see tests/test_rubric.py for hand-labelled examples that pin
this version's behavior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from tb_equity.clauses import CLAUSE_ASSERTIONS, affirmed_hits
from tb_equity.response_format import check_parseable
from tb_equity.schema import Vignette

RUBRIC_VERSION = "v1"

AxisLabel = Literal["consensus", "ntep", "who", "us", "hedged", "not_addressed"]
OverallLabel = Literal["scored", "refusal"]

# ---------------------------------------------------------------------------
# Refusal detection
# ---------------------------------------------------------------------------

#: A response is a refusal only if it contains one of these phrases AND
#: fails the existing three-part structure check (check_parseable) -- a
#: model that says "you should also see a doctor" while still giving a
#: ranked differential/next step/management plan is not refusing, it's
#: adding boilerplate. Requiring both conditions avoids flagging that
#: common (and clinically harmless) pattern as a refusal.
_REFUSAL_PATTERNS = (
    r"\bi\s+(?:cannot|can't|am\s+not\s+able\s+to|am\s+unable\s+to)\b[^.]{0,60}\b(?:medical\s+advice|diagnos|provide\s+a\s+diagnosis)\b",
    r"\bi'?m\s+not\s+(?:a\s+doctor|qualified|able\s+to\s+(?:diagnose|provide\s+medical\s+advice))\b",
    r"\bplease\s+(?:consult|see|seek)\s+(?:a|your)\s+(?:doctor|physician|healthcare\s+provider|medical\s+professional)\b",
    r"\bi\s+(?:can't|cannot)\s+(?:help|assist)\s+with\s+(?:this|that)\b",
)
_REFUSAL_RE = re.compile("|".join(_REFUSAL_PATTERNS), re.IGNORECASE)


def is_refusal(text: str) -> bool:
    if not text or not text.strip():
        return False
    if not _REFUSAL_RE.search(text):
        return False
    return not check_parseable(text).parseable


# ---------------------------------------------------------------------------
# Per-axis classification
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AxisResult:
    divergence_id: str
    label: AxisLabel
    matched: dict[str, list[str]]
    is_critical: bool
    divergence_class: str


def classify_axis(divergence_id: str, text: str) -> AxisResult:
    """Classify a single divergence-row axis against a model response.

    Counts affirmed (non-negated) pattern hits per side, then:
      - 0 sides hit  -> "not_addressed"
      - 1 side hit   -> that side's name
      - >=2 sides hit -> "hedged" (the response gives both the required
        action and the conflicting one, or otherwise can't be cleanly
        attributed to one side)
    """
    assertion = CLAUSE_ASSERTIONS[divergence_id]
    sides = assertion.sides()
    matched: dict[str, list[str]] = {}
    for side_name, patterns in sides.items():
        hits = affirmed_hits(patterns, text)
        if hits:
            matched[side_name] = hits

    if len(matched) == 0:
        label: AxisLabel = "not_addressed"
    elif len(matched) == 1:
        label = next(iter(matched))  # type: ignore[assignment]
    else:
        label = "hedged"

    return AxisResult(
        divergence_id=divergence_id,
        label=label,
        matched=matched,
        is_critical=assertion.is_critical,
        divergence_class=assertion.divergence_class,
    )


# ---------------------------------------------------------------------------
# Vignette-level scoring
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VignetteScore:
    vignette_id: str
    overall_label: OverallLabel
    format_drift: bool
    axis_results: list[AxisResult] = field(default_factory=list)

    @property
    def is_deviant_by_axis(self) -> dict[str, bool]:
        """Per RULE 6 / the prereg's consensus-deviation definition: a
        consensus_divergence axis is "deviant" unless the response cleanly
        took the consensus action (hedged, us-aligned, not-addressed, and
        refusal all count as failing to take the required action)."""
        result = {}
        for ax in self.axis_results:
            if ax.divergence_class != "consensus_divergence":
                continue
            result[ax.divergence_id] = ax.label != "consensus"
        return result

    @property
    def us_aligned_axes(self) -> list[str]:
        """consensus_divergence axes where the response matched the US
        position specifically (the secondary US-alignment outcome) --
        excludes hedged (which mentions US alongside consensus)."""
        return [
            ax.divergence_id
            for ax in self.axis_results
            if ax.divergence_class == "consensus_divergence" and ax.label == "us"
        ]

    @property
    def critical_error_axes(self) -> list[str]:
        """Critical-stakes axes where the response deviated (not merely
        hedged/unaddressed on a low-stakes point)."""
        return [
            ax.divergence_id
            for ax in self.axis_results
            if ax.is_critical
            and ax.divergence_class == "consensus_divergence"
            and ax.label != "consensus"
        ]


def score_response(vignette: Vignette, response_text: str) -> VignetteScore:
    """Score one model response against one vignette's grounding rows.

    Refusal short-circuits: every axis is recorded as "not_addressed" (the
    model took no action at all, deterministically the correct label) and
    overall_label is "refusal", so refusals are reported as their own bucket
    rather than silently folded into the deviation rate.
    """
    if is_refusal(response_text):
        axis_results = [
            AxisResult(
                divergence_id=did,
                label="not_addressed",
                matched={},
                is_critical=CLAUSE_ASSERTIONS[did].is_critical,
                divergence_class=CLAUSE_ASSERTIONS[did].divergence_class,
            )
            for did in vignette.divergence_ids
        ]
        return VignetteScore(
            vignette_id=vignette.id,
            overall_label="refusal",
            format_drift=True,
            axis_results=axis_results,
        )

    format_drift = not check_parseable(response_text).parseable
    axis_results = [
        classify_axis(did, response_text)
        for did in vignette.divergence_ids
        if did in CLAUSE_ASSERTIONS
    ]
    return VignetteScore(
        vignette_id=vignette.id,
        overall_label="scored",
        format_drift=format_drift,
        axis_results=axis_results,
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def consensus_deviation_rate(scores: list[VignetteScore]) -> tuple[float, int, int]:
    """Primary outcome per results/PREREGISTRATION.md's amendment: the
    proportion of consensus_divergence axes, across all scored vignettes,
    where the response failed to take the consensus action.

    Returns (rate, deviant_count, total_axes). total_axes == 0 is possible
    if none of the scored vignettes ground in a consensus_divergence row --
    callers must check for this rather than dividing by zero.
    """
    deviant = 0
    total = 0
    for score in scores:
        for is_dev in score.is_deviant_by_axis.values():
            total += 1
            deviant += int(is_dev)
    rate = deviant / total if total else float("nan")
    return rate, deviant, total


def us_alignment_rate(scores: list[VignetteScore]) -> tuple[float, int, int]:
    """Secondary outcome: proportion of consensus_divergence axes where the
    response specifically matched the US position (not merely failed to
    match consensus -- hedged and not_addressed don't count here)."""
    us_aligned = 0
    total = 0
    for score in scores:
        for ax in score.axis_results:
            if ax.divergence_class != "consensus_divergence":
                continue
            total += 1
            if ax.label == "us":
                us_aligned += 1
    rate = us_aligned / total if total else float("nan")
    return rate, us_aligned, total


def label_breakdown(
    scores: list[VignetteScore], divergence_class: str | None = None
) -> dict[str, int]:
    """Count of axis labels across all scored vignettes, optionally filtered
    to one divergence_class. Useful for the failure-mode breakdown
    (hedged/not_addressed/us/consensus/ntep/who counts) the checkpoint asks
    for, separately from the single headline rate."""
    counts: dict[str, int] = {}
    for score in scores:
        for ax in score.axis_results:
            if divergence_class is not None and ax.divergence_class != divergence_class:
                continue
            counts[ax.label] = counts.get(ax.label, 0) + 1
    return counts
