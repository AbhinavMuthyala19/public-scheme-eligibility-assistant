"""Thin wrapper around the Ollama chat API for structured (schema-validated) JSON output."""

from __future__ import annotations

import json
import re
from typing import TypeVar

import ollama
from pydantic import BaseModel, ValidationError

ModelT = TypeVar("ModelT", bound=BaseModel)

_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


class LLMResponseError(RuntimeError):
    """Raised when the model's response cannot be parsed into the expected schema."""


def _strip_code_fences(text: str) -> str:
    return _CODE_FENCE_RE.sub("", text).strip()


def chat_structured(
    model: str,
    system_prompt: str,
    user_content: str,
    schema: type[ModelT],
) -> ModelT:
    """Call Ollama chat, constraining output to `schema`'s JSON schema, and parse the result.

    Ollama's structured-output mode still occasionally returns text wrapped in markdown
    fences or fields it invented, so we fall back to fence-stripping before giving up.
    """
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        format=schema.model_json_schema(),
    )

    content = response["message"]["content"]

    try:
        return schema.model_validate_json(content)
    except (json.JSONDecodeError, ValidationError):
        pass

    cleaned = _strip_code_fences(content)
    try:
        return schema.model_validate_json(cleaned)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise LLMResponseError(
            f"Model '{model}' did not return output matching {schema.__name__}: {content!r}"
        ) from exc
