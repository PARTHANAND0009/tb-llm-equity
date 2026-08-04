from tb_equity.llm_client import CachingLLMClient, GenerationParams, cache_key_for


def _params(**overrides):
    defaults = {"temperature": 0.9, "top_p": 1.0, "max_tokens": 1600, "seed": 42}
    defaults.update(overrides)
    return GenerationParams(**defaults)


def _key(*, system_prompt="sys", messages=None, params=None):
    messages = messages if messages is not None else [{"role": "user", "content": "hello"}]
    params = params if params is not None else _params()
    return cache_key_for(
        family="anthropic", model="m", system_prompt=system_prompt, messages=messages, params=params
    )


def test_cache_key_is_deterministic():
    assert _key() == _key()


def test_cache_key_changes_with_prompt():
    assert _key(system_prompt="sys") != _key(system_prompt="different")


def test_cache_key_changes_with_params():
    assert _key(params=_params()) != _key(params=_params(temperature=0.1))


def test_complete_hits_cache_on_second_call(tmp_path, monkeypatch):
    call_count = {"n": 0}

    def fake_call_provider(self, *, system_prompt, messages, params):
        call_count["n"] += 1
        return ("fake response text", {"raw": "payload"}, 10, 20)

    monkeypatch.setattr(CachingLLMClient, "_call_provider", fake_call_provider)

    client = CachingLLMClient(family="anthropic", model="test-model", cache_dir=tmp_path)
    params = _params()
    messages = [{"role": "user", "content": "hello"}]

    first = client.complete(system_prompt="sys", messages=messages, params=params)
    assert first.from_cache is False
    assert first.text == "fake response text"
    assert call_count["n"] == 1

    second = client.complete(system_prompt="sys", messages=messages, params=params)
    assert second.from_cache is True
    assert second.text == "fake response text"
    assert call_count["n"] == 1  # not called again -- cache hit

    cached_files = list(tmp_path.glob("*.json"))
    assert len(cached_files) == 1


def test_complete_stores_full_raw_response(tmp_path, monkeypatch):
    def fake_call_provider(self, *, system_prompt, messages, params):
        return ("text", {"id": "resp_123", "usage": {"input": 1, "output": 2}}, 1, 2)

    monkeypatch.setattr(CachingLLMClient, "_call_provider", fake_call_provider)
    client = CachingLLMClient(family="openai", model="test-model", cache_dir=tmp_path)
    response = client.complete(
        system_prompt="sys", messages=[{"role": "user", "content": "x"}], params=_params()
    )
    assert response.raw == {"id": "resp_123", "usage": {"input": 1, "output": 2}}
