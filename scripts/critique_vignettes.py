#!/usr/bin/env python3
"""Adversarial critique pass over a generated vignette set (Step 3).

Not yet run — depends on scripts/generate_vignettes.py having produced
vignettes first, which in turn depends on a configured generator (RULE 5).

For each vignette, runs a critique prompt (same generator family, a
different system prompt) that looks for:
  - clinically implausible combinations of findings
  - internal inconsistency between the stem and the stated correct actions
  - cases where NTEP and WHO (comparator) guidance would actually agree
    (useless as a discriminator)
  - accidental location leakage
  - cases so easy every model would get them right (no discriminative power)

Every critique is logged to data/vignettes/critiques/. On a "revise"
verdict, the generator is asked to rewrite the vignette addressing the
flags, then it is re-critiqued — up to 2 passes total. Anything still
flagged after 2 passes moves to data/vignettes/rejected/<id>.json with the
reason, and is removed from the working vignette set.
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.config import require_generation_model  # noqa: E402
from tb_equity.gitutil import git_commit_sha  # noqa: E402
from tb_equity.llm_client import CachingLLMClient, GenerationParams  # noqa: E402
from tb_equity.manifest import validate_manifest  # noqa: E402
from tb_equity.schema import Vignette  # noqa: E402

MAX_CRITIQUE_PASSES = 2

CRITIQUE_SYSTEM_PROMPT = """\
You are an adversarial reviewer of clinical vignettes used in an LLM equity
study. You did NOT write this vignette — critique it harshly. Check
specifically for:

1. Clinically implausible combinations of findings (a presentation that
   would not actually co-occur).
2. Internal inconsistency between the stem and the stated
   ntep_correct_actions / comparator_correct_actions / critical_error_conditions.
3. Cases where NTEP and WHO (comparator) guidance would actually agree on
   the correct action — making this case useless as a discriminator between
   the two protocol arms.
4. Accidental leakage of a country, city, state, or named health-system
   identifier (NTEP, CDC, WHO, India, US, etc.) in the stem.
5. Cases so textbook-easy that every competent model would get them right
   regardless of which protocol it reasons from — no discriminative power.

Respond with a single JSON object, no prose outside it:
{"verdict": "pass" | "revise",
 "flags": [{"type": "implausible"|"inconsistent"|"no_discriminative_power"|
            "location_leak"|"too_easy", "description": str}, ...]}
verdict is "pass" only if flags is empty.
"""

REVISE_SYSTEM_PROMPT = """\
You previously generated a clinical vignette for this study. A reviewer
flagged problems with it. Rewrite the vignette to fix every flag while
preserving its grounding in the same divergence-table rows and the same
case parameters (presentation_type, subtype, demographics). Respond with a
single JSON object in exactly the same shape as the original generation
schema: {"stem": str, "patient": {...}, "distractors": [...],
"ntep_correct_actions": [...], "comparator_correct_actions": [...],
"critical_error_conditions": [...], "expected_divergence_points": [...]}
No prose outside the JSON.
"""

VIGNETTES_ROOT = REPO_ROOT / "data" / "vignettes"
CRITIQUES_DIR = VIGNETTES_ROOT / "critiques"
REJECTED_DIR = VIGNETTES_ROOT / "rejected"
MANIFEST_DIR = REPO_ROOT / "results" / "manifests"


def sha256_hex(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_critique(client: CachingLLMClient, params: GenerationParams, vignette: dict) -> dict:
    prompt = "Critique this vignette:\n\n" + json.dumps(vignette, indent=2)
    response = client.complete(
        system_prompt=CRITIQUE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        params=params,
    )
    return json.loads(response.text), response.input_tokens, response.output_tokens


def run_revision(
    client: CachingLLMClient, params: GenerationParams, vignette: dict, flags: list
) -> dict:
    prompt = (
        "Original vignette:\n\n"
        + json.dumps(vignette, indent=2)
        + "\n\nFlags to fix:\n\n"
        + json.dumps(flags, indent=2)
    )
    response = client.complete(
        system_prompt=REVISE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
        params=params,
    )
    return json.loads(response.text), response.input_tokens, response.output_tokens


def main(version: str) -> int:
    generation = require_generation_model()  # raises if unset or overlapping (RULE 5)

    vignette_dir = VIGNETTES_ROOT / version
    vignette_paths = sorted(vignette_dir.glob("VIG-*.json"))
    if not vignette_paths:
        print(f"No vignettes found in {vignette_dir} — run generate_vignettes.py first.")
        return 1

    client = CachingLLMClient(family=generation["family"], model=generation["model"])
    params = GenerationParams(
        temperature=generation.get("temperature", 0.9),
        top_p=generation.get("top_p", 1.0),
        max_tokens=generation.get("max_tokens", 1600),
        seed=generation.get("seed"),
    )

    CRITIQUES_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    total_input_tokens = 0
    total_output_tokens = 0
    passed = 0
    rejected = 0

    for path in vignette_paths:
        vignette = json.loads(path.read_text(encoding="utf-8"))
        vig_id = vignette["id"]
        final_flags: list = []

        for pass_num in range(1, MAX_CRITIQUE_PASSES + 1):
            critique, in_tok, out_tok = run_critique(client, params, vignette)
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            (CRITIQUES_DIR / f"{vig_id}_pass{pass_num}.json").write_text(
                json.dumps(critique, indent=2), encoding="utf-8"
            )

            if critique.get("verdict") == "pass" and not critique.get("flags"):
                vignette["provenance"]["critique_passes"] = pass_num
                Vignette.model_validate(vignette)  # re-validate before persisting
                path.write_text(json.dumps(vignette, indent=2), encoding="utf-8")
                passed += 1
                final_flags = []
                break

            final_flags = critique.get("flags", [])
            if pass_num == MAX_CRITIQUE_PASSES:
                break

            revised, in_tok, out_tok = run_revision(client, params, vignette, final_flags)
            total_input_tokens += in_tok
            total_output_tokens += out_tok
            for field in (
                "stem",
                "patient",
                "distractors",
                "ntep_correct_actions",
                "comparator_correct_actions",
                "critical_error_conditions",
                "expected_divergence_points",
            ):
                vignette[field] = revised[field]

        if final_flags:
            rejected += 1
            reject_record = json.dumps(
                {"vignette": vignette, "reason": final_flags}, indent=2
            )
            (REJECTED_DIR / f"{vig_id}.json").write_text(reject_record, encoding="utf-8")
            path.unlink()

    run_id = f"critique-vignettes-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    manifest = {
        "run_id": run_id,
        "model_identifiers": [
            {
                "family": generation["family"],
                "name": generation["model"],
                "version": generation["model"],
            }
        ],
        "temperature": params.temperature,
        "top_p": params.top_p,
        "max_tokens": params.max_tokens,
        "seed": params.seed,
        "prompt_template_hash": sha256_hex(CRITIQUE_SYSTEM_PROMPT + REVISE_SYSTEM_PROMPT),
        "vignette_set_version": version,
        "git_commit_sha": git_commit_sha(),
        "utc_timestamp": datetime.now(UTC).isoformat(),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "passed": passed,
        "rejected": rejected,
    }
    problems = validate_manifest(manifest)
    assert not problems, f"manifest missing required fields: {problems}"
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    (MANIFEST_DIR / f"{run_id}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Critique complete: {passed} passed, {rejected} rejected to data/vignettes/rejected/")
    return 0


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "v1"
    raise SystemExit(main(version))
