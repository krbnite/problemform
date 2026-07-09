import pytest

from problemform.core.language_models import (
    DEFAULT_ANTHROPIC_MODEL,
    DEFAULT_OPENAI_MODEL,
    AnthropicProvider,
    OpenAIProvider,
    make_provider,
)


@pytest.fixture
def fake_keys(monkeypatch):
    """SDK clients read API keys at __init__; give them dummy values."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.delenv("PROBLEMFORM_PROVIDER", raising=False)
    monkeypatch.delenv("PROBLEMFORM_MODEL", raising=False)


def test_make_provider_defaults_to_openai(fake_keys):
    p = make_provider()
    assert isinstance(p, OpenAIProvider)
    assert p.model == DEFAULT_OPENAI_MODEL


def test_make_provider_explicit_openai(fake_keys):
    p = make_provider("openai")
    assert isinstance(p, OpenAIProvider)
    assert p.model == DEFAULT_OPENAI_MODEL


def test_make_provider_explicit_anthropic(fake_keys):
    p = make_provider("anthropic")
    assert isinstance(p, AnthropicProvider)
    assert p.model == DEFAULT_ANTHROPIC_MODEL


def test_make_provider_model_arg_overrides_default(fake_keys):
    p = make_provider("anthropic", model="claude-opus-4-8")
    assert isinstance(p, AnthropicProvider)
    assert p.model == "claude-opus-4-8"


def test_make_provider_env_provider_overrides_default(fake_keys, monkeypatch):
    monkeypatch.setenv("PROBLEMFORM_PROVIDER", "anthropic")
    p = make_provider()
    assert isinstance(p, AnthropicProvider)
    assert p.model == DEFAULT_ANTHROPIC_MODEL


def test_make_provider_env_model_overrides_default(fake_keys, monkeypatch):
    monkeypatch.setenv("PROBLEMFORM_MODEL", "gpt-5")
    p = make_provider("openai")
    assert isinstance(p, OpenAIProvider)
    assert p.model == "gpt-5"


def test_make_provider_explicit_model_beats_env(fake_keys, monkeypatch):
    monkeypatch.setenv("PROBLEMFORM_MODEL", "from-env")
    p = make_provider("openai", model="from-arg")
    assert p.model == "from-arg"


def test_make_provider_rejects_unknown_name(fake_keys):
    with pytest.raises(ValueError, match="Unknown provider"):
        make_provider("cohere")


def test_make_provider_is_case_insensitive(fake_keys):
    assert isinstance(make_provider("ANTHROPIC"), AnthropicProvider)
    assert isinstance(make_provider("OpenAI"), OpenAIProvider)


# ---------- Anthropic response validation ----------------------------------


from types import SimpleNamespace

from pydantic import BaseModel

from problemform.core.language_models import (
    EmptyResponseError,
    RefusalError,
    StructuredOutputError,
    TruncatedResponseError,
    _extract_anthropic_text,
)


def _msg(stop_reason, blocks):
    return SimpleNamespace(stop_reason=stop_reason, content=blocks)


def _text_block(text):
    return SimpleNamespace(type="text", text=text)


def test_extract_anthropic_text_returns_joined_text_for_normal_stop():
    msg = _msg("end_turn", [_text_block("a"), _text_block("b")])
    assert _extract_anthropic_text(msg) == "a\nb"


def test_extract_anthropic_text_raises_truncated_error_on_max_tokens():
    msg = _msg("max_tokens", [_text_block("partial")])
    with pytest.raises(TruncatedResponseError, match="truncated at max_tokens"):
        _extract_anthropic_text(msg)


def test_extract_anthropic_text_raises_refusal_error():
    msg = _msg("refusal", [])
    with pytest.raises(RefusalError, match="refused"):
        _extract_anthropic_text(msg)


def test_extract_anthropic_text_raises_for_unexpected_tool_use():
    msg = _msg("tool_use", [SimpleNamespace(type="tool_use")])
    with pytest.raises(StructuredOutputError) as exc:
        _extract_anthropic_text(msg)
    assert "tool_use" in str(exc.value)
    # base error, not one of the more specific subclasses
    assert not isinstance(exc.value, (TruncatedResponseError, RefusalError, EmptyResponseError))


def test_extract_anthropic_text_raises_empty_on_no_text_blocks():
    msg = _msg("end_turn", [SimpleNamespace(type="image")])
    with pytest.raises(EmptyResponseError, match="no text content"):
        _extract_anthropic_text(msg)


def test_extract_anthropic_text_raises_empty_on_whitespace_only_text():
    msg = _msg("end_turn", [_text_block(" \n ")])
    with pytest.raises(EmptyResponseError):
        _extract_anthropic_text(msg)


class _Echo(BaseModel):
    value: str


def test_anthropic_provider_passes_specific_errors_through_generate_structured(fake_keys, monkeypatch):
    provider = AnthropicProvider("claude-test")

    def boom(*a, **kw):
        raise TruncatedResponseError("response truncated")

    monkeypatch.setattr(provider, "generate_text", boom)

    with pytest.raises(TruncatedResponseError, match="response truncated"):
        provider.generate_structured("prompt", _Echo)


def test_anthropic_generate_text_omits_system_when_none(fake_keys, monkeypatch):
    """Regression: ``system=None`` must not be sent to the API.

    Passing ``system=None`` made the SDK serialize ``system: null``, which the
    Anthropic API rejects (``400 ... system: Input should be a valid array``).
    The provider must omit the key entirely when no system prompt is given.
    """
    provider = AnthropicProvider("claude-test")
    calls: dict = {}

    def fake_create(**kwargs):
        calls.update(kwargs)
        return _msg("end_turn", [_text_block("hello")])

    monkeypatch.setattr(provider.client.messages, "create", fake_create)

    out = provider.generate_text("hi")  # system defaults to None
    assert out == "hello"
    assert "system" not in calls
    assert calls["messages"] == [{"role": "user", "content": "hi"}]


def test_anthropic_generate_text_includes_system_when_provided(fake_keys, monkeypatch):
    """When a system prompt is given, it is forwarded as-is."""
    provider = AnthropicProvider("claude-test")
    calls: dict = {}

    def fake_create(**kwargs):
        calls.update(kwargs)
        return _msg("end_turn", [_text_block("ok")])

    monkeypatch.setattr(provider.client.messages, "create", fake_create)

    provider.generate_text("hi", system="be terse")
    assert calls.get("system") == "be terse"


# ---------- OpenAI response validation -------------------------------------


from problemform.core.language_models import (
    ContentFilterError,
    _validate_openai_response,
)


def _openai_response(
    *,
    status="completed",
    reason=None,
    output_parsed=None,
    output_text=None,
    output=None,
):
    incomplete = SimpleNamespace(reason=reason) if reason is not None else None
    return SimpleNamespace(
        status=status,
        incomplete_details=incomplete,
        output_parsed=output_parsed,
        output_text=output_text,
        output=output or [],
    )


def _message_with_blocks(blocks):
    return SimpleNamespace(content=blocks)


def _refusal_block(text="not allowed"):
    return SimpleNamespace(type="refusal", refusal=text)


def _output_text_block(text):
    return SimpleNamespace(type="output_text", text=text)


def test_validate_openai_response_returns_parsed_on_completed():
    echo = _Echo(value="ok")
    r = _openai_response(status="completed", output_parsed=echo)
    assert _validate_openai_response(r, _Echo) is echo


def test_validate_openai_response_raises_truncated_on_max_output_tokens():
    r = _openai_response(status="incomplete", reason="max_output_tokens")
    with pytest.raises(TruncatedResponseError, match="max_output_tokens"):
        _validate_openai_response(r, _Echo)


def test_validate_openai_response_raises_content_filter():
    r = _openai_response(status="incomplete", reason="content_filter")
    with pytest.raises(ContentFilterError, match="content filter"):
        _validate_openai_response(r, _Echo)


def test_validate_openai_response_unknown_incomplete_reason_is_base_error():
    r = _openai_response(status="incomplete", reason="something_else")
    with pytest.raises(StructuredOutputError) as exc:
        _validate_openai_response(r, _Echo)
    assert "something_else" in str(exc.value)
    assert not isinstance(
        exc.value,
        (TruncatedResponseError, RefusalError, ContentFilterError, EmptyResponseError),
    )


def test_validate_openai_response_raises_refusal_when_block_present():
    r = _openai_response(
        status="completed",
        output=[_message_with_blocks([_refusal_block("policy violation")])],
        output_parsed=_Echo(value="ignored"),  # refusal beats parsed presence
    )
    with pytest.raises(RefusalError, match="policy violation"):
        _validate_openai_response(r, _Echo)


def test_validate_openai_response_raises_empty_when_parsed_is_none():
    r = _openai_response(status="completed", output_parsed=None)
    with pytest.raises(EmptyResponseError, match="no parsed output"):
        _validate_openai_response(r, _Echo)


def test_openai_generate_text_raises_empty_on_blank_output_text(fake_keys, monkeypatch):
    provider = OpenAIProvider("gpt-test")

    def fake_create(*a, **kw):
        return _openai_response(status="completed", output_text="   \n  ")

    monkeypatch.setattr(provider.client.responses, "create", fake_create)

    with pytest.raises(EmptyResponseError):
        provider.generate_text("prompt")


def test_openai_generate_structured_passes_specific_errors_through(fake_keys, monkeypatch):
    provider = OpenAIProvider("gpt-test")

    def fake_parse(*a, **kw):
        return _openai_response(status="incomplete", reason="content_filter")

    monkeypatch.setattr(provider.client.responses, "parse", fake_parse)

    with pytest.raises(ContentFilterError):
        provider.generate_structured("prompt", _Echo)


def test_openai_provider_specific_errors_are_caught_by_umbrella(fake_keys, monkeypatch):
    """Existing callers that catch StructuredOutputError still work."""
    provider = OpenAIProvider("gpt-test")

    def fake_parse(*a, **kw):
        return _openai_response(status="incomplete", reason="max_output_tokens")

    monkeypatch.setattr(provider.client.responses, "parse", fake_parse)

    with pytest.raises(StructuredOutputError):
        provider.generate_structured("prompt", _Echo)
