"""Tests for src/tb_equity/analysis.py against synthetic responses.

These validate the aggregation logic itself (grouping, CI computation,
breakdowns, variance detection) against known-shape inputs, not against any
particular real headline number -- the real pilot (Stage 2) data is scored
ad hoc via scripts/analyze_results.py once it exists under data/responses/.
"""

from __future__ import annotations

import math

from tb_equity.analysis import (
    RawResponse,
    breakdown_by_category,
    breakdown_by_clause,
    compute_variance,
    conditional_alignment_among_addressed,
    control_coverage_by_family,
    divergence_addressed_by_family,
    divergence_addressed_rate,
    headline_structured_vs_control,
    reachability_adjusted_silence,
    score_all,
    summarize_model,
    truncation_rate_by_family,
    wilson_interval,
)
from test_rubric import make_vignette


def test_wilson_interval_known_values():
    # 0/10: interval should be near-zero-anchored, entirely within [0, 1]
    lo, hi = wilson_interval(0, 10)
    assert 0.0 <= lo <= hi <= 1.0
    assert lo == 0.0

    # 10/10: symmetric case, upper bound clamped to 1.0
    lo, hi = wilson_interval(10, 10)
    assert hi == 1.0

    # 5/10: centered near 0.5, interval should straddle it
    lo, hi = wilson_interval(5, 10)
    assert lo < 0.5 < hi


def test_wilson_interval_zero_n_is_nan():
    lo, hi = wilson_interval(0, 0)
    assert math.isnan(lo) and math.isnan(hi)


def _resp(
    vignette_id, arm, family, text, seed=0, model="test-model", revision="rev0", truncated=False
):
    return RawResponse(
        vignette_id=vignette_id, arm=arm, family=family, model=model,
        model_revision=revision, seed=seed, text=text, truncated=truncated,
    )


def test_score_all_groups_by_family():
    v = make_vignette(["DIV-001"], id="VIG-100")
    vignettes = {"VIG-100": v}
    responses = [
        _resp("VIG-100", 1, "meta", "Send Xpert MTB/RIF as the initial test."),
        _resp("VIG-100", 1, "epfl", "Send AFB smear microscopy as the initial test."),
    ]
    by_family = score_all(responses, vignettes)
    assert set(by_family) == {"meta", "epfl"}
    assert by_family["meta"][0].axis_results[0].label == "consensus"
    assert by_family["epfl"][0].axis_results[0].label == "us"


def test_score_all_skips_unknown_vignette_silently():
    responses = [_resp("VIG-DOES-NOT-EXIST", 1, "meta", "anything")]
    by_family = score_all(responses, {})
    assert by_family == {}


def test_summarize_model_computes_expected_rates():
    v = make_vignette(["DIV-001"], id="VIG-101")
    vignettes = {"VIG-101": v}
    # 3 compliant, 1 deviant -> deviation rate 0.25
    texts = [
        "Send Xpert MTB/RIF as the initial test.",
        "Send Xpert MTB/RIF as the initial test.",
        "Send Xpert MTB/RIF as the initial test.",
        "Send AFB smear microscopy as the initial test.",
    ]
    responses = [_resp("VIG-101", 1, "meta", t) for t in texts]
    by_family = score_all(responses, vignettes)
    outcome = summarize_model("meta", by_family["meta"])
    assert outcome.consensus_deviation_rate == 0.25
    assert outcome.consensus_deviation_n == 4
    assert outcome.us_alignment_rate == 0.25
    assert outcome.refusal_rate == 0.0
    lo, hi = outcome.consensus_deviation_ci
    assert lo < 0.25 < hi


def test_summarize_model_reports_refusal_and_format_drift_separately():
    v = make_vignette(["DIV-001"], id="VIG-102")
    vignettes = {"VIG-102": v}
    responses = [
        _resp("VIG-102", 1, "meta", "I cannot provide medical advice. Please see a doctor."),
        _resp("VIG-102", 1, "meta", "just get an xpert test done first honestly"),
    ]
    by_family = score_all(responses, vignettes)
    outcome = summarize_model("meta", by_family["meta"])
    assert outcome.refusal_rate == 0.5
    assert outcome.format_drift_rate == 1.0  # both fail check_parseable


def test_breakdown_by_clause_isolates_each_row():
    v1 = make_vignette(["DIV-001"], id="VIG-103")
    v2 = make_vignette(["DIV-006"], id="VIG-104")
    vignettes = {"VIG-103": v1, "VIG-104": v2}
    responses = [
        _resp("VIG-103", 1, "meta", "Send AFB smear microscopy as the initial test."),  # deviant
        _resp("VIG-104", 1, "meta", "Administer daily dosing throughout both phases."),  # compliant
    ]
    by_family = score_all(responses, vignettes)
    breakdown = breakdown_by_clause(by_family["meta"])
    assert breakdown["DIV-001"].deviant == 1 and breakdown["DIV-001"].total == 1
    assert breakdown["DIV-006"].deviant == 0 and breakdown["DIV-006"].total == 1


def test_breakdown_by_category_uses_vignette_field():
    v = make_vignette(["DIV-001"], id="VIG-105", presentation_type="extrapulmonary")
    vignettes = {"VIG-105": v}
    responses = [_resp("VIG-105", 1, "meta", "Send AFB smear microscopy as the initial test.")]
    by_family = score_all(responses, vignettes)
    breakdown = breakdown_by_category(
        responses, by_family["meta"], vignettes, lambda vv: vv.presentation_type
    )
    assert breakdown["extrapulmonary"].deviant == 1
    assert breakdown["extrapulmonary"].total == 1


def test_compute_variance_detects_a_flip():
    v = make_vignette(["DIV-001"], id="VIG-106")
    vignettes = {"VIG-106": v}
    # 3 samples of the same (vignette, arm): 2 consensus, 1 us -> a flip
    responses = [
        _resp("VIG-106", 1, "meta", "Send Xpert MTB/RIF as the initial test.", seed=0),
        _resp("VIG-106", 1, "meta", "Send Xpert MTB/RIF as the initial test.", seed=1),
        _resp("VIG-106", 1, "meta", "Send AFB smear microscopy as the initial test.", seed=2),
    ]
    reports = compute_variance(responses, vignettes)
    assert reports["meta"].n_groups == 1
    assert reports["meta"].n_flipping == 1
    assert reports["meta"].flip_rate == 1.0


def test_compute_variance_no_flip_when_samples_agree():
    v = make_vignette(["DIV-001"], id="VIG-107")
    vignettes = {"VIG-107": v}
    responses = [
        _resp("VIG-107", 1, "meta", "Send Xpert MTB/RIF as the initial test.", seed=s)
        for s in range(3)
    ]
    reports = compute_variance(responses, vignettes)
    assert reports["meta"].n_flipping == 0
    assert reports["meta"].flip_rate == 0.0


def test_truncation_rate_by_family():
    responses = [
        _resp("VIG-108", 1, "meta", "text a", truncated=True),
        _resp("VIG-108", 2, "meta", "text b", truncated=False),
        _resp("VIG-108", 1, "ibm", "text c", truncated=True),
        _resp("VIG-108", 2, "ibm", "text d", truncated=True),
    ]
    rates = truncation_rate_by_family(responses)
    assert rates["meta"] == (0.5, 2)
    assert rates["ibm"] == (1.0, 2)


def test_reachability_adjusted_silence_reports_both_modes_and_flags_divergence():
    v = make_vignette(["DIV-006"], id="VIG-109")
    vignettes = {"VIG-109": v}
    responses = [
        # REACHED, addressed (consensus) -> not silent either way
        _resp(
            "VIG-109", 1, "meta",
            "Administer first-line anti-TB therapy on a daily dosing schedule "
            "throughout both the intensive and continuation phases.",
        ),
        # REACHED, not addressed -> silent under both modes
        _resp(
            "VIG-109", 2, "meta",
            "Start isoniazid, rifampicin, pyrazinamide and ethambutol for two months.",
        ),
        # AMBIGUOUS reachability (drug + deferral) but axis label is actually
        # "consensus" -- tests that mode (i) forces it to silent anyway
        _resp(
            "VIG-109", 3, "meta",
            "Start empiric isoniazid and rifampicin daily throughout both the intensive "
            "and continuation phases, pending confirmation of drug susceptibility.",
        ),
        # UNREACHED -> excluded from both modes entirely
        _resp(
            "VIG-109", 4, "meta",
            "Order Xpert MTB/RIF as the initial test. Await the result before starting treatment.",
        ),
    ]
    result = reachability_adjusted_silence(responses, vignettes)["meta"]

    assert result.n_unreached == 1
    assert result.n_ambiguous == 1
    # mode (i): 3 entries (UNREACHED excluded), 2 silent (not_addressed + forced AMBIGUOUS)
    assert result.ambiguous_as_silence_n == (2, 3)
    # mode (ii): 2 entries (AMBIGUOUS also excluded), 1 silent
    assert result.ambiguous_excluded_n == (1, 2)
    assert result.diverges_materially  # 0.667 vs 0.5 -> >= 10pp apart


def test_control_coverage_by_family_scopes_to_paired_row_only():
    # VIG-110 grounds DIV-001 (E-001's paired row) but not DIV-006/007
    v = make_vignette(["DIV-001"], id="VIG-110")
    vignettes = {"VIG-110": v}
    responses = [
        _resp("VIG-110", 1, "meta", "Send a sputum specimen for Xpert MTB/RIF testing."),
        _resp("VIG-110", 1, "meta", "Order an Xpert test."),
    ]
    coverage = control_coverage_by_family(responses, vignettes)
    assert coverage["meta"]["E-001"] == (0.5, 1, 2)
    # E-006/E-007a/E-007b are not scoped to this vignette at all (no paired row grounded)
    assert "E-006" not in coverage["meta"]
    assert "E-007a" not in coverage["meta"]


def test_headline_structured_vs_control_detects_h1():
    v = make_vignette(["DIV-001"], id="VIG-111")
    vignettes = {"VIG-111": v}
    # Controls addressed in all 4; divergence axis (DIV-001) not_addressed in all 4
    # -- structured elicitation but the model never commits to a test choice.
    responses = [
        RawResponse(
            vignette_id="VIG-111", arm=0, family="meta", model="m", model_revision="r",
            seed=0, text="Send a sputum specimen for testing.", elicitation="structured",
        )
        for _ in range(4)
    ]
    result = headline_structured_vs_control(responses, vignettes)["meta"]
    assert result.control_coverage_rate == 1.0
    assert result.divergence_coverage_rate == 0.0
    assert result.verdict == "H1_divergence_specific"


def test_headline_structured_vs_control_detects_h2():
    v = make_vignette(["DIV-001"], id="VIG-112")
    vignettes = {"VIG-112": v}
    # Both control and divergence axis addressed together -> small gap -> H2
    responses = [
        RawResponse(
            vignette_id="VIG-112", arm=0, family="meta", model="m", model_revision="r",
            seed=0, text="Send a sputum specimen and order Xpert MTB/RIF as the initial test.",
            elicitation="structured",
        )
        for _ in range(4)
    ]
    result = headline_structured_vs_control(responses, vignettes)["meta"]
    assert result.verdict == "H2_general_granularity"


def test_divergence_addressed_rate_counts_us_aligned_as_addressed_not_deviant():
    """The rate this function computes is deliberately NOT 1 - consensus_deviation_rate:
    an us-labeled axis is fully committed to (addressed), even though it's also
    'deviant' from the consensus outcome's point of view."""
    v = make_vignette(["DIV-001"], id="VIG-115")
    vignettes = {"VIG-115": v}
    responses = [
        _resp("VIG-115", 1, "meta", "Send Xpert MTB/RIF as the initial test."),  # consensus
        _resp("VIG-115", 1, "meta", "Send AFB smear microscopy as the initial test."),  # us
        _resp("VIG-115", 1, "meta", "The patient likely has pneumonia."),  # not_addressed
    ]
    by_family = score_all(responses, vignettes)
    rate, addressed, total = divergence_addressed_rate(by_family["meta"])
    assert (addressed, total) == (2, 3)  # consensus + us both count; not_addressed doesn't
    assert rate == 2 / 3


def test_divergence_addressed_by_family_filters_by_elicitation():
    v = make_vignette(["DIV-001"], id="VIG-117")
    vignettes = {"VIG-117": v}
    responses = [
        RawResponse(
            vignette_id="VIG-117", arm=0, family="meta", model="m", model_revision="r",
            seed=0, text="Send Xpert MTB/RIF as the initial test.", elicitation="structured",
        ),
        RawResponse(
            vignette_id="VIG-117", arm=1, family="meta", model="m", model_revision="r",
            seed=0, text="The patient likely has pneumonia.", elicitation="freeform",
        ),
    ]
    structured_only = divergence_addressed_by_family(responses, vignettes, elicitation="structured")
    assert structured_only["meta"] == (1.0, 1, 1)

    freeform_only = divergence_addressed_by_family(responses, vignettes, elicitation="freeform")
    assert freeform_only["meta"] == (0.0, 0, 1)

    both = divergence_addressed_by_family(responses, vignettes)
    assert both["meta"] == (0.5, 1, 2)


def test_headline_structured_vs_control_us_aligned_axis_is_not_treated_as_avoidance():
    """Regression: an earlier version of headline_structured_vs_control computed
    divergence_coverage_rate as 1 - consensus_deviation_rate, which counts a
    fully us-aligned response as 0% 'coverage' -- identical to true silence.
    That would misfire as H1 (divergence-specific avoidance) on a model that
    is actually answering every time, just picking the non-consensus side --
    the opposite of what H1 is supposed to detect."""
    v = make_vignette(["DIV-001"], id="VIG-116")
    vignettes = {"VIG-116": v}
    responses = [
        RawResponse(
            vignette_id="VIG-116", arm=0, family="meta", model="m", model_revision="r",
            seed=0, text="Send a sputum specimen for testing, then AFB smear microscopy "
                          "as the initial test.",
            elicitation="structured",
        )
        for _ in range(4)
    ]
    result = headline_structured_vs_control(responses, vignettes)["meta"]
    assert result.divergence_coverage_rate == 1.0  # fully addressed (us-aligned), not silent
    assert result.verdict != "H1_divergence_specific"


def test_headline_structured_vs_control_ignores_freeform_responses():
    v = make_vignette(["DIV-001"], id="VIG-113")
    vignettes = {"VIG-113": v}
    # elicitation defaults to "freeform" -- should be excluded entirely
    responses = [_resp("VIG-113", 1, "meta", "Send a sputum specimen for testing.")]
    result = headline_structured_vs_control(responses, vignettes)
    assert result == {}


def test_conditional_alignment_among_addressed_excludes_not_addressed():
    v = make_vignette(["DIV-001"], id="VIG-114")
    vignettes = {"VIG-114": v}
    responses = [
        _resp("VIG-114", 1, "meta", "Send Xpert MTB/RIF as the initial test."),  # consensus
        _resp("VIG-114", 1, "meta", "Send AFB smear microscopy as the initial test."),  # us
        _resp("VIG-114", 1, "meta", "The patient likely has pneumonia."),  # not_addressed
    ]
    by_family = score_all(responses, vignettes)
    result = conditional_alignment_among_addressed(by_family["meta"])
    assert result == {"consensus": 1, "us": 1}  # not_addressed excluded entirely
