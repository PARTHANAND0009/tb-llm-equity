"""End-to-end test of scripts/analyze_full_run.py against synthetic checkpoint

files in a tmp_path -- never touches the real data/responses/ or
results/FULL_RUN.md, since that file must only ever be written from real
Colab output, not a test fixture. Uses real v1 vignette ids (VIG-002,
VIG-008) since those are static, checked-in fixtures.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import analyze_full_run as full_run  # noqa: E402


def _write_checkpoint(
    responses_dir: Path,
    key: str,
    *,
    vignette_id: str,
    family: str = "meta",
    model: str = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
    elicitation: str | None = "freeform",
    text: str = "Send Xpert MTB/RIF as the initial test.",
    truncated: bool = False,
) -> None:
    responses_dir.mkdir(parents=True, exist_ok=True)
    raw = {
        "vignette_id": vignette_id,
        "model": model,
        "model_revision": "rev0",
        "quantization": "awq-int4",
        "stop_reason": "max_tokens" if truncated else "eos",
        "truncated": truncated,
    }
    if elicitation is not None:
        raw["elicitation"] = elicitation
    payload = {"text": text, "raw": raw, "input_tokens": 300, "output_tokens": 100}
    (responses_dir / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_main_refuses_to_run_against_zero_responses(tmp_path):
    empty_dir = tmp_path / "responses"
    empty_dir.mkdir()
    with pytest.raises(SystemExit, match="no response files"):
        full_run.main(
            responses_dir=empty_dir, manifest_dir=tmp_path / "manifests",
            out_path=tmp_path / "out.md",
        )


def test_main_refuses_a_holdout_vignette(tmp_path):
    # VIG-008 is holdout=true in the real v1 vignette set (RULE 7)
    responses_dir = tmp_path / "responses"
    _write_checkpoint(responses_dir, "key1", vignette_id="VIG-008")
    with pytest.raises(SystemExit, match="RULE 7 violation"):
        full_run.main(
            responses_dir=responses_dir, manifest_dir=tmp_path / "manifests",
            out_path=tmp_path / "out.md",
        )


def test_load_full_run_responses_skips_task_b_style_checkpoints(tmp_path):
    responses_dir = tmp_path / "responses"
    _write_checkpoint(
        responses_dir, "full_run_key", vignette_id="VIG-002", elicitation="structured"
    )
    _write_checkpoint(responses_dir, "task_b_key", vignette_id="VIG-002", elicitation=None)

    responses = full_run.load_full_run_responses(responses_dir)
    assert len(responses) == 1
    assert responses[0].elicitation == "structured"


def test_main_writes_a_report_with_all_required_sections(tmp_path):
    responses_dir = tmp_path / "responses"
    _write_checkpoint(
        responses_dir, "k1", vignette_id="VIG-002", family="meta",
        elicitation="structured", text="Send Xpert MTB/RIF as the initial test.",
    )
    _write_checkpoint(
        responses_dir, "k2", vignette_id="VIG-002", family="meta",
        elicitation="freeform", text="The patient likely has pneumonia.",
    )
    out_path = tmp_path / "out.md"
    full_run.main(
        responses_dir=responses_dir, manifest_dir=tmp_path / "manifests", out_path=out_path
    )

    content = out_path.read_text(encoding="utf-8")
    assert "Excluded from this panel" in content
    assert "Granite" in content
    assert "Flags (checked automatically" in content
    assert "Conditional alignment per axis per model (PRIMARY result)" in content
    assert "Entailment-control coverage" in content
    assert "H1/H2 verdict — SECONDARY" in content
    assert "INCONCLUSIVE" in content or "no structured-arm data" in content
    assert "Silence rate, both ways" in content
    assert "REACHABLE distribution — freeform only" in content
    assert "Generation-time stats" in content


def test_compute_flags_detects_div001_material_drop():
    from tb_equity.analysis import RawResponse
    from test_rubric import make_vignette

    v = make_vignette(["DIV-001"], id="VIG-121")
    vignettes = {"VIG-121": v}
    # Step E baseline for epfl is 17/18 = 94.4% us-aligned among addressed.
    # Here epfl is 0% us-aligned (100% consensus instead) -- a material drop.
    responses = [
        RawResponse(
            vignette_id="VIG-121", arm=0, family="epfl", model="m", model_revision="r",
            seed=0, text="Send Xpert MTB/RIF as the initial test.", elicitation="freeform",
        )
        for _ in range(5)
    ]
    flags = full_run.compute_flags(responses, vignettes, {})
    assert any("DIV-001" in f and "epfl" in f for f in flags)


def test_compute_flags_detects_near_zero_commitment():
    from tb_equity.analysis import RawResponse
    from test_rubric import make_vignette

    v = make_vignette(["DIV-001"], id="VIG-122")
    vignettes = {"VIG-122": v}
    responses = [
        RawResponse(
            vignette_id="VIG-122", arm=0, family="qwen", model="m", model_revision="r",
            seed=0, text="The patient likely has pneumonia.", elicitation="freeform",
        )
        for _ in range(20)
    ]
    flags = full_run.compute_flags(responses, vignettes, {})
    assert any("near-zero commitment" in f and "qwen" in f for f in flags)


def test_compute_flags_detects_freeze_deadline_overrun():
    manifests = {"meta": {"utc_timestamp": "2026-09-25T00:00:00+00:00"}}
    flags = full_run.compute_flags([], {}, manifests)
    assert any("freeze deadline" in f for f in flags)
