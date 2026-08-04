import pytest
import yaml

from tb_equity.config import (
    GenerationNotConfiguredError,
    GeneratorEvaluatorOverlapError,
    assert_generator_evaluator_disjoint,
    require_generation_model,
)


def _write_config(tmp_path, *, gen_family, gen_model, eval_families):
    path = tmp_path / "models.yaml"
    config = {
        "generation": {"model": gen_model, "family": gen_family},
        "evaluation": {
            "models": [{"family": f, "model": "placeholder"} for f in eval_families]
        },
    }
    path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return path


def test_disjoint_families_pass(tmp_path):
    path = _write_config(
        tmp_path, gen_family="anthropic", gen_model="claude-x", eval_families=["openai", "google"]
    )
    assert_generator_evaluator_disjoint(path)  # should not raise


def test_overlapping_family_raises(tmp_path):
    path = _write_config(
        tmp_path, gen_family="openai", gen_model="gpt-x", eval_families=["openai", "google"]
    )
    with pytest.raises(GeneratorEvaluatorOverlapError):
        assert_generator_evaluator_disjoint(path)


def test_empty_config_passes(tmp_path):
    path = tmp_path / "models.yaml"
    path.write_text(
        "generation:\n  model: null\n  family: null\nevaluation:\n  models: []\n", encoding="utf-8"
    )
    assert_generator_evaluator_disjoint(path)  # should not raise


def test_require_generation_model_raises_when_unset(tmp_path):
    path = _write_config(tmp_path, gen_family=None, gen_model=None, eval_families=[])
    with pytest.raises(GenerationNotConfiguredError):
        require_generation_model(path)


def test_require_generation_model_returns_block_when_set(tmp_path):
    path = _write_config(tmp_path, gen_family="anthropic", gen_model="claude-x", eval_families=[])
    block = require_generation_model(path)
    assert block == {"model": "claude-x", "family": "anthropic"}


def test_require_generation_model_enforces_disjointness(tmp_path):
    path = _write_config(
        tmp_path, gen_family="openai", gen_model="gpt-x", eval_families=["openai"]
    )
    with pytest.raises(GeneratorEvaluatorOverlapError):
        require_generation_model(path)
