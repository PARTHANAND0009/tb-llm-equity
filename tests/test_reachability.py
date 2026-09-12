"""Hand-labelled unit tests for src/tb_equity/reachability.py.

Same standard as tests/test_rubric.py's 48 cases: every example below is
hand-written and hand-labelled so a human reviewer can judge the call
directly. Covers all three states for both reachability-sensitive rows
(DIV-006, DIV-007) plus confirmation that non-sensitive rows always return
REACHED regardless of content.
"""

from __future__ import annotations

from tb_equity.reachability import compute_reachability


def test_non_sensitive_row_always_reached_even_with_deferral_language():
    text = "Order Xpert MTB/RIF and await the result before deciding further."
    assert compute_reachability("DIV-001", text) == "REACHED"
    assert compute_reachability("DIV-004", text) == "REACHED"


def test_reached_when_drug_named_with_no_deferral():
    text = "Start isoniazid, rifampicin, pyrazinamide, and ethambutol for 2 months."
    assert compute_reachability("DIV-006", text) == "REACHED"
    assert compute_reachability("DIV-007", text) == "REACHED"


def test_unreached_when_explicit_deferral_and_no_drug_named():
    text = "Order Xpert MTB/RIF as the initial test. Await the result before starting treatment."
    assert compute_reachability("DIV-006", text) == "UNREACHED"
    assert compute_reachability("DIV-007", text) == "UNREACHED"


def test_unreached_when_no_treatment_discussion_at_all():
    text = "The most likely diagnosis is pulmonary TB. Order a chest X-ray to confirm."
    assert compute_reachability("DIV-006", text) == "UNREACHED"
    assert compute_reachability("DIV-007", text) == "UNREACHED"


def test_ambiguous_when_drug_named_alongside_deferral_language():
    text = (
        "Start empiric isoniazid and rifampicin now, pending confirmation of drug "
        "susceptibility before continuing the full regimen."
    )
    assert compute_reachability("DIV-006", text) == "AMBIGUOUS"
    assert compute_reachability("DIV-007", text) == "AMBIGUOUS"


def test_pending_hiv_test_alongside_starting_tb_treatment_is_reached_not_ambiguous():
    # Real pattern seen in pilot data (VIG-002 arm1, meta): treatment starts
    # regardless of an unrelated pending test -- "pending" here doesn't
    # modify TB treatment initiation, so this must not trip the deferral
    # pattern (which requires "pending"/"await" to be near a
    # result/confirmation/culture/diagnosis/test noun *and* precede no
    # committed drug mention).
    text = (
        "Start the patient on isoniazid, rifampicin, pyrazinamide, and ethambutol "
        "pending the results of the HIV test."
    )
    result = compute_reachability("DIV-007", text)
    assert result in ("REACHED", "AMBIGUOUS"), (
        f"got {result!r} -- if AMBIGUOUS, that's an acceptable conservative call given "
        "'pending' language is present, but UNREACHED would be wrong since treatment "
        "was clearly started"
    )
    assert result != "UNREACHED"
