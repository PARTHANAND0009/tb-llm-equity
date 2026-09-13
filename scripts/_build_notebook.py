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
    " (Colab T4), zero API cost. See `results/PREREGISTRATION.md` Amendments"
    " (2026-08-06, open-weight pivot) for why: zero compute budget authorized,"
    " single seed at temperature 0, 4-bit quantization throughout.",
    "",
    "**Inference backend: `transformers`, not vLLM.** The original version of this"
    " notebook used vLLM for continuous-batching throughput. vLLM's CUDA-library"
    " resolution failed twice live in Colab (`libcudart.so.13: cannot open shared"
    " object file`) across two different install strategies -- a known, documented"
    " class of vLLM/Colab packaging issue, not something specific to this notebook's"
    " code. `transformers` uses whatever torch/CUDA Colab already ships with"
    " working, so it sidesteps that whole failure mode. The cost: no continuous"
    " batching, so checkpointing is per-*batch* (`BATCH_SIZE`, default 4) rather"
    " than strictly per-response -- a crash mid-batch loses at most `BATCH_SIZE - 1`"
    " responses, not the whole run. Set `BATCH_SIZE = 1` if you want the original"
    " per-response guarantee back, at a real throughput cost.",
    "",
    "**Two phases, in order -- do not skip the gate between them:**",
    "",
    "1. **Pilot** (Task A): 20 stratified prompts (5 vignettes x 4 arms) through"
    " Llama-3.1-8B-Instruct, then the same 20 through Meditron3-8B, then Granite-4.2-8B"
    " (added 2026-09-10, Stage 2 Step 3 -- see Section 9b). Reports real measured"
    " output-token stats, throughput, response parseability, and a corrected"
    " full-run ETA -- the planning-time 700-tokens/response assumption was never"
    " validated against a real completion, and this is where that happens, before"
    " you commit hours to the full run.",
    "2. **Full run** (Task B): all 5 models x 400 prompts x `N_SAMPLES` (3 by"
    " default -- see Section 10) sampled completions. Checkpoints to Drive after"
    " every batch -- free Colab disconnects without warning, and a lost session"
    " should cost you minutes of re-warmup, not hours of regenerated work."
    " Resumable: re-running this notebook after a disconnect skips every response"
    " already checkpointed.",
    "",
    "**What was and wasn't tested before you run this.** The checkpoint/resume"
    " logic (`src/tb_equity/checkpoint.py`) and the response-parseability heuristic"
    " (`src/tb_equity/response_format.py`) are unit-tested against a stub generator"
    " in `tests/test_checkpoint.py` / `tests/test_response_format.py` -- including a"
    " simulated mid-write kill. **The model-loading/generation cells below have not"
    " been run end-to-end against a real GPU by me** -- the vLLM version was"
    " statically reviewed and then failed for real when you ran it; this"
    " `transformers` version fixes that specific failure but has not itself been"
    " confirmed working end-to-end. Treat the pilot as the actual first test of it,"
    " which is exactly what the pilot/gate structure is for.",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 1. Install dependencies",
    "",
    "`autoawq` and `gptqmodel` are both required for `transformers` to load the"
    " three AWQ-quantized checkpoints -- the installed `transformers` version's AWQ"
    " quantizer validates against `gptqmodel`'s availability specifically (confirmed"
    " live: `transformers` raised `ImportError: Loading an AWQ quantized model"
    " requires gptqmodel` with only `autoawq` installed), not just `autoawq` alone as"
    " older docs describe. `bitsandbytes` is for Meditron3-8B's on-the-fly NF4"
    " quantization. No vLLM.",
    "",
    "**The cell below captures Colab's own preinstalled `numpy` version FIRST, then"
    " restores exactly that version after everything else installs.** Confirmed live"
    " (2026-08-08): installing `gptqmodel` pulled in a different `numpy` version that"
    " left the environment broken (`ImportError: cannot import name '_center' from"
    " 'numpy._core.umath'` on the next `import transformers`) -- a binary mismatch"
    " between numpy's Python and compiled-C layers, from Colab's pre-existing numpy"
    " (already matched to Colab's preinstalled torch build) getting disturbed by a"
    " later pip install's own dependency resolution.",
    "",
    "Two earlier revisions of this fix force-reinstalled numpy to a hardcoded pin"
    " instead (unpinned 'whatever is newest', then `<2.4`, then `<2`) and each one"
    " eventually broke again as PyPI's numpy releases moved past whatever line was"
    " guessed -- confirmed live 2026-09-10, `<2.4` still hit `AttributeError: module"
    " 'numpy._core._multiarray_umath' has no attribute '_blas_supports_fpe'` (numpy"
    " 2.4.4 dropped that symbol; Colab's preinstalled torch/transformers build still"
    " calls it), and numpy 1.x-vs-2.x is a large enough ABI break on its own that"
    " even `<2` isn't guaranteed safe against every possible Colab torch build."
    " Guessing a version ceiling is the wrong shape of fix for a number that keeps"
    " moving -- capturing and restoring Colab's own already-correct version sidesteps"
    " the guessing entirely, whichever numpy generation Colab currently ships.",
    "",
    "**If you already ran an earlier version of this cell in this session:"
    " re-running this cell alone will NOT fix a broken numpy that's already loaded.**"
    " `Runtime -> Restart session` (keep the T4 GPU setting) is required after this"
    " cell runs, every time, before re-running anything below it -- `pip install`"
    " only changes files on disk, never the already-imported modules sitting in the"
    " current Python process's memory. An identical error after editing this cell"
    " almost always means the restart step was skipped, not that the fix is wrong.",
))
CELLS.append(code(
    "import numpy",
    "_colab_numpy_version = numpy.__version__  # captured BEFORE anything below can disturb it",
    "print(f'Colab preinstalled numpy: {_colab_numpy_version} (will be restored after installs below)')",
    "",
    "# Must be set before the first `import torch` anywhere in this notebook's process --",
    "# PyTorch reads this once, at CUDA-allocator init, not per-call. Confirmed live",
    "# (2026-09-10): loading a 3rd 8B model in the same T4 session (Granite-4.2-8B, after",
    "# Llama then Meditron) hit 'CUDA out of memory, tried to allocate 3.27 GiB ... 3.21",
    "# GiB free' -- a fragmentation failure (the T4 has 14.56 GiB total; the model itself",
    "# fits comfortably), not an actual out-of-capacity failure. expandable_segments lets",
    "# PyTorch grow one contiguous memory segment instead of many separately-cached",
    "# fixed-size blocks, which is the standard fix for exactly this OOM-despite-free-",
    "# memory pattern across sequential model loads in one process.",
    "import os",
    "os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True')",
))
CELLS.append(code(
    "!pip install -q transformers accelerate bitsandbytes autoawq gptqmodel huggingface_hub pyyaml",
    "!pip install -q --force-reinstall --no-deps \"numpy=={_colab_numpy_version}\"",
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
    "# Checkpoints, final responses, and pilot results ALWAYS go to Drive directly,",
    "# independent of REPO_SOURCE -- created now, before any generation happens below,",
    "# so the first checkpoint/pilot-result write always lands on durable storage.",
    "RESPONSES_DIR = DRIVE_ROOT / 'data' / 'responses'",
    "MANIFEST_DIR = DRIVE_ROOT / 'results' / 'manifests'",
    "PILOT_RESULTS_DIR = DRIVE_ROOT / 'results' / 'pilot'",
    "RESPONSES_DIR.mkdir(parents=True, exist_ok=True)",
    "MANIFEST_DIR.mkdir(parents=True, exist_ok=True)",
    "PILOT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)",
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
    "Only **one** of the five models actually needs this: `EPFLiGHT/Meditron3-8B`"
    " is auto-gated (accept terms on its model page, access is granted instantly,"
    " but a token is required to download it). Verified directly against the HF"
    " Hub API when this notebook was built: the other four --"
    " `hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4`, `Orion-zhen/Qwen3-8B-AWQ`,"
    " `solidrust/Mistral-7B-Instruct-v0.3-AWQ`, `ibm-granite/granite-4.2-8b` -- are"
    " all ungated, and the Llama AWQ repo bundles its own tokenizer files, so it"
    " never touches the gated base `meta-llama/Llama-3.1-8B-Instruct` repo.",
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
    "MODEL_REGISTRY = [m for m in models_cfg['evaluation']['models'] if m.get('runtime') == 'colab_hf']",
    "assert len(MODEL_REGISTRY) == 5, f'expected 5 open-weight models, found {len(MODEL_REGISTRY)}'",
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
    "## 7. Model loading + generation helpers (transformers)",
    "",
    "`EPFLiGHT/Meditron3-8B` has no pre-quantized AWQ checkpoint on the Hub (checked"
    " 2026-08-06 -- searched, none found), so it loads via on-the-fly bitsandbytes"
    " NF4 quantization; the other three load pre-quantized AWQ checkpoints directly"
    " (`transformers` reads the quantization config from the repo automatically, via"
    " `autoawq` + `gptqmodel` -- confirmed live that this `transformers` version's AWQ"
    " quantizer needs both, not `autoawq` alone).",
    "",
    "**T4-specific settings, verified when this notebook was built (not guessed):**",
    "",
    "- `torch.float16` everywhere, including `bnb_4bit_compute_dtype` for the"
    " bitsandbytes path -- T4 is Turing (compute capability 7.5) and lacks native"
    " bf16 tensor-core support. Several bitsandbytes usage examples online default"
    " to `bfloat16` because they're written against Ampere+ GPUs; using that here"
    " would silently run at a fraction of the expected speed, or fail outright.",
    "- `BATCH_SIZE = 4` -- deliberately conservative. `transformers`' `.generate()`"
    " does not have vLLM's paged-attention admission control, so an oversized batch"
    " OOMs hard rather than gracefully queuing; padding every sequence in a batch to"
    " the longest one in that batch means memory scales with batch size x longest"
    " prompt, not the average. Lower it if you still OOM; raise it once a run"
    " completes cleanly and you want more throughput.",
    "- Prompts are truncated to 3000 input tokens (`truncation=True, max_length=3000`)"
    " as a hard safety cap -- the longest real Arm 4 prompt is ~2500 tokens (see"
    " `data/prompts/manifest.json`'s `estimated_tokens`), so this should never"
    " actually trigger against real data; `generate_batch` asserts this per-prompt"
    " and names the offending vignette/arm rather than silently truncating (a"
    " truncated Arm 4 prompt would drop injected protocol text off the end).",
    "- Every prompt is rendered through `tokenizer.apply_chat_template(...,"
    " add_generation_prompt=True)` before tokenization -- `data/prompts/*.txt` itself"
    " is never touched, only wrapped at generation time. Without this, an"
    " instruction-tuned model sees raw text with no turn boundary and tends to keep"
    " writing the case narrative instead of answering it, which is exactly what an"
    " earlier live pilot run showed (every response hit `GENERATION_MAX_TOKENS`)."
    " `load_hf_model` refuses to proceed if a model's tokenizer has no"
    " `chat_template` rather than silently falling back to unformatted text.",
))
CELLS.append(code(
    "import gc",
    "import time",
    "",
    "import torch",
    "from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig",
    "",
    "GENERATION_MAX_TOKENS = 1600  # matches config/models.yaml generation.max_tokens",
    "BATCH_SIZE = 4  # tunable -- see note above",
    "",
    "",
    "def load_hf_model(model_cfg: dict):",
    "    tokenizer = AutoTokenizer.from_pretrained(model_cfg['model'], revision=model_cfg['revision'])",
    "    if tokenizer.chat_template is None:",
    "        raise ValueError(",
    "            f\"{model_cfg['model']} (revision {model_cfg['revision']}) has no chat_template -- \"",
    "            'refusing to fall back to raw-text continuation, which would silently feed this '",
    "            'instruction-tuned model an unformatted prompt while the rest of the roster gets '",
    "            'properly templated ones. Verify the repo actually ships tokenizer_config.json '",
    "            \"with a chat_template before retrying (Meditron3-8B's is gated -- this has not \"",
    "            'been verified as of this notebook revision, see KNOWN_ISSUES.md).'",
    "        )",
    "    if tokenizer.pad_token is None:",
    "        tokenizer.pad_token = tokenizer.eos_token",
    "    tokenizer.padding_side = 'left'  # required for correct batched causal-LM generation",
    "",
    "    if model_cfg['quantization'] == 'bitsandbytes-nf4':",
    "        bnb_config = BitsAndBytesConfig(",
    "            load_in_4bit=True,",
    "            bnb_4bit_quant_type='nf4',",
    "            bnb_4bit_compute_dtype=torch.float16,  # NOT bfloat16 -- see T4/Turing note above",
    "        )",
    "        model = AutoModelForCausalLM.from_pretrained(",
    "            model_cfg['model'], revision=model_cfg['revision'],",
    "            quantization_config=bnb_config, device_map='cuda:0',",
    "        )",
    "    else:",
    "        # AWQ pre-quantized checkpoints -- quantization config read from the repo's",
    "        # own config.json; requires autoawq + gptqmodel (installed in Section 1).",
    "        model = AutoModelForCausalLM.from_pretrained(",
    "            model_cfg['model'], revision=model_cfg['revision'],",
    "            dtype=torch.float16, device_map='cuda:0',  # dtype, not torch_dtype (deprecated)",
    "        )",
    "    model.eval()",
    "    return model, tokenizer",
    "",
    "",
    "def unload_hf_model(model) -> None:",
    "    \"\"\"A single del+collect+empty_cache pass can leave CUDA memory fragmented",
    "    rather than actually freed -- confirmed live (2026-09-10): loading a 3rd model",
    "    in the same T4 session (Granite-4.2-8B, after Llama then Meditron) hit",
    "    'CUDA out of memory. Tried to allocate 3.27 GiB ... of which 3.21 GiB is free'",
    "    despite the model itself being well under the T4's 14.56 GiB. Running gc twice",
    "    (a reference cycle can survive one pass) and synchronizing before",
    "    empty_cache() gives PyTorch's allocator a real chance to coalesce free blocks",
    "    instead of leaving them fragmented across many small unreleased chunks.",
    "    \"\"\"",
    "    del model",
    "    gc.collect()",
    "    torch.cuda.synchronize()",
    "    torch.cuda.empty_cache()",
    "    gc.collect()",
    "    torch.cuda.empty_cache()",
    "",
    "",
    "def read_prompt_text(entry: dict) -> str:",
    "    rel = entry['path'].removeprefix('data/prompts/')",
    "    return (PROMPTS_DIR / rel).read_text(encoding='utf-8')",
    "",
    "",
    "def render_chat_prompt(tokenizer, prompt_text: str) -> str:",
    "    \"\"\"Wraps `prompt_text` in the model's own chat template at generation time --",
    "    data/prompts/*.txt itself is never modified, only wrapped here. Without this,",
    "    an instruction-tuned model receives raw text with no turn boundary and tends to",
    "    keep writing the case narrative instead of answering it.",
    "",
    "    `enable_thinking=False` -- added 2026-09-10 for Granite-4.2-8B, which defaults to",
    "    verbose chain-of-thought reasoning that would otherwise eat into GENERATION_MAX_TOKENS",
    "    before ever producing the ranked-DDx/next-step/management-plan answer this study scores.",
    "    Verified safe to pass unconditionally: Llama-3.1/Mistral's chat templates don't",
    "    reference this variable and silently ignore it (checked live against all three",
    "    ungated tokenizers), Qwen3 and Granite both honor it (empty <think></think>",
    "    output, confirmed live). Meditron3-8B is untested (gated, no HF_TOKEN available",
    "    when this was checked) -- if it errors on this kwarg, that itself is useful",
    "    information about its template and should be reported, not silently caught.",
    "    \"\"\"",
    "    return tokenizer.apply_chat_template(",
    "        [{'role': 'user', 'content': prompt_text}], tokenize=False, add_generation_prompt=True,",
    "        enable_thinking=False,",
    "    )",
    "",
    "",
    "def generate_batch(model, tokenizer, entries: list[dict], *, seed: int | None = None,",
    "                    temperature: float = 0.0, top_p: float = 1.0,",
    "                    max_new_tokens: int | None = None):",
    "    \"\"\"One model.generate() call across `entries` (each chat-templated via",
    "    render_chat_prompt, then padded to the longest one in the batch) -- batched,",
    "    but NOT vLLM-style continuous batching. `temperature=0.0` (the default) means",
    "    greedy decoding (`do_sample=False`) -- deterministic, `seed` has no effect.",
    "    `temperature > 0.0` means true sampling (`do_sample=True`) with `torch.manual_seed(seed)`",
    "    set immediately before `model.generate()` so a given seed is independently",
    "    reproducible (see Section 10's note on why Task B uses this path). `max_new_tokens`",
    "    defaults to the module-level GENERATION_MAX_TOKENS when omitted -- pass an explicit",
    "    value to cap a shorter-format arm (e.g. the full run's structured arm, Section 12)",
    "    without inheriting the free-form arm's higher ceiling. Returns (texts,",
    "    output_token_counts, input_token_counts, stop_reasons, elapsed); each",
    "    stop_reasons[i] is 'eos' if that sequence emitted one of",
    "    model.generation_config.eos_token_id, else 'max_tokens'.",
    "    \"\"\"",
    "    prompts = [read_prompt_text(e) for e in entries]",
    "    rendered = [render_chat_prompt(tokenizer, p) for p in prompts]",
    "    effective_max_new_tokens = (",
    "        max_new_tokens if max_new_tokens is not None else GENERATION_MAX_TOKENS",
    "    )",
    "",
    "    # Fail loudly rather than silently truncate -- a truncated Arm 4 prompt would",
    "    # drop injected protocol text off the end without anyone noticing.",
    "    for e, r in zip(entries, rendered):",
    "        full_length = len(tokenizer(r, truncation=False)['input_ids'])",
    "        entry_label = f\"arm{e['arm']}\" if 'arm' in e else e.get('elicitation', '?')",
    "        assert full_length <= 3000, (",
    "            f\"{e['vignette_id']} {entry_label}: {full_length} tokens after chat-template \"",
    "            'rendering, exceeds the 3000-token truncation cap -- would silently drop text '",
    "            '(protocol excerpts for Arm 4) off the end.'",
    "        )",
    "",
    "    inputs = tokenizer(",
    "        rendered, return_tensors='pt', padding=True, truncation=True, max_length=3000,",
    "    ).to(model.device)",
    "    prompt_len = inputs['input_ids'].shape[1]",
    "    input_token_counts = inputs['attention_mask'].sum(dim=1).tolist()",
    "",
    "    do_sample = temperature > 0.0",
    "    if do_sample and seed is not None:",
    "        torch.manual_seed(seed)",
    "",
    "    start = time.time()",
    "    with torch.no_grad():",
    "        output_ids = model.generate(",
    "            **inputs, max_new_tokens=effective_max_new_tokens, do_sample=do_sample,",
    "            **({'temperature': temperature, 'top_p': top_p} if do_sample else {}),",
    "            pad_token_id=tokenizer.pad_token_id,",
    "        )",
    "    elapsed = time.time() - start",
    "",
    "    eos_ids = model.generation_config.eos_token_id",
    "    if eos_ids is None:",
    "        eos_ids = set()",
    "    elif isinstance(eos_ids, int):",
    "        eos_ids = {eos_ids}",
    "    else:",
    "        eos_ids = set(eos_ids)",
    "",
    "    texts = []",
    "    output_token_counts = []",
    "    stop_reasons = []",
    "    for i in range(len(entries)):",
    "        gen_ids = output_ids[i][prompt_len:]",
    "        texts.append(tokenizer.decode(gen_ids, skip_special_tokens=True))",
    "        output_token_counts.append(int((gen_ids != tokenizer.pad_token_id).sum()))",
    "        hit_eos = bool(eos_ids) and any(t in eos_ids for t in gen_ids.tolist())",
    "        stop_reasons.append('eos' if hit_eos else 'max_tokens')",
    "    return texts, output_token_counts, input_token_counts, stop_reasons, elapsed",
    "",
    "",
    "def save_pilot_results(family: str, entries: list[dict], texts: list[str],",
    "                        output_token_counts: list[int], input_token_counts: list[int],",
    "                        stop_reasons: list[str], parse_results, elapsed: float) -> Path:",
    "    \"\"\"Written to Drive immediately after each pilot run -- a disconnect right",
    "    after the pilot finishes (before you've read the printed report) must not",
    "    force re-running the GPU generations just to see the numbers again.",
    "    \"\"\"",
    "    payload = {",
    "        'family': family,",
    "        'elapsed_seconds': elapsed,",
    "        'responses': [",
    "            {",
    "                'vignette_id': e['vignette_id'],",
    "                'arm': e['arm'],",
    "                'input_tokens': in_tok,",
    "                'output_tokens': out_tok,",
    "                'stop_reason': stop_reason,",
    "                'parseable': r.parseable,",
    "                'parseable_reason': r.reason,",
    "                'text': text,",
    "            }",
    "            for e, text, out_tok, in_tok, stop_reason, r in zip(",
    "                entries, texts, output_token_counts, input_token_counts,",
    "                stop_reasons, parse_results,",
    "            )",
    "        ],",
    "    }",
    "    out_path = PILOT_RESULTS_DIR / f'{family}.json'",
    "    out_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')",
    "    print(f'Pilot results saved to {out_path}')",
    "    return out_path",
    "",
    "",
    "def run_pilot(model_cfg: dict, family: str):",
    "    \"\"\"model/tokenizer load and cleanup live in a try/finally -- added",
    "    2026-09-10 after a live OOM during load_hf_model() left a partially-",
    "    materialized model pinned in GPU memory for the rest of the session.",
    "    Root cause: unload_hf_model() previously only ran after a FULLY",
    "    successful load+generate, so a load-time exception skipped it entirely",
    "    -- and Jupyter/Colab's own exception history keeps every frame in the",
    "    traceback alive (including transformers' internal frames holding the",
    "    partially-loaded tensors), so the failed attempt's GPU memory stayed",
    "    reserved even though the cell 'failed'. finally guarantees cleanup",
    "    runs whether or not loading/generation succeeded.",
    "    \"\"\"",
    "    print(f\"=== PILOT: {model_cfg['model']} ===\")",
    "    print(f'GPU memory before load: {torch.cuda.memory_allocated() / 1e9:.2f} GB allocated, '",
    "          f'{torch.cuda.memory_reserved() / 1e9:.2f} GB reserved')",
    "    model = None",
    "    tokenizer = None",
    "    try:",
    "        model, tokenizer = load_hf_model(model_cfg)",
    "        return _run_pilot_body(model, tokenizer, model_cfg, family)",
    "    finally:",
    "        if model is not None:",
    "            unload_hf_model(model)",
    "        if tokenizer is not None:",
    "            del tokenizer",
    "        gc.collect()",
    "        torch.cuda.empty_cache()",
    "        print(f'GPU memory after cleanup: {torch.cuda.memory_allocated() / 1e9:.2f} GB allocated, '",
    "              f'{torch.cuda.memory_reserved() / 1e9:.2f} GB reserved')",
    "",
    "",
    "def _run_pilot_body(model, tokenizer, model_cfg: dict, family: str):",
    "    sample_entry = PILOT_ENTRIES[0]",
    "    sample_rendered = render_chat_prompt(tokenizer, read_prompt_text(sample_entry))",
    "    print(f\"Render check ({sample_entry['vignette_id']} arm{sample_entry['arm']}, last 120 \"",
    "           'chars after chat-template rendering):')",
    "    print(repr(sample_rendered[-120:]))",
    "",
    "    texts, output_token_counts, input_token_counts, stop_reasons, elapsed = [], [], [], [], 0.0",
    "    for start_idx in range(0, len(PILOT_ENTRIES), BATCH_SIZE):",
    "        chunk = PILOT_ENTRIES[start_idx:start_idx + BATCH_SIZE]",
    "        chunk_texts, chunk_out_tok, chunk_in_tok, chunk_stop, chunk_elapsed = generate_batch(",
    "            model, tokenizer, chunk",
    "        )",
    "        texts.extend(chunk_texts)",
    "        output_token_counts.extend(chunk_out_tok)",
    "        input_token_counts.extend(chunk_in_tok)",
    "        stop_reasons.extend(chunk_stop)",
    "        elapsed += chunk_elapsed",
    "",
    "    mean_out = sum(output_token_counts) / len(output_token_counts)",
    "    max_out = max(output_token_counts)",
    "    throughput = sum(output_token_counts) / elapsed",
    "",
    "    print(f'Mean output tokens/response: {mean_out:.1f}')",
    "    print(f'Max output tokens/response: {max_out}')",
    "    print(f'Wall time for {len(PILOT_ENTRIES)} prompts: {elapsed:.1f}s')",
    "    print(f'Aggregate throughput: {throughput:.1f} tok/s (batch_size={BATCH_SIZE}, T4)')",
    "",
    "    n_eos = sum(1 for s in stop_reasons if s == 'eos')",
    "    n_max_tokens = len(stop_reasons) - n_eos",
    "    print(f'{family}: {n_eos}/{len(stop_reasons)} EOS, {n_max_tokens}/{len(stop_reasons)} '",
    "          'max_tokens')",
    "",
    "    parse_results = [check_parseable(t) for t in texts]",
    "    n_parseable = sum(r.parseable for r in parse_results)",
    "    print(f'Parseable: {n_parseable}/{len(texts)}')",
    "    for e, r in zip(PILOT_ENTRIES, parse_results):",
    "        if not r.parseable:",
    "            print(f\"  NOT PARSEABLE: {e['vignette_id']} arm{e['arm']}: {r.reason}\")",
    "",
    "    full_run_eta_min = (400 * mean_out / throughput) / 60",
    "    print(f'Corrected full-run (400 prompts) ETA for this model, using MEASURED '",
    "          f'throughput: {full_run_eta_min:.1f} min')",
    "",
    "    save_pilot_results(",
    "        family, PILOT_ENTRIES, texts, output_token_counts, input_token_counts,",
    "        stop_reasons, parse_results, elapsed,",
    "    )",
    "    return texts, output_token_counts, input_token_counts, stop_reasons, parse_results, n_parseable",
))

# ---------------------------------------------------------------------------
CELLS.append(code(
    "# --- 12-prompt stratified pilot subset (overrides Section 6's 20-prompt sample",
    "# when PILOT_MODE=True) -- smaller, cheaper OOM/parseability/ETA check before the",
    "# fuller Task A pilot runs below. -------------------------------------------------",
    "PILOT_MODE = True  # flip to False and re-run this cell to leave PILOT_ENTRIES",
    "                   # (Section 6, 20 prompts) and BATCH_SIZE (Section 7 default, 4)",
    "                   # untouched -- Task B below never reads PILOT_ENTRIES at all, so",
    "                   # this flag only affects Task A.",
    "",
    "# Divergence class per vignette -- generic vignette metadata (not pilot-subset-",
    "# specific), computed unconditionally since the pilot report cell below needs it",
    "# regardless of PILOT_MODE.",
    "_div_table = json.loads(",
    "    (REPO_DIR / 'data' / 'divergence' / 'divergence_table.json').read_text(encoding='utf-8')",
    ")",
    "DIV_CLASS_BY_ID = {row['id']: row['divergence_class'] for row in _div_table['rows']}",
    "",
    "",
    "def divergence_class_for(vignette_id: str) -> str:",
    "    classes = {DIV_CLASS_BY_ID[d] for d in vignette_meta[vignette_id]['divergence_ids']}",
    "    assert len(classes) == 1, f'{vignette_id} grounds mixed divergence classes: {classes}'",
    "    return classes.pop()",
    "",
    "",
    "if PILOT_MODE:",
    "    # RULE 7 (CLAUDE.md): holdout vignettes stay excluded from everything except the",
    "    # final confirmation run -- a throughput/parseability pilot doesn't qualify.",
    "    non_holdout = [e for e in all_entries if not vignette_meta[e['vignette_id']]['holdout']]",
    "",
    "    # Backbone: 2 india_high + 1 consensus_control vignette, deterministically the",
    "    # lowest VIG-id in each burden class among non-holdout vignettes (sorted, fixed",
    "    # slice, no random sampling). Supplying all of Arms 1-3 from this backbone alone",
    "    # already yields 6 india_high + 3 consensus_control prompts, so the >=6/>=2 floor",
    "    # holds regardless of which burden class Arm 4's token-driven pick lands on below.",
    "    india_high_ids = sorted(",
    "        {e['vignette_id'] for e in non_holdout if e['burden_class'] == 'india_high'}",
    "    )",
    "    consensus_control_ids = sorted(",
    "        {e['vignette_id'] for e in non_holdout if e['burden_class'] == 'consensus_control'}",
    "    )",
    "    BACKBONE_VIGNETTE_IDS = india_high_ids[:2] + consensus_control_ids[:1]",
    "    assert len(BACKBONE_VIGNETTE_IDS) == 3, (",
    "        f'expected 3 backbone vignettes, got {len(BACKBONE_VIGNETTE_IDS)} '",
    "        f'(india_high available={len(india_high_ids)}, '",
    "        f'consensus_control available={len(consensus_control_ids)})'",
    "    )",
    "",
    "    arms_123 = []",
    "    for arm_num in (1, 2, 3):",
    "        arm_entries = sorted(",
    "            (e for e in non_holdout",
    "             if e['arm'] == arm_num and e['vignette_id'] in BACKBONE_VIGNETTE_IDS),",
    "            key=lambda e: e['vignette_id'],",
    "        )",
    "        assert len(arm_entries) == 3, (",
    "            f'expected 3 arm-{arm_num} entries from the backbone, got {len(arm_entries)}'",
    "        )",
    "        arms_123.extend(arm_entries)",
    "",
    "    # Arm 4: the 3 largest estimated_tokens -- the OOM and retrieval-quality risk --",
    "    # independent of the backbone, since prompt size (not vignette identity) is what's",
    "    # being stress-tested here. At least one must be consensus_divergence: it's the",
    "    # primary-outcome class, and a naive top-3-by-tokens cut lands all 3 in",
    "    # national_adaptation (the secondary class), leaving Arm 4 untested on the",
    "    # question the whole study exists to answer.",
    "    arm4_candidates = sorted(",
    "        (e for e in non_holdout if e['arm'] == 4),",
    "        key=lambda e: (-e['estimated_tokens'], e['vignette_id']),",
    "    )",
    "    arm4_consensus_divergence = [",
    "        e for e in arm4_candidates",
    "        if divergence_class_for(e['vignette_id']) == 'consensus_divergence'",
    "    ]",
    "    assert arm4_consensus_divergence, 'no non-holdout Arm 4 consensus_divergence candidates found'",
    "    required_cd_entry = arm4_consensus_divergence[0]  # largest-token one -- still deterministic",
    "    other_candidates = [",
    "        e for e in arm4_candidates if e['vignette_id'] != required_cd_entry['vignette_id']",
    "    ]",
    "    arm_4 = sorted(",
    "        [required_cd_entry, *other_candidates[:2]],",
    "        key=lambda e: (-e['estimated_tokens'], e['vignette_id']),",
    "    )",
    "    assert any(",
    "        divergence_class_for(e['vignette_id']) == 'consensus_divergence' for e in arm_4",
    "    ), 'consensus_divergence floor violated in Arm 4 selection'",
    "",
    "    PILOT_ENTRIES = sorted(arms_123 + arm_4, key=lambda e: (e['vignette_id'], e['arm']))",
    "    assert len(PILOT_ENTRIES) == 12",
    "",
    "    n_india_high = sum(1 for e in PILOT_ENTRIES if e['burden_class'] == 'india_high')",
    "    n_consensus_control = sum(",
    "        1 for e in PILOT_ENTRIES if e['burden_class'] == 'consensus_control'",
    "    )",
    "    assert n_india_high >= 6, f'india_high floor violated: {n_india_high}/12'",
    "    assert n_consensus_control >= 2, f'consensus_control floor violated: {n_consensus_control}/12'",
    "",
    "    BATCH_SIZE = 1  # pilot: minimize blast radius while validating the transformers path",
    "                    # on real weights -- raise back to the Section 7 default (4) only",
    "                    # after a clean pass",
    "",
    "    print(f'PILOT_MODE: PILOT_ENTRIES overridden to {len(PILOT_ENTRIES)} prompts '",
    "          f'({n_india_high} india_high, {n_consensus_control} consensus_control), '",
    "          f'BATCH_SIZE={BATCH_SIZE}')",
    "    for e in PILOT_ENTRIES:",
    "        print(f\"  {e['vignette_id']} arm{e['arm']} {e['burden_class']:<17s} \"",
    "              f\"div_class={divergence_class_for(e['vignette_id']):<20s} \"",
    "              f\"est_tokens={e['estimated_tokens']}\")",
    "else:",
    "    print(f'PILOT_MODE is False -- leaving PILOT_ENTRIES ({len(PILOT_ENTRIES)} prompts, '",
    "          f'Section 6) and BATCH_SIZE ({BATCH_SIZE}, Section 7) untouched.')",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 8. TASK A -- Pilot: Meta-Llama-3.1-8B-Instruct",
    "",
    "Real measured numbers, not the planning-time 700-token assumption.",
))
CELLS.append(code(
    "llama_cfg = next(m for m in MODEL_REGISTRY if m['family'] == 'meta')",
    "(",
    "    llama_texts, llama_output_token_counts, llama_input_token_counts,",
    "    llama_stop_reasons, llama_parse_results, llama_n_parseable,",
    ") = run_pilot(llama_cfg, 'meta')",
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
    "(",
    "    meditron_texts, meditron_output_token_counts, meditron_input_token_counts,",
    "    meditron_stop_reasons, meditron_parse_results, meditron_n_parseable,",
    ") = run_pilot(meditron_cfg, 'epfl')",
    "",
    "if meditron_n_parseable < llama_n_parseable:",
    "    print()",
    "    print(f'*** WARNING: Meditron3-8B parseable rate ({meditron_n_parseable}/{len(PILOT_ENTRIES)}) is '",
    "          f'LOWER than Llama-3.1-8B-Instruct ({llama_n_parseable}/{len(PILOT_ENTRIES)}). This is the '",
    "          f'exact instruction-following degradation risk flagged before running -- inspect '",
    "          f'meditron_texts by hand before committing to the full run for this model. ***')",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## GPU memory recovery (run only if a pilot cell above OOM'd)",
    "",
    "Skip this cell if everything above ran cleanly. If a pilot cell failed with"
    " `CUDA out of memory`, `run_pilot`'s `finally` block already unloaded that"
    " model's weights -- but Jupyter/Colab separately keeps the failed cell's"
    " exception and traceback alive for inspection (`%tb`, `Explain error`, etc.),"
    " and that traceback holds references to every frame between here and where"
    " the error was actually raised -- including `transformers`-internal frames"
    " holding the partially-loaded tensors that caused the OOM in the first"
    " place. Clearing that history here reclaims that memory without a full"
    " `Runtime -> Restart session` (which would also discard every pilot that"
    " already succeeded, forcing them to be re-run from scratch).",
))
CELLS.append(code(
    "import sys",
    "",
    "sys.last_traceback = None",
    "for _attr in ('last_value', 'last_type'):",
    "    if hasattr(sys, _attr):",
    "        delattr(sys, _attr)",
    "gc.collect()",
    "torch.cuda.empty_cache()",
    "print(f'GPU memory now: {torch.cuda.memory_allocated() / 1e9:.2f} GB allocated, '",
    "      f'{torch.cuda.memory_reserved() / 1e9:.2f} GB reserved (of ~14.6 GB on a T4)')",
    "print('If allocated is still several GB with nothing currently loading, the pinned '",
    "      'memory is likely in a frame this cell cannot reach -- a full runtime restart '",
    "      'is the remaining option.')",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 9b. TASK A -- Pilot: Granite-4.2-8B",
    "",
    "Added 2026-09-10 (Stage 2, Step 3). This is the first time this specific"
    " loader path has been exercised against `ibm-granite/granite-4.2-8b` --"
    " unlike Llama/Qwen/Mistral (proven AWQ checkpoints already used in this"
    " notebook) it has never been run through `load_hf_model`/`generate_batch`"
    " before, so it gets a pilot the same way Meditron3-8B did, comparing its"
    " parseable rate against Llama's baseline.",
))
CELLS.append(code(
    "granite_cfg = next(m for m in MODEL_REGISTRY if m['family'] == 'ibm')",
    "(",
    "    granite_texts, granite_output_token_counts, granite_input_token_counts,",
    "    granite_stop_reasons, granite_parse_results, granite_n_parseable,",
    ") = run_pilot(granite_cfg, 'ibm')",
    "",
    "if granite_n_parseable < llama_n_parseable:",
    "    print()",
    "    print(f'*** WARNING: Granite-4.2-8B parseable rate ({granite_n_parseable}/{len(PILOT_ENTRIES)}) is '",
    "          f'LOWER than Llama-3.1-8B-Instruct ({llama_n_parseable}/{len(PILOT_ENTRIES)}). Granite 4.2 has '",
    "          f'a native reasoning/thinking mode -- if responses look truncated mid-reasoning rather than '",
    "          f'unparseable in content, that may mean the model needs its thinking mode disabled via its '",
    "          f'chat template rather than a higher GENERATION_MAX_TOKENS. Inspect granite_texts by hand. ***')",
))

# ---------------------------------------------------------------------------
CELLS.append(code(
    "# --- Full per-prompt pilot report: input/output token counts, stop reason, full",
    "# raw output, and (Arm 4 only) the full retrieved protocol context block that was",
    "# injected -- for every prompt in PILOT_ENTRIES, both models run above. ----------",
    "PROTOCOL_BLOCK_MARKER = '\\n\\nRelevant protocol excerpts:\\n'  # see scripts/expand_arms.py",
    "                                                              # (arm4 = arm2 + this + protocol_section)",
    "",
    "",
    "def print_pilot_report(family: str, model_cfg: dict, texts: list[str],",
    "                        output_token_counts: list[int], input_token_counts: list[int],",
    "                        stop_reasons: list[str]) -> None:",
    "    print(f\"\\n{'=' * 100}\\nPILOT REPORT -- {family} ({model_cfg['model']})\\n{'=' * 100}\")",
    "    for e, text, out_tok, in_tok, stop_reason in zip(",
    "        PILOT_ENTRIES, texts, output_token_counts, input_token_counts, stop_reasons",
    "    ):",
    "        print(f\"\\n--- {e['vignette_id']} arm{e['arm']} \"",
    "              f\"| divergence_class={divergence_class_for(e['vignette_id'])} \"",
    "              f\"| input_tokens={in_tok} | output_tokens={out_tok} | stop={stop_reason} ---\")",
    "        print(text)",
    "        if e['arm'] == 4:",
    "            protocol_block = read_prompt_text(e).split(PROTOCOL_BLOCK_MARKER, 1)[1]",
    "            print(f'\\n[retrieved protocol context injected into this prompt]\\n{protocol_block}')",
    "",
    "",
    "print_pilot_report(",
    "    'meta', llama_cfg, llama_texts, llama_output_token_counts,",
    "    llama_input_token_counts, llama_stop_reasons,",
    ")",
    "print_pilot_report(",
    "    'epfl', meditron_cfg, meditron_texts, meditron_output_token_counts,",
    "    meditron_input_token_counts, meditron_stop_reasons,",
    ")",
    "print_pilot_report(",
    "    'ibm', granite_cfg, granite_texts, granite_output_token_counts,",
    "    granite_input_token_counts, granite_stop_reasons,",
    ")",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 9c. Checkpoint 2b-v Step E: structured vs free-form re-pilot",
    "",
    "12 DIV-001-repaired, non-holdout vignettes x 3 models (meta/epfl/ibm -- deliberately"
    " not all 5; this is a small targeted diagnostic pilot, not a Task-B-scale run) x 2"
    " elicitation conditions (structured, `data/prompts/<vignette_id>/structured.txt`;"
    " free-form, the same vignette's `arm1.txt`, unchanged) = 72 generations. Answers the"
    " Checkpoint 2b-v CRITICAL ANALYSIS CHANGE's pre-specified H1/H2 question: does control"
    " coverage approach ceiling in the structured arm while divergence-axis coverage stays"
    " low (H1, divergence-specific avoidance), or do both rise together (H2, a general"
    " granularity effect)? That verdict, plus per-control coverage, conditional alignment,"
    " and the REACHABLE/UNREACHED/AMBIGUOUS distribution, is computed locally afterward by"
    " `scripts/analyze_step_e_repilot.py` against the JSON this section writes -- **this"
    " section itself only captures what requires the GPU**: raw text, token counts, stop"
    " reasons, wall-clock, and which batch size actually ran.",
    "",
    "**Single greedy-decoded generation per (vignette, elicitation, model)** -- this pilot"
    " measures whether an axis gets addressed at all, not response-to-response variance,"
    " so it doesn't need Task B's multi-seed sampling. Reuses `load_hf_model`/"
    " `generate_batch`/`unload_hf_model` from Section 7 unchanged -- no new model-loading"
    " path to trust.",
    "",
    "**The Granite batch-size question.** `config/models.yaml`'s `ibm` entry overrides"
    " `batch_size` to 1 for the full 400-prompt arms, which are long. The structured arm's"
    " prompts are much shorter (a fixed 1-3-sentence-per-question format instead of an"
    " open management plan), so the *structured* condition specifically retries at"
    " `batch_size=4` first and falls back to 1 only on a real CUDA OOM -- the free-form"
    " condition keeps the existing override throughout, since the restoration claim is"
    " about the constrained format's length, not about Granite in general. Whichever batch"
    " size actually ran is recorded per elicitation, alongside the exact pinned"
    " `model_cfg['revision']`, regardless of outcome.",
))
CELLS.append(code(
    "STEP_E_PROMPTS_MANIFEST = json.loads(",
    "    (PROMPTS_DIR / 'structured_pilot_manifest.json').read_text(encoding='utf-8')",
    ")",
    "STEP_E_VIGNETTES = STEP_E_PROMPTS_MANIFEST['vignettes']",
    "assert len(STEP_E_VIGNETTES) == 12, f'expected 12 Step E vignettes, got {len(STEP_E_VIGNETTES)}'",
    "",
    "STEP_E_FAMILIES = ('meta', 'epfl', 'ibm')",
    "STEP_E_MODEL_CFGS = {f: next(m for m in MODEL_REGISTRY if m['family'] == f) for f in STEP_E_FAMILIES}",
    "",
    "STEP_E_RESULTS_DIR = DRIVE_ROOT / 'results' / 'pilot' / 'step_e_repilot'",
    "STEP_E_RESULTS_DIR.mkdir(parents=True, exist_ok=True)",
    "",
    "print(f'Step E re-pilot: {len(STEP_E_VIGNETTES)} vignettes x {len(STEP_E_FAMILIES)} models x 2 arms '",
    "      f'= {len(STEP_E_VIGNETTES) * len(STEP_E_FAMILIES) * 2} generations')",
))
CELLS.append(code(
    "def _entries_for_elicitation(elicitation: str) -> list[dict]:",
    "    key = 'structured_path' if elicitation == 'structured' else 'freeform_path'",
    "    return [{'vignette_id': v['vignette_id'], 'path': v[key]} for v in STEP_E_VIGNETTES]",
    "",
    "",
    "def generate_with_batch_fallback(model, tokenizer, entries, *, attempt_batch_size):",
    "    \"\"\"Try attempt_batch_size; on a real CUDA OOM, clear the cache and restart the",
    "    WHOLE elicitation at batch_size=1 rather than resuming mid-way -- an OOM partway",
    "    through a batched run can leave the allocator fragmented, so a clean restart at a",
    "    smaller batch size is safer than trying to salvage the failed batch. Returns",
    "    (texts, output_token_counts, input_token_counts, stop_reasons, elapsed,",
    "    batch_size_used).",
    "    \"\"\"",
    "    for batch_size in sorted({attempt_batch_size, 1}, reverse=True):",
    "        try:",
    "            texts, out_tok, in_tok, stop_reasons, elapsed = [], [], [], [], 0.0",
    "            for start in range(0, len(entries), batch_size):",
    "                chunk = entries[start:start + batch_size]",
    "                c_texts, c_out, c_in, c_stop, c_elapsed = generate_batch(model, tokenizer, chunk)",
    "                texts.extend(c_texts)",
    "                out_tok.extend(c_out)",
    "                in_tok.extend(c_in)",
    "                stop_reasons.extend(c_stop)",
    "                elapsed += c_elapsed",
    "            return texts, out_tok, in_tok, stop_reasons, elapsed, batch_size",
    "        except RuntimeError as e:",
    "            if 'out of memory' not in str(e).lower() or batch_size == 1:",
    "                raise",
    "            print(f'  batch_size={batch_size} OOM\\'d; clearing cache and retrying at batch_size=1')",
    "            gc.collect()",
    "            torch.cuda.empty_cache()",
    "    raise AssertionError('unreachable -- batch_size=1 always either succeeds or re-raises above')",
))
CELLS.append(code(
    "import hashlib",
    "import subprocess",
    "from datetime import UTC, datetime",
    "",
    "",
    "def _repo_git_commit_sha() -> str:",
    "    try:",
    "        return subprocess.check_output(",
    "            ['git', 'rev-parse', 'HEAD'], cwd=REPO_DIR, text=True",
    "        ).strip()",
    "    except Exception:",
    "        return 'unknown'",
    "",
    "",
    "def _structured_pilot_manifest_hash() -> str:",
    "    return hashlib.sha256(",
    "        (PROMPTS_DIR / 'structured_pilot_manifest.json').read_bytes()",
    "    ).hexdigest()",
    "",
    "",
    "def run_step_e_repilot(family: str) -> dict:",
    "    \"\"\"model/tokenizer load and cleanup live in a try/finally, same reasoning as",
    "    run_pilot above: a load-time or mid-run failure must not leave GPU memory pinned",
    "    for the rest of the session.",
    "    \"\"\"",
    "    model_cfg = STEP_E_MODEL_CFGS[family]",
    "    print(f\"\\n=== STEP E RE-PILOT: {family} ({model_cfg['model']}, \"",
    "          f\"revision={model_cfg['revision']}) ===\")",
    "    model = None",
    "    tokenizer = None",
    "    per_elicitation = {}",
    "    try:",
    "        model, tokenizer = load_hf_model(model_cfg)",
    "        for elicitation in ('structured', 'freeform'):",
    "            entries = _entries_for_elicitation(elicitation)",
    "            # Only the structured arm tests batch_size=4 restoration for Granite -- the",
    "            # freeform arm keeps the config's existing override throughout (see markdown",
    "            # above for why this split, not a blanket attempt, is the correct test).",
    "            if family == 'ibm' and elicitation == 'structured':",
    "                attempt_batch_size = 4",
    "            else:",
    "                attempt_batch_size = model_cfg.get('batch_size', BATCH_SIZE)",
    "",
    "            texts, out_tok, in_tok, stop_reasons, elapsed, batch_size_used = (",
    "                generate_with_batch_fallback(",
    "                    model, tokenizer, entries, attempt_batch_size=attempt_batch_size,",
    "                )",
    "            )",
    "            per_elicitation[elicitation] = {",
    "                'texts': texts, 'output_tokens': out_tok, 'input_tokens': in_tok,",
    "                'stop_reasons': stop_reasons, 'elapsed': elapsed, 'batch_size_used': batch_size_used,",
    "            }",
    "",
    "            mean_out = sum(out_tok) / len(out_tok)",
    "            n_truncated = sum(1 for s in stop_reasons if s == 'max_tokens')",
    "            throughput = sum(out_tok) / elapsed if elapsed > 0 else float('nan')",
    "            restoration_note = ''",
    "            if family == 'ibm' and elicitation == 'structured':",
    "                restoration_note = (",
    "                    ' (batch_size=4 RESTORED)' if batch_size_used == 4",
    "                    else ' (fell back to 1 -- restoration NOT achieved)'",
    "                )",
    "            print(f'  {elicitation}: mean_output_tokens={mean_out:.1f}, '",
    "                  f'truncated={n_truncated}/{len(texts)}, wall_clock={elapsed:.1f}s, '",
    "                  f'throughput={throughput:.1f} tok/s, batch_size_used={batch_size_used}'",
    "                  + restoration_note)",
    "    finally:",
    "        if model is not None:",
    "            unload_hf_model(model)",
    "        if tokenizer is not None:",
    "            del tokenizer",
    "        gc.collect()",
    "        torch.cuda.empty_cache()",
    "",
    "    responses = []",
    "    for elicitation, data in per_elicitation.items():",
    "        for v, text, out_tok_i, in_tok_i, stop_reason in zip(",
    "            STEP_E_VIGNETTES, data['texts'], data['output_tokens'], data['input_tokens'],",
    "            data['stop_reasons'],",
    "        ):",
    "            responses.append({",
    "                'vignette_id': v['vignette_id'],",
    "                'family': family,",
    "                'model': model_cfg['model'],",
    "                'model_revision': model_cfg['revision'],",
    "                'elicitation': elicitation,",
    "                'text': text,",
    "                'input_tokens': in_tok_i,",
    "                'output_tokens': out_tok_i,",
    "                'stop_reason': stop_reason,",
    "                'truncated': stop_reason == 'max_tokens',",
    "                'batch_size_used': data['batch_size_used'],",
    "            })",
    "",
    "    payload = {",
    "        'family': family,",
    "        'model': model_cfg['model'],",
    "        'model_revision': model_cfg['revision'],",
    "        'responses': responses,",
    "        'elicitation_summary': {",
    "            elicitation: {",
    "                'elapsed_seconds': data['elapsed'],",
    "                'batch_size_used': data['batch_size_used'],",
    "            }",
    "            for elicitation, data in per_elicitation.items()",
    "        },",
    "    }",
    "    out_path = STEP_E_RESULTS_DIR / f'{family}.json'",
    "    out_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')",
    "    print(f'Saved: {out_path}')",
    "",
    "    # RULE 1 manifest -- this feeds the actual Checkpoint 2b-v H1/H2 report, unlike",
    "    # Task A's throughput-only pilot above, so it gets one despite being a pilot.",
    "    run_id = f\"checkpoint2b-v-repilot-{family}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}\"",
    "    manifest = {",
    "        'run_id': run_id,",
    "        'model_identifiers': [{",
    "            'family': family, 'name': model_cfg['model'], 'version': model_cfg['revision'],",
    "        }],",
    "        'temperature': 0.0,",
    "        'top_p': 1.0,",
    "        'max_tokens': GENERATION_MAX_TOKENS,",
    "        'seed': None,",
    "        'prompt_template_hash': _structured_pilot_manifest_hash(),",
    "        'vignette_set_version': 'v1',",
    "        'rubric_version': 'v1',",
    "        'git_commit_sha': _repo_git_commit_sha(),",
    "        'utc_timestamp': datetime.now(UTC).isoformat(),",
    "        'total_input_tokens': sum(r['input_tokens'] for r in responses),",
    "        'total_output_tokens': sum(r['output_tokens'] for r in responses),",
    "        'quantization': model_cfg['quantization'],",
    "        'base_model': model_cfg['base_model'],",
    "        'base_model_revision': model_cfg['base_model_revision'],",
    "        'n_responses_this_run': len(responses),",
    "        'elicitations': ['structured', 'freeform'],",
    "        'n_vignettes': len(STEP_E_VIGNETTES),",
    "        'notes': (",
    "            'Checkpoint 2b-v Step E re-pilot: structured-vs-freeform elicitation, greedy '",
    "            'decoding, single generation per (vignette, elicitation) -- distinct from the '",
    "            'Task B full run (5 models x 400 prompts x N_SAMPLES) and from Task A\\'s '",
    "            'throughput-only pilot above.'",
    "        ),",
    "    }",
    "    (MANIFEST_DIR / f'{run_id}.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')",
    "    print(f'Manifest written: {run_id}.json')",
    "    return payload",
))
CELLS.append(code(
    "step_e_results = {family: run_step_e_repilot(family) for family in STEP_E_FAMILIES}",
    "",
    "print('\\nStep E re-pilot generation complete. Copy this back into the main repo before analysis:')",
    "print(f'  {STEP_E_RESULTS_DIR} -> results/pilot/step_e_repilot/ (meta.json, epfl.json, ibm.json)')",
    "print(f'  {MANIFEST_DIR} -> results/manifests/ (3 new checkpoint2b-v-repilot-*.json manifests)')",
    "print('Then, locally, no GPU needed: python scripts/analyze_step_e_repilot.py')",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## STOP -- read the pilot report above before continuing",
    "",
    "This gate is about Task B (the 5-model x 400-prompt x N_SAMPLES full run) only."
    " Section 9c's Step E re-pilot above is independent of `PILOT_APPROVED` -- it neither"
    " reads nor sets it, and can be run (or re-run) on its own regardless of whether Task B"
    " is ever approved.",
    "",
    "Confirm before proceeding to the full run (Task B):",
    "",
    "- Mean/max output tokens are in a sane range (not near `GENERATION_MAX_TOKENS`,"
    " which would mean responses are being truncated).",
    "- Parseable rate is high (ideally 20/20) for all three piloted models. If"
    " Meditron's or Granite's is meaningfully lower, read the texts by hand -- it"
    " may need a different parsing strategy downstream (or, for Granite, a"
    " thinking-mode toggle -- see the warning above), not a rerun.",
    "- The corrected ETA (measured throughput, not the planning-time 700-token"
    " guess) times 5 models times `N_SAMPLES` (Section 10 below) fits your"
    " session-time budget.",
    "",
    "Once satisfied, set `PILOT_APPROVED = True` in the next cell to unlock the full"
    " run -- this is a deliberate gate, not a formality.",
))
CELLS.append(code(
    "PILOT_APPROVED = False  # <-- change to True only after reading the pilot report above",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 10. TASK B -- Full run: all 5 models x 400 prompts x N_SAMPLES",
    "",
    "Updated 2026-09-10 (Stage 2, Step 4): `results/PREREGISTRATION.md`'s"
    " open-weight-pivot amendment fixed single-seed, temperature-0 (greedy)"
    " decoding, for a stated, explicit reason -- zero compute budget, not a"
    " methodological preference, and it says multi-seed 'would still be"
    " preferred for the same reliability reasons' with more budget. That"
    " reasoning still holds, but greedy decoding (`do_sample=False`) is"
    " *deterministic*: running it N times with different `seed` values under"
    " the old design produces byte-identical output every time, since `seed`"
    " never reaches an actual random draw. Measuring within-vignette response"
    " variance -- this stage's explicit ask -- is structurally impossible under"
    " greedy decoding. This run therefore switches to true sampling"
    " (`do_sample=True`) for Task B specifically, restoring the property the"
    " original pivot amendment said was preferable, now that Colab GPU-hours"
    " (not per-token API cost) are the only budget constraint.",
    "",
    "**N_SAMPLES = 3, SAMPLE_TEMPERATURE = 0.7, top_p = 1.0.** 3 samples is the"
    " smallest N that can distinguish a stable answer (3/3 agree) from a"
    " genuinely split one (2/1) while keeping the cost multiplier low -- this"
    " triples Task B's generation cost (in wall-clock GPU-time; still $0, this"
    " remains the free-tier T4 path) across 5 models instead of 4, so it is a"
    " real increase, not a free upgrade. 0.7 is a conventional moderate"
    " sampling temperature: high enough to surface genuine decision-flips,"
    " low enough that responses should stay coherent rather than degenerate."
    " Each of the 3 samples uses a distinct, logged seed (`torch.manual_seed`)"
    " so any individual sample is independently reproducible. Adjust"
    " `N_SAMPLES`/`SAMPLE_TEMPERATURE` below before running if you want a"
    " different tradeoff -- this is a proposal, not a hard requirement.",
    "",
    "Checkpoints after every *batch* (`BATCH_SIZE`, default 4 -- see Section 7's"
    " note on why this isn't strictly per-response with `transformers`);"
    " resumable; identical JSON shape to the API-path cache (each sample's seed"
    " is part of the cache key, so re-running never collides across samples);"
    " one RULE 1 manifest per (model, seed).",
))
CELLS.append(code(
    "assert PILOT_APPROVED, 'Set PILOT_APPROVED = True in the cell above after reading the pilot report.'",
    "",
    "N_SAMPLES = 3  # see markdown above -- adjust before running if you want a different n",
    "SAMPLE_TEMPERATURE = 0.7",
    "TOP_P = 1.0",
    "PROGRESS_EVERY = 25  # print a progress line at least this often",
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
    "def run_model_full(model_cfg: dict, seed: int) -> None:",
    "    family = model_cfg['family']",
    "    print(f\"\\n=== FULL RUN: {family}/{model_cfg['model']} (seed={seed}) ===\")",
    "",
    "    all_keys = [",
    "        cache_key_for(",
    "            family=family,",
    "            model=model_cfg['model'],",
    "            system_prompt='',",
    "            messages=[{'role': 'user', 'content': read_prompt_text(e)}],",
    "            params=GenerationParams(",
    "                temperature=SAMPLE_TEMPERATURE, top_p=TOP_P,",
    "                max_tokens=GENERATION_MAX_TOKENS, seed=seed,",
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
    "    # model/tokenizer load + generation wrapped in try/finally so a load-time or",
    "    # mid-run OOM still triggers cleanup (see run_pilot's docstring for why this",
    "    # matters -- the same failure mode applies here).",
    "    total_input_tokens = 0",
    "    total_output_tokens = 0",
    "    n_done = 0",
    "    model = None",
    "    tokenizer = None",
    "    # Per-model override, not a global -- see config/models.yaml's comment on the",
    "    # ibm/Granite entry. batch_size is an infrastructure knob (no effect on any",
    "    # individual sequence's generated content), unlike temperature/top_p/max_tokens,",
    "    # so varying it per model doesn't compromise cross-model comparability.",
    "    batch_size = model_cfg.get('batch_size', BATCH_SIZE)",
    "    print(f'Using batch_size={batch_size} for {family}'",
    "          + (' (per-model override)' if 'batch_size' in model_cfg else ' (Section 7 default)'))",
    "    try:",
    "        model, tokenizer = load_hf_model(model_cfg)",
    "        start = time.time()",
    "",
    "        for batch_start in range(0, len(todo), batch_size):",
    "            chunk_keys = todo[batch_start:batch_start + batch_size]",
    "            chunk_entries = [key_to_entry[k] for k in chunk_keys]",
    "",
    "            chunk_texts, chunk_out_tok, chunk_in_tok, chunk_stop, _elapsed = generate_batch(",
    "                model, tokenizer, chunk_entries,",
    "                seed=seed, temperature=SAMPLE_TEMPERATURE, top_p=TOP_P,",
    "            )",
    "",
    "            for key, entry, text, out_tok, in_tok, stop_reason in zip(",
    "                chunk_keys, chunk_entries, chunk_texts, chunk_out_tok, chunk_in_tok, chunk_stop",
    "            ):",
    "                total_input_tokens += in_tok",
    "                total_output_tokens += out_tok",
    "                write_response_atomic(",
    "                    RESPONSES_DIR,",
    "                    key,",
    "                    text=text,",
    "                    raw={",
    "                        'vignette_id': entry['vignette_id'],",
    "                        'arm': entry['arm'],",
    "                        'model': model_cfg['model'],",
    "                        'model_revision': model_cfg['revision'],",
    "                        'quantization': model_cfg['quantization'],",
    "                        'seed': seed,",
    "                        'stop_reason': stop_reason,",
    "                        'truncated': stop_reason == 'max_tokens',",
    "                    },",
    "                    input_tokens=in_tok,",
    "                    output_tokens=out_tok,",
    "                )",
    "                n_done += 1",
    "",
    "            if n_done % PROGRESS_EVERY < batch_size or n_done == len(todo):",
    "                elapsed = time.time() - start",
    "                rate = n_done / elapsed if elapsed > 0 else 0",
    "                remaining = (len(todo) - n_done) / rate if rate > 0 else float('inf')",
    "                print(f'  {n_done}/{len(todo)} done, {elapsed/60:.1f}min elapsed, '",
    "                      f'ETA {remaining/60:.1f}min remaining')",
    "    finally:",
    "        if model is not None:",
    "            unload_hf_model(model)",
    "        if tokenizer is not None:",
    "            del tokenizer",
    "        gc.collect()",
    "        torch.cuda.empty_cache()",
    "",
    "    # RULE 1 manifest -- one per (model, seed): tb_equity.manifest's flat schema",
    "    # can't represent more than one temperature/seed value, and a Colab run is",
    "    # naturally sequential per model anyway (VRAM precludes loading >1 8B model).",
    "    run_id = f\"open-weight-{family}-seed{seed}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}\"",
    "    manifest = {",
    "        'run_id': run_id,",
    "        'model_identifiers': [{",
    "            'family': family,",
    "            'name': model_cfg['model'],",
    "            'version': model_cfg['revision'],",
    "        }],",
    "        'temperature': SAMPLE_TEMPERATURE,",
    "        'top_p': TOP_P,",
    "        'max_tokens': GENERATION_MAX_TOKENS,",
    "        'seed': seed,",
    "        'prompt_template_hash': prompts_manifest_hash(),",
    "        'vignette_set_version': 'v1',",
    "        'rubric_version': 'v1',  # frozen for this run -- see RUBRIC_SPEC.md / Stage 2 instructions",
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
    "    for seed in range(N_SAMPLES):",
    "        run_model_full(model_cfg, seed=seed)",
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
    "expected = len(MODEL_REGISTRY) * len(all_entries) * N_SAMPLES  # models x 400 x N_SAMPLES",
    "actual = len(load_completed_keys(RESPONSES_DIR))",
    "print(f'Expected {expected} responses ({len(MODEL_REGISTRY)} models x 400 prompts x '",
    "      f'{N_SAMPLES} samples), found {actual} checkpointed.')",
    "",
    "empty_or_truncated = []",
    "for key in load_completed_keys(RESPONSES_DIR):",
    "    data = json.loads(checkpoint_path(RESPONSES_DIR, key).read_text(encoding='utf-8'))",
    "    if not data['text'].strip():",
    "        empty_or_truncated.append((key, 'empty'))",
    "    elif data['raw'].get('truncated'):",
    "        empty_or_truncated.append((key, 'truncated (hit max_tokens)'))",
    "",
    "print(f'Empty or truncated responses: {len(empty_or_truncated)}')",
    "for key, reason in empty_or_truncated[:20]:",
    "    print(f'  {key}: {reason}')",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 12. IRIS TMED full run -- 3-model panel x freeform/structured, n=1",
    "",
    "**Distinct from Task B above** (Section 10, 5-model x 400-prompt x N_SAMPLES"
    " sampled-variance design) -- this is a separate, simpler run: a single"
    " greedy-decoded (`temperature=0.0`) generation per (vignette, model, arm),"
    " across every non-holdout vignette (RULE 7), for the free-form condition"
    " (Arm 1, all 85) and the structured condition"
    " (`src/tb_equity/structured_elicitation.py`'s 5 covered axes, 39 of the 85 --"
    " the other 46 ground none of those axes and are not force-fit; see"
    " `data/prompts/full_run_manifest.json` and `results/LIMITATIONS.md`)."
    " Reuses `load_hf_model`/`generate_batch`/`unload_hf_model` from Section 7"
    " unchanged.",
    "",
    "**Granite (`ibm`) and Meditron3-8B (`epfl`) are both excluded from this"
    " run**, for different reasons -- `ibm` OOM'd during model loading in the"
    " Checkpoint 2b-v Step E re-pilot; `epfl` was dropped ahead of time to"
    " protect the 20 September freeze deadline after repeated Colab free-tier"
    " quota exhaustion/disconnects during meta/qwen/mistral's generation, not"
    " due to any epfl-specific failure. See `results/LIMITATIONS.md` for both."
    " `FULL_RUN_MODEL_REGISTRY` below filters out any `config/models.yaml`"
    " entry with `excluded: true` rather than assuming a fixed model count, so"
    " removing the flag later (should either ever be revisited) is the only"
    " change needed to bring a model back in.",
    "",
    "**Free-form generates before structured, for every model** -- not"
    " interleaved per vignette, but every free-form response across all 85"
    " vignettes is written before any structured response starts, for each"
    " model in turn. This ordering is preserved across a resume: grouping"
    " `todo` by elicitation (not just chunking blindly through it) means a"
    " session that disconnects partway through free-form still finishes ALL"
    " free-form before starting structured when it resumes, rather than"
    " interleaving because some free-form keys happened to already be done.",
    "",
    "**Per-arm `max_tokens`, not inherited from the free-form ceiling:**"
    " free-form keeps `GENERATION_MAX_TOKENS` (1600, Section 7); structured uses"
    " `STRUCTURED_MAX_TOKENS = 800` below -- grounded in the real Checkpoint 2b-v"
    " Step E re-pilot data (max observed structured-arm output was 482 tokens"
    " across 24 real generations; 800 leaves comfortable headroom for the ~5x"
    " larger full-run sample and for qwen/mistral, untested on this specific"
    " prompt format, without just inheriting free-form's much higher cap).",
    "",
    "**Resumable via the same `data/responses/` checkpoint convention as Task B**"
    " (`src/tb_equity/checkpoint.py`) -- a disconnect mid-run loses at most the"
    " current batch, not the whole model, and re-running this section after a"
    " disconnect or a fresh Colab session skips every response already"
    " checkpointed.",
))
CELLS.append(code(
    "STRUCTURED_MAX_TOKENS = 800  # see markdown above -- grounded in Step E's real observed max (482)",
    "PROGRESS_EVERY = 25  # print a progress line at least this often -- self-contained here",
    "                     # (not read from Section 10, which this section's own markdown",
    "                     # says to skip) rather than assuming a prior cell defined it",
    "",
    "FULL_RUN_MANIFEST = json.loads((PROMPTS_DIR / 'full_run_manifest.json').read_text(encoding='utf-8'))",
    "FULL_RUN_FREEFORM = FULL_RUN_MANIFEST['freeform']      # 85 non-holdout vignettes",
    "FULL_RUN_STRUCTURED = FULL_RUN_MANIFEST['structured']  # 39 of those 85 -- see markdown above",
    "",
    "FULL_RUN_MODEL_REGISTRY = [m for m in MODEL_REGISTRY if not m.get('excluded')]",
    "assert len(FULL_RUN_MODEL_REGISTRY) == 3, (",
    "    f'expected 3 models (ibm and epfl both excluded -- see results/LIMITATIONS.md), '",
    "    f'got {len(FULL_RUN_MODEL_REGISTRY)}: {[m[\"family\"] for m in FULL_RUN_MODEL_REGISTRY]}'",
    ")",
    "",
    "_total_prompts = len(FULL_RUN_FREEFORM) + len(FULL_RUN_STRUCTURED)",
    "print(f'Full run: {len(FULL_RUN_FREEFORM)} freeform + {len(FULL_RUN_STRUCTURED)} structured '",
    "      f'= {_total_prompts} prompts x {len(FULL_RUN_MODEL_REGISTRY)} models '",
    "      f'= {_total_prompts * len(FULL_RUN_MODEL_REGISTRY)} generations (n=1, greedy)')",
    "for m in FULL_RUN_MODEL_REGISTRY:",
    "    print(f\"  {m['family']:8s} {m['model']}\")",
))
CELLS.append(code(
    "import hashlib",
    "import subprocess",
    "from datetime import UTC, datetime, timedelta",
    "",
    "FREEZE_DEADLINE = datetime(2026, 9, 20, tzinfo=UTC)  # instrument freeze -- see project instructions",
    "",
    "",
    "def _repo_git_commit_sha() -> str:",
    "    try:",
    "        return subprocess.check_output(",
    "            ['git', 'rev-parse', 'HEAD'], cwd=REPO_DIR, text=True",
    "        ).strip()",
    "    except Exception:",
    "        return 'unknown'",
    "",
    "",
    "def _full_run_prompts_hash() -> str:",
    "    return hashlib.sha256((PROMPTS_DIR / 'full_run_manifest.json').read_bytes()).hexdigest()",
    "",
    "",
    "def _full_run_entries_for(elicitation: str) -> list[dict]:",
    "    if elicitation == 'freeform':",
    "        return [",
    "            {'vignette_id': e['vignette_id'], 'path': e['freeform_path']}",
    "            for e in FULL_RUN_FREEFORM",
    "        ]",
    "    return [",
    "        {'vignette_id': e['vignette_id'], 'path': e['structured_path']}",
    "        for e in FULL_RUN_STRUCTURED",
    "    ]",
    "",
    "",
    "def run_full_run_model(model_cfg: dict) -> dict:",
    "    family = model_cfg['family']",
    "    print(f\"\\n=== FULL RUN: {family}/{model_cfg['model']} ===\")",
    "",
    "    records = []  # (elicitation, entry, cache_key) -- freeform block first, by construction",
    "    for elicitation in ('freeform', 'structured'):",
    "        max_tokens = GENERATION_MAX_TOKENS if elicitation == 'freeform' else STRUCTURED_MAX_TOKENS",
    "        for e in _full_run_entries_for(elicitation):",
    "            key = cache_key_for(",
    "                family=family, model=model_cfg['model'], system_prompt='',",
    "                messages=[{'role': 'user', 'content': read_prompt_text(e)}],",
    "                params=GenerationParams(",
    "                    temperature=0.0, top_p=1.0, max_tokens=max_tokens, seed=None,",
    "                ),",
    "            )",
    "            records.append((elicitation, e, key))",
    "",
    "    all_keys = [r[2] for r in records]",
    "    key_to_record = {r[2]: r for r in records}",
    "    todo = pending_keys(all_keys, RESPONSES_DIR)",
    "    already_done = len(all_keys) - len(todo)",
    "    print(f'{already_done}/{len(all_keys)} already checkpointed (resuming)' if already_done",
    "          else f'0/{len(all_keys)} checkpointed -- starting fresh')",
    "    if not todo:",
    "        print('Nothing to do for this model.')",
    "        return {'family': family, 'n_done': 0, 'elapsed': 0.0}",
    "",
    "    total_input_tokens = 0",
    "    total_output_tokens = 0",
    "    n_done = 0",
    "    model = None",
    "    tokenizer = None",
    "    batch_size = model_cfg.get('batch_size', BATCH_SIZE)",
    "    print(f'Using batch_size={batch_size} for {family}'",
    "          + (' (per-model override)' if 'batch_size' in model_cfg else ' (Section 7 default)'))",
    "    try:",
    "        model, tokenizer = load_hf_model(model_cfg)",
    "        start = time.time()",
    "",
    "        # Grouping todo BY ELICITATION (not blindly chunking through it) keeps free-form-",
    "        # before-structured true even after resuming a partially-completed run.",
    "        for elicitation in ('freeform', 'structured'):",
    "            max_tokens = GENERATION_MAX_TOKENS if elicitation == 'freeform' else STRUCTURED_MAX_TOKENS",
    "            elicitation_todo = [k for k in todo if key_to_record[k][0] == elicitation]",
    "            for batch_start in range(0, len(elicitation_todo), batch_size):",
    "                chunk_keys = elicitation_todo[batch_start:batch_start + batch_size]",
    "                chunk_entries = [key_to_record[k][1] for k in chunk_keys]",
    "",
    "                chunk_texts, chunk_out_tok, chunk_in_tok, chunk_stop, _elapsed = generate_batch(",
    "                    model, tokenizer, chunk_entries,",
    "                    temperature=0.0, top_p=1.0, max_new_tokens=max_tokens,",
    "                )",
    "",
    "                for key, entry, text, out_tok, in_tok, stop_reason in zip(",
    "                    chunk_keys, chunk_entries, chunk_texts, chunk_out_tok, chunk_in_tok,",
    "                    chunk_stop,",
    "                ):",
    "                    total_input_tokens += in_tok",
    "                    total_output_tokens += out_tok",
    "                    write_response_atomic(",
    "                        RESPONSES_DIR,",
    "                        key,",
    "                        text=text,",
    "                        raw={",
    "                            'vignette_id': entry['vignette_id'],",
    "                            'elicitation': elicitation,",
    "                            'model': model_cfg['model'],",
    "                            'model_revision': model_cfg['revision'],",
    "                            'quantization': model_cfg['quantization'],",
    "                            'seed': None,",
    "                            'stop_reason': stop_reason,",
    "                            'truncated': stop_reason == 'max_tokens',",
    "                        },",
    "                        input_tokens=in_tok,",
    "                        output_tokens=out_tok,",
    "                    )",
    "                    n_done += 1",
    "",
    "                if n_done % PROGRESS_EVERY < batch_size or n_done == len(todo):",
    "                    elapsed = time.time() - start",
    "                    rate = n_done / elapsed if elapsed > 0 else 0",
    "                    remaining = (len(todo) - n_done) / rate if rate > 0 else float('inf')",
    "                    print(f'  {n_done}/{len(todo)} done, {elapsed/60:.1f}min elapsed, '",
    "                          f'ETA {remaining/60:.1f}min remaining')",
    "        elapsed_total = time.time() - start",
    "    finally:",
    "        if model is not None:",
    "            unload_hf_model(model)",
    "        if tokenizer is not None:",
    "            del tokenizer",
    "        gc.collect()",
    "        torch.cuda.empty_cache()",
    "",
    "    run_id = f\"iris-tmed-full-run-{family}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}\"",
    "    manifest = {",
    "        'run_id': run_id,",
    "        'model_identifiers': [{",
    "            'family': family, 'name': model_cfg['model'], 'version': model_cfg['revision'],",
    "        }],",
    "        'temperature': 0.0,",
    "        'top_p': 1.0,",
    "        'max_tokens': {'freeform': GENERATION_MAX_TOKENS, 'structured': STRUCTURED_MAX_TOKENS},",
    "        'seed': None,",
    "        'prompt_template_hash': _full_run_prompts_hash(),",
    "        'vignette_set_version': 'v1',",
    "        'rubric_version': 'v1',",
    "        'git_commit_sha': _repo_git_commit_sha(),",
    "        'utc_timestamp': datetime.now(UTC).isoformat(),",
    "        'total_input_tokens': total_input_tokens,",
    "        'total_output_tokens': total_output_tokens,",
    "        'quantization': model_cfg['quantization'],",
    "        'base_model': model_cfg['base_model'],",
    "        'base_model_revision': model_cfg['base_model_revision'],",
    "        'batch_size': batch_size,",
    "        'n_responses_this_run': len(todo),",
    "        'n_responses_total': len(all_keys),",
    "        'n_freeform_vignettes': len(FULL_RUN_FREEFORM),",
    "        'n_structured_vignettes': len(FULL_RUN_STRUCTURED),",
    "        'holdout_excluded': True,",
    "        'excluded_models': ['ibm'],",
    "        'notes': (",
    "            'IRIS TMED full run: n=1 greedy decoding, freeform (all non-holdout) + '",
    "            'structured (subset grounding a QUESTION_BANK axis), per-arm max_tokens. '",
    "            'Granite/ibm excluded -- see results/LIMITATIONS.md.'",
    "        ),",
    "    }",
    "    (MANIFEST_DIR / f'{run_id}.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')",
    "    print(f'Manifest written: {run_id}.json')",
    "    return {'family': family, 'n_done': len(todo), 'elapsed': elapsed_total}",
))
CELLS.append(code(
    "_full_run_start = time.time()",
    "_full_run_results = []",
    "for _i, model_cfg in enumerate(FULL_RUN_MODEL_REGISTRY):",
    "    _full_run_results.append(run_full_run_model(model_cfg))",
    "",
    "    # Flag immediately if projected wall-clock would run past the freeze deadline --",
    "    # projected from the models actually run so far, not guessed up front.",
    "    _elapsed_so_far = time.time() - _full_run_start",
    "    _models_done = _i + 1",
    "    _models_left = len(FULL_RUN_MODEL_REGISTRY) - _models_done",
    "    if _models_left and _models_done:",
    "        _projected_remaining = (_elapsed_so_far / _models_done) * _models_left",
    "        _projected_finish = datetime.now(UTC) + timedelta(seconds=_projected_remaining)",
    "        if _projected_finish > FREEZE_DEADLINE:",
    "            print(f'\\n*** FLAG: projected finish {_projected_finish.isoformat()} is PAST the '",
    "                  f'{FREEZE_DEADLINE.date()} instrument freeze deadline. Report this before '",
    "                  f'continuing rather than letting the run silently overrun it. ***')",
    "",
    "print('\\nFull run complete (or resumed to completion).')",
))

# ---------------------------------------------------------------------------
CELLS.append(md(
    "## 13. Full-run post-run sanity check",
    "",
    "Same shape as Section 11 -- confirms every (model, vignette, arm) pair"
    " produced exactly one checkpointed response before you copy"
    " `data/responses/` and `results/manifests/` back into the main repo for"
    " `scripts/analyze_full_run.py` to consume.",
))
CELLS.append(code(
    "_expected_full_run = (",
    "    len(FULL_RUN_FREEFORM) + len(FULL_RUN_STRUCTURED)",
    ") * len(FULL_RUN_MODEL_REGISTRY)",
    "_full_run_keys = set()",
    "for model_cfg in FULL_RUN_MODEL_REGISTRY:",
    "    for elicitation in ('freeform', 'structured'):",
    "        max_tokens = GENERATION_MAX_TOKENS if elicitation == 'freeform' else STRUCTURED_MAX_TOKENS",
    "        for e in _full_run_entries_for(elicitation):",
    "            _full_run_keys.add(cache_key_for(",
    "                family=model_cfg['family'], model=model_cfg['model'], system_prompt='',",
    "                messages=[{'role': 'user', 'content': read_prompt_text(e)}],",
    "                params=GenerationParams(",
    "                    temperature=0.0, top_p=1.0, max_tokens=max_tokens, seed=None,",
    "                ),",
    "            ))",
    "",
    "_actual_full_run = len(_full_run_keys & load_completed_keys(RESPONSES_DIR))",
    "print(f'Expected {_expected_full_run} full-run responses, found {_actual_full_run} checkpointed.')",
    "",
    "_empty_or_truncated = []",
    "for key in _full_run_keys:",
    "    path = checkpoint_path(RESPONSES_DIR, key)",
    "    if not path.exists():",
    "        continue",
    "    data = json.loads(path.read_text(encoding='utf-8'))",
    "    if not data['text'].strip():",
    "        _empty_or_truncated.append((key, 'empty'))",
    "    elif data['raw'].get('truncated'):",
    "        _empty_or_truncated.append((key, 'truncated (hit max_tokens)'))",
    "",
    "print(f'Empty or truncated full-run responses: {len(_empty_or_truncated)}')",
    "for key, reason in _empty_or_truncated[:20]:",
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
