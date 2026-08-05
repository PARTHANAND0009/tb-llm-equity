# tb-llm-equity

Equity audit of LLM diagnostic reasoning under NTEP (India's National TB
Elimination Programme) protocols versus the WHO consolidated guidelines on
tuberculosis (the "comparator"), using paired vignettes and frozen,
versioned scoring.

This repo is currently a scaffold — see [CLAUDE.md](CLAUDE.md) for the
project rules that govern every later task, and `make help`-style targets
below.

## Layout

```
data/protocols/     raw NTEP + WHO + CDC source docs
data/divergence/    structured NTEP-vs-WHO divergence table
data/vignettes/     vignette JSON files, versioned
data/responses/     cached raw model responses
results/            scored outputs, stats, figures
results/manifests/  one JSON manifest per experiment run (RULE 1)
src/tb_equity/      package code
notebooks/          Colab-compatible notebooks for open-weight models
tests/
```

## Setup

Requires Python 3.11 and [uv](https://docs.astral.sh/uv/).

```
make setup   # uv sync + install pre-commit hooks
make test    # pytest
make lint    # ruff check
```

## Rules

See [CLAUDE.md](CLAUDE.md). In short: every run gets a manifest, the rubric
is frozen per version, no identifying school/city/state strings anywhere
under `data/` or `results/`, all API responses are cached, generator and
evaluator model families never overlap, every dimension has a deterministic
scorer first, and 15 vignettes are held out until final confirmation.
