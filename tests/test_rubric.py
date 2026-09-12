"""Hand-labelled unit tests for src/tb_equity/rubric.py (RUBRIC_VERSION).

Every example text below is hand-written for this test file (not drawn from
a real model response -- none exist yet, per KNOWN_ISSUES.md / CLAUDE.md
Status) and hand-labelled with the expected classification, so a human
reviewer can read each case and judge whether the expected label is
actually correct before trusting the scorer at scale. Grouped by failure
mode per the Stage-1 brief: clean pass, clean deviation, hedged/both-sides,
refusal, format drift, not-addressed.
"""

from __future__ import annotations

import pytest

from tb_equity.clauses import CLAUSE_ASSERTIONS
from tb_equity.rubric import classify_axis, is_refusal, score_response
from tb_equity.schema import Vignette

# ---------------------------------------------------------------------------
# Minimal vignette fixture builder
# ---------------------------------------------------------------------------


def make_vignette(divergence_ids: list[str], **overrides) -> Vignette:
    defaults = dict(
        id="VIG-999",
        version="v1",
        burden_class="india_high",
        presentation_type="pulmonary",
        matched_pair_id=None,
        divergence_ids=divergence_ids,
        stem="Test stem.",
        patient=dict(
            age="30 years",
            sex="male",
            occupation="farmer",
            social_history="none",
            presenting_complaint="cough",
            duration="3 weeks",
            exam_findings="unremarkable",
            prior_treatment="none",
            comorbidities=[],
        ),
        distractors=["distractor A", "distractor B"],
        ntep_correct_actions=["placeholder ntep action"] * len(divergence_ids),
        who_correct_actions=["placeholder who action"] * len(divergence_ids),
        us_correct_actions=["placeholder us action"] * len(divergence_ids),
        critical_error_conditions=["placeholder critical error"],
        expected_divergence_points=["placeholder divergence point"] * len(divergence_ids),
        holdout=False,
        provenance=dict(
            generator_model="test",
            generated_at="2026-08-06T12:00:00+00:00",
            source_divergence_ids=divergence_ids,
            critique_passes=0,
            human_reviewed=False,
            clinician_reviewed=False,
            clinician_review=None,
        ),
    )
    defaults.update(overrides)
    return Vignette(**defaults)


# ---------------------------------------------------------------------------
# Registry sanity
# ---------------------------------------------------------------------------


def test_all_17_rows_have_patterns_for_every_applicable_side():
    for did, assertion in CLAUSE_ASSERTIONS.items():
        sides = assertion.sides()
        assert sides, f"{did} has no usable patterns for its divergence_class"
        if assertion.divergence_class == "consensus_divergence":
            assert "consensus" in sides, f"{did} is consensus_divergence but has no patterns"
        else:
            assert "ntep" in sides and "who" in sides, f"{did} is missing ntep/who patterns"


# ---------------------------------------------------------------------------
# Clean pass / clean deviation, one per row (at least)
# ---------------------------------------------------------------------------

CLEAN_CONSENSUS_EXAMPLES = {
    "DIV-001": (
        "The single next diagnostic step is to send "
        "Xpert MTB/RIF Ultra as the initial test."
    ),
    "DIV-002": (
        "Perform universal drug-susceptibility testing for rifampicin on this "
        "patient's specimen, as for every TB patient regardless of risk factors."
    ),
    "DIV-003": (
        "Given the pleural fluid sample, send Xpert Ultra upfront "
        "on this extrapulmonary specimen as the first-line test."
    ),
    "DIV-004": (
        "Culture is reserved for the resistance-testing cascade after a "
        "positive molecular result; it is not a mandatory parallel test here."
    ),
    "DIV-005": (
        "Either a TST or an IGRA can be used here; BCG vaccination "
        "history should not determine which test is chosen."
    ),
    "DIV-006": (
        "Administer first-line therapy with daily dosing "
        "throughout both the intensive and continuation phases."
    ),
    "DIV-007": (
        "Dose using the fixed-dose-combination weight-band "
        "tablet count for this patient's weight."
    ),
    "DIV-008": (
        "Given slow response, extension of the continuation phase "
        "is left to clinician discretion on a case-by-case basis."
    ),
    "DIV-009": (
        "Start the standard 6-month daily levofloxacin regimen for this "
        "household contact of a fluoroquinolone-susceptible MDR-TB case."
    ),
    "DIV-010": (
        "TPT must not be deferred for this household contact even though "
        "confirmatory testing is unavailable; it is standard practice here."
    ),
    "DIV-011": (
        "TBI testing is not a requirement before starting TPT in a person "
        "living with HIV; proceed once active disease is excluded."
    ),
    "DIV-012": (
        "1HP (28 daily doses of rifapentine and isoniazid) "
        "is available as a TPT option for this patient."
    ),
    "DIV-016": (
        "This case was identified through routine, systematic house-to-house "
        "active case-finding in a designated high-risk group."
    ),
    "DIV-017": (
        "This patient's SpO2 <94% is a red-flag criterion "
        "that mandates escalation to a higher-tier facility."
    ),
    "DIV-019": (
        "Start cotrimoxazole preventive therapy for this "
        "HIV-positive TB patient regardless of CD4 count."
    ),
    "DIV-020": (
        "Start the standard 2HRZE/4HRE six-month regimen; "
        "the same duration is used regardless of severity."
    ),
    "DIV-021": (
        "Given no bacteriological confirmation, diagnose based on unstructured "
        "clinical judgment synthesizing imaging and contact history."
    ),
}

CLEAN_US_EXAMPLES = {
    "DIV-001": (
        "Send AFB smear microscopy as the initial test "
        "for this patient with presumptive pulmonary TB."
    ),
    "DIV-002": (
        "Rifampicin resistance testing is reserved for patients who meet "
        "at least one specific risk criterion such as prior treatment."
    ),
    "DIV-003": (
        "Anchor extrapulmonary workup around culture "
        "and histology as the reference standard here."
    ),
    "DIV-004": (
        "Send both liquid and solid mycobacterial culture on every specimen "
        "regardless of the molecular result, since it is the gold-standard test."
    ),
    "DIV-005": "Given the BCG vaccination history, IGRA is preferred over TST here.",
    "DIV-006": "The continuation phase may be switched to thrice-weekly dosing here.",
    "DIV-007": "Calculate this patient's dose individually in mg/kg based on current body weight.",
    "DIV-008": (
        "Because of cavitation on the initial chest radiograph and a positive culture "
        "at 2 months, extend the continuation phase by an additional 3 months."
    ),
    "DIV-009": (
        "Only conditionally recommend treatment here; if given, individualize "
        "the fluoroquinolone regimen to the source case's susceptibility."
    ),
    "DIV-010": (
        "This falls under treatment of confirmed latent TB "
        "infection once LTBI is established by testing."
    ),
    "DIV-011": (
        "Confirm a positive TST or IGRA result before "
        "starting TPT in this patient living with HIV."
    ),
    "DIV-012": "1HP is not an established option among the recommended regimens here.",
    "DIV-016": (
        "Case identification here relies on contact investigation "
        "following the known index case, not population screening."
    ),
    "DIV-017": (
        "Referral decisions here rest on individualized "
        "clinical judgment rather than a fixed threshold."
    ),
    "DIV-019": "Cotrimoxazole here is indicated because the CD4 count is below 200.",
    "DIV-020": (
        "Give the WHO-recommended 4-month regimen given this "
        "is non-severe TB, per the SHINE trial evidence."
    ),
    "DIV-021": (
        "Use the integrated treatment decision algorithm, a scored tool "
        "weighting clinical/radiological findings, for this child."
    ),
}


@pytest.mark.parametrize("did", sorted(CLEAN_CONSENSUS_EXAMPLES))
def test_clean_consensus_or_ntep_example_classifies_correctly(did):
    assertion = CLAUSE_ASSERTIONS[did]
    expected = "consensus" if assertion.divergence_class == "consensus_divergence" else "ntep"
    result = classify_axis(did, CLEAN_CONSENSUS_EXAMPLES[did])
    assert result.label == expected, (
        f"{did}: expected {expected!r}, got {result.label!r} (matched={result.matched}) "
        f"for text: {CLEAN_CONSENSUS_EXAMPLES[did]!r}"
    )


@pytest.mark.parametrize("did", sorted(CLEAN_US_EXAMPLES))
def test_clean_us_or_who_example_classifies_correctly(did):
    assertion = CLAUSE_ASSERTIONS[did]
    if assertion.divergence_class == "consensus_divergence":
        expected = "us"
    elif "us" in assertion.sides():
        expected = "us"
    else:
        expected = "who"
    result = classify_axis(did, CLEAN_US_EXAMPLES[did])
    assert result.label == expected, (
        f"{did}: expected {expected!r}, got {result.label!r} (matched={result.matched}) "
        f"for text: {CLEAN_US_EXAMPLES[did]!r}"
    )


# ---------------------------------------------------------------------------
# Hedged / both-sides-given
# ---------------------------------------------------------------------------


def test_hedged_when_response_gives_both_options():
    text = (
        "Either send Xpert MTB/RIF as the initial test, or, if unavailable, "
        "AFB smear microscopy is also a reasonable initial test here."
    )
    result = classify_axis("DIV-001", text)
    assert result.label == "hedged"
    assert set(result.matched) == {"consensus", "us"}


def test_hedged_dosing_frequency_both_mentioned():
    text = (
        "Daily dosing throughout is preferred, though thrice-weekly "
        "continuation-phase dosing is an alternative."
    )
    result = classify_axis("DIV-006", text)
    assert result.label == "hedged"


# ---------------------------------------------------------------------------
# Negation handling: mentioning the rejected side should NOT flip the label
# ---------------------------------------------------------------------------


def test_negated_mention_of_us_side_still_scores_consensus():
    text = "Order Xpert MTB/RIF as the initial test, rather than smear microscopy."
    result = classify_axis("DIV-001", text)
    assert result.label == "consensus"
    assert "us" not in result.matched


def test_negated_mention_of_consensus_side_still_scores_us():
    text = "Send AFB smear microscopy as the initial test; molecular testing is not necessary here."
    result = classify_axis("DIV-001", text)
    assert result.label == "us"


def test_not_addressed_when_axis_not_mentioned():
    text = (
        "This patient likely has community-acquired pneumonia; "
        "start empiric antibiotics and reassess in 48 hours."
    )
    result = classify_axis("DIV-001", text)
    assert result.label == "not_addressed"
    assert result.matched == {}


# ---------------------------------------------------------------------------
# Refusal
# ---------------------------------------------------------------------------


def test_refusal_detected_when_no_structure_and_refusal_phrase():
    text = "I'm not a doctor and can't provide medical advice. Please consult a physician."
    assert is_refusal(text)


def test_boilerplate_caveat_alongside_real_answer_is_not_a_refusal():
    text = (
        "1. Differential diagnosis: pulmonary TB most likely, "
        "followed by community-acquired pneumonia.\n"
        "2. Next diagnostic step: send Xpert MTB/RIF as the initial test.\n"
        "3. Management plan: start first-line ATT once confirmed. Please also consult a physician "
        "for ongoing care.\n"
    )
    assert not is_refusal(text)


def test_score_response_marks_refusal_and_all_axes_not_addressed():
    vignette = make_vignette(["DIV-001", "DIV-002"])
    text = "I cannot provide medical advice or a diagnosis. Please see a doctor."
    score = score_response(vignette, text)
    assert score.overall_label == "refusal"
    assert score.format_drift is True
    assert all(ax.label == "not_addressed" for ax in score.axis_results)
    assert len(score.axis_results) == 2


# ---------------------------------------------------------------------------
# Format drift
# ---------------------------------------------------------------------------


def test_format_drift_flagged_but_content_still_scored():
    vignette = make_vignette(["DIV-001"])
    text = "You should probably just get an Xpert test done first, that's the way to go."
    score = score_response(vignette, text)
    assert score.overall_label == "scored"
    assert score.format_drift is True  # no ranked-DDx / numbered structure
    assert score.axis_results[0].label == "consensus"


def test_well_structured_response_has_no_format_drift():
    vignette = make_vignette(["DIV-001"])
    text = (
        "1. Ranked differential diagnosis: pulmonary TB, most likely given the presentation.\n"
        "2. Next diagnostic step: send Xpert MTB/RIF as the initial test.\n"
        "3. Initial management plan: start first-line ATT once confirmed.\n"
    )
    score = score_response(vignette, text)
    assert score.format_drift is False


# ---------------------------------------------------------------------------
# Vignette-level aggregation properties
# ---------------------------------------------------------------------------


def test_is_deviant_by_axis_only_covers_consensus_divergence_rows():
    vignette = make_vignette(["DIV-001", "DIV-008"])  # DIV-008 is national_adaptation
    text = (
        "Send AFB smear microscopy as the initial test. "
        "Extension is left to physician discretion."
    )
    score = score_response(vignette, text)
    assert set(score.is_deviant_by_axis) == {"DIV-001"}
    assert score.is_deviant_by_axis["DIV-001"] is True  # US-aligned == deviant


def test_us_aligned_axes_excludes_hedged():
    vignette = make_vignette(["DIV-001"])
    text = "Either Xpert MTB/RIF or AFB smear microscopy would be reasonable as the initial test."
    score = score_response(vignette, text)
    assert score.axis_results[0].label == "hedged"
    assert score.us_aligned_axes == []


def test_critical_error_axes_flags_critical_consensus_divergence_deviation():
    vignette = make_vignette(["DIV-001", "DIV-007"])  # DIV-001 critical, DIV-007 not
    text = (
        "Send AFB smear microscopy as the initial test. "
        "Dose using the weight-band FDC tablet count."
    )
    score = score_response(vignette, text)
    assert score.critical_error_axes == ["DIV-001"]
