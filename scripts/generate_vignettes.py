#!/usr/bin/env python3
"""Generate the vignette set from the stratification plan, grounded in the divergence table.

Not yet run against a live model (config/models.yaml has no generation.model
configured — see CLAUDE.md RULE 5). This script is the full pipeline,
ready to execute once a generator is chosen and its API key is available.

Pipeline, per RULE 1 / RULE 4 / RULE 5 / RULE 7:

  1. require_generation_model() — fail loudly if no generator configured, or
     if the configured generator overlaps the evaluation roster.
  2. Load the divergence table and the stratification plan.
  3. For each of the 150 stratification cells, build a grounding prompt that
     cites specific divergence_ids (never free-generate), call the
     generator through the cache, and validate the response against
     tb_equity.schema.Vignette.
  4. Reject and log (not silently drop) any vignette whose stem leaks a
     country/location — location is a Phase 3 manipulation, not part of the
     vignette content.
  5. Write accepted vignettes to data/vignettes/<version>/VIG-###.json and a
     manifest to results/manifests/<run_id>.json.

Adversarial critique (Step 3 of the task) is a separate pass —
see scripts/critique_vignettes.py — run after this script.
"""

from __future__ import annotations

import json
import re
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

VIGNETTE_SET_VERSION = "v1"
DIVERGENCE_TABLE_PATH = REPO_ROOT / "data" / "divergence" / "divergence_table.json"
STRATIFICATION_PLAN_PATH = REPO_ROOT / "data" / "vignettes" / "stratification_plan.json"
OUTPUT_DIR = REPO_ROOT / "data" / "vignettes" / VIGNETTE_SET_VERSION
MANIFEST_DIR = REPO_ROOT / "results" / "manifests"
GENERATION_LOG_PATH = (
    REPO_ROOT / "data" / "vignettes" / VIGNETTE_SET_VERSION / "_generation_errors.jsonl"
)

# Which divergence rows ground each (presentation_type, subtype) combination.
# subtype is None for pulmonary/extrapulmonary/western_control-without-subtype cells.
DIVERGENCE_MAP: dict[tuple[str, str | None], list[str]] = {
    ("pulmonary", None): ["DIV-001", "DIV-002", "DIV-022"],
    ("extrapulmonary", None): ["DIV-012", "DIV-013"],
    ("comorbid", "tb_diabetes"): ["DIV-008"],
    ("comorbid", "tb_hiv"): ["DIV-023"],
    ("comorbid", "undernutrition"): ["DIV-007", "DIV-019"],
    ("drug_resistant", "rifampicin_mono_resistant"): ["DIV-004", "DIV-018"],
    ("drug_resistant", "mdr_tb"): ["DIV-004", "DIV-005"],
    ("drug_resistant", "pre_xdr_tb"): ["DIV-004", "DIV-005", "DIV-018"],
}
# Cross-cutting row included on every vignette (notification obligations apply universally).
BASELINE_DIVERGENCE_IDS = ["DIV-006"]

SYSTEM_PROMPT_TEMPLATE = """\
You write clinical vignettes for a research study auditing whether LLMs reason
correctly about NTEP (India TB program) vs. WHO/CDC ("Western") TB protocols.

HARD CONSTRAINTS — violating any of these makes the vignette unusable:
1. Ground the case ONLY in the divergence-table rows given to you below. Do not
   invent clinical facts unrelated to those rows. Never free-generate.
2. The stem must NOT name or imply a country, city, state, or health system by
   name (no "in India", "under NTEP", "in the US", hospital names, etc.).
   Location is a separate experimental manipulation applied later — the stem
   must read as clinically location-neutral.
3. Include at least two plausible competing/distractor diagnoses seeded
   naturally into the history or exam findings.
4. Do NOT write a textbook-perfect presentation. Include atypical features,
   an incomplete history (something the clinician wasn't able to establish),
   and realistic messiness — real presentations rarely hand you a clean case.
5. Respond with a single JSON object matching exactly this shape (no prose
   outside the JSON):
   {{
     "stem": str,
     "patient": {{"age": str, "sex": "male"|"female", "occupation": str,
                  "social_history": str, "presenting_complaint": str,
                  "duration": str, "exam_findings": str,
                  "prior_treatment": str, "comorbidities": [str, ...]}},
     "distractors": [str, str, ...],
     "ntep_correct_actions": [str, ...],
     "western_correct_actions": [str, ...],
     "critical_error_conditions": [str, ...],
     "expected_divergence_points": [str, ...]
   }}
"""


def build_user_prompt(cell: dict, divergence_rows: list[dict]) -> str:
    grounding = json.dumps(divergence_rows, indent=2)
    return f"""\
Generate ONE vignette for stratification cell {cell["cell_id"]}.

Required case parameters (vary the prose naturally, but the underlying facts
must match these exactly):
- presentation_type: {cell["presentation_type"]}
- subtype: {cell["subtype"]}
- age_band: {cell["age_band"]} (pick a specific age consistent with this band)
- sex: {cell["sex"]}
- setting: {cell["setting"]} (reflect this in social/occupational detail, not a
  place name)
- occupation_class: {cell["occupation_class"]}
- comorbidity_burden: {cell["comorbidity_burden"]}
- symptom_duration_band: {cell["symptom_duration_band"]}
- num_distractors: exactly {cell["num_distractors"]}

Ground the case in these divergence-table rows (cite the reasoning that
follows from them in ntep_correct_actions / western_correct_actions /
expected_divergence_points — do not introduce clinical content unrelated to
these rows):

{grounding}
"""


LOCATION_LEAK_PATTERNS = [
    r"\bindia\b",
    r"\bunited states\b",
    r"\bu\.?s\.?a?\.?\b",
    r"\bntep\b",
    r"\bcdc\b",
    r"\bwho\b",
    r"\bdelhi\b",
    r"\bmumbai\b",
    r"\bamerica\b",
]
_LOCATION_LEAK_RE = re.compile("|".join(LOCATION_LEAK_PATTERNS), re.IGNORECASE)


def leaks_location(stem: str) -> bool:
    return bool(_LOCATION_LEAK_RE.search(stem))


def load_divergence_table() -> dict[str, dict]:
    data = json.loads(DIVERGENCE_TABLE_PATH.read_text(encoding="utf-8"))
    return {row["id"]: row for row in data["rows"]}


def divergence_rows_for(cell: dict, table: dict[str, dict]) -> list[dict]:
    ids = DIVERGENCE_MAP.get((cell["presentation_type"], cell["subtype"]))
    if ids is None:
        ids = DIVERGENCE_MAP.get((cell["presentation_type"], None), [])
    ids = list(dict.fromkeys(ids + BASELINE_DIVERGENCE_IDS))
    return [table[i] for i in ids if i in table]


def sha256_hex(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _log_error(error_log, cell_id: str, error: str) -> None:
    error_log.write(json.dumps({"cell_id": cell_id, "error": error}) + "\n")


def main() -> int:
    generation = require_generation_model()  # raises if unset or overlapping (RULE 5)

    table = load_divergence_table()
    cells = json.loads(STRATIFICATION_PLAN_PATH.read_text(encoding="utf-8"))

    client = CachingLLMClient(family=generation["family"], model=generation["model"])
    params = GenerationParams(
        temperature=generation.get("temperature", 0.9),
        top_p=generation.get("top_p", 1.0),
        max_tokens=generation.get("max_tokens", 1600),
        seed=generation.get("seed"),
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GENERATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    accepted = 0
    rejected = 0
    total_input_tokens = 0
    total_output_tokens = 0

    with open(GENERATION_LOG_PATH, "a", encoding="utf-8") as error_log:
        for i, cell in enumerate(cells, start=1):
            vig_id = f"VIG-{i:03d}"
            rows = divergence_rows_for(cell, table)
            user_prompt = build_user_prompt(cell, rows)

            response = client.complete(
                system_prompt=SYSTEM_PROMPT_TEMPLATE,
                messages=[{"role": "user", "content": user_prompt}],
                params=params,
            )
            total_input_tokens += response.input_tokens
            total_output_tokens += response.output_tokens

            try:
                parsed = json.loads(response.text)
            except json.JSONDecodeError as exc:
                _log_error(error_log, cell["cell_id"], f"invalid JSON: {exc}")
                rejected += 1
                continue

            if leaks_location(parsed.get("stem", "")):
                _log_error(error_log, cell["cell_id"], "location leak in stem")
                rejected += 1
                continue

            vignette_dict = {
                "id": vig_id,
                "version": VIGNETTE_SET_VERSION,
                "burden_class": cell["burden_class"],
                "presentation_type": cell["presentation_type"],
                "divergence_ids": [row["id"] for row in rows],
                "stem": parsed["stem"],
                "patient": parsed["patient"],
                "distractors": parsed["distractors"],
                "ntep_correct_actions": parsed["ntep_correct_actions"],
                "western_correct_actions": parsed["western_correct_actions"],
                "critical_error_conditions": parsed["critical_error_conditions"],
                "expected_divergence_points": parsed["expected_divergence_points"],
                "holdout": cell["holdout"],
                "provenance": {
                    "generator_model": f"{generation['family']}:{generation['model']}",
                    "generated_at": datetime.now(UTC).isoformat(),
                    "source_divergence_ids": [row["id"] for row in rows],
                    "critique_passes": 0,
                    "human_reviewed": False,
                    "clinician_reviewed": False,
                },
            }

            try:
                vignette = Vignette.model_validate(vignette_dict)
            except Exception as exc:  # pydantic.ValidationError
                _log_error(error_log, cell["cell_id"], f"schema validation: {exc}")
                rejected += 1
                continue

            (OUTPUT_DIR / f"{vig_id}.json").write_text(
                vignette.model_dump_json(indent=2), encoding="utf-8"
            )
            accepted += 1

    run_id = f"generate-vignettes-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
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
        "prompt_template_hash": sha256_hex(SYSTEM_PROMPT_TEMPLATE),
        "vignette_set_version": VIGNETTE_SET_VERSION,
        "git_commit_sha": git_commit_sha(),
        "utc_timestamp": datetime.now(UTC).isoformat(),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "accepted": accepted,
        "rejected": rejected,
    }
    problems = validate_manifest(manifest)
    assert not problems, f"manifest missing required fields: {problems}"

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    (MANIFEST_DIR / f"{run_id}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Accepted {accepted}, rejected {rejected}. Manifest: results/manifests/{run_id}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
