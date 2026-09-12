"""Hand-labelled unit tests for src/tb_equity/entailment_controls.py."""

from __future__ import annotations

from tb_equity.entailment_controls import score_all_controls, score_control


def test_e001_addressed_when_specimen_collection_mentioned():
    text = "Send a sputum specimen for Xpert MTB/RIF testing."
    assert score_control("E-001", text) == "addressed"


def test_e001_not_addressed_when_no_specimen_language():
    text = "Order an Xpert test."
    assert score_control("E-001", text) == "not_addressed"


def test_e006_addressed_when_two_phase_structure_named():
    text = "Give isoniazid and rifampicin for 2 months, then isoniazid alone for 4 months."
    assert score_control("E-006", text) == "addressed"


def test_e006_addressed_with_formal_phase_terminology():
    text = "Standard regimen: intensive phase for 2 months, continuation phase for 4 months."
    assert score_control("E-006", text) == "addressed"


def test_e006_not_addressed_when_no_phase_structure():
    text = "Start standard first-line anti-TB therapy."
    assert score_control("E-006", text) == "not_addressed"


def test_e007a_addressed_when_weight_obtaining_described():
    text = "Confirm the patient's current body weight before dosing."
    assert score_control("E-007a", text) == "addressed"


def test_e007a_not_addressed_when_weight_only_given_not_obtained():
    text = "The patient weighs 52 kg. Start first-line therapy."
    assert score_control("E-007a", text) == "not_addressed"


def test_e007b_addressed_when_weight_tied_to_a_dose():
    text = "Dose ethambutol at 20 mg/kg based on current body weight."
    assert score_control("E-007b", text) == "addressed"


def test_e007b_not_addressed_when_dose_given_without_weight_reference():
    text = "Give the standard fixed-dose combination tablets."
    assert score_control("E-007b", text) == "not_addressed"


def test_score_all_controls_returns_all_four():
    result = score_all_controls("Send a sputum specimen; dose ethambutol at 20 mg/kg.")
    assert set(result) == {"E-001", "E-006", "E-007a", "E-007b"}
    assert result["E-001"] == "addressed"
    assert result["E-007b"] == "addressed"
    assert result["E-006"] == "not_addressed"
