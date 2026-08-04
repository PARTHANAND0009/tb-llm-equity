"""Config loading and RULE 5 (GENERATOR/EVALUATOR SEPARATION) enforcement.

The model family used to generate or critique vignettes must never be a
family under evaluation. ``assert_generator_evaluator_disjoint`` reads the
roster from config/models.yaml and raises if the two sets intersect. Call it
at the start of any script that generates/critiques vignettes or runs
evaluation arms.
"""

from pathlib import Path

import yaml

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
MODELS_CONFIG_PATH = CONFIG_DIR / "models.yaml"


class GeneratorEvaluatorOverlapError(Exception):
    """Raised when a model family appears in both the generator and evaluator rosters."""


def load_models_config(path: Path = MODELS_CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def assert_generator_evaluator_disjoint(path: Path = MODELS_CONFIG_PATH) -> None:
    config = load_models_config(path)
    generators = set(config.get("generator_model_families") or [])
    evaluators = set(config.get("evaluator_model_families") or [])
    overlap = generators & evaluators
    if overlap:
        raise GeneratorEvaluatorOverlapError(
            f"Model family/families {sorted(overlap)} listed as both generator "
            "and evaluator in config/models.yaml. RULE 5 forbids this — the "
            "family used to generate or critique vignettes must not be a "
            "family under evaluation."
        )
