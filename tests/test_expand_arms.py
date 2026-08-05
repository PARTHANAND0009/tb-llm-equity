import json
from pathlib import Path

import expand_arms
from expand_arms import (
    INDIA_LOCATION_SENTENCE,
    INSTRUCTION_BLOCK,
    US_LOCATION_SENTENCE,
    build_arms,
    estimate_tokens,
    expand,
    gather_protocol_chunks,
    load_divergence_table,
    main,
    sha256_hex,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "example_vignettes"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _table() -> dict[str, dict]:
    return load_divergence_table()


# ---------------------------------------------------------------------------
# Arm structure: byte-identical instruction block, correct containment
# ---------------------------------------------------------------------------


def test_four_arms_emitted_per_vignette():
    vignette = _load_fixture("VIG-901.json")
    arms, _log = build_arms(vignette, _table())
    assert set(arms) == {1, 2, 3, 4}
    assert all(isinstance(text, str) and text for text in arms.values())


def test_instruction_block_is_byte_identical_across_all_four_arms():
    vignette = _load_fixture("VIG-901.json")
    arms, _log = build_arms(vignette, _table())
    for arm_num, text in arms.items():
        assert text.startswith(INSTRUCTION_BLOCK), (
            f"arm {arm_num} does not start with the exact fixed instruction block"
        )


def test_arm2_contains_arm1_verbatim():
    vignette = _load_fixture("VIG-901.json")
    arms, _log = build_arms(vignette, _table())
    assert arms[1] in arms[2]


def test_arm3_and_arm4_each_contain_arm2_verbatim():
    """Arm 3 and Arm 4 are siblings that both branch off Arm 2 (not off each
    other) -- Task 5's spec: 'ARM 3 ... Arm 2 plus ...' and 'ARM 4 ... Arm 2
    plus ...', not Arm 3 plus more."""
    vignette = _load_fixture("VIG-901.json")
    arms, _log = build_arms(vignette, _table())
    assert arms[2] in arms[3]
    assert arms[2] in arms[4]


def test_arm2_adds_exactly_the_location_sentence_and_nothing_else():
    vignette = _load_fixture("VIG-901.json")  # india_high
    arms, _log = build_arms(vignette, _table())
    added = arms[2][len(arms[1]) :]
    assert added == f"\n\n{INDIA_LOCATION_SENTENCE}"


def test_consensus_control_gets_the_symmetric_mirror():
    india_vignette = _load_fixture("VIG-901.json")
    us_vignette = dict(india_vignette, burden_class="consensus_control")
    table = _table()

    india_arms, _ = build_arms(india_vignette, table)
    us_arms, _ = build_arms(us_vignette, table)

    assert INDIA_LOCATION_SENTENCE in india_arms[2]
    assert US_LOCATION_SENTENCE not in india_arms[2]
    assert US_LOCATION_SENTENCE in us_arms[2]
    assert INDIA_LOCATION_SENTENCE not in us_arms[2]
    # Arm 1 (no location) is identical regardless of burden_class -- the
    # mirror only kicks in from Arm 2 onward.
    assert india_arms[1] == us_arms[1]
    assert india_arms[3] != us_arms[3]
    assert india_arms[4] != us_arms[4]


def test_consensus_control_arm4_retrieves_us_side_citations():
    """VIG-902 is grounded in DIV-006/DIV-008, both of which have a real
    us_citation pointing at a locally fetched ATS/CDC/IDSA file -- the
    consensus_control mirror's Arm 4 should inject that, not the NTEP text."""
    vignette = dict(_load_fixture("VIG-902.json"), burden_class="consensus_control")
    table = _table()
    _combined, log = gather_protocol_chunks(vignette, table, side="us")
    included = [entry for entry in log if entry["included"]]
    assert included
    assert all("ATS_CDC_IDSA" in entry["source"] for entry in included)


def test_epidemiology_block_states_numbers_and_no_answer_hints():
    """The epi block legitimately says 'TB incidence' -- this is a TB study,
    every arm is about TB, that's not a leak. What must NOT appear is
    anything that hints at the specific correct action/answer for this
    vignette (a named test, a named drug/regimen, a specific finding)."""
    vignette = _load_fixture("VIG-901.json")
    arms, _log = build_arms(vignette, _table())
    added = arms[3][len(arms[2]) :]
    assert any(ch.isdigit() for ch in added)
    for leaky_term in (
        "NAAT",
        "Xpert",
        "smear",
        "culture",
        "molecular test",
        "differential",
        "management plan",
    ):
        assert leaky_term.lower() not in added.lower(), (
            f"epidemiology block should state base rates only, not hint at "
            f"the correct action -- found {leaky_term!r}"
        )


# ---------------------------------------------------------------------------
# Protocol retrieval: token cap, per-vignette logging
# ---------------------------------------------------------------------------


def test_protocol_injection_respects_the_token_cap(monkeypatch):
    monkeypatch.setattr(expand_arms, "MAX_PROTOCOL_TOKENS", 50)
    vignette = _load_fixture("VIG-902.json")  # DIV-006 + DIV-008, both have local NTEP files
    combined, log = gather_protocol_chunks(vignette, _table(), side="ntep")
    assert estimate_tokens(combined) <= 50
    assert any(entry.get("truncated") or not entry["included"] for entry in log)


def test_gather_protocol_chunks_logs_every_divergence_id():
    vignette = _load_fixture("VIG-901.json")  # DIV-001 (no local ntep file) + DIV-002 (has one)
    _combined, log = gather_protocol_chunks(vignette, _table(), side="ntep")
    logged_ids = {entry["divergence_id"] for entry in log}
    assert logged_ids == set(vignette["divergence_ids"])


def test_gather_protocol_chunks_falls_back_when_no_local_file_matches():
    """DIV-001's ntep_citation doc (an NTEP knowledge-base web page) was
    never archived locally -- gather_protocol_chunks must fall back to the
    table's ntep_position prose rather than silently dropping the row or
    crashing."""
    table = _table()
    vignette = {"divergence_ids": ["DIV-001"]}
    combined, log = gather_protocol_chunks(vignette, table, side="ntep")
    assert log[0]["included"] is True
    assert log[0]["source"].startswith("fallback:")
    assert combined  # fell back to real prose, not empty


def test_gather_protocol_chunks_handles_rows_with_no_us_position():
    """DIV-020/DIV-021 have us_position: null -- must be logged as excluded
    with a reason, not crash."""
    table = _table()
    vignette = {"divergence_ids": ["DIV-020"]}
    combined, log = gather_protocol_chunks(vignette, table, side="us")
    assert log[0]["included"] is False
    assert combined == ""


def test_estimate_tokens_is_a_positive_rough_proxy():
    assert estimate_tokens("a" * 400) == 100
    assert estimate_tokens("") == 1  # never zero -- avoids div-by-zero-style surprises downstream


# ---------------------------------------------------------------------------
# expand() / manifest integrity
# ---------------------------------------------------------------------------


def test_expand_produces_four_prompts_per_fixture_vignette():
    vignettes = [_load_fixture("VIG-901.json"), _load_fixture("VIG-902.json")]
    entries, texts = expand(vignettes, _table())
    assert len(entries) == 8
    assert len(texts) == 8
    for vig_id in ("VIG-901", "VIG-902"):
        for arm in (1, 2, 3, 4):
            assert f"{vig_id}/arm{arm}.txt" in texts


def test_manifest_entry_sha256_matches_written_text():
    vignettes = [_load_fixture("VIG-901.json")]
    entries, texts = expand(vignettes, _table())
    for entry in entries:
        rel_path = entry["path"].removeprefix("data/prompts/")
        assert entry["sha256"] == sha256_hex(texts[rel_path])


def test_arm2_manifest_entries_record_the_location_sentence():
    vignettes = [_load_fixture("VIG-901.json")]
    entries, _texts = expand(vignettes, _table())
    arm2_entries = [e for e in entries if e["arm"] == 2]
    assert len(arm2_entries) == 1
    assert arm2_entries[0]["location_sentence"] == INDIA_LOCATION_SENTENCE


def test_arm4_manifest_entries_record_protocol_chunks_injected():
    vignettes = [_load_fixture("VIG-901.json")]
    entries, _texts = expand(vignettes, _table())
    arm4_entries = [e for e in entries if e["arm"] == 4]
    assert len(arm4_entries) == 1
    assert "protocol_chunks_injected" in arm4_entries[0]
    assert len(arm4_entries[0]["protocol_chunks_injected"]) == len(vignettes[0]["divergence_ids"])


# ---------------------------------------------------------------------------
# main(): fail-loudly-if-empty, --dry-run, real write path
# ---------------------------------------------------------------------------


def test_main_fails_loudly_when_vignette_dir_is_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(expand_arms, "VIGNETTES_ROOT", tmp_path)
    exit_code = main(["v1"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "generation must run first" in captured.err.lower()


def test_main_fails_loudly_when_version_dir_does_not_exist(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(expand_arms, "VIGNETTES_ROOT", tmp_path)
    exit_code = main(["nonexistent-version"])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "generation must run first" in captured.err.lower()


def _seed_vignette_dir(tmp_path) -> Path:
    version_dir = tmp_path / "v1"
    version_dir.mkdir(parents=True)
    for name in ("VIG-901.json", "VIG-902.json"):
        (version_dir / name).write_text(
            json.dumps(_load_fixture(name)), encoding="utf-8"
        )
    return tmp_path


def test_dry_run_writes_nothing(tmp_path, monkeypatch, capsys):
    vignettes_root = _seed_vignette_dir(tmp_path)
    prompts_dir = tmp_path / "prompts"
    monkeypatch.setattr(expand_arms, "VIGNETTES_ROOT", vignettes_root)
    monkeypatch.setattr(expand_arms, "PROMPTS_DIR", prompts_dir)
    monkeypatch.setattr(expand_arms, "PROMPTS_MANIFEST_PATH", prompts_dir / "manifest.json")
    monkeypatch.setattr(expand_arms, "MANIFEST_DIR", tmp_path / "manifests")

    exit_code = main(["v1", "--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert not prompts_dir.exists()
    assert not (tmp_path / "manifests").exists()
    assert "8 prompts" in captured.out or "-> 8" in captured.out


def test_real_run_writes_prompts_and_both_manifests(tmp_path, monkeypatch):
    vignettes_root = _seed_vignette_dir(tmp_path)
    prompts_dir = tmp_path / "prompts"
    manifest_dir = tmp_path / "manifests"
    monkeypatch.setattr(expand_arms, "VIGNETTES_ROOT", vignettes_root)
    monkeypatch.setattr(expand_arms, "PROMPTS_DIR", prompts_dir)
    monkeypatch.setattr(expand_arms, "PROMPTS_MANIFEST_PATH", prompts_dir / "manifest.json")
    monkeypatch.setattr(expand_arms, "MANIFEST_DIR", manifest_dir)

    exit_code = main(["v1"])
    assert exit_code == 0

    for vig_id in ("VIG-901", "VIG-902"):
        for arm in (1, 2, 3, 4):
            assert (prompts_dir / vig_id / f"arm{arm}.txt").exists()

    prompts_manifest = json.loads((prompts_dir / "manifest.json").read_text(encoding="utf-8"))
    assert prompts_manifest["prompt_count"] == 8
    assert prompts_manifest["vignette_count"] == 2
    assert len(prompts_manifest["prompts"]) == 8

    run_manifests = list(manifest_dir.glob("*.json"))
    assert len(run_manifests) == 1
    run_manifest = json.loads(run_manifests[0].read_text(encoding="utf-8"))
    for field in (
        "run_id",
        "model_identifiers",
        "temperature",
        "top_p",
        "max_tokens",
        "seed",
        "prompt_template_hash",
        "vignette_set_version",
        "git_commit_sha",
        "utc_timestamp",
        "total_input_tokens",
        "total_output_tokens",
    ):
        assert field in run_manifest
    assert run_manifest["model_identifiers"] == []  # no model in the loop
