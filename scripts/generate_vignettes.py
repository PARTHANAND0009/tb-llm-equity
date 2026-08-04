#!/usr/bin/env python3
"""Generate the vignette set from the stratification plan, grounded in the divergence table.

Two generation modes (RULE 5 -- require_generation_model() -- applies to
both; a generator family/model must be configured in config/models.yaml and
must not overlap the evaluation roster, regardless of how it's actually run):

  --mode=api (default): call the configured generator through
    tb_equity.llm_client.CachingLLMClient (sha256-cached, RULE 4) over its
    provider API. Requires the provider's API key to be set.

  --mode=claude-code: no API key needed. Writes the per-cell grounding
    prompt to data/vignettes/prompts/<cell_id>.md instead of calling an API,
    for a coding agent (e.g. Claude Code) to read and act as the generator
    directly, writing the resulting vignette JSON to
    data/vignettes/<version>/<VIG-###>.json by hand. Re-running in this mode
    picks up whatever vignette files already exist, validates them, and
    folds them into the manifest -- so it can be run repeatedly as the agent
    works through the prompt files.

Pipeline, per RULE 1 / RULE 4 / RULE 5 / RULE 7:

  1. require_generation_model() — fail loudly if no generator configured, or
     if the configured generator overlaps the evaluation roster.
  2. Load the divergence table and the stratification plan.
  3. For each stratification cell, build a grounding prompt that cites
     specific divergence_ids (never free-generate), obtain a response
     (API call, or a hand-authored file in claude-code mode), and validate
     it against tb_equity.schema.Vignette.
  4. Reject and log (not silently drop) any vignette whose stem leaks a
     country/location — location is a Phase 3 manipulation, not part of the
     vignette content.
  5. Write accepted vignettes to data/vignettes/<version>/VIG-###.json and a
     manifest to results/manifests/<run_id>.json.

Adversarial critique (Step 3 of the task) is a separate pass —
see scripts/critique_vignettes.py — run after this script.
"""

from __future__ import annotations

import argparse
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
PROMPTS_DIR = REPO_ROOT / "data" / "vignettes" / "prompts"
MANIFEST_DIR = REPO_ROOT / "results" / "manifests"
GENERATION_LOG_PATH = (
    REPO_ROOT / "data" / "vignettes" / VIGNETTE_SET_VERSION / "_generation_errors.jsonl"
)

# Which divergence rows ground each (presentation_type, subtype) combination.
# subtype is None for pulmonary/extrapulmonary cells (no subtype axis).
#
# Rebuilt for the 19-row divergence_table.json (2026-08 primary-source rebuild
# -- see data/divergence/SUMMARY.md). Every non-convergent row grounds at
# least one combination here; tests/test_divergence_coverage.py asserts the
# union of ids used below equals the full set of row ids in the table.
DIVERGENCE_MAP: dict[tuple[str, str | None], list[str]] = {
    ("pulmonary", None): [
        "DIV-001",  # initial diagnostic test
        "DIV-002",  # scope of molecular DST
        "DIV-004",  # culture requirement scope
        "DIV-006",  # regimen dosing schedule
        "DIV-007",  # weight-band vs mg/kg dosing
        "DIV-008",  # treatment extension approach
        "DIV-015",  # notification platform
    ],
    ("extrapulmonary", None): [
        "DIV-003",  # EPTB specimen testing pathway
        "DIV-008",  # treatment extension approach (disseminated/EPTB)
        "DIV-016",  # active case-finding vs contact investigation
        "DIV-017",  # structured national triage protocol
    ],
    ("comorbid", "tb_diabetes"): ["DIV-018"],  # diabetes triage threshold
    ("comorbid", "tb_hiv"): ["DIV-019"],  # cotrimoxazole preventive therapy scope
    ("comorbid", "undernutrition"): [
        "DIV-013",  # Nikshay Poshan Yojana DBT
        "DIV-014",  # Ni-kshay Mitra community support
    ],
    ("drug_resistant", "rifampicin_mono_resistant"): ["DIV-002", "DIV-007"],
    ("drug_resistant", "mdr_tb"): ["DIV-002", "DIV-007"],
    ("drug_resistant", "pre_xdr_tb"): ["DIV-002", "DIV-007"],
    ("contact_management", "household_contact_ds_tb"): [
        "DIV-005",  # TST vs IGRA given BCG history
        "DIV-010",  # household contact TPT eligibility scope
        "DIV-012",  # 1HP regimen adoption status
    ],
    ("contact_management", "household_contact_mdr_tb"): ["DIV-009"],  # TPT for MDR-TB contacts
    ("contact_management", "plhiv_tpt"): [
        "DIV-005",  # TST vs IGRA given BCG history
        "DIV-011",  # TPT for PLHIV without required TBI testing
        "DIV-019",  # cotrimoxazole preventive therapy scope
    ],
}

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
   {
     "stem": str,
     "patient": {"age": str, "sex": "male"|"female", "occupation": str,
                  "social_history": str, "presenting_complaint": str,
                  "duration": str, "exam_findings": str,
                  "prior_treatment": str, "comorbidities": [str, ...]},
     "distractors": [str, str, ...],
     "ntep_correct_actions": [str, ...],
     "western_correct_actions": [str, ...],
     "critical_error_conditions": [str, ...],
     "expected_divergence_points": [str, ...]
   }
"""


BURDEN_CLASS_FRAMING = {
    "india_high": """\
burden_class: india_high — this case represents TB as it presents in a
high-TB-burden population: community/household exposure is plausible and
unremarkable, and the grounding should reflect NTEP program realities
(molecular-first diagnostics where available, weight-band dosing, mandated
program steps like notification/DBT/bidirectional screening where the
grounding rows call for them).""",
    "western_control": """\
burden_class: western_control — this is NOT the same case relabeled. Write a
case whose epidemiology is plausible for a LOW-TB-burden Western setting:
e.g. reactivation disease in an older adult, a recent-immigration or travel
history to a high-burden country, HIV/immunosuppression, a
congregate-setting exposure (shelter, correctional facility, healthcare
occupational exposure), or another risk factor pattern that is what actually
drives TB case-finding where background incidence is low. Ground the
Western-arm reasoning in the culture-based/individualized/risk-based
practices the grounding rows describe. This case must be matched to its
india_high counterpart (stratification cell {matched_pair_id}) on
presentation complexity, age band, and number of distractors — but it must
read as a distinct clinical scenario, not the same stem with a different
label.""",
}


def build_user_prompt(cell: dict, divergence_rows: list[dict]) -> str:
    grounding = json.dumps(divergence_rows, indent=2)
    burden_framing = BURDEN_CLASS_FRAMING[cell["burden_class"]].format(
        matched_pair_id=cell.get("matched_pair_id")
    )
    return f"""\
Generate ONE vignette for stratification cell {cell["cell_id"]}.

{burden_framing}

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


# Case-insensitive: safe because none of these collide with common English
# words ("india", "delhi" etc. don't appear as ordinary vocabulary).
LOCATION_LEAK_PATTERNS_CASE_INSENSITIVE = [
    r"\bindia\b",
    r"\bdelhi\b",
    r"\bmumbai\b",
    r"\bamerica\b",
    r"\bunited states\b",
    r"\bntep\b",
]
# Case-SENSITIVE: "who" and "us"/"U.S." collide with common English words
# ("...a patient who presented...", "...told us..."). Matching case-sensitively
# on the all-caps acronym form avoids flagging ordinary prose while still
# catching the organization/country references.
LOCATION_LEAK_PATTERNS_CASE_SENSITIVE = [
    r"\bWHO\b",
    r"\bCDC\b",
    r"\bU\.S\.",
    r"\bUSA\b",
    r"\bNTEP\b",
]
_LOCATION_LEAK_RE_CI = re.compile(
    "|".join(LOCATION_LEAK_PATTERNS_CASE_INSENSITIVE), re.IGNORECASE
)
_LOCATION_LEAK_RE_CS = re.compile("|".join(LOCATION_LEAK_PATTERNS_CASE_SENSITIVE))


def leaks_location(stem: str) -> bool:
    return bool(_LOCATION_LEAK_RE_CI.search(stem)) or bool(_LOCATION_LEAK_RE_CS.search(stem))


def load_divergence_table() -> dict[str, dict]:
    data = json.loads(DIVERGENCE_TABLE_PATH.read_text(encoding="utf-8"))
    return {row["id"]: row for row in data["rows"]}


def divergence_rows_for(cell: dict, table: dict[str, dict]) -> list[dict]:
    ids = DIVERGENCE_MAP.get((cell["presentation_type"], cell["subtype"]))
    if ids is None:
        ids = DIVERGENCE_MAP.get((cell["presentation_type"], None), [])
    return [table[i] for i in ids if i in table]


def sha256_hex(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _log_error(error_log, cell_id: str, error: str) -> None:
    error_log.write(json.dumps({"cell_id": cell_id, "error": error}) + "\n")


def _cell_id_to_vig_id_map(cells: list[dict]) -> dict[str, str]:
    # vig_id is assigned sequentially over `cells`, so this mapping is known up
    # front -- lets us translate a cell's matched_pair_id (a STRAT-### cell id)
    # into the VIG-### id of the vignette that cell will become.
    return {cell["cell_id"]: f"VIG-{i:03d}" for i, cell in enumerate(cells, start=1)}


def _build_vignette_dict(
    *,
    cell: dict,
    vig_id: str,
    rows: list[dict],
    parsed: dict,
    generator_model_label: str,
    cell_id_to_vig_id: dict[str, str],
) -> dict:
    matched_cell_id = cell.get("matched_pair_id")
    return {
        "id": vig_id,
        "version": VIGNETTE_SET_VERSION,
        "burden_class": cell["burden_class"],
        "presentation_type": cell["presentation_type"],
        "matched_pair_id": cell_id_to_vig_id.get(matched_cell_id) if matched_cell_id else None,
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
            "generator_model": generator_model_label,
            "generated_at": parsed.get("_generated_at", datetime.now(UTC).isoformat()),
            "source_divergence_ids": [row["id"] for row in rows],
            "critique_passes": 0,
            "human_reviewed": False,
            "clinician_reviewed": False,
        },
    }


def _write_manifest(
    *,
    run_id_prefix: str,
    generation: dict,
    params: GenerationParams | None,
    total_input_tokens: int,
    total_output_tokens: int,
    accepted: int,
    rejected: int,
    extra: dict | None = None,
) -> str:
    run_id = f"{run_id_prefix}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
    manifest = {
        "run_id": run_id,
        "model_identifiers": [
            {
                "family": generation["family"],
                "name": generation["model"],
                "version": generation["model"],
            }
        ],
        "temperature": params.temperature if params else generation.get("temperature", 0.9),
        "top_p": params.top_p if params else generation.get("top_p", 1.0),
        "max_tokens": params.max_tokens if params else generation.get("max_tokens", 1600),
        "seed": params.seed if params else generation.get("seed"),
        "prompt_template_hash": sha256_hex(SYSTEM_PROMPT_TEMPLATE),
        "vignette_set_version": VIGNETTE_SET_VERSION,
        "git_commit_sha": git_commit_sha(),
        "utc_timestamp": datetime.now(UTC).isoformat(),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "accepted": accepted,
        "rejected": rejected,
    }
    if extra:
        manifest.update(extra)
    problems = validate_manifest(manifest)
    assert not problems, f"manifest missing required fields: {problems}"

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    (MANIFEST_DIR / f"{run_id}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return run_id


def run_api_mode(generation: dict, table: dict[str, dict], cells: list[dict]) -> int:
    cell_id_to_vig_id = _cell_id_to_vig_id_map(cells)
    client = CachingLLMClient(family=generation["family"], model=generation["model"])
    params = GenerationParams(
        temperature=generation.get("temperature", 0.9),
        top_p=generation.get("top_p", 1.0),
        max_tokens=generation.get("max_tokens", 1600),
        seed=generation.get("seed"),
    )

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

            vignette_dict = _build_vignette_dict(
                cell=cell,
                vig_id=vig_id,
                rows=rows,
                parsed=parsed,
                generator_model_label=f"{generation['family']}:{generation['model']}",
                cell_id_to_vig_id=cell_id_to_vig_id,
            )

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

    run_id = _write_manifest(
        run_id_prefix="generate-vignettes-api",
        generation=generation,
        params=params,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        accepted=accepted,
        rejected=rejected,
    )
    print(f"Accepted {accepted}, rejected {rejected}. Manifest: results/manifests/{run_id}.json")
    return 0


def _render_prompt_file(
    *, cell: dict, vig_id: str, rows: list[dict], cell_id_to_vig_id: dict[str, str]
) -> str:
    user_prompt = build_user_prompt(cell, rows)
    matched_cell_id = cell.get("matched_pair_id")
    matched_vig_id = cell_id_to_vig_id.get(matched_cell_id) if matched_cell_id else None
    divergence_ids = [row["id"] for row in rows]
    output_path = f"data/vignettes/{VIGNETTE_SET_VERSION}/{vig_id}.json"

    output_contract = {
        "id": vig_id,
        "version": VIGNETTE_SET_VERSION,
        "burden_class": cell["burden_class"],
        "presentation_type": cell["presentation_type"],
        "matched_pair_id": matched_vig_id,
        "divergence_ids": divergence_ids,
        "stem": "...",
        "patient": {
            "age": "...",
            "sex": "male|female",
            "occupation": "...",
            "social_history": "...",
            "presenting_complaint": "...",
            "duration": "...",
            "exam_findings": "...",
            "prior_treatment": "...",
            "comorbidities": ["..."],
        },
        "distractors": ["...", "..."],
        "ntep_correct_actions": ["..."],
        "western_correct_actions": ["..."],
        "critical_error_conditions": ["..."],
        "expected_divergence_points": ["..."],
        "holdout": cell["holdout"],
        "provenance": {
            "generator_model": "<see manifest -- claude-code mode>",
            "generated_at": "<ISO 8601 UTC timestamp at the time you write this file>",
            "source_divergence_ids": divergence_ids,
            "critique_passes": 0,
            "human_reviewed": False,
            "clinician_reviewed": False,
        },
    }

    return f"""\
# Vignette generation prompt -- {cell["cell_id"]} -> {vig_id}

**Mode:** claude-code (no API call -- you are the generator)
**Target output file:** `{output_path}`

## System instructions

{SYSTEM_PROMPT_TEMPLATE}

## Case brief

{user_prompt}

## Output contract

Write the complete vignette to `{output_path}` as a single JSON object
matching `tb_equity.schema.Vignette` exactly (fill in every `"..."` below
with real content; `id`, `version`, `burden_class`, `presentation_type`,
`matched_pair_id`, `divergence_ids`, and `holdout` are already correct as
shown -- do not change them):

```json
{json.dumps(output_contract, indent=2)}
```

Then re-run `python scripts/generate_vignettes.py --mode=claude-code` to
validate this file against the schema and fold it into the run manifest.
"""


def run_claude_code_mode(generation: dict, table: dict[str, dict], cells: list[dict]) -> int:
    cell_id_to_vig_id = _cell_id_to_vig_id_map(cells)
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    written_prompts = 0
    for i, cell in enumerate(cells, start=1):
        vig_id = f"VIG-{i:03d}"
        if (OUTPUT_DIR / f"{vig_id}.json").exists():
            continue  # already generated -- no need to (re)write its prompt
        rows = divergence_rows_for(cell, table)
        prompt_text = _render_prompt_file(
            cell=cell, vig_id=vig_id, rows=rows, cell_id_to_vig_id=cell_id_to_vig_id
        )
        (PROMPTS_DIR / f"{cell['cell_id']}.md").write_text(prompt_text, encoding="utf-8")
        written_prompts += 1

    # Validate whatever vignette files already exist (written by the agent on
    # this or a prior invocation) and fold them into the manifest.
    accepted = 0
    rejected = 0
    with open(GENERATION_LOG_PATH, "a", encoding="utf-8") as error_log:
        for i, cell in enumerate(cells, start=1):
            vig_id = f"VIG-{i:03d}"
            path = OUTPUT_DIR / f"{vig_id}.json"
            if not path.exists():
                continue

            try:
                vignette_dict = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                _log_error(error_log, cell["cell_id"], f"invalid JSON in {vig_id}.json: {exc}")
                rejected += 1
                continue

            if leaks_location(vignette_dict.get("stem", "")):
                _log_error(error_log, cell["cell_id"], "location leak in stem")
                rejected += 1
                continue

            try:
                Vignette.model_validate(vignette_dict)
            except Exception as exc:  # pydantic.ValidationError
                _log_error(error_log, cell["cell_id"], f"schema validation: {exc}")
                rejected += 1
                continue

            accepted += 1

    pending = len(cells) - accepted - rejected
    run_id = _write_manifest(
        run_id_prefix="generate-vignettes-claude-code",
        generation=generation,
        params=None,
        total_input_tokens=0,
        total_output_tokens=0,
        accepted=accepted,
        rejected=rejected,
        extra={
            "mode": "claude-code",
            "prompts_written_this_run": written_prompts,
            "pending": pending,
        },
    )
    print(
        f"claude-code mode: wrote {written_prompts} new prompt(s) to {PROMPTS_DIR}/. "
        f"Validated {accepted} accepted, {rejected} rejected, {pending} still pending. "
        f"Manifest: results/manifests/{run_id}.json"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["api", "claude-code"],
        default="api",
        help="api (default): call the configured generator over its provider API. "
        "claude-code: write per-cell prompts for a coding agent to answer by hand, "
        "no API key required.",
    )
    args = parser.parse_args(argv)

    generation = require_generation_model()  # raises if unset or overlapping (RULE 5)
    table = load_divergence_table()
    cells = json.loads(STRATIFICATION_PLAN_PATH.read_text(encoding="utf-8"))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GENERATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "claude-code":
        return run_claude_code_mode(generation, table, cells)
    return run_api_mode(generation, table, cells)


if __name__ == "__main__":
    raise SystemExit(main())
