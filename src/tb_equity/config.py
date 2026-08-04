"""Config loading and RULE 5 (GENERATOR/EVALUATOR SEPARATION) enforcement.

The model family used to generate or critique vignettes must never be a
family under evaluation. ``assert_generator_evaluator_disjoint`` reads
config/models.yaml and raises if ``generation.family`` appears among
``evaluation.models[].family``. ``require_generation_model`` additionally
checks that a generator has actually been configured yet. Call
``require_generation_model`` at the start of any script that
generates/critiques vignettes.
"""

from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
MODELS_CONFIG_PATH = CONFIG_DIR / "models.yaml"


class GeneratorEvaluatorOverlapError(Exception):
    """Raised when the generation model family also appears in the evaluation roster."""


class GenerationNotConfiguredError(Exception):
    """Raised when generation.model/family in config/models.yaml is unset."""


def load_models_config(path: Path = MODELS_CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def assert_generator_evaluator_disjoint(path: Path = MODELS_CONFIG_PATH) -> None:
    config = load_models_config(path)
    generation_family = (config.get("generation") or {}).get("family")
    evaluation_families = {
        m.get("family") for m in (config.get("evaluation") or {}).get("models") or []
    }
    if generation_family and generation_family in evaluation_families:
        raise GeneratorEvaluatorOverlapError(
            f"Model family {generation_family!r} is configured as both the vignette "
            "generator (generation.family) and a model under evaluation "
            "(evaluation.models[].family) in config/models.yaml. RULE 5 forbids this — "
            "the family used to generate or critique vignettes must not be a family "
            "under evaluation."
        )


def require_generation_model(path: Path = MODELS_CONFIG_PATH) -> dict:
    """Return the `generation` config block; raise if not yet configured.

    Also enforces RULE 5 disjointness as a side effect, so callers only need
    to call this one function before generating or critiquing vignettes.
    """
    config = load_models_config(path)
    generation = config.get("generation") or {}
    if not generation.get("model") or not generation.get("family"):
        raise GenerationNotConfiguredError(
            "config/models.yaml: generation.model and generation.family are not set. "
            "Choose a generator model/provider and set both fields before running "
            "vignette generation or critique. See CLAUDE.md RULE 5."
        )
    assert_generator_evaluator_disjoint(path)
    return generation
