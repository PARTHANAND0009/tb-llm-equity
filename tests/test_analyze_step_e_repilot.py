"""End-to-end test of scripts/analyze_step_e_repilot.py against synthetic

notebook-output JSON in a tmp_path -- never touches the real
results/pilot/step_e_repilot/ or results/CHECKPOINT_STEP_E.md, since that
file must only ever be written from real Colab output, not a test fixture.
Uses real v1 vignette ids (VIG-002, VIG-008) since those are static,
checked-in fixtures -- same pattern as test_analyze_results.py.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import analyze_step_e_repilot as step_e  # noqa: E402


def _write_family_payload(
    step_e_dir: Path,
    family: str,
    *,
    model: str = "test/model",
    revision: str = "rev0",
    responses: list[dict],
    elicitation_summary: dict | None = None,
) -> None:
    step_e_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "family": family,
        "model": model,
        "model_revision": revision,
        "responses": responses,
        "elicitation_summary": elicitation_summary
        or {
            "structured": {"elapsed_seconds": 10.0, "batch_size_used": 4},
            "freeform": {"elapsed_seconds": 20.0, "batch_size_used": 1},
        },
    }
    (step_e_dir / f"{family}.json").write_text(json.dumps(payload), encoding="utf-8")


def _resp(vignette_id, elicitation, text, *, family="meta", output_tokens=100, truncated=False):
    return {
        "vignette_id": vignette_id,
        "family": family,
        "model": "test/model",
        "model_revision": "rev0",
        "elicitation": elicitation,
        "text": text,
        "input_tokens": 300,
        "output_tokens": output_tokens,
        "stop_reason": "max_tokens" if truncated else "eos",
        "truncated": truncated,
        "batch_size_used": 4 if elicitation == "structured" else 1,
    }


def test_main_refuses_to_run_against_zero_responses(tmp_path):
    empty_dir = tmp_path / "step_e"
    empty_dir.mkdir()
    with pytest.raises(SystemExit, match="no response files"):
        step_e.main(step_e_dir=empty_dir, out_path=tmp_path / "out.md")


def test_main_refuses_a_holdout_vignette(tmp_path):
    # VIG-008 is holdout=true in the real v1 vignette set (RULE 7) -- this
    # should never happen from the real pipeline (structured_pilot_manifest.json
    # is built only from non-holdout ids), but the guard must fire if it does.
    step_e_dir = tmp_path / "step_e"
    _write_family_payload(
        step_e_dir,
        "meta",
        responses=[_resp("VIG-008", "structured", "Send Xpert MTB/RIF as the initial test.")],
    )
    with pytest.raises(SystemExit, match="RULE 7 violation"):
        step_e.main(step_e_dir=step_e_dir, out_path=tmp_path / "out.md")


def test_main_writes_a_report_against_real_v1_vignette(tmp_path):
    # VIG-002's real divergence_ids are [DIV-004, DIV-007, DIV-001] (non-holdout).
    step_e_dir = tmp_path / "step_e"
    _write_family_payload(
        step_e_dir,
        "meta",
        responses=[
            _resp(
                "VIG-002", "structured",
                "Send a sputum specimen for Xpert MTB/RIF as the initial test.",
            ),
            _resp(
                "VIG-002", "freeform",
                "The patient likely has community-acquired pneumonia.",
            ),
        ],
    )
    out_path = tmp_path / "out.md"
    step_e.main(step_e_dir=step_e_dir, out_path=out_path)

    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "H1/H2 headline" in content
    assert "Divergence-axis coverage" in content
    assert "Entailment-control coverage" in content
    assert "Conditional alignment among ADDRESSED" in content
    assert "REACHABLE distribution" in content
    assert "If it stays at zero, investigate" in content or "should fire against" in content
    assert "Generation-time stats" in content
    assert "Granite batch-size question" in content
    assert "meta" in content


def test_main_reports_missing_ibm_data_distinctly_from_oom_fallback(tmp_path):
    """A model whose cell never completed (e.g. OOM'd during loading, before
    any generation) must be reported as missing, not misread as 'ran and
    fell back to batch_size=1 on OOM' -- those are different findings."""
    step_e_dir = tmp_path / "step_e"
    _write_family_payload(
        step_e_dir, "meta",
        responses=[_resp("VIG-002", "structured", "Send Xpert MTB/RIF as the initial test.")],
    )
    out_path = tmp_path / "out.md"
    step_e.main(step_e_dir=step_e_dir, out_path=out_path)

    content = out_path.read_text(encoding="utf-8")
    assert "No `ibm` data in this run" in content
    assert "restoration NOT achieved" not in content


def test_load_step_e_responses_tags_elicitation_correctly(tmp_path):
    step_e_dir = tmp_path / "step_e"
    _write_family_payload(
        step_e_dir, "ibm",
        responses=[
            _resp("VIG-002", "structured", "structured text", family="ibm"),
            _resp("VIG-002", "freeform", "freeform text", family="ibm"),
        ],
    )
    responses = step_e.load_step_e_responses(step_e_dir)
    assert {r.elicitation for r in responses} == {"structured", "freeform"}
    assert all(r.family == "ibm" for r in responses)


def test_load_generation_stats_reports_batch_size_and_wall_clock(tmp_path):
    step_e_dir = tmp_path / "step_e"
    _write_family_payload(
        step_e_dir, "ibm",
        responses=[
            _resp("VIG-002", "structured", "text", family="ibm", output_tokens=50),
            _resp("VIG-003", "structured", "text", family="ibm", output_tokens=150),
        ],
        elicitation_summary={
            "structured": {"elapsed_seconds": 10.0, "batch_size_used": 4},
            "freeform": {"elapsed_seconds": 0.0, "batch_size_used": 1},
        },
    )
    stats = step_e.load_generation_stats(step_e_dir)
    structured = stats["ibm"]["by_elicitation"]["structured"]
    assert structured["n"] == 2
    assert structured["mean_output_tokens"] == 100.0
    assert structured["batch_size_used"] == 4
    assert structured["wall_clock_per_generation"] == 5.0
