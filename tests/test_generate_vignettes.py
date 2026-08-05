import json

import generate_vignettes
from generate_vignettes import (
    _render_prompt_file,
    build_user_prompt,
    leaks_location,
    run_claude_code_mode,
)


def test_pronoun_who_does_not_leak():
    assert leaks_location("A 34-year-old man who presents with cough.") is False


def test_pronoun_us_does_not_leak():
    assert leaks_location("The family told us about the exposure.") is False


def test_india_leaks_case_insensitively():
    assert leaks_location("The patient is presenting in India this week.") is True
    assert leaks_location("The patient is presenting in india this week.") is True


def test_who_acronym_leaks_when_capitalized():
    assert leaks_location("Management follows per WHO guidance.") is True


def test_lowercase_who_word_does_not_leak_even_at_sentence_start():
    assert leaks_location("Who else was exposed is unclear from the history.") is False


def test_ntep_and_cdc_leak():
    assert leaks_location("Care was coordinated under NTEP.") is True
    assert leaks_location("The CDC recommends further testing.") is True


def _cell(**overrides):
    base = {
        "cell_id": "STRAT-001",
        "presentation_type": "pulmonary",
        "subtype": None,
        "burden_class": "india_high",
        "age_band": "adult_18_59",
        "sex": "male",
        "setting": "urban",
        "occupation_class": "student",
        "comorbidity_burden": "none",
        "symptom_duration_band": "2_4_weeks",
        "num_distractors": 2,
        "holdout": False,
        "matched_pair_id": None,
    }
    base.update(overrides)
    return base


def test_india_high_and_consensus_control_prompts_differ_for_same_presentation_type():
    india_cell = _cell(burden_class="india_high")
    comparator_cell = _cell(burden_class="consensus_control", matched_pair_id="STRAT-001")

    india_prompt = build_user_prompt(india_cell, divergence_rows=[])
    comparator_prompt = build_user_prompt(comparator_cell, divergence_rows=[])

    assert india_prompt != comparator_prompt
    assert "india_high" in india_prompt
    assert "consensus_control" in comparator_prompt
    assert "not the same case relabeled" in comparator_prompt.lower()


def test_consensus_control_prompt_references_matched_pair():
    comparator_cell = _cell(burden_class="consensus_control", matched_pair_id="STRAT-042")
    prompt = build_user_prompt(comparator_cell, divergence_rows=[])
    assert "STRAT-042" in prompt


_SAMPLE_ROW = {
    "id": "DIV-001",
    "decision_point": "test decision point",
    "domain": "diagnosis",
    "divergence_class": "consensus_divergence",
    "applicable_age_bands": ["adult_18_59", "older_adult_60_plus"],
    "ntep_position": "ntep test position",
    "ntep_citation": {"doc": "doc", "section": "sec", "url": "https://example.com/ntep"},
    "who_position": "who test position",
    "who_citation": {"doc": "doc", "section": "sec", "url": "https://example.com/who"},
    "us_position": "us test position",
    "us_citation": {"doc": "doc", "section": "sec", "url": "https://example.com/us"},
    "consensus_position": "consensus test position",
    "clinical_stakes": "high",
    "is_critical_error_if_wrong": False,
    "still_diverges_as_of": "2026-08",
}


def test_render_prompt_file_contains_key_fields():
    cell = _cell()
    text = _render_prompt_file(
        cell=cell, vig_id="VIG-001", rows=[_SAMPLE_ROW], cell_id_to_vig_id={}
    )
    assert "STRAT-001 -> VIG-001" in text
    assert "data/vignettes/v1/VIG-001.json" in text
    assert "DIV-001" in text
    assert '"id": "VIG-001"' in text
    assert "claude-code" in text.lower()


def test_render_prompt_file_embeds_matched_pair_id_translated_to_vig_id():
    cell = _cell(burden_class="consensus_control", matched_pair_id="STRAT-099")
    text = _render_prompt_file(
        cell=cell,
        vig_id="VIG-002",
        rows=[_SAMPLE_ROW],
        cell_id_to_vig_id={"STRAT-099": "VIG-099"},
    )
    assert '"matched_pair_id": "VIG-099"' in text


def test_claude_code_mode_writes_prompts_and_skips_generated_ones(tmp_path, monkeypatch):
    output_dir = tmp_path / "v1"
    prompts_dir = tmp_path / "prompts"
    monkeypatch.setattr(generate_vignettes, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(generate_vignettes, "PROMPTS_DIR", prompts_dir)
    monkeypatch.setattr(generate_vignettes, "GENERATION_LOG_PATH", tmp_path / "errors.jsonl")
    monkeypatch.setattr(generate_vignettes, "MANIFEST_DIR", tmp_path / "manifests")
    output_dir.mkdir(parents=True)

    table = {"DIV-001": _SAMPLE_ROW}
    cells = [_cell(cell_id="STRAT-001"), _cell(cell_id="STRAT-002")]
    monkeypatch.setitem(
        generate_vignettes.DIVERGENCE_MAP, ("pulmonary", None), ["DIV-001"]
    )

    generation = {"family": "anthropic", "model": "test-model"}
    exit_code = run_claude_code_mode(generation, table, cells)

    assert exit_code == 0
    assert (prompts_dir / "STRAT-001.md").exists()
    assert (prompts_dir / "STRAT-002.md").exists()
    manifests = list((tmp_path / "manifests").glob("*.json"))
    assert len(manifests) == 1
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert manifest["mode"] == "claude-code"
    assert manifest["accepted"] == 0
    assert manifest["pending"] == 2


def test_claude_code_mode_validates_a_hand_written_vignette(tmp_path, monkeypatch):
    output_dir = tmp_path / "v1"
    prompts_dir = tmp_path / "prompts"
    monkeypatch.setattr(generate_vignettes, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(generate_vignettes, "PROMPTS_DIR", prompts_dir)
    monkeypatch.setattr(generate_vignettes, "GENERATION_LOG_PATH", tmp_path / "errors.jsonl")
    monkeypatch.setattr(generate_vignettes, "MANIFEST_DIR", tmp_path / "manifests")
    output_dir.mkdir(parents=True)

    table = {"DIV-001": _SAMPLE_ROW}
    cells = [_cell(cell_id="STRAT-001")]
    monkeypatch.setitem(
        generate_vignettes.DIVERGENCE_MAP, ("pulmonary", None), ["DIV-001"]
    )

    vignette = {
        "id": "VIG-001",
        "version": "v1",
        "burden_class": "india_high",
        "presentation_type": "pulmonary",
        "matched_pair_id": None,
        "divergence_ids": ["DIV-001"],
        "stem": "A patient presents with a cough for three weeks.",
        "patient": {
            "age": "30 years",
            "sex": "male",
            "occupation": "student",
            "social_history": "lives alone",
            "presenting_complaint": "cough",
            "duration": "3 weeks",
            "exam_findings": "mild crackles",
            "prior_treatment": "none",
            "comorbidities": [],
        },
        "distractors": ["distractor one", "distractor two"],
        "ntep_correct_actions": ["action one"],
        "who_correct_actions": ["action one"],
        "us_correct_actions": ["a different action"],
        "critical_error_conditions": ["error one"],
        "expected_divergence_points": ["point one"],
        "holdout": False,
        "provenance": {
            "generator_model": "manual-test",
            "generated_at": "2026-08-05T00:00:00+00:00",
            "source_divergence_ids": ["DIV-001"],
            "critique_passes": 0,
            "human_reviewed": False,
            "clinician_reviewed": False,
        },
    }
    (output_dir / "VIG-001.json").write_text(json.dumps(vignette), encoding="utf-8")

    generation = {"family": "anthropic", "model": "test-model"}
    run_claude_code_mode(generation, table, cells)

    manifests = list((tmp_path / "manifests").glob("*.json"))
    manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
    assert manifest["accepted"] == 1
    assert manifest["rejected"] == 0
    assert manifest["pending"] == 0
    # already-generated cell should not get a (re-)written prompt file
    assert not (prompts_dir / "STRAT-001.md").exists()
