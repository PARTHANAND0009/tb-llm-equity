"""Stage 2 / Step 5 primary analysis: turns raw model responses under

`data/responses/` into the preregistered outcomes, computed via
`tb_equity.rubric` (RUBRIC_VERSION frozen per Stage 2's instruction --
nothing here may alter scoring logic, only aggregate its output).

This module contains no I/O beyond what's passed to it, so it can be
exercised in tests against synthetic responses. `scripts/analyze_results.py`
is the CLI that loads real `data/responses/*.json` + `data/vignettes/v1/`
and calls into this module.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Literal

from tb_equity.reachability import REACHABILITY_SENSITIVE_ROWS, compute_reachability
from tb_equity.rubric import (
    VignetteScore,
    consensus_deviation_rate,
    score_response,
    us_alignment_rate,
)
from tb_equity.schema import Vignette


@dataclass(frozen=True)
class RawResponse:
    """One checkpointed response, as read from data/responses/<key>.json's
    'raw' field plus its 'text'. Deliberately mirrors what the notebook
    actually writes (see src/tb_equity/checkpoint.py) rather than requiring
    the caller to recompute a cache key."""

    vignette_id: str
    arm: int
    family: str
    model: str
    model_revision: str
    seed: int
    text: str
    truncated: bool = False
    #: "freeform" (the preregistered arm1-4 prompts) or "structured" (the
    #: Checkpoint 2b-v elicitation-arm re-pilot, not a preregistered arm --
    #: see src/tb_equity/structured_elicitation.py). Defaults to "freeform"
    #: so every existing/future preregistered-arm response needs no change.
    elicitation: str = "freeform"


def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% (z=1.96) Wilson score interval for a binomial proportion.

    Chosen over the normal (Wald) approximation because it stays within
    [0, 1] and remains well-behaved at proportions near 0 or 1 -- exactly
    the range a "near-zero or near-total deviation" pilot-stop condition
    would land in, where a Wald interval can misbehave.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    phat = successes / n
    denom = 1 + z**2 / n
    center = (phat + z**2 / (2 * n)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / n + z**2 / (4 * n**2))) / denom
    return (max(0.0, center - half), min(1.0, center + half))


@dataclass
class ModelOutcome:
    family: str
    consensus_deviation_rate: float
    consensus_deviation_ci: tuple[float, float]
    consensus_deviation_n: int
    us_alignment_rate: float
    us_alignment_ci: tuple[float, float]
    us_alignment_n: int
    refusal_rate: float
    format_drift_rate: float
    n_responses_scored: int
    label_breakdown: dict[str, int]


def truncation_rate_by_family(responses: list[RawResponse]) -> dict[str, tuple[float, int]]:
    """Proportion of responses that hit GENERATION_MAX_TOKENS rather than a
    real stop token, per family. Reported separately from deviation/refusal/
    format-drift for the same reason those are: a truncated response can cut
    off before addressing a later divergence axis, inflating that axis's
    not_addressed count for a reason that has nothing to do with the model's
    actual protocol preference -- see RUBRIC_SPEC.md and the pilot finding
    that motivated adding this (Granite-4.2-8B truncated 10/12 pilot
    responses at 1600 tokens of visible pre-answer deliberation)."""
    by_family: dict[str, list[bool]] = defaultdict(list)
    for r in responses:
        by_family[r.family].append(r.truncated)
    return {fam: (sum(flags) / len(flags), len(flags)) for fam, flags in by_family.items()}


def score_all(
    responses: list[RawResponse], vignettes_by_id: dict[str, Vignette]
) -> dict[str, list[VignetteScore]]:
    """Score every response, grouped by family. Responses whose vignette_id
    isn't found are skipped with no error -- callers should check counts
    against what they expected rather than rely on this to fail loudly,
    since a partial/in-progress Colab run is an expected input shape, not
    an error condition."""
    by_family: dict[str, list[VignetteScore]] = {}
    for r in responses:
        vignette = vignettes_by_id.get(r.vignette_id)
        if vignette is None:
            continue
        score = score_response(vignette, r.text)
        by_family.setdefault(r.family, []).append(score)
    return by_family


def summarize_model(family: str, scores: list[VignetteScore]) -> ModelOutcome:
    dev_rate, dev_n, dev_total = consensus_deviation_rate(scores)
    us_rate, us_n, us_total = us_alignment_rate(scores)
    n_refusal = sum(1 for s in scores if s.overall_label == "refusal")
    n_format_drift = sum(1 for s in scores if s.format_drift)
    dev_ci = wilson_interval(dev_n, dev_total) if dev_total else (float("nan"),) * 2
    return ModelOutcome(
        family=family,
        consensus_deviation_rate=dev_rate,
        consensus_deviation_ci=dev_ci,
        consensus_deviation_n=dev_total,
        us_alignment_rate=us_rate,
        us_alignment_ci=wilson_interval(us_n, us_total) if us_total else (float("nan"),) * 2,
        us_alignment_n=us_total,
        refusal_rate=n_refusal / len(scores) if scores else float("nan"),
        format_drift_rate=n_format_drift / len(scores) if scores else float("nan"),
        n_responses_scored=len(scores),
        label_breakdown=_label_breakdown(scores),
    )


def _label_breakdown(scores: list[VignetteScore]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for s in scores:
        for ax in s.axis_results:
            if ax.divergence_class != "consensus_divergence":
                continue
            counts[ax.label] = counts.get(ax.label, 0) + 1
    return counts


@dataclass
class ClauseOutcome:
    divergence_id: str
    deviant: int
    total: int

    @property
    def rate(self) -> float:
        return self.deviant / self.total if self.total else float("nan")


def breakdown_by_clause(scores: list[VignetteScore]) -> dict[str, ClauseOutcome]:
    """Per-DIV-### deviation rate, consensus_divergence axes only (the ones
    with a defined "deviant" concept -- see VignetteScore.is_deviant_by_axis)."""
    counts: dict[str, list[int]] = {}
    for s in scores:
        for did, is_dev in s.is_deviant_by_axis.items():
            counts.setdefault(did, [0, 0])
            counts[did][0] += int(is_dev)
            counts[did][1] += 1
    return {
        did: ClauseOutcome(divergence_id=did, deviant=dev, total=total)
        for did, (dev, total) in counts.items()
    }


@dataclass
class CategoryOutcome:
    category: str
    deviant: int
    total: int

    @property
    def rate(self) -> float:
        return self.deviant / self.total if self.total else float("nan")


def breakdown_by_category(
    responses: list[RawResponse],
    scores_by_response_index: list[VignetteScore],
    vignettes_by_id: dict[str, Vignette],
    category_fn,
) -> dict[str, CategoryOutcome]:
    """category_fn(Vignette) -> str, e.g. lambda v: v.presentation_type."""
    counts: dict[str, list[int]] = {}
    for r, score in zip(responses, scores_by_response_index, strict=True):
        vignette = vignettes_by_id.get(r.vignette_id)
        if vignette is None:
            continue
        category = category_fn(vignette)
        for is_dev in score.is_deviant_by_axis.values():
            counts.setdefault(category, [0, 0])
            counts[category][0] += int(is_dev)
            counts[category][1] += 1
    return {
        cat: CategoryOutcome(category=cat, deviant=dev, total=total)
        for cat, (dev, total) in counts.items()
    }


@dataclass
class VarianceReport:
    """Within-vignette-axis response variance across samples (Step 4's ask):
    for each (family, vignette_id, arm, divergence_id), do the N sampled
    responses agree on the axis label, or does it flip?"""

    n_groups: int
    n_flipping: int

    @property
    def flip_rate(self) -> float:
        return self.n_flipping / self.n_groups if self.n_groups else float("nan")

    flipping_examples: list[tuple[str, str, int, str]] = field(default_factory=list)


def compute_variance(
    responses: list[RawResponse], vignettes_by_id: dict[str, Vignette]
) -> dict[str, VarianceReport]:
    """One VarianceReport per family. A 'group' is (vignette_id, arm,
    divergence_id) -- flips if the set of axis labels across that group's
    samples has more than one distinct value."""
    groups: dict[tuple[str, str, int], dict[str, set[str]]] = {}
    for r in responses:
        vignette = vignettes_by_id.get(r.vignette_id)
        if vignette is None:
            continue
        score = score_response(vignette, r.text)
        key = (r.family, r.vignette_id, r.arm)
        per_axis = groups.setdefault(key, {})
        for ax in score.axis_results:
            per_axis.setdefault(ax.divergence_id, set()).add(ax.label)

    reports: dict[str, VarianceReport] = {}
    for (family, vignette_id, arm), per_axis in groups.items():
        report = reports.setdefault(family, VarianceReport(n_groups=0, n_flipping=0))
        for did, labels in per_axis.items():
            report.n_groups += 1
            if len(labels) > 1:
                report.n_flipping += 1
                report.flipping_examples.append((vignette_id, did, arm, "/".join(sorted(labels))))
    return reports


@dataclass
class ReachabilityAdjustedSilence:
    """Silence rate on REACHABILITY_SENSITIVE_ROWS (DIV-006/DIV-007),
    reported both ways per Checkpoint 2b-iv's explicit requirement -- never
    report only one of these, and flag it if they diverge materially."""

    ambiguous_as_silence_rate: float
    ambiguous_as_silence_n: tuple[int, int]  # (silent, total)
    ambiguous_excluded_rate: float
    ambiguous_excluded_n: tuple[int, int]  # (silent, total-after-exclusion)
    n_unreached: int
    n_ambiguous: int

    @property
    def diverges_materially(self) -> bool:
        """True if the two rates differ by >= 10 percentage points -- an
        arbitrary but stated threshold for flagging, not a hidden judgment
        call buried in a number."""
        if math.isnan(self.ambiguous_as_silence_rate) or math.isnan(self.ambiguous_excluded_rate):
            return False
        return abs(self.ambiguous_as_silence_rate - self.ambiguous_excluded_rate) >= 0.10


def reachability_adjusted_silence(
    responses: list[RawResponse], vignettes_by_id: dict[str, Vignette]
) -> dict[str, ReachabilityAdjustedSilence]:
    """Per family: not_addressed rate on DIV-006/DIV-007 axes only, computed
    both with AMBIGUOUS reachability counted as silence and with it
    excluded. UNREACHED instances are excluded from both computations in
    every case -- an axis that was never reachable was never available to
    be silent about, under either accounting.
    """
    by_family: dict[str, list[tuple[str, bool]]] = defaultdict(list)  # (reachability, is_silent)
    unreached_counts: dict[str, int] = defaultdict(int)
    ambiguous_counts: dict[str, int] = defaultdict(int)

    for r in responses:
        vignette = vignettes_by_id.get(r.vignette_id)
        if vignette is None:
            continue
        score = score_response(vignette, r.text)
        for ax in score.axis_results:
            if ax.divergence_id not in REACHABILITY_SENSITIVE_ROWS:
                continue
            reach = compute_reachability(ax.divergence_id, r.text)
            is_silent = ax.label == "not_addressed"
            if reach == "UNREACHED":
                unreached_counts[r.family] += 1
                continue
            if reach == "AMBIGUOUS":
                ambiguous_counts[r.family] += 1
            by_family[r.family].append((reach, is_silent))

    results = {}
    for family, entries in by_family.items():
        # (i) AMBIGUOUS counted as silence: forced to silent=True regardless
        # of its actual axis label -- the conservative reading (an
        # unresolved reachability call doesn't get credited as addressed).
        total_incl = len(entries)
        silent_incl = sum(1 for reach, is_silent in entries if reach == "AMBIGUOUS" or is_silent)
        rate_incl = silent_incl / total_incl if total_incl else float("nan")

        # (ii) AMBIGUOUS excluded from the denominator entirely -- neither
        # counted as silent nor as addressed.
        excl_entries = [(r, s) for r, s in entries if r != "AMBIGUOUS"]
        total_excl = len(excl_entries)
        silent_excl = sum(1 for _, is_silent in excl_entries if is_silent)
        rate_excl = silent_excl / total_excl if total_excl else float("nan")

        results[family] = ReachabilityAdjustedSilence(
            ambiguous_as_silence_rate=rate_incl,
            ambiguous_as_silence_n=(silent_incl, total_incl),
            ambiguous_excluded_rate=rate_excl,
            ambiguous_excluded_n=(silent_excl, total_excl),
            n_unreached=unreached_counts[family],
            n_ambiguous=ambiguous_counts[family],
        )
    return results


def control_coverage_by_family(
    responses: list[RawResponse],
    vignettes_by_id: dict[str, Vignette],
    elicitation: str | None = None,
) -> dict[str, dict[str, tuple[float, int, int]]]:
    """Per family, per entailment control: (coverage_rate, n_addressed,
    n_total). Only counted for responses whose vignette actually grounds
    that control's paired divergence row (see CONTROL_PAIRED_ROW) -- a
    control's underlying question is only asked/relevant when its paired
    row is live for that vignette. `elicitation` optionally filters to
    "structured" or "freeform" only; None includes both.
    """
    from tb_equity.entailment_controls import CONTROL_PAIRED_ROW, score_control

    tallies: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in responses:
        if elicitation is not None and r.elicitation != elicitation:
            continue
        vignette = vignettes_by_id.get(r.vignette_id)
        if vignette is None:
            continue
        for control_id, paired_row in CONTROL_PAIRED_ROW.items():
            if paired_row not in vignette.divergence_ids:
                continue
            label = score_control(control_id, r.text)
            entry = tallies[r.family][control_id]
            entry[1] += 1
            entry[0] += int(label == "addressed")

    return {
        family: {
            cid: (n_addr / n_tot if n_tot else float("nan"), n_addr, n_tot)
            for cid, (n_addr, n_tot) in controls.items()
        }
        for family, controls in tallies.items()
    }


H1H2Label = Literal[
    "H1_divergence_specific", "H2_general_granularity", "directional_nondefinitive"
]


@dataclass
class H1H2Verdict:
    family: str
    control_coverage_rate: float
    divergence_coverage_rate: float
    gap_pp: float  # percentage points, control minus divergence
    verdict: H1H2Label


def divergence_addressed_rate(scores: list[VignetteScore]) -> tuple[float, int, int]:
    """Proportion of consensus_divergence axes where the response committed
    to EITHER side (consensus, us, or hedged) rather than staying silent.

    This is deliberately NOT `1 - consensus_deviation_rate`: that rate
    treats a fully-committed `us`-labeled answer as "deviant" identically to
    a `not_addressed` one, which conflates "chose the non-consensus side"
    (the actual phenomenon under study) with "said nothing about this axis
    at all" (avoidance/silence). The H1/H2 discriminator is specifically
    about the latter, so it needs its own denominator: addressed = anything
    other than not_addressed, regardless of which side.
    """
    addressed = 0
    total = 0
    for score in scores:
        for ax in score.axis_results:
            if ax.divergence_class != "consensus_divergence":
                continue
            total += 1
            addressed += int(ax.label != "not_addressed")
    rate = addressed / total if total else float("nan")
    return rate, addressed, total


def divergence_addressed_by_family(
    responses: list[RawResponse],
    vignettes_by_id: dict[str, Vignette],
    elicitation: str | None = None,
) -> dict[str, tuple[float, int, int]]:
    """Per family: divergence_addressed_rate, restricted to `elicitation` if
    given (None includes both structured and freeform) -- the per-model,
    per-arm divergence-axis coverage breakdown Checkpoint 2b-v Step E asks
    for, reported alongside control_coverage_by_family's per-control rates.
    """
    filtered = [r for r in responses if elicitation is None or r.elicitation == elicitation]
    by_family = score_all(filtered, vignettes_by_id)
    return {family: divergence_addressed_rate(scores) for family, scores in by_family.items()}


def headline_structured_vs_control(
    responses: list[RawResponse], vignettes_by_id: dict[str, Vignette]
) -> dict[str, H1H2Verdict]:
    """The Checkpoint 2b-v headline: in the STRUCTURED arm only, does control
    coverage approach ceiling while divergence coverage stays low (H1,
    divergence-specific avoidance), or do both rise together (H2, a general
    granularity effect not specific to contested axes)? Pre-specified rule
    (stated before Step E ran, not fit afterward):
      - control_rate >= 0.70 AND gap >= 0.20  -> H1
      - gap < 0.20                             -> H2
      - otherwise                              -> directional, non-definitive
    """
    structured = [r for r in responses if r.elicitation == "structured"]
    controls = control_coverage_by_family(structured, vignettes_by_id, elicitation="structured")

    by_family_scores = score_all(structured, vignettes_by_id)
    results: dict[str, H1H2Verdict] = {}
    for family, control_rates in controls.items():
        rates = [rate for rate, _, _ in control_rates.values() if not math.isnan(rate)]
        control_rate = sum(rates) / len(rates) if rates else float("nan")

        divergence_coverage_rate, _, _ = divergence_addressed_rate(by_family_scores.get(family, []))

        gap = control_rate - divergence_coverage_rate
        if math.isnan(control_rate) or math.isnan(divergence_coverage_rate):
            verdict = "directional_nondefinitive"
        elif control_rate >= 0.70 and gap >= 0.20:
            verdict = "H1_divergence_specific"
        elif gap < 0.20:
            verdict = "H2_general_granularity"
        else:
            verdict = "directional_nondefinitive"

        results[family] = H1H2Verdict(
            family=family,
            control_coverage_rate=control_rate,
            divergence_coverage_rate=divergence_coverage_rate,
            gap_pp=gap * 100,
            verdict=verdict,
        )
    return results


def conditional_alignment_among_addressed(scores: list[VignetteScore]) -> dict[str, int]:
    """Same shape as the internal _label_breakdown, but with not_addressed
    excluded from the tally -- answers the question 'among responses that
    DID address this axis, what did they say', as opposed to the headline
    deviation rate which treats not_addressed as a form of deviation."""
    counts: dict[str, int] = {}
    for s in scores:
        for ax in s.axis_results:
            if ax.divergence_class != "consensus_divergence" or ax.label == "not_addressed":
                continue
            counts[ax.label] = counts.get(ax.label, 0) + 1
    return counts
