"""Manifest schema for RULE 1 — REPRODUCIBILITY.

Every experiment run must write results/manifests/<run_id>.json containing
all of REQUIRED_MANIFEST_FIELDS. This module only defines and validates the
schema; nothing here writes a manifest yet (no experiment code has been
written).
"""

REQUIRED_MANIFEST_FIELDS = (
    "run_id",
    "model_identifiers",  # list of {family, name, version} — every model+version string involved
    "temperature",
    "top_p",
    "max_tokens",
    "seed",
    "prompt_template_hash",  # sha256
    "vignette_set_version",
    "git_commit_sha",
    "utc_timestamp",
    "total_input_tokens",
    "total_output_tokens",
)


def validate_manifest(manifest: dict) -> list[str]:
    """Return a list of problems with `manifest`; empty list means valid."""
    problems = []
    for field in REQUIRED_MANIFEST_FIELDS:
        if field not in manifest:
            problems.append(f"missing required field: {field}")
    return problems
