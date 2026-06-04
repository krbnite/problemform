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
        return response.output_text

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
            return response.output_parsed
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
        message = self.client.messages.create(
            model=self.model,
            max_tokens=8000,
            temperature=temperature,
            system=system,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        return "\n".join(
            block.text for block in message.content if block.type == "text"
        )

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