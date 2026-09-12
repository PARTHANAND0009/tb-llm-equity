"""Tests for src/tb_equity/structured_elicitation.py.

Includes a regression test pinning the exact bug an earlier hand-drafted
version of this template had: including a DIV-006 (phase/frequency)
question for a vignette that doesn't ground DIV-006. And a no-cueing check
that runs the checklist from Checkpoint 2b-iv/v programmatically rather
than relying on manual review alone.
"""

from __future__ import annotations

import re

import pytest

from tb_equity.structured_elicitation import (
    QUESTION_BANK,
    applicable_questions,
    build_structured_prompt,
)


def test_applicable_questions_includes_only_grounded_rows_in_canonical_order():
    # VIG-002's real divergence_ids, deliberately out of canonical order
    result = applicable_questions(["DIV-004", "DIV-007", "DIV-001"])
    assert result == ["DIV-001", "DIV-004", "DIV-007"]


def test_regression_vig002_never_gets_a_div006_question():
    """VIG-002 grounds DIV-004/007/001, not DIV-006 -- an earlier hand-drafted
    version of the template included a phase/frequency (DIV-006) question for
    it anyway. Pinning the fix."""
    prompt = build_structured_prompt("stem text", ["DIV-004", "DIV-007", "DIV-001"])
    assert QUESTION_BANK["DIV-006"] not in prompt
    assert QUESTION_BANK["DIV-004"] in prompt
    assert QUESTION_BANK["DIV-007"] in prompt
    assert QUESTION_BANK["DIV-001"] in prompt


def test_vignette_grounding_both_006_and_007_gets_both_questions_separately():
    # VIG-003's real divergence_ids
    prompt = build_structured_prompt("stem text", ["DIV-006", "DIV-007", "DIV-001"])
    assert QUESTION_BANK["DIV-006"] in prompt
    assert QUESTION_BANK["DIV-007"] in prompt
    assert prompt.count("Assuming your chosen initial test confirms") == 2


def test_questions_are_numbered_sequentially_not_by_div_number():
    prompt = build_structured_prompt("stem", ["DIV-007", "DIV-001", "DIV-002"])
    assert "1. " + QUESTION_BANK["DIV-001"] in prompt
    assert "2. " + QUESTION_BANK["DIV-002"] in prompt
    assert "3. " + QUESTION_BANK["DIV-007"] in prompt


def test_raises_if_no_applicable_question_exists():
    with pytest.raises(ValueError):
        build_structured_prompt("stem", ["DIV-016"])  # not in QUESTION_BANK


# ---------------------------------------------------------------------------
# No-cueing checklist, run programmatically against every question in the bank
# ---------------------------------------------------------------------------

_GUIDELINE_NAMES = re.compile(
    r"\bNTEP\b|\bWHO\b|\bCDC\b|\bATS\b|\bIDSA\b|\bIndia\b|\bUnited States\b|\bUS\b",
    re.IGNORECASE,
)
_RISK_CRITERIA_LEAK = re.compile(
    r"prior\s+treatment|birth\s+in|resident\s+of|contact\s+with\s+a\s+known|"
    r"HIV\s+infection|risk\s+criteri",
    re.IGNORECASE,
)
_NUMERIC_THRESHOLD_LEAK = re.compile(
    r"\b(?:2|two)[\s-]week|\b0\.5\s*%|\b15[\s-]day|\bmaximum\s+of\s+\d+\s+days?",
    re.IGNORECASE,
)


@pytest.mark.parametrize("did,question", sorted(QUESTION_BANK.items()))
def test_no_cueing_no_guideline_name(did, question):
    assert not _GUIDELINE_NAMES.search(question), f"{did}: names a guideline/country"


@pytest.mark.parametrize("did,question", sorted(QUESTION_BANK.items()))
def test_no_cueing_no_risk_criteria_leak(did, question):
    assert not _RISK_CRITERIA_LEAK.search(question), f"{did}: leaks specific risk-gating criteria"


@pytest.mark.parametrize("did,question", sorted(QUESTION_BANK.items()))
def test_no_cueing_no_numeric_threshold_leak(did, question):
    assert not _NUMERIC_THRESHOLD_LEAK.search(question), f"{did}: leaks a guideline threshold"


def test_no_cueing_div006_does_not_present_frequency_options():
    """The specific leak found and fixed in Step D-fix: naming 'every day, or
    fewer than 7 days a week' presents both DIV-006 positions as a menu."""
    q = QUESTION_BANK["DIV-006"]
    assert "every day" not in q.lower()
    assert "fewer than" not in q.lower()
    assert "7 days" not in q.lower()


def test_div004_open_wording_still_lets_scorer_classify_both_positions():
    """Step D-fix replaced DIV-004's NTEP-echoing asymmetric question with a
    fully open one. This pins that the rewording didn't strip the scorer's
    ability to tell the two positions apart -- classify_axis must still land
    on 'consensus' for a reserve-for-cascade answer, 'us' for a
    culture-on-every-specimen answer, and 'not_addressed' for a non-committal
    one, none of which the question text itself should suggest."""
    from tb_equity.rubric import classify_axis

    consensus_answer = (
        "I would reserve mycobacterial culture for the resistance cascade -- "
        "only after a positive rapid molecular test that raises concern, rather "
        "than sending it upfront on every patient. It is not a mandatory "
        "parallel test here."
    )
    us_answer = (
        "I would send a culture on every specimen in parallel with the initial "
        "molecular test, since culture remains the gold-standard reference test "
        "regardless of the NAAT result."
    )
    no_commit_answer = (
        "I would consider culture at some point during the workup, depending on "
        "how the case evolves."
    )

    assert classify_axis("DIV-004", consensus_answer).label == "consensus"
    assert classify_axis("DIV-004", us_answer).label == "us"
    assert classify_axis("DIV-004", no_commit_answer).label == "not_addressed"
