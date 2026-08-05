import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tb_equity.schema import Vignette

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "example_vignettes"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_fixture_vignette_parses():
    data = _load_fixture("VIG-901.json")
    vignette = Vignette.model_validate(data)
    assert vignette.id == "VIG-901"
    assert vignette.holdout is False


def test_holdout_fixture_parses():
    data = _load_fixture("VIG-902.json")
    vignette = Vignette.model_validate(data)
    assert vignette.holdout is True
    assert vignette.provenance.critique_passes == 1


def test_requires_at_least_two_distractors():
    data = _load_fixture("VIG-901.json")
    data["distractors"] = ["only one"]
    with pytest.raises(ValidationError):
        Vignette.model_validate(data)


def test_requires_at_least_one_divergence_id():
    data = _load_fixture("VIG-901.json")
    data["divergence_ids"] = []
    with pytest.raises(ValidationError):
        Vignette.model_validate(data)


def test_rejects_malformed_id():
    data = _load_fixture("VIG-901.json")
    data["id"] = "VIGNETTE-1"
    with pytest.raises(ValidationError):
        Vignette.model_validate(data)


def test_rejects_blank_stem():
    data = _load_fixture("VIG-901.json")
    data["stem"] = "   "
    with pytest.raises(ValidationError):
        Vignette.model_validate(data)


def test_rejects_unknown_field():
    data = _load_fixture("VIG-901.json")
    data["unexpected_field"] = "nope"
    with pytest.raises(ValidationError):
        Vignette.model_validate(data)


def test_rejects_consensus_correct_actions_if_present_in_input():
    """consensus_correct_actions is derived, never authored -- supplying it
    in the input JSON must be rejected the same as any other unknown field,
    so nobody can silently override the computed intersection."""
    data = _load_fixture("VIG-901.json")
    data["consensus_correct_actions"] = ["whatever"]
    with pytest.raises(ValidationError):
        Vignette.model_validate(data)


def test_consensus_correct_actions_is_the_verbatim_intersection():
    data = _load_fixture("VIG-901.json")
    vignette = Vignette.model_validate(data)
    expected = [a for a in vignette.ntep_correct_actions if a in set(vignette.who_correct_actions)]
    assert vignette.consensus_correct_actions == expected
    assert vignette.consensus_correct_actions  # VIG-901 is grounded in consensus_divergence rows


def test_consensus_correct_actions_can_be_empty_for_national_adaptation_grounding():
    data = _load_fixture("VIG-901.json")
    data["ntep_correct_actions"] = ["NTEP-only action, no WHO overlap"]
    data["who_correct_actions"] = ["WHO-only action, no NTEP overlap"]
    vignette = Vignette.model_validate(data)
    assert vignette.consensus_correct_actions == []


def test_consensus_correct_actions_appears_in_serialized_output():
    data = _load_fixture("VIG-901.json")
    vignette = Vignette.model_validate(data)
    dumped = json.loads(vignette.model_dump_json())
    assert dumped["consensus_correct_actions"] == vignette.consensus_correct_actions
