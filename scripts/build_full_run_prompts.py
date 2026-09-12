#!/usr/bin/env python3
"""IRIS TMED full run: generate structured-arm prompts for every non-holdout

vignette that grounds at least one of structured_elicitation.py's 5 covered
axes (DIV-001/002/004/006/007). Pure deterministic templating, no model call.

Unlike scripts/build_structured_pilot_prompts.py (Checkpoint 2b-v Step E's
fixed 12-vignette re-pilot subset), this covers the full non-holdout set --
85 of 100 vignettes -- but the structured arm's own coverage is narrower
than that: only 39 of those 85 ground one of the 5 QUESTION_BANK axes. The
other 46 have no structured question at all. This is NOT extended here --
doing so would mean writing new no-cueing-reviewed questions for the other
12 divergence rows, which the 20 September 2026 instrument freeze forbids.
The asymmetry (freeform n=85, structured n=39) is intentional and reported
plainly, not silently narrowed to the smaller set -- every downstream
report states its own per-axis n rather than assuming a fixed denominator.

The free-form condition is Arm 1 (baseline), already generated for every
non-holdout vignette by scripts/expand_arms.py -- this script only checks
it exists, never regenerates it.

Usage: python scripts/build_full_run_prompts.py
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
MANIFEST_PATH = PROMPTS_DIR / "full_run_manifest.json"

sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.structured_elicitation import (  # noqa: E402
    applicable_questions,
    build_structured_prompt,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    all_vignette_files = sorted(VIGNETTES_DIR.glob("VIG-*.json"))
    assert all_vignette_files, f"{VIGNETTES_DIR} is empty -- generate vignettes first."

    freeform_entries = []
    structured_entries = []
    skipped_no_question = []

    for path in all_vignette_files:
        data = json.loads(path.read_text(encoding="utf-8"))
        vid = data["id"]
        if data["holdout"]:
            continue  # RULE 7

        arm1_path = PROMPTS_DIR / vid / "arm1.txt"
        assert arm1_path.exists(), (
            f"{arm1_path} missing -- run scripts/expand_arms.py before this script."
        )
        freeform_entries.append({
            "vignette_id": vid,
            "divergence_ids": data["divergence_ids"],
            "freeform_path": f"data/prompts/{vid}/arm1.txt",
            "freeform_sha256": _sha256_file(arm1_path),
        })

        if not applicable_questions(data["divergence_ids"]):
            skipped_no_question.append(vid)
            continue

        prompt_text = build_structured_prompt(data["stem"], data["divergence_ids"])
        out_dir = PROMPTS_DIR / vid
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "structured.txt"
        out_path.write_text(prompt_text, encoding="utf-8", newline="")
        structured_entries.append({
            "vignette_id": vid,
            "divergence_ids": data["divergence_ids"],
            "structured_path": f"data/prompts/{vid}/structured.txt",
            "structured_sha256": _sha256_file(out_path),
        })

    manifest = {
        "run_id": f"full-run-prompts-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        "generated_at": datetime.now(UTC).isoformat(),
        "vignette_set_version": "v1",
        "freeform_vignette_count": len(freeform_entries),
        "structured_vignette_count": len(structured_entries),
        "structured_vignettes_skipped_no_question": skipped_no_question,
        "freeform": freeform_entries,
        "structured": structured_entries,
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Freeform: {len(freeform_entries)} non-holdout vignettes (all of them).")
    print(
        f"Structured: {len(structured_entries)} vignettes ground a QUESTION_BANK axis "
        f"-- {len(skipped_no_question)} skipped (no applicable question, not an error)."
    )
    print(f"Manifest written: {MANIFEST_PATH.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
