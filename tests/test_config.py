import textwrap

import pytest

from tb_equity.config import (
    GeneratorEvaluatorOverlapError,
    assert_generator_evaluator_disjoint,
)


def _write_config(tmp_path, generators, evaluators):
    path = tmp_path / "models.yaml"
    path.write_text(
        textwrap.dedent(f"""\
            generator_model_families: {generators}
            evaluator_model_families: {evaluators}
            """),
        encoding="utf-8",
    )
    return path


def test_disjoint_families_pass(tmp_path):
    path = _write_config(tmp_path, ["anthropic"], ["openai", "meta-llama"])
    assert_generator_evaluator_disjoint(path)  # should not raise


def test_overlapping_family_raises(tmp_path):
    path = _write_config(tmp_path, ["openai"], ["openai", "meta-llama"])
    with pytest.raises(GeneratorEvaluatorOverlapError):
        assert_generator_evaluator_disjoint(path)


def test_empty_config_passes(tmp_path):
    path = tmp_path / "models.yaml"
    path.write_text(
        "generator_model_families: []\nevaluator_model_families: []\n", encoding="utf-8"
    )
    assert_generator_evaluator_disjoint(path)  # should not raise
