"""Cached, provider-pluggable model client (RULE 4 — CACHE EVERYTHING).

Every call is cached to disk keyed by sha256(model + prompt + params). The
full raw response object is stored, not just parsed fields, and a re-run
with an identical cache key must hit cache rather than call the API again.

Provider SDKs are imported lazily inside `_call_<provider>` so this module
imports cleanly even when no provider extra is installed — only the extra
for the configured provider is required at call time.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = REPO_ROOT / "data" / "responses"


@dataclass(frozen=True)
class GenerationParams:
    temperature: float
    top_p: float
    max_tokens: int
    seed: int | None = None


@dataclass(frozen=True)
class ModelResponse:
    text: str
    raw: dict[str, Any]
    input_tokens: int
    output_tokens: int
    cache_key: str
    from_cache: bool


def cache_key_for(
    *, family: str, model: str, system_prompt: str, messages: list[dict], params: GenerationParams
) -> str:
    """sha256(model + prompt + params) per RULE 4 — deterministic across processes."""
    payload = {
        "family": family,
        "model": model,
        "system_prompt": system_prompt,
        "messages": messages,
        "params": {
            "temperature": params.temperature,
            "top_p": params.top_p,
            "max_tokens": params.max_tokens,
            "seed": params.seed,
        },
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class CachingLLMClient:
    """Wraps a provider call with a disk cache keyed by cache_key_for(...)."""

    family: str
    model: str
    cache_dir: Path = field(default_factory=lambda: DEFAULT_CACHE_DIR)

    def _cache_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.json"

    def complete(
        self, *, system_prompt: str, messages: list[dict], params: GenerationParams
    ) -> ModelResponse:
        key = cache_key_for(
            family=self.family,
            model=self.model,
            system_prompt=system_prompt,
            messages=messages,
            params=params,
        )
        cache_path = self._cache_path(key)
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            return ModelResponse(
                text=cached["text"],
                raw=cached["raw"],
                input_tokens=cached["input_tokens"],
                output_tokens=cached["output_tokens"],
                cache_key=key,
                from_cache=True,
            )

        text, raw, input_tokens, output_tokens = self._call_provider(
            system_prompt=system_prompt, messages=messages, params=params
        )

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "text": text,
                    "raw": raw,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return ModelResponse(
            text=text,
            raw=raw,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_key=key,
            from_cache=False,
        )

    def _call_provider(
        self, *, system_prompt: str, messages: list[dict], params: GenerationParams
    ) -> tuple[str, dict[str, Any], int, int]:
        if self.family == "anthropic":
            return self._call_anthropic(
                system_prompt=system_prompt, messages=messages, params=params
            )
        if self.family == "openai":
            return self._call_openai(system_prompt=system_prompt, messages=messages, params=params)
        if self.family == "google":
            return self._call_google(system_prompt=system_prompt, messages=messages, params=params)
        raise ValueError(
            f"Unknown model family {self.family!r}. Add a _call_<family> method to "
            "CachingLLMClient before configuring it as generation.family."
        )

    def _call_anthropic(
        self, *, system_prompt: str, messages: list[dict], params: GenerationParams
    ) -> tuple[str, dict[str, Any], int, int]:
        import anthropic

        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self.model,
            max_tokens=params.max_tokens,
            system=system_prompt,
            messages=messages,
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return (
            text,
            response.to_dict(),
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

    def _call_openai(
        self, *, system_prompt: str, messages: list[dict], params: GenerationParams
    ) -> tuple[str, dict[str, Any], int, int]:
        import openai

        client = openai.OpenAI()
        response = client.chat.completions.create(
            model=self.model,
            temperature=params.temperature,
            top_p=params.top_p,
            max_tokens=params.max_tokens,
            messages=[{"role": "system", "content": system_prompt}, *messages],
        )
        text = response.choices[0].message.content or ""
        return (
            text,
            response.model_dump(),
            response.usage.prompt_tokens,
            response.usage.completion_tokens,
        )

    def _call_google(
        self, *, system_prompt: str, messages: list[dict], params: GenerationParams
    ) -> tuple[str, dict[str, Any], int, int]:
        from google import genai

        client = genai.Client()
        contents = "\n\n".join(m["content"] for m in messages)
        response = client.models.generate_content(
            model=self.model,
            contents=contents,
            config={"system_instruction": system_prompt, "temperature": params.temperature},
        )
        usage = response.usage_metadata
        return (
            response.text or "",
            response.to_json_dict(),
            usage.prompt_token_count,
            usage.candidates_token_count,
        )
