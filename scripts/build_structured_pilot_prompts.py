#!/usr/bin/env python3
"""Checkpoint 2b-v Step E: generate structured-arm prompts for the 12-vignette

re-pilot. Pure deterministic templating (src/tb_equity/structured_elicitation.py),
no model call -- writes data/prompts/<vignette_id>/structured.txt alongside the
existing arm1.txt (already regenerated from the repaired stems via
scripts/expand_arms.py; arm1.txt is what the notebook uses as this re-pilot's
free-form condition, unchanged).

Vignette selection (12 of the 16 DIV-001-repaired vignettes): VIG-008 and
VIG-015 are holdout=true and excluded per RULE 7. The remaining 12 are
stratified for DIV-002 coupling coverage -- see Checkpoint 2b-v for the
selection rationale.

Usage: python scripts/build_structured_pilot_prompts.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
VIGNETTES_DIR = REPO_ROOT / "data" / "vignettes" / "v1"
PROMPTS_DIR = REPO_ROOT / "data" / "prompts"
MANIFEST_PATH = PROMPTS_DIR / "structured_pilot_manifest.json"

sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.structured_elicitation import build_structured_prompt  # noqa: E402

PILOT_VIGNETTE_IDS = [
    "VIG-002", "VIG-003", "VIG-004", "VIG-006", "VIG-010", "VIG-014",
    "VIG-018", "VIG-019", "VIG-026", "VIG-028", "VIG-079", "VIG-080",
]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    assert len(PILOT_VIGNETTE_IDS) == 12, f"expected 12, got {len(PILOT_VIGNETTE_IDS)}"

    written = []
    manifest_entries = []
    for vid in PILOT_VIGNETTE_IDS:
        data = json.loads((VIGNETTES_DIR / f"{vid}.json").read_text(encoding="utf-8"))
        assert not data["holdout"], f"{vid} is holdout=true -- RULE 7 forbids including it here"

        prompt_text = build_structured_prompt(data["stem"], data["divergence_ids"])
        out_dir = PROMPTS_DIR / vid
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "structured.txt"
        out_path.write_text(prompt_text, encoding="utf-8", newline="")
        written.append((vid, data["divergence_ids"], out_path))

        # The paired free-form condition for this re-pilot is Arm 1 (baseline,
        # already regenerated from the repaired stems by scripts/expand_arms.py)
        # -- recorded here, not just assumed by callers, so the notebook and
        # analysis script read this list from one place instead of each
        # hardcoding PILOT_VIGNETTE_IDS and independently assuming arm1 = freeform.
        arm1_path = out_dir / "arm1.txt"
        assert arm1_path.exists(), (
            f"{arm1_path} missing -- run scripts/expand_arms.py before this script."
        )
        manifest_entries.append({
            "vignette_id": vid,
            "divergence_ids": data["divergence_ids"],
            "structured_path": f"data/prompts/{vid}/structured.txt",
            "structured_sha256": _sha256_file(out_path),
            "freeform_path": f"data/prompts/{vid}/arm1.txt",
            "freeform_sha256": _sha256_file(arm1_path),
        })

    manifest = {
        "run_id": f"structured-pilot-prompts-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        "generated_at": datetime.now(UTC).isoformat(),
        "vignette_set_version": "v1",
        "vignette_count": len(manifest_entries),
        "vignettes": manifest_entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {len(written)} structured-arm prompts:")
    for vid, dids, path in written:
        print(f"  {vid} (grounds {dids}) -> {path.relative_to(REPO_ROOT)}")
    print(f"Manifest written: {MANIFEST_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
