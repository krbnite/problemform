from __future__ import annotations

import os
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError


StructuredOutputT = TypeVar("StructuredOutputT", bound=BaseModel)

class LLMProvider(Protocol):
    def generate_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        """Generate an unstructured text response."""

    def generate_structured(
        self,
        prompt: str,
        output_model: type[StructuredOutputT],
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> StructuredOutputT:
        """Generate a structured response validated against a Pydantic model."""


class LLMError(RuntimeError):
    """Base exception for language model provider errors."""


class StructuredOutputError(LLMError):
    """Raised when a provider cannot return or validate structured output."""


class TruncatedResponseError(StructuredOutputError):
    """Raised when the provider stopped early due to a token / length limit."""


class RefusalError(StructuredOutputError):
    """Raised when the provider refused to respond."""


class EmptyResponseError(StructuredOutputError):
    """Raised when the provider returned no usable text content."""


class ContentFilterError(StructuredOutputError):
    """Raised when the provider's safety/content filter stopped generation."""


def _extract_anthropic_text(message) -> str:
    """Validate an Anthropic Messages response and return its joined text.

    Surfaces known failure modes (truncation, refusal, unexpected tool_use,
    empty content) as specific ``StructuredOutputError`` subclasses, so callers
    see meaningful errors rather than downstream JSON validation failures.
    """
    stop_reason = getattr(message, "stop_reason", None)
    if stop_reason == "max_tokens":
        raise TruncatedResponseError(
            "Anthropic response was truncated at max_tokens; "
            "increase the limit or shorten the input."
        )
    if stop_reason == "refusal":
        raise RefusalError("Anthropic refused to respond to the request.")
    if stop_reason == "tool_use":
        # ProblemForm registers no tools with the Anthropic client.
        raise StructuredOutputError(
            "Anthropic returned stop_reason='tool_use' but no tools were configured."
        )

    text = "\n".join(
        block.text
        for block in (message.content or [])
        if getattr(block, "type", None) == "text"
    )
    if not text.strip():
        raise EmptyResponseError(
            f"Anthropic returned no text content (stop_reason={stop_reason!r})."
        )
    return text


def _check_openai_status(response) -> None:
    """Raise a specific error if an OpenAI Responses object signals failure.

    Handles ``status == "incomplete"`` with its known reasons. Uses defensive
    ``getattr`` access so a future SDK that renames or wraps fields degrades to
    a generic StructuredOutputError instead of crashing.
    """
    status = getattr(response, "status", None)
    if status != "incomplete":
        return
    incomplete = getattr(response, "incomplete_details", None)
    reason = getattr(incomplete, "reason", None) if incomplete is not None else None
    if reason == "max_output_tokens":
        raise TruncatedResponseError(
            "OpenAI response was truncated at max_output_tokens; "
            "increase the limit or shorten the input."
        )
    if reason == "content_filter":
        raise ContentFilterError(
            "OpenAI stopped generation due to its content filter."
        )
    raise StructuredOutputError(
        f"OpenAI response incomplete (reason={reason!r})."
    )


def _check_openai_refusal(response) -> None:
    """Raise RefusalError if any output content block is a refusal."""
    for item in getattr(response, "output", None) or []:
        for block in getattr(item, "content", None) or []:
            if getattr(block, "type", None) == "refusal":
                detail = (getattr(block, "refusal", "") or "").strip()
                raise RefusalError(
                    f"OpenAI refused to respond: {detail or 'no reason given'}"
                )


def _validate_openai_response(response, output_model: type[StructuredOutputT]) -> StructuredOutputT:
    """Validate an OpenAI ParsedResponse and return its ``output_parsed``.

    Surfaces known failure modes (truncation, content filter, refusal blocks,
    missing parsed output) as specific ``StructuredOutputError`` subclasses.
    """
    _check_openai_status(response)
    _check_openai_refusal(response)
    parsed = getattr(response, "output_parsed", None)
    if parsed is None:
        status = getattr(response, "status", None)
        raise EmptyResponseError(
            f"OpenAI returned no parsed output (status={status!r})."
        )
    return parsed


class OpenAIProvider:
    def __init__(self, model: str):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError(
                "OpenAIProvider requires the 'openai' package. "
                "Install it with `pip install problemform[openai]`."
            ) from exc
        self.client = OpenAI()
        self.model = model

    def generate_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system or ""},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
        )
        _check_openai_status(response)
        _check_openai_refusal(response)
        text = getattr(response, "output_text", None) or ""
        if not text.strip():
            status = getattr(response, "status", None)
            raise EmptyResponseError(
                f"OpenAI returned no text content (status={status!r})."
            )
        return text

    def generate_structured(
        self,
        prompt: str,
        output_model: type[StructuredOutputT],
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> StructuredOutputT:
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": system or ""},
                    {"role": "user", "content": prompt},
                ],
                text_format=output_model,
                temperature=temperature,
            )
            return _validate_openai_response(response, output_model)
        except StructuredOutputError:
            raise
        except Exception as exc:
            raise StructuredOutputError(
                "OpenAI provider failed to generate structured output."
            ) from exc


class AnthropicProvider:
    def __init__(self, model: str):
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise ImportError(
                "AnthropicProvider requires the 'anthropic' package. "
                "Install it with `pip install problemform[anthropic]`."
            ) from exc
        self.client = Anthropic()
        self.model = model

    def generate_text(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> str:
        # Only pass ``system`` when it is a non-empty string. Passing
        # ``system=None`` makes the Anthropic SDK send ``system: null``, which the
        # API rejects with ``400 invalid_request_error: system: Input should be a
        # valid array``. Omitting the key entirely is the documented way to send
        # no system prompt.
        kwargs: dict = {
            "model": self.model,
            "max_tokens": 8000,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        message = self.client.messages.create(**kwargs)
        return _extract_anthropic_text(message)

    def generate_structured(
        self,
        prompt: str,
        output_model: type[StructuredOutputT],
        *,
        system: str | None = None,
        temperature: float = 0.0,
    ) -> StructuredOutputT:
        json_prompt = f"""
{prompt}

Return only valid JSON matching the requested schema.
Do not include Markdown, commentary, or code fences.
"""
        try:
            text = self.generate_text(
                json_prompt,
                system=system,
                temperature=temperature,
            )
            return output_model.model_validate_json(text)
        except StructuredOutputError:
            raise
        except ValidationError as exc:
            raise StructuredOutputError(
                "Anthropic provider returned JSON that did not match the output model."
            ) from exc
        except Exception as exc:
            raise StructuredOutputError(
                "Anthropic provider failed to generate structured output."
            ) from exc


DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"


def make_provider(name: str | None = None, model: str | None = None) -> LLMProvider:
    name = (name or os.environ.get("PROBLEMFORM_PROVIDER") or "openai").lower()
    env_model = os.environ.get("PROBLEMFORM_MODEL")
    if name == "openai":
        return OpenAIProvider(model or env_model or DEFAULT_OPENAI_MODEL)
    if name == "anthropic":
        return AnthropicProvider(model or env_model or DEFAULT_ANTHROPIC_MODEL)
    raise ValueError(f"Unknown provider: {name!r}. Use 'openai' or 'anthropic'.")