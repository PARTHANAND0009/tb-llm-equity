"""Resumable per-response checkpointing for the open-weight (Colab) inference

path (RULE 4 — CACHE EVERYTHING, applied without a live API client).

The API path (CachingLLMClient in llm_client.py) gets resumability for free:
its disk cache is keyed by cache_key_for(...) and a re-run that hits an
existing cache file skips the call entirely. The Colab notebook has no such
client in the loop — it calls vLLM directly — so this module replicates the
same cache_key_for(...) addressing and the same on-disk JSON shape
({"text", "raw", "input_tokens", "output_tokens"}) by hand, so a checkpoint
written here is byte-for-byte interchangeable with one CachingLLMClient
would have written, and the Phase 5 scorer never has to know which path
produced a given file under data/responses/.

Free Colab disconnects without warning, so every write here is atomic
(write to a sibling temp file, then os.replace onto the real path) — a kill
mid-write must never leave a checkpoint file that looks done but contains
truncated JSON. On restart, load_completed_keys() reads whatever checkpoint
files exist and the caller skips exactly those, so no response is ever
regenerated and none is ever silently skipped.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any


def checkpoint_path(checkpoint_dir: Path, cache_key: str) -> Path:
    return checkpoint_dir / f"{cache_key}.json"


def is_done(checkpoint_dir: Path, cache_key: str) -> bool:
    return checkpoint_path(checkpoint_dir, cache_key).exists()


def load_completed_keys(checkpoint_dir: Path) -> set[str]:
    if not checkpoint_dir.exists():
        return set()
    return {p.stem for p in checkpoint_dir.glob("*.json")}


def write_response_atomic(
    checkpoint_dir: Path,
    cache_key: str,
    *,
    text: str,
    raw: dict[str, Any],
    input_tokens: int,
    output_tokens: int,
) -> Path:
    """Write one response checkpoint, atomically.

    A crash (Colab disconnect, killed process) partway through this
    function must leave either the complete old state (no file) or the
    complete new state (a valid, fully-written file) — never a half-written
    file that load_completed_keys() would count as done. Achieved by
    writing to a uniquely-named temp file in the same directory (so the
    final os.replace is same-filesystem, hence atomic) and only replacing
    the real target once the write is fully flushed to disk.
    """
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    target = checkpoint_path(checkpoint_dir, cache_key)
    tmp_path = checkpoint_dir / f".tmp-{cache_key}-{uuid.uuid4().hex}.json"
    payload = {
        "text": text,
        "raw": raw,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, indent=2))
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, target)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
    return target


def pending_keys(all_keys: list[str], checkpoint_dir: Path) -> list[str]:
    """all_keys, minus whatever's already checkpointed -- order preserved."""
    completed = load_completed_keys(checkpoint_dir)
    return [k for k in all_keys if k not in completed]
