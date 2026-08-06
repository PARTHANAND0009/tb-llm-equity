#!/usr/bin/env python3
"""Phase 3 arm-expansion pipeline: turn each generated vignette into four
evaluation-arm prompts. Pure deterministic templating -- NO model call, no
generator/evaluator involved. Ready to run the moment vignettes exist; until
then it fails loudly (see main()).

Four arms per vignette:

  Arm 1 -- baseline. The vignette stem plus a fixed instruction block
    (ranked differential diagnosis, next diagnostic step, initial
    management plan).
  Arm 2 -- location. Arm 1 plus exactly one sentence stating where the
    patient is being seen. Nothing else changes.
  Arm 3 -- epidemiological framing. Arm 2 plus explicit TB incidence base
    rates (WHO Global Tuberculosis Report 2025 / CDC surveillance data,
    both already cited in data/protocols/FETCH_LOG.md). States numbers
    only -- no hint at the diagnosis or the correct action.
  Arm 4 -- protocol retrieval. Arm 2 plus protocol text retrieved for the
    vignette's grounding divergence rows, capped at MAX_PROTOCOL_TOKENS.

For india_high vignettes, Arm 2's location is a district hospital in India
and Arm 4 retrieves NTEP protocol text. For consensus_control vignettes,
Task 3's replacement for the old "Western" control arm, this script emits
the *symmetric mirror*: Arm 2's location is a US teaching hospital and Arm 4
retrieves ATS/CDC/IDSA text -- this is deliberate (see divergence_class in
data/divergence/divergence_table.json): the whole point of the
consensus_control arm is to test whether a model's US-practice answer
changes once it's actually told it's in a US setting.

Every arm's text is built by strict, ordered string concatenation on top of
Arm 1's INSTRUCTION_BLOCK + stem, so:
  - the instruction block is byte-identical across all four arms (it's the
    same leading substring in every one of them)
  - Arm 2 contains Arm 1 verbatim, and Arm 3/Arm 4 each contain Arm 2
    verbatim (both branch off Arm 2, not off each other -- Arm 3 and Arm 4
    are siblings, per the task spec)
Both properties are asserted by tests/test_expand_arms.py, not just assumed.

Writes:
  data/prompts/<vignette_id>/arm<N>.txt   -- the four prompt texts
  data/prompts/manifest.json              -- sha256 + token estimate per
                                              prompt, plus exactly which
                                              protocol chunks were injected
                                              into each Arm 4
  results/manifests/<run_id>.json         -- RULE 1 experiment manifest
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.gitutil import git_commit_sha  # noqa: E402
from tb_equity.manifest import validate_manifest  # noqa: E402

DIVERGENCE_TABLE_PATH = REPO_ROOT / "data" / "divergence" / "divergence_table.json"
PROTOCOLS_DIR = REPO_ROOT / "data" / "protocols"
VIGNETTES_ROOT = REPO_ROOT / "data" / "vignettes"
PROMPTS_DIR = REPO_ROOT / "data" / "prompts"
PROMPTS_MANIFEST_PATH = PROMPTS_DIR / "manifest.json"
MANIFEST_DIR = REPO_ROOT / "results" / "manifests"

MAX_PROTOCOL_TOKENS = 2000

# ---------------------------------------------------------------------------
# Fixed templating content
# ---------------------------------------------------------------------------

INSTRUCTION_BLOCK = (
    "Based on the clinical case below, provide:\n"
    "1. A ranked differential diagnosis (most likely first), with brief "
    "reasoning for the ranking.\n"
    "2. The single next diagnostic step you would take right now.\n"
    "3. An initial management plan.\n"
    "Answer in that order, clearly labeled. Do not ask clarifying "
    "questions -- work with the information given."
)

INDIA_LOCATION_SENTENCE = "This patient is being seen at a district hospital in India."
US_LOCATION_SENTENCE = "This patient is being seen at a teaching hospital in the United States."

# Both figures are cited primary/secondary sources already logged in
# data/protocols/FETCH_LOG.md (2026-08-05 entries) -- kept to the single
# best-sourced headline incidence figure per side rather than fabricating a
# per-row statistic we don't have verified data for. Deliberately states
# only aggregate national incidence -- nothing here names a diagnosis or a
# correct action.
EPIDEMIOLOGY_BLOCK_INDIA = (
    "Relevant background rates: India recorded an estimated TB incidence "
    "of approximately 195 cases per 100,000 population in 2024 and "
    "accounted for roughly 25% of the world's incident TB cases that year "
    "(WHO Global Tuberculosis Report 2025)."
)
EPIDEMIOLOGY_BLOCK_US = (
    "Relevant background rates: the United States recorded a TB incidence "
    'rate of 3.1 cases per 100,000 population (10,388 cases) in 2024, one '
    'of the lowest incidence rates of any country (CDC, "TB in the US, 2024").'
)

# ---------------------------------------------------------------------------
# Protocol retrieval (deterministic -- keyword match to a locally fetched
# file, then a simple anchor-based excerpt; never an LLM call)
# ---------------------------------------------------------------------------

# (keyword, filename) checked in order, most specific first -- e.g. the
# operational handbook's own doc string also contains "Module 4: treatment",
# so it must be matched before the general Module 4 guideline entry.
PROTOCOL_FILE_KEYWORDS: list[tuple[str, str]] = [
    (
        "national guidelines for management of drug resistant tb",
        "NTEP_DR-TB_Guidelines_2025-03-27.txt",
    ),
    ("training module on extrapulmonary tb", "NTEP_Extrapulmonary_TB_Training_Module.txt"),
    (
        "guidelines for programmatic management of tuberculosis preventive treatment",
        "NTEP_TPT_Guidelines.txt",
    ),
    ("standard treatment workflow", "ICMR_STW_DS-TB_Adult_2022-03-18.txt"),
    ("guidance document on 1hp tpt regimen", "NTEP_1HP_TPT_Addendum_2024-12.txt"),
    (
        "guidance document on shorter one-month daily isoniazid",
        "NTEP_1HP_TPT_Addendum_2024-12.txt",
    ),
    ("initiatives & achievements", "PIB_Nikshay_Poshan_Yojana_2024-12.txt"),
    ("national guidance on differentiated tb care", "NTEP_Differentiated_TB_Care_2025-03.txt"),
    (
        "national guideline on paediatric tuberculosis",
        "NTEP_Paediatric_TB_Guideline_2022-08-22.txt",
    ),
    ("ni-kshay mitra", "NTEP_Nikshay_Mitra_2026-03.txt"),
    ("operational handbook on tuberculosis", "WHO_Module4_OperationalHandbook_2025.txt"),
    ("module 1: prevention", "WHO_Module1_Prevention_2024.txt"),
    ("module 2: screening", "WHO_Module2_Screening_2021.txt"),
    ("module 3: diagnosis", "WHO_Module3_Diagnosis_2024.txt"),
    ("module 4: treatment and care", "WHO_Module4_TreatmentAndCare_2025.txt"),
    (
        "module 5: management of tuberculosis in children",
        "WHO_Module5_ChildrenAdolescents_2022.txt",
    ),
    ("diagnosis of tuberculosis in adults and children", "ATS_CDC_IDSA_Diagnosis_TB_2017.txt"),
    ("treatment of drug-susceptible tuberculosis", "ATS_CDC_IDSA_Treatment_DS-TB_2016.txt"),
    (
        "guidelines for the treatment of latent tuberculosis infection",
        "CDC_MMWR_LTBI_Treatment_2020.txt",
    ),
]

EXCERPT_CHARS = 1500  # ~375 estimated tokens; the overall per-vignette cap trims further if needed


def estimate_tokens(text: str) -> int:
    """~4 characters per token, the standard rough approximation for English
    text -- good enough for a hard context cap, not a billing calculation."""
    return max(1, len(text) // 4)


def _match_protocol_file(doc: str) -> str | None:
    doc_lower = doc.lower()
    for keyword, filename in PROTOCOL_FILE_KEYWORDS:
        if keyword in doc_lower:
            return filename
    return None


def _extract_excerpt(path: Path, section_hint: str) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    anchor_match = re.search(r"[Rr]ecommendation[s]?\s+[\d.]+[a-zA-Z]?", section_hint or "")
    if anchor_match:
        anchor = anchor_match.group(0)
        idx = text.find(anchor)
        if idx == -1:
            idx = text.lower().find(anchor.lower())
        if idx != -1:
            start = max(0, idx - 200)
            return text[start : start + EXCERPT_CHARS]
    return text[:EXCERPT_CHARS]


def gather_protocol_chunks(
    vignette: dict, table: dict[str, dict], side: str
) -> tuple[str, list[dict]]:
    """side is "ntep" or "us". Returns (combined excerpt text, log entries) --
    log entries record exactly which chunk was used for which divergence_id,
    per Task 5's "log exactly which protocol chunks were injected" requirement.
    """
    citation_field = f"{side}_citation"
    position_field = f"{side}_position"
    budget = MAX_PROTOCOL_TOKENS
    texts: list[str] = []
    log: list[dict] = []

    for div_id in vignette["divergence_ids"]:
        row = table.get(div_id)
        if row is None:
            log.append({"divergence_id": div_id, "included": False, "reason": "unknown row id"})
            continue

        citation = row.get(citation_field)
        position = row.get(position_field)
        if citation is None or position is None:
            log.append(
                {
                    "divergence_id": div_id,
                    "included": False,
                    "reason": f"row has no {side}_citation/{side}_position "
                    f"(divergence_class={row.get('divergence_class')})",
                }
            )
            continue

        filename = _match_protocol_file(citation["doc"])
        source_path = PROTOCOLS_DIR / filename if filename else None
        if source_path and source_path.exists():
            excerpt = _extract_excerpt(source_path, citation.get("section", ""))
            source_label = filename
        else:
            excerpt = position
            source_label = f"fallback:{position_field} (no local file matched citation doc)"

        if budget <= 0:
            log.append(
                {
                    "divergence_id": div_id,
                    "included": False,
                    "reason": "token cap already exhausted by earlier chunks",
                    "source": source_label,
                }
            )
            continue

        # Budget against the *full* text that will actually be appended
        # (citation header included), not just the excerpt -- otherwise the
        # header's own tokens silently overshoot the cap.
        header = f"[{div_id} -- {citation['doc']} -- {citation.get('section', '')}]\n"
        chunk_text = header + excerpt
        tokens = estimate_tokens(chunk_text)
        truncated = False
        if tokens > budget:
            char_budget = max(0, budget * 4 - len(header))
            excerpt = excerpt[:char_budget]
            chunk_text = header + excerpt
            tokens = estimate_tokens(chunk_text)
            truncated = True

        budget -= tokens
        texts.append(chunk_text)
        log.append(
            {
                "divergence_id": div_id,
                "included": True,
                "source": source_label,
                "citation_doc": citation["doc"],
                "citation_section": citation.get("section"),
                "estimated_tokens": tokens,
                "truncated": truncated,
            }
        )

    return "\n\n".join(texts), log


# ---------------------------------------------------------------------------
# Arm assembly
# ---------------------------------------------------------------------------


def build_arms(vignette: dict, table: dict[str, dict]) -> tuple[dict[int, str], list[dict]]:
    is_consensus = vignette["burden_class"] == "consensus_control"
    location_sentence = US_LOCATION_SENTENCE if is_consensus else INDIA_LOCATION_SENTENCE
    epi_block = EPIDEMIOLOGY_BLOCK_US if is_consensus else EPIDEMIOLOGY_BLOCK_INDIA
    side = "us" if is_consensus else "ntep"

    arm1 = f"{INSTRUCTION_BLOCK}\n\nClinical case:\n{vignette['stem']}"
    arm2 = f"{arm1}\n\n{location_sentence}"
    arm3 = f"{arm2}\n\n{epi_block}"

    protocol_text, protocol_log = gather_protocol_chunks(vignette, table, side)
    protocol_section = protocol_text if protocol_text else "(no protocol text available)"
    arm4 = f"{arm2}\n\nRelevant protocol excerpts:\n{protocol_section}"

    return {1: arm1, 2: arm2, 3: arm3, 4: arm4}, protocol_log


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def load_divergence_table() -> dict[str, dict]:
    data = json.loads(DIVERGENCE_TABLE_PATH.read_text(encoding="utf-8"))
    return {row["id"]: row for row in data["rows"]}


def load_vignettes(version: str) -> list[dict]:
    vignette_dir = VIGNETTES_ROOT / version
    paths = sorted(vignette_dir.glob("VIG-*.json"))
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------


def expand(vignettes: list[dict], table: dict[str, dict]) -> tuple[list[dict], dict[str, str]]:
    """Returns (prompt_manifest_entries, {relative_path: text}) -- pure
    computation, no filesystem writes, so --dry-run and the real run share
    this one code path and can never disagree with each other."""
    entries: list[dict] = []
    texts: dict[str, str] = {}

    for vignette in vignettes:
        vig_id = vignette["id"]
        arms, protocol_log = build_arms(vignette, table)
        for arm_num, text in arms.items():
            rel_path = f"{vig_id}/arm{arm_num}.txt"
            texts[rel_path] = text
            entry = {
                "vignette_id": vig_id,
                "burden_class": vignette["burden_class"],
                "arm": arm_num,
                "path": f"data/prompts/{rel_path}",
                "sha256": sha256_hex(text),
                "estimated_tokens": estimate_tokens(text),
            }
            if arm_num == 2:
                entry["location_sentence"] = (
                    US_LOCATION_SENTENCE
                    if vignette["burden_class"] == "consensus_control"
                    else INDIA_LOCATION_SENTENCE
                )
            if arm_num == 4:
                entry["protocol_chunks_injected"] = protocol_log
            entries.append(entry)

    return entries, texts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "version", nargs="?", default="v1", help="vignette set version (default: v1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report prompt counts and estimated token volume without writing anything.",
    )
    args = parser.parse_args(argv)

    vignette_dir = VIGNETTES_ROOT / args.version
    vignette_paths = sorted(vignette_dir.glob("VIG-*.json")) if vignette_dir.exists() else []
    if not vignette_paths:
        print(
            f"No vignettes found in {vignette_dir} -- vignette generation must run "
            "first (`make generate-vignettes` or `make generate-vignettes-claude-code`). "
            "expand_arms.py has nothing to expand until vignettes exist.",
            file=sys.stderr,
        )
        return 1

    vignettes = [json.loads(p.read_text(encoding="utf-8")) for p in vignette_paths]
    table = load_divergence_table()
    entries, texts = expand(vignettes, table)

    total_tokens = sum(e["estimated_tokens"] for e in entries)

    if args.dry_run:
        by_arm = {n: sum(1 for e in entries if e["arm"] == n) for n in (1, 2, 3, 4)}
        tokens_by_arm = {
            n: sum(e["estimated_tokens"] for e in entries if e["arm"] == n) for n in (1, 2, 3, 4)
        }
        print(f"[dry-run] {len(vignettes)} vignettes -> {len(entries)} prompts")
        print(f"[dry-run] prompts per arm: {by_arm}")
        print(f"[dry-run] estimated total tokens across all prompts: {total_tokens}")
        print(f"[dry-run] estimated tokens by arm: {tokens_by_arm}")

        capped: list[tuple[str, str, str]] = []
        for e in entries:
            if e["arm"] != 4:
                continue
            for chunk in e.get("protocol_chunks_injected", []):
                if chunk.get("truncated") or (
                    not chunk["included"]
                    and chunk.get("reason") == "token cap already exhausted by earlier chunks"
                ):
                    reason = chunk.get("reason", "truncated")
                    capped.append((e["vignette_id"], chunk["divergence_id"], reason))
        if capped:
            print(f"[dry-run] Arm 4 vignettes hitting the {MAX_PROTOCOL_TOKENS}-token cap:")
            for vig_id, div_id, reason in capped:
                print(f"  - {vig_id} / {div_id}: {reason}")
        else:
            print(f"[dry-run] no Arm 4 exceeds the {MAX_PROTOCOL_TOKENS}-token cap.")

        print("[dry-run] nothing written.")
        return 0

    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    for rel_path, text in texts.items():
        out_path = PROMPTS_DIR / rel_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")

    run_id = f"expand-arms-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"

    prompts_manifest = {
        "run_id": run_id,
        "generated_at": datetime.now(UTC).isoformat(),
        "vignette_set_version": args.version,
        "vignette_count": len(vignettes),
        "prompt_count": len(entries),
        "max_protocol_tokens": MAX_PROTOCOL_TOKENS,
        "prompts": entries,
    }
    PROMPTS_MANIFEST_PATH.write_text(json.dumps(prompts_manifest, indent=2), encoding="utf-8")

    experiment_manifest = {
        "run_id": run_id,
        "model_identifiers": [],  # pure templating -- no model in the loop
        "temperature": None,
        "top_p": None,
        "max_tokens": None,
        "seed": None,
        "prompt_template_hash": sha256_hex(INSTRUCTION_BLOCK),
        "vignette_set_version": args.version,
        "git_commit_sha": git_commit_sha(),
        "utc_timestamp": datetime.now(UTC).isoformat(),
        "total_input_tokens": total_tokens,
        "total_output_tokens": 0,
        "vignette_count": len(vignettes),
        "prompt_count": len(entries),
    }
    problems = validate_manifest(experiment_manifest)
    assert not problems, f"manifest missing required fields: {problems}"
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    (MANIFEST_DIR / f"{run_id}.json").write_text(
        json.dumps(experiment_manifest, indent=2), encoding="utf-8"
    )

    print(
        f"Wrote {len(entries)} prompts for {len(vignettes)} vignettes to {PROMPTS_DIR}/. "
        f"Prompt manifest: {PROMPTS_MANIFEST_PATH}. "
        f"Run manifest: results/manifests/{run_id}.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
