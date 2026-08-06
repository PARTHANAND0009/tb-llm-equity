#!/usr/bin/env python3
"""Generates notebooks/open_weight_inference.ipynb. Run once to (re)build

the notebook from the cell source below -- easier to review/edit as Python
strings than as raw notebook JSON. Not part of the pipeline; a build tool
for this one file.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = REPO_ROOT / "notebooks" / "open_weight_inference.ipynb"


def md(*lines: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": _src(lines)}


def code(*lines: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": _src(lines),
    }


def _src(lines: tuple[str, ...]) -> list[str]:
    text = "\n".join(lines)
    out = [line + "\n" for line in text.split("\n")]
    if out:
        out[-1] = out[-1].rstrip("\n")
    return out


CELLS = []

# ---------------------------------------------------------------------------
CELLS.append(md(
    "# Open-weight Phase 4 inference (tb-llm-equity)",
    "",
    "Runs the 400 Phase-3 arm prompts through four open-weight models, fully local"
    " (vLLM on a Colab T4), zero API cost. See `results/PREREGISTRATION.md`"
    " Amendments (2026-08-06, open-weight pivot) for why: zero compute budget"
    " authorized, single seed at temperature 0, 4-bit quantization throughout.",
    "",
    "**Two phases, in order -- do not skip the gate between them:**",
    "",
    "1. **Pilot** (Task A): 20 stratified prompts (5 vignettes x 4 arms) through"
    " Llama-3.1-8B-Instruct, then the same 20 through Meditron3-8B. Reports real"
    " measured output-token stats, throughput, response parseability, and a"
    " corrected full-run ETA -- the planning-time 700-tokens/response assumption"
    " was never validated against a real completion, and this is where that"
    " happens, before you commit hours to the full run.",
    "2. **Full run** (Task B): all 4 models x 400 prompts x 1 seed. Checkpoints to"
    " Drive after **every single response**, not per-batch -- free Colab"
    " disconnects without warning, and a lost session should cost you minutes of"
    " re-warmup, not hours of regenerated work. Resumable: re-running this"
    " notebook after a disconnect skips every response already checkpointed.",
    "",
    "**What was and wasn't tested before you run this.** The checkpoint/resume"
    " logic (`src/tb_equity/checkpoint.py`) and the response-parseability heuristic"
    " (`src/tb_equity/response_format.py`) are unit-tested against a stub generator"
    " in `tests/test_checkpoint.py` / `tests/test_response_format.py` -- including a"
    " simulated mid-write kill. **The vLLM/model-loading cells below have not been"
    " run against a real GPU** -- this environment had no GPU or Colab execution"
    " channel available when this notebook was built. Standard, stable vLLM APIs"
    " are used throughout, but treat the first full run of each cell as the actual"
    " first test of it.",
))

# ---------------------------------------------------------------------------
CELLS.append(md("## 1. Install dependencies"))
CELLS.append(code(
    "!pip install -q vllm transformers accelerate bitsandbytes huggingface_hub pyyaml",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 2. Mount Drive and locate the repo",
    "",
    "Checkpoints always go to Drive (`DRIVE_ROOT`), regardless of where the repo"
    " itself comes from, so they survive a disconnect even if the repo was"
    " git-cloned into ephemeral `/content` storage.",
    "",
    "Set exactly one of `REPO_SOURCE` (a git remote URL, if you've pushed this repo"
    " somewhere) or sync the repo folder into `DRIVE_ROOT` yourself before running"
    " this cell -- this repo had no git remote configured when this notebook was"
    " built (`git remote -v` was empty), so a Drive sync is the default path.",
))
CELLS.append(code(
    "from google.colab import drive",
    "drive.mount('/content/drive')",
))
CELLS.append(code(
    "from pathlib import Path",
    "",
    "DRIVE_ROOT = Path('/content/drive/MyDrive/tb-llm-equity')  # adjust if you synced elsewhere",
    "REPO_SOURCE = None  # e.g. 'https://github.com/you/tb-llm-equity.git' -- leave None to use DRIVE_ROOT directly",
    "",
    "if REPO_SOURCE:",
    "    import subprocess",
    "    subprocess.run(['git', 'clone', REPO_SOURCE, '/content/repo'], check=True)",
    "    REPO_DIR = Path('/content/repo')",
    "else:",
    "    REPO_DIR = DRIVE_ROOT",
    "",
    "assert REPO_DIR.exists(), (",
    "    f'{REPO_DIR} not found -- sync the repo into your Drive at this path, '",
    "    'or set REPO_SOURCE to a git URL above.'",
    ")",
    "",
    "PROMPTS_DIR = REPO_DIR / 'data' / 'prompts'",
    "MODELS_CONFIG_PATH = REPO_DIR / 'config' / 'models.yaml'",
    "VIGNETTES_DIR = REPO_DIR / 'data' / 'vignettes' / 'v1'",
    "assert PROMPTS_DIR.exists(), f'{PROMPTS_DIR} not found -- run scripts/expand_arms.py in the main repo first.'",
    "",
    "# Checkpoints and final responses ALWAYS go to Drive directly, independent of REPO_SOURCE.",
    "RESPONSES_DIR = DRIVE_ROOT / 'data' / 'responses'",
    "MANIFEST_DIR = DRIVE_ROOT / 'results' / 'manifests'",
    "RESPONSES_DIR.mkdir(parents=True, exist_ok=True)",
    "MANIFEST_DIR.mkdir(parents=True, exist_ok=True)",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 3. Import tb_equity (checkpoint/resume + parseability + cache addressing)",
    "",
    "Reuses the exact, unit-tested modules from the main repo rather than"
    " duplicating their logic in notebook cells -- `cache_key_for` also makes the"
    " checkpoint filenames byte-identical to what `CachingLLMClient` would have"
    " produced for the same (model, prompt, params), so the Phase 5 scorer never"
    " needs to know which path -- API or this notebook -- produced a given file.",
))
CELLS.append(code(
    "import sys",
    "sys.path.insert(0, str(REPO_DIR / 'src'))",
    "",
    "import yaml",
    "",
    "from tb_equity.checkpoint import (",
    "    checkpoint_path,",
    "    load_completed_keys,",
    "    pending_keys,",
    "    write_response_atomic,",
    ")",
    "from tb_equity.llm_client import GenerationParams, cache_key_for",
    "from tb_equity.response_format import check_parseable",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 4. HuggingFace login",
    "",
    "Two of the four models need a token that has **accepted the model's license**"
    " on huggingface.co before download will work:",
    "",
    "- `meta-llama/Llama-3.1-8B-Instruct` -- manually gated (visit the model page,"
    " request access, wait for approval). The AWQ checkpoint we actually load"
    " (`hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4`) is itself ungated, but"
    " vLLM still needs the base tokenizer/config which may reference the gated repo.",
    "- `EPFLiGHT/Meditron3-8B` -- auto-gated (accept terms on the model page, access"
    " is granted immediately).",
    "",
    "Store your token as a Colab secret named `HF_TOKEN` (key icon in the left"
    " sidebar), not hardcoded here.",
))
CELLS.append(code(
    "from google.colab import userdata",
    "from huggingface_hub import login",
    "",
    "login(token=userdata.get('HF_TOKEN'))",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 5. Model registry (from config/models.yaml -- single source of truth)",
))
CELLS.append(code(
    "with open(MODELS_CONFIG_PATH, encoding='utf-8') as f:",
    "    models_cfg = yaml.safe_load(f)",
    "",
    "MODEL_REGISTRY = [m for m in models_cfg['evaluation']['models'] if m.get('runtime') == 'colab_vllm']",
    "assert len(MODEL_REGISTRY) == 4, f'expected 4 open-weight models, found {len(MODEL_REGISTRY)}'",
    "",
    "for m in MODEL_REGISTRY:",
    "    print(f\"{m['family']:8s} {m['model']:55s} rev={m['revision'][:12]} quant={m['quantization']}\")",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 6. Load the 400 prompts and build the stratified 20-prompt pilot sample",
    "",
    "5 vignettes (one per `presentation_type`, deterministically the lowest"
    " `VIG-id` in each stratum) x 4 arms = 20 prompts, per Task A.",
))
CELLS.append(code(
    "import json",
    "",
    "prompts_manifest = json.loads((PROMPTS_DIR / 'manifest.json').read_text(encoding='utf-8'))",
    "all_entries = prompts_manifest['prompts']  # 400: vignette_id, arm, path, sha256, estimated_tokens, burden_class",
    "assert len(all_entries) == 400",
    "",
    "vignette_meta = {}",
    "for p in VIGNETTES_DIR.glob('VIG-*.json'):",
    "    v = json.loads(p.read_text(encoding='utf-8'))",
    "    vignette_meta[v['id']] = v",
    "",
    "by_type: dict[str, list[str]] = {}",
    "for vid, v in vignette_meta.items():",
    "    by_type.setdefault(v['presentation_type'], []).append(vid)",
    "",
    "PILOT_VIGNETTE_IDS = sorted(min(ids) for ids in by_type.values())  # deterministic, 1 per type",
    "print('Pilot vignettes (1 per presentation_type):', PILOT_VIGNETTE_IDS)",
    "assert len(PILOT_VIGNETTE_IDS) == 5, f'expected 5 presentation types, got {len(PILOT_VIGNETTE_IDS)}: {sorted(by_type)}'",
    "",
    "PILOT_ENTRIES = [e for e in all_entries if e['vignette_id'] in PILOT_VIGNETTE_IDS]",
    "assert len(PILOT_ENTRIES) == 20, f'expected 20 pilot prompts, got {len(PILOT_ENTRIES)}'",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 7. vLLM helpers",
    "",
    "`EPFLiGHT/Meditron3-8B` has no pre-quantized AWQ checkpoint on the Hub (checked"
    " 2026-08-06 -- searched, none found), so it loads via on-the-fly bitsandbytes"
    " NF4 quantization instead of a pre-quantized AWQ repo; the other three load"
    " pre-quantized AWQ checkpoints directly.",
))
CELLS.append(code(
    "import gc",
    "import time",
    "",
    "import torch",
    "from vllm import LLM, SamplingParams",
    "",
    "GENERATION_MAX_TOKENS = 1600  # matches config/models.yaml generation.max_tokens",
    "",
    "",
    "def load_vllm_model(model_cfg: dict) -> LLM:",
    "    kwargs = dict(",
    "        model=model_cfg['model'],",
    "        revision=model_cfg['revision'],",
    "        dtype='float16',",
    "        gpu_memory_utilization=0.85,",
    "        max_model_len=4096,  # comfortably covers the longest Arm 4 prompt (~2500 tok) + output",
    "    )",
    "    if model_cfg['quantization'] == 'bitsandbytes-nf4':",
    "        kwargs['quantization'] = 'bitsandbytes'",
    "        kwargs['load_format'] = 'bitsandbytes'",
    "    else:",
    "        kwargs['quantization'] = 'awq'",
    "    return LLM(**kwargs)",
    "",
    "",
    "def unload_vllm_model(llm: LLM) -> None:",
    "    del llm",
    "    gc.collect()",
    "    torch.cuda.empty_cache()",
    "",
    "",
    "def read_prompt_text(entry: dict) -> str:",
    "    rel = entry['path'].removeprefix('data/prompts/')",
    "    return (PROMPTS_DIR / rel).read_text(encoding='utf-8')",
    "",
    "",
    "def generate_batch(llm: LLM, entries: list[dict], temperature: float = 0.0):",
    "    sampling_params = SamplingParams(",
    "        temperature=temperature, top_p=1.0, max_tokens=GENERATION_MAX_TOKENS,",
    "    )",
    "    prompts = [read_prompt_text(e) for e in entries]",
    "    start = time.time()",
    "    outputs = llm.generate(prompts, sampling_params)",
    "    elapsed = time.time() - start",
    "    return outputs, elapsed",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 8. TASK A -- Pilot: Meta-Llama-3.1-8B-Instruct",
    "",
    "Real measured numbers, not the planning-time 700-token assumption.",
))
CELLS.append(code(
    "llama_cfg = next(m for m in MODEL_REGISTRY if m['family'] == 'meta')",
    "print(f\"=== PILOT: {llama_cfg['model']} ===\")",
    "",
    "llm = load_vllm_model(llama_cfg)",
    "outputs, elapsed = generate_batch(llm, PILOT_ENTRIES)",
    "",
    "output_token_counts = [len(o.outputs[0].token_ids) for o in outputs]",
    "texts = [o.outputs[0].text for o in outputs]",
    "",
    "mean_out = sum(output_token_counts) / len(output_token_counts)",
    "max_out = max(output_token_counts)",
    "throughput = sum(output_token_counts) / elapsed",
    "",
    "print(f'Mean output tokens/response: {mean_out:.1f}')",
    "print(f'Max output tokens/response: {max_out}')",
    "print(f'Wall time for 20 prompts: {elapsed:.1f}s')",
    "print(f'Aggregate throughput: {throughput:.1f} tok/s (batched, T4)')",
    "",
    "parse_results = [check_parseable(t) for t in texts]",
    "n_parseable = sum(r.parseable for r in parse_results)",
    "print(f'Parseable: {n_parseable}/{len(texts)}')",
    "for e, r in zip(PILOT_ENTRIES, parse_results):",
    "    if not r.parseable:",
    "        print(f\"  NOT PARSEABLE: {e['vignette_id']} arm{e['arm']}: {r.reason}\")",
    "",
    "llama_full_run_eta_min = (400 * mean_out / throughput) / 60",
    "print(f'Corrected full-run (400 prompts) ETA for this model, using MEASURED throughput: {llama_full_run_eta_min:.1f} min')",
    "print(f\"(Planning-time estimate assumed 700 tok/response at ~43 tok/s single-stream = ~2.0h unbatched; \"",
    "      f\"compare against the measured number above, not the planning assumption.)\")",
    "",
    "unload_vllm_model(llm)",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 9. TASK A -- Pilot: Meditron3-8B",
    "",
    "Continued-pretrained models sometimes degrade at instruction-following"
    " relative to their base -- if this comes back with a much lower parseable"
    " rate than Llama's, that needs to be known now, not at hour six of the full"
    " run.",
))
CELLS.append(code(
    "meditron_cfg = next(m for m in MODEL_REGISTRY if m['family'] == 'epfl')",
    "print(f\"=== PILOT: {meditron_cfg['model']} ===\")",
    "",
    "llm = load_vllm_model(meditron_cfg)",
    "outputs, elapsed = generate_batch(llm, PILOT_ENTRIES)",
    "",
    "meditron_output_token_counts = [len(o.outputs[0].token_ids) for o in outputs]",
    "meditron_texts = [o.outputs[0].text for o in outputs]",
    "",
    "meditron_mean_out = sum(meditron_output_token_counts) / len(meditron_output_token_counts)",
    "meditron_throughput = sum(meditron_output_token_counts) / elapsed",
    "",
    "print(f'Mean output tokens/response: {meditron_mean_out:.1f}')",
    "print(f'Max output tokens/response: {max(meditron_output_token_counts)}')",
    "print(f'Wall time for 20 prompts: {elapsed:.1f}s')",
    "print(f'Aggregate throughput: {meditron_throughput:.1f} tok/s (batched, T4)')",
    "",
    "meditron_parse_results = [check_parseable(t) for t in meditron_texts]",
    "meditron_n_parseable = sum(r.parseable for r in meditron_parse_results)",
    "print(f'Parseable: {meditron_n_parseable}/{len(meditron_texts)}')",
    "for e, r in zip(PILOT_ENTRIES, meditron_parse_results):",
    "    if not r.parseable:",
    "        print(f\"  NOT PARSEABLE: {e['vignette_id']} arm{e['arm']}: {r.reason}\")",
    "",
    "if meditron_n_parseable < n_parseable:",
    "    print()",
    "    print(f'*** WARNING: Meditron3-8B parseable rate ({meditron_n_parseable}/20) is LOWER than '",
    "          f'Llama-3.1-8B-Instruct ({n_parseable}/20). This is the exact instruction-following '",
    "          f'degradation risk flagged before running -- inspect meditron_texts by hand before '",
    "          f'committing to the full run for this model. ***')",
    "",
    "meditron_full_run_eta_min = (400 * meditron_mean_out / meditron_throughput) / 60",
    "print(f'Corrected full-run ETA for this model: {meditron_full_run_eta_min:.1f} min')",
    "",
    "unload_vllm_model(llm)",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## STOP -- read the pilot report above before continuing",
    "",
    "Confirm before proceeding to the full run (Task B):",
    "",
    "- Mean/max output tokens are in a sane range (not near `GENERATION_MAX_TOKENS`,"
    " which would mean responses are being truncated).",
    "- Parseable rate is high (ideally 20/20) for both models. If Meditron's is"
    " meaningfully lower, read `meditron_texts` by hand -- it may need a different"
    " parsing strategy downstream, not a rerun.",
    "- The corrected ETA (measured throughput, not the planning-time 700-token"
    " guess) times 4 models fits your session-time budget.",
    "",
    "Once satisfied, set `PILOT_APPROVED = True` in the next cell to unlock the full"
    " run -- this is a deliberate gate, not a formality.",
))
CELLS.append(code(
    "PILOT_APPROVED = False  # <-- change to True only after reading the pilot report above",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 10. TASK B -- Full run: all 4 models x 400 prompts x 1 seed",
    "",
    "Single seed at temperature 0 (see `results/PREREGISTRATION.md` Amendments,"
    " open-weight pivot -- zero compute budget is the reason, not a methodological"
    " preference). Checkpoints after every response; resumable; identical JSON"
    " shape to the API-path cache; one RULE 1 manifest per model.",
))
CELLS.append(code(
    "assert PILOT_APPROVED, 'Set PILOT_APPROVED = True in the cell above after reading the pilot report.'",
    "",
    "SEED = 0",
    "TEMPERATURE = 0.0",
    "PROGRESS_EVERY = 25  # 400 prompts/model -- more frequent than the API harness's 500, since a model-local run is much shorter",
))
CELLS.append(code(
    "import hashlib",
    "import subprocess",
    "from datetime import UTC, datetime",
    "",
    "",
    "def repo_git_commit_sha() -> str:",
    "    try:",
    "        return subprocess.check_output(",
    "            ['git', 'rev-parse', 'HEAD'], cwd=REPO_DIR, text=True",
    "        ).strip()",
    "    except Exception:",
    "        return 'unknown'",
    "",
    "",
    "def prompts_manifest_hash() -> str:",
    "    return hashlib.sha256((PROMPTS_DIR / 'manifest.json').read_bytes()).hexdigest()",
    "",
    "",
    "def run_model_full(model_cfg: dict) -> None:",
    "    family = model_cfg['family']",
    "    print(f\"\\n=== FULL RUN: {family}/{model_cfg['model']} ===\")",
    "",
    "    all_keys = [",
    "        cache_key_for(",
    "            family=family,",
    "            model=model_cfg['model'],",
    "            system_prompt='',",
    "            messages=[{'role': 'user', 'content': read_prompt_text(e)}],",
    "            params=GenerationParams(",
    "                temperature=TEMPERATURE, top_p=1.0, max_tokens=GENERATION_MAX_TOKENS, seed=SEED",
    "            ),",
    "        )",
    "        for e in all_entries",
    "    ]",
    "    key_to_entry = dict(zip(all_keys, all_entries))",
    "",
    "    todo = pending_keys(all_keys, RESPONSES_DIR)",
    "    already_done = len(all_keys) - len(todo)",
    "    print(f'{already_done}/{len(all_keys)} already checkpointed (resuming)' if already_done",
    "          else f'0/{len(all_keys)} checkpointed -- starting fresh')",
    "    if not todo:",
    "        print('Nothing to do for this model.')",
    "        return",
    "",
    "    llm = load_vllm_model(model_cfg)",
    "    total_input_tokens = 0",
    "    total_output_tokens = 0",
    "    start = time.time()",
    "",
    "    sampling_params = SamplingParams(",
    "        temperature=TEMPERATURE, top_p=1.0, max_tokens=GENERATION_MAX_TOKENS,",
    "    )",
    "",
    "    for i, key in enumerate(todo, start=1):",
    "        entry = key_to_entry[key]",
    "        prompt_text = read_prompt_text(entry)",
    "        [output] = llm.generate([prompt_text], sampling_params, use_tqdm=False)",
    "",
    "        response_text = output.outputs[0].text",
    "        in_tok = len(output.prompt_token_ids)",
    "        out_tok = len(output.outputs[0].token_ids)",
    "        total_input_tokens += in_tok",
    "        total_output_tokens += out_tok",
    "",
    "        write_response_atomic(",
    "            RESPONSES_DIR,",
    "            key,",
    "            text=response_text,",
    "            raw={",
    "                'vignette_id': entry['vignette_id'],",
    "                'arm': entry['arm'],",
    "                'model': model_cfg['model'],",
    "                'model_revision': model_cfg['revision'],",
    "                'quantization': model_cfg['quantization'],",
    "                'seed': SEED,",
    "                'finish_reason': output.outputs[0].finish_reason,",
    "            },",
    "            input_tokens=in_tok,",
    "            output_tokens=out_tok,",
    "        )",
    "",
    "        if i % PROGRESS_EVERY == 0 or i == len(todo):",
    "            elapsed = time.time() - start",
    "            rate = i / elapsed if elapsed > 0 else 0",
    "            remaining = (len(todo) - i) / rate if rate > 0 else float('inf')",
    "            print(f'  {i}/{len(todo)} done, {elapsed/60:.1f}min elapsed, '",
    "                  f'ETA {remaining/60:.1f}min remaining')",
    "",
    "    unload_vllm_model(llm)",
    "",
    "    # RULE 1 manifest -- one per model, since a Colab run is naturally sequential",
    "    # per model (VRAM constraints preclude loading more than one 8B model at once).",
    "    run_id = f\"open-weight-{family}-seed{SEED}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}\"",
    "    manifest = {",
    "        'run_id': run_id,",
    "        'model_identifiers': [{",
    "            'family': family,",
    "            'name': model_cfg['model'],",
    "            'version': model_cfg['revision'],",
    "        }],",
    "        'temperature': TEMPERATURE,",
    "        'top_p': 1.0,",
    "        'max_tokens': GENERATION_MAX_TOKENS,",
    "        'seed': SEED,",
    "        'prompt_template_hash': prompts_manifest_hash(),",
    "        'vignette_set_version': 'v1',",
    "        'git_commit_sha': repo_git_commit_sha(),",
    "        'utc_timestamp': datetime.now(UTC).isoformat(),",
    "        'total_input_tokens': total_input_tokens,",
    "        'total_output_tokens': total_output_tokens,",
    "        'quantization': model_cfg['quantization'],",
    "        'base_model': model_cfg['base_model'],",
    "        'base_model_revision': model_cfg['base_model_revision'],",
    "        'n_responses_this_run': len(todo),",
    "        'n_responses_total': len(all_keys),",
    "    }",
    "    (MANIFEST_DIR / f'{run_id}.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')",
    "    print(f'Manifest written: {run_id}.json')",
))
CELLS.append(code(
    "for model_cfg in MODEL_REGISTRY:",
    "    run_model_full(model_cfg)",
    "",
    "print('\\nAll models done (or resumed to completion).')",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 11. Post-run sanity check",
    "",
    "Confirms every (model, prompt) pair produced exactly one checkpointed"
    " response, before you copy `data/responses/` and `results/manifests/` back"
    " into the main repo.",
))
CELLS.append(code(
    "expected = len(MODEL_REGISTRY) * len(all_entries)  # models x 400, single seed",
    "actual = len(load_completed_keys(RESPONSES_DIR))",
    "print(f'Expected {expected} responses (4 models x 400 prompts x 1 seed), found {actual} checkpointed.')",
    "",
    "empty_or_truncated = []",
    "for key in load_completed_keys(RESPONSES_DIR):",
    "    data = json.loads(checkpoint_path(RESPONSES_DIR, key).read_text(encoding='utf-8'))",
    "    if not data['text'].strip():",
    "        empty_or_truncated.append((key, 'empty'))",
    "    elif data['raw'].get('finish_reason') == 'length':",
    "        empty_or_truncated.append((key, 'truncated (hit max_tokens)'))",
    "",
    "print(f'Empty or truncated responses: {len(empty_or_truncated)}')",
    "for key, reason in empty_or_truncated[:20]:",
    "    print(f'  {key}: {reason}')",
))

nb = {
    "cells": CELLS,
    "metadata": {
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "T4"},
        "kernelspec": {"display_name": "Python 3", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(nb, indent=1) + "\n", encoding="utf-8")
print(f"Wrote {OUT_PATH} ({len(CELLS)} cells)")
