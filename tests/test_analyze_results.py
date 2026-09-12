"""End-to-end test of scripts/analyze_results.py against synthetic response

files in a tmp_path -- never touches the real data/responses/ or
results/CHECKPOINT2.md, since that file must only ever be written from real
Colab output, not a test fixture.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import analyze_results  # noqa: E402


def _write_response(
    responses_dir: Path, key: str, *, vignette_id: str, arm: int, model: str, seed: int, text: str
) -> None:
    responses_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "text": text,
        "raw": {
            "vignette_id": vignette_id,
            "arm": arm,
            "model": model,
            "model_revision": "rev0",
            "quantization": "awq-int4",
            "seed": seed,
            "stop_reason": "eos",
            "truncated": False,
        },
        "input_tokens": 500,
        "output_tokens": 100,
    }
    (responses_dir / f"{key}.json").write_text(json.dumps(payload), encoding="utf-8")


def test_main_refuses_to_run_against_zero_responses(tmp_path):
    empty_dir = tmp_path / "responses"
    empty_dir.mkdir()
    with pytest.raises(SystemExit, match="no response files"):
        analyze_results.main("v1", responses_dir=empty_dir, out_path=tmp_path / "out.md")


def test_main_writes_a_report_against_real_v1_vignettes(tmp_path):
    # VIG-001's real divergence_ids are [DIV-002, DIV-004, DIV-007]
    # (see data/vignettes/v1/VIG-001.json)
    responses_dir = tmp_path / "responses"
    _write_response(
        responses_dir, "key1", vignette_id="VIG-001", arm=1,
        model="hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4", seed=0,
        text=(
            "Perform rifampicin-resistance testing regardless of prior treatment history. "
            "Reserve culture for the resistance-testing cascade. "
            "Dose using the fixed-dose-combination weight-band tablet count."
        ),
    )
    _write_response(
        responses_dir, "key2", vignette_id="VIG-001", arm=1,
        model="EPFLiGHT/Meditron3-8B", seed=0,
        text=(
            "Reserve rapid rifampicin-resistance testing for patients meeting "
            "a specific risk criterion. "
            "Send both liquid and solid mycobacterial culture on the initial specimen. "
            "Calculate this patient's anti-TB drug doses individually in mg/kg."
        ),
    )
    out_path = tmp_path / "CHECKPOINT2.md"
    analyze_results.main("v1", responses_dir=responses_dir, out_path=out_path)

    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    assert "consensus deviation rate" in content
    assert "truncation rate" in content
    assert "What the deviation rate is made of" in content
    assert "meta" in content
    assert "epfl" in content
    assert "DIV-002" in content or "DIV-004" in content or "DIV-007" in content


def test_family_mapping_resolves_known_model_repos():
    assert analyze_results._family_for({"model": "Orion-zhen/Qwen3-8B-AWQ"}) == "qwen"
    assert analyze_results._family_for({"model": "ibm-granite/granite-4.2-8b"}) == "ibm"
    assert analyze_results._family_for({"model": "some/unknown-repo"}) == "some/unknown-repo"
