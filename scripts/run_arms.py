#!/usr/bin/env python3
"""Phase 4 evaluation harness -- runs every arm prompt against every model in

config/models.yaml's evaluation.models roster, at every seed requested.

RULE 4 (CACHE EVERYTHING): every call goes through
tb_equity.llm_client.CachingLLMClient, keyed by sha256(model + prompt +
params) -- params includes the seed, so re-running this script (after an
abort, a crash, or just to pick up where a previous invocation left off)
transparently resumes: cached (model, prompt, seed) combinations are read
from disk, not re-called.

RULE 1 (REPRODUCIBILITY): one manifest is written per seed to
results/manifests/ (a single manifest can't represent more than one
temperature/seed value under tb_equity.manifest's flat schema, so a 3-seed
run writes 3 manifests, each listing all models run at that seed).

RULE 5 (GENERATOR/EVALUATOR SEPARATION): checked via
tb_equity.config.assert_generator_evaluator_disjoint() before any call is
made, in addition to whatever check already ran when config/models.yaml was
edited -- belt and suspenders, since this is the script that would actually
spend money against the roster.

--dry-run performs no API calls and writes nothing: it loads the 400 prompts
from data/prompts/manifest.json, sums their already-computed input-token
estimates, applies an assumed output-token count per response (see
--assumed-output-tokens; this is the single biggest source of uncertainty in
the estimate, since actual completions haven't been generated yet), and
prices both against evaluation.models[].pricing_usd_per_1m from
config/models.yaml. Use this to size --budget-usd before a real run.

A real run enforces a hard budget ceiling (--budget-usd): if the running
total of newly-incurred (non-cache-hit) cost would cross it, the run stops
making new calls immediately, finishes writing manifests for what completed,
and reports what was skipped. Provider failures are logged and skipped, not
fatal -- the run continues and failures are summarized at the end.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_MANIFEST = REPO_ROOT / "data" / "prompts" / "manifest.json"
MANIFEST_DIR = REPO_ROOT / "results" / "manifests"
RUN_LOG_DIR = REPO_ROOT / "results" / "run_logs"

sys.path.insert(0, str(REPO_ROOT / "src"))

from tb_equity.config import (  # noqa: E402
    assert_generator_evaluator_disjoint,
    load_models_config,
)
from tb_equity.gitutil import git_commit_sha  # noqa: E402
from tb_equity.llm_client import CachingLLMClient, GenerationParams  # noqa: E402
from tb_equity.manifest import validate_manifest  # noqa: E402

DEFAULT_ASSUMED_OUTPUT_TOKENS = 700
DEFAULT_SEEDS = [0, 1, 2]
PROGRESS_EVERY = 500


def load_prompt_entries() -> list[dict]:
    if not PROMPTS_MANIFEST.exists():
        raise SystemExit(
            f"{PROMPTS_MANIFEST} does not exist -- run scripts/expand_arms.py first."
        )
    manifest = json.loads(PROMPTS_MANIFEST.read_text(encoding="utf-8"))
    return manifest["prompts"]


def cost_usd(*, input_tokens: int, output_tokens: int, pricing: dict) -> float:
    return (input_tokens / 1_000_000) * pricing["input"] + (
        output_tokens / 1_000_000
    ) * pricing["output"]


def dry_run(*, models: list[dict], seeds: list[int], assumed_output_tokens: int) -> float:
    entries = load_prompt_entries()
    total_input_tokens = sum(e["estimated_tokens"] for e in entries)
    n_prompts = len(entries)
    n_calls = n_prompts * len(models) * len(seeds)

    print(f"[dry-run] prompts: {n_prompts}")
    print(f"[dry-run] models: {[m['model'] for m in models]}")
    print(f"[dry-run] seeds: {seeds}")
    print(f"[dry-run] total calls (prompts x models x seeds): {n_calls}")
    print(f"[dry-run] input tokens per full pass (all 400 prompts, one model/seed): "
          f"{total_input_tokens}")
    print(f"[dry-run] assumed output tokens per response: {assumed_output_tokens} "
          "(single biggest source of uncertainty here -- no real completions exist yet)")
    print()

    grand_total = 0.0
    per_model_totals: dict[str, float] = {}
    for model_cfg in models:
        if model_cfg.get("runtime") == "colab_vllm":
            print(f"[dry-run] {model_cfg['family']}/{model_cfg['model']}: runtime=colab_vllm "
                  "-- run via notebooks/open_weight_inference.ipynb, not this script. "
                  "$0 (no API cost).")
            continue
        pricing = model_cfg.get("pricing_usd_per_1m")
        if not pricing:
            print(f"[dry-run] WARNING: no pricing_usd_per_1m for {model_cfg['model']!r} "
                  "-- skipping cost estimate for this model.")
            continue
        in_tokens = total_input_tokens * len(seeds)
        out_tokens = n_prompts * assumed_output_tokens * len(seeds)
        cost = cost_usd(input_tokens=in_tokens, output_tokens=out_tokens, pricing=pricing)
        per_model_totals[model_cfg["model"]] = cost
        grand_total += cost
        print(f"[dry-run] {model_cfg['family']}/{model_cfg['model']}: "
              f"{len(seeds)} seed(s) x {n_prompts} prompts -> "
              f"{in_tokens} input tok, {out_tokens} output tok (assumed) "
              f"-> ${cost:,.2f}")

    print()
    print(f"[dry-run] grand total estimated cost: ${grand_total:,.2f}")
    print("[dry-run] nothing written, no API calls made.")
    return grand_total


def real_run(
    *,
    models: list[dict],
    seeds: list[int],
    temperature: float,
    max_tokens: int,
    budget_usd: float,
) -> None:
    assert_generator_evaluator_disjoint()

    colab_models = [m for m in models if m.get("runtime") == "colab_vllm"]
    if colab_models:
        names = ", ".join(f"{m['family']}/{m['model']}" for m in colab_models)
        raise SystemExit(
            f"config/models.yaml lists {len(colab_models)} model(s) with "
            f"runtime=colab_vllm ({names}) -- this script calls provider APIs and has no "
            "GPU, so it cannot run them. Run notebooks/open_weight_inference.ipynb instead."
        )

    entries = load_prompt_entries()
    n_calls_total = len(entries) * len(models) * len(seeds)
    print(f"[run] {len(entries)} prompts x {len(models)} models x {len(seeds)} seeds "
          f"= {n_calls_total} calls. Hard budget ceiling: ${budget_usd:,.2f}")

    RUN_LOG_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(UTC)

    spent_usd = 0.0
    n_done = 0
    n_cache_hits = 0
    n_new_calls = 0
    failures: list[dict] = []
    aborted_on_budget = False

    for seed in seeds:
        seed_input_tokens = 0
        seed_output_tokens = 0
        seed_model_identifiers = []

        for model_cfg in models:
            if aborted_on_budget:
                break
            client = CachingLLMClient(
                family=model_cfg["family"],
                model=model_cfg["model"],
                base_url=model_cfg.get("base_url"),
                api_key_env=model_cfg.get("api_key_env"),
            )
            pricing = model_cfg.get("pricing_usd_per_1m")
            seed_model_identifiers.append(
                {
                    "family": model_cfg["family"],
                    "name": model_cfg["model"],
                    "version": model_cfg["model"],
                }
            )
            params = GenerationParams(
                temperature=temperature, top_p=1.0, max_tokens=max_tokens, seed=seed
            )

            for entry in entries:
                if aborted_on_budget:
                    break
                prompt_path = REPO_ROOT / entry["path"]
                prompt_text = prompt_path.read_text(encoding="utf-8")

                try:
                    response = client.complete(
                        system_prompt="",
                        messages=[{"role": "user", "content": prompt_text}],
                        params=params,
                    )
                except Exception as exc:  # noqa: BLE001 -- provider failures must not abort the run
                    failures.append(
                        {
                            "vignette_id": entry["vignette_id"],
                            "arm": entry["arm"],
                            "model": model_cfg["model"],
                            "seed": seed,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )
                    n_done += 1
                    continue

                seed_input_tokens += response.input_tokens
                seed_output_tokens += response.output_tokens
                if response.from_cache:
                    n_cache_hits += 1
                else:
                    n_new_calls += 1
                    if pricing:
                        spent_usd += cost_usd(
                            input_tokens=response.input_tokens,
                            output_tokens=response.output_tokens,
                            pricing=pricing,
                        )

                n_done += 1
                if n_done % PROGRESS_EVERY == 0:
                    print(
                        f"[run] {n_done}/{n_calls_total} calls "
                        f"({n_cache_hits} cache hits, {n_new_calls} new, "
                        f"{len(failures)} failures) -- spent ${spent_usd:,.2f} "
                        f"of ${budget_usd:,.2f} budget"
                    )

                if spent_usd >= budget_usd:
                    aborted_on_budget = True
                    print(
                        f"\n[run] BUDGET CEILING HIT: spent ${spent_usd:,.2f} >= "
                        f"${budget_usd:,.2f}. Stopping new calls; writing manifests "
                        "for what completed."
                    )
                    break

        run_id = f"run-arms-seed{seed}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"
        manifest = {
            "run_id": run_id,
            "model_identifiers": seed_model_identifiers,
            "temperature": temperature,
            "top_p": 1.0,
            "max_tokens": max_tokens,
            "seed": seed,
            "prompt_template_hash": _prompts_manifest_hash(),
            "vignette_set_version": "v1",
            "git_commit_sha": git_commit_sha(),
            "utc_timestamp": datetime.now(UTC).isoformat(),
            "total_input_tokens": seed_input_tokens,
            "total_output_tokens": seed_output_tokens,
        }
        problems = validate_manifest(manifest)
        assert not problems, f"manifest missing required fields: {problems}"
        MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
        (MANIFEST_DIR / f"{run_id}.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )
        print(f"[run] seed {seed}: manifest written to results/manifests/{run_id}.json")

        if aborted_on_budget:
            break

    finished_at = datetime.now(UTC)
    log = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "n_calls_total": n_calls_total,
        "n_done": n_done,
        "n_cache_hits": n_cache_hits,
        "n_new_calls": n_new_calls,
        "spent_usd": spent_usd,
        "budget_usd": budget_usd,
        "aborted_on_budget": aborted_on_budget,
        "n_failures": len(failures),
        "failures": failures,
    }
    log_path = RUN_LOG_DIR / f"run-arms-{started_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    log_path.write_text(json.dumps(log, indent=2), encoding="utf-8")

    print(f"\n[run] done: {n_done}/{n_calls_total} calls attempted "
          f"({n_cache_hits} cache hits, {n_new_calls} new calls, {len(failures)} failures)")
    print(f"[run] spent ${spent_usd:,.2f} of ${budget_usd:,.2f} budget")
    print(f"[run] failure log: {log_path}")
    if failures:
        by_model: dict[str, int] = defaultdict(int)
        for f in failures:
            by_model[f["model"]] += 1
        print(f"[run] failures by model: {dict(by_model)}")


def _prompts_manifest_hash() -> str:
    import hashlib

    return hashlib.sha256(PROMPTS_MANIFEST.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--seeds", default=",".join(str(s) for s in DEFAULT_SEEDS), help="comma-separated seeds"
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-tokens", type=int, default=1600)
    parser.add_argument(
        "--assumed-output-tokens",
        type=int,
        default=DEFAULT_ASSUMED_OUTPUT_TOKENS,
        help="dry-run only: assumed completion length per response",
    )
    parser.add_argument(
        "--budget-usd",
        type=float,
        default=None,
        help="real run only: hard ceiling, run aborts new calls once crossed",
    )
    parser.add_argument(
        "--budget-multiplier",
        type=float,
        default=3.0,
        help="if --budget-usd is not given, budget = this x the dry-run estimate",
    )
    args = parser.parse_args()

    seeds = [int(s) for s in args.seeds.split(",") if s.strip() != ""]
    config = load_models_config()
    models = config.get("evaluation", {}).get("models") or []
    if not models:
        raise SystemExit("config/models.yaml: evaluation.models is empty -- nothing to run.")

    dry_run_estimate = dry_run(
        models=models, seeds=seeds, assumed_output_tokens=args.assumed_output_tokens
    )

    if args.dry_run:
        return

    budget_usd = args.budget_usd
    if budget_usd is None:
        budget_usd = dry_run_estimate * args.budget_multiplier
        print(f"\n[run] no --budget-usd given: using {args.budget_multiplier}x the "
              f"dry-run estimate = ${budget_usd:,.2f}")

    real_run(
        models=models,
        seeds=seeds,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        budget_usd=budget_usd,
    )


if __name__ == "__main__":
    main()
