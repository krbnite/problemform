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
