"""Tests the resumable checkpoint logic that notebooks/open_weight_inference.ipynb

uses, by simulating a kill mid-run with a stub generator (no GPU/vLLM
involved — this tests the resume mechanics, not model quality).
"""

import json

import pytest

from tb_equity.checkpoint import (
    checkpoint_path,
    is_done,
    load_completed_keys,
    pending_keys,
    write_response_atomic,
)


def _run_all(keys, checkpoint_dir, generate, kill_after=None):
    """Mimics the notebook's main loop: for each pending key, call

    generate(key) and checkpoint the result. If kill_after is given, stop
    (simulating a Colab disconnect) once that many NEW responses have been
    written in this call.
    """
    written_this_call = 0
    for key in pending_keys(keys, checkpoint_dir):
        if kill_after is not None and written_this_call >= kill_after:
            return  # simulated kill: stop before processing more
        text = generate(key)
        write_response_atomic(
            checkpoint_dir,
            key,
            text=text,
            raw={"stub": True, "key": key},
            input_tokens=10,
            output_tokens=5,
        )
        written_this_call += 1


def test_kill_mid_run_then_resume_completes_exactly_once_each(tmp_path):
    checkpoint_dir = tmp_path / "checkpoints"
    keys = [f"key-{i}" for i in range(20)]
    call_log: list[str] = []

    def generate(key):
        call_log.append(key)
        return f"response for {key}"

    # First "session": killed after 7 responses.
    _run_all(keys, checkpoint_dir, generate, kill_after=7)
    assert len(load_completed_keys(checkpoint_dir)) == 7
    assert len(call_log) == 7

    # Second "session" (fresh process, same checkpoint_dir): resumes.
    _run_all(keys, checkpoint_dir, generate, kill_after=5)
    assert len(load_completed_keys(checkpoint_dir)) == 12
    assert len(call_log) == 12  # no key generated twice

    # Third "session": runs to completion.
    _run_all(keys, checkpoint_dir, generate)
    assert load_completed_keys(checkpoint_dir) == set(keys)
    assert len(call_log) == 20
    assert len(set(call_log)) == 20  # every key generated exactly once, ever

    # Every checkpoint file has the right content, and is intact JSON.
    for key in keys:
        data = json.loads(checkpoint_path(checkpoint_dir, key).read_text(encoding="utf-8"))
        assert data["text"] == f"response for {key}"
        assert data["raw"]["key"] == key
        assert data["input_tokens"] == 10
        assert data["output_tokens"] == 5


def test_a_crash_during_write_leaves_no_checkpoint_file(tmp_path, monkeypatch):
    """A kill *during* the write itself (not just between responses) must

    not leave a file that load_completed_keys() would count as done --
    os.replace only happens after the full write+flush+fsync succeeds.
    """
    checkpoint_dir = tmp_path / "checkpoints"

    import tb_equity.checkpoint as checkpoint_mod

    real_replace = checkpoint_mod.os.replace

    def exploding_replace(*args, **kwargs):
        raise OSError("simulated disconnect mid-write")

    monkeypatch.setattr(checkpoint_mod.os, "replace", exploding_replace)

    with pytest.raises(OSError):
        write_response_atomic(
            checkpoint_dir, "key-x", text="partial", raw={}, input_tokens=1, output_tokens=1
        )

    assert not is_done(checkpoint_dir, "key-x")
    # no leftover temp file either
    leftovers = list(checkpoint_dir.glob(".tmp-*"))
    assert leftovers == []

    monkeypatch.setattr(checkpoint_mod.os, "replace", real_replace)
    write_response_atomic(
        checkpoint_dir, "key-x", text="full", raw={}, input_tokens=1, output_tokens=1
    )
    assert is_done(checkpoint_dir, "key-x")


def test_resume_on_a_checkpoint_dir_with_nothing_completed_yet(tmp_path):
    checkpoint_dir = tmp_path / "checkpoints"  # never created
    assert load_completed_keys(checkpoint_dir) == set()
    assert pending_keys(["a", "b"], checkpoint_dir) == ["a", "b"]


def test_pending_keys_preserves_order_and_skips_only_completed(tmp_path):
    checkpoint_dir = tmp_path / "checkpoints"
    write_response_atomic(checkpoint_dir, "b", text="x", raw={}, input_tokens=1, output_tokens=1)
    assert pending_keys(["a", "b", "c"], checkpoint_dir) == ["a", "c"]
