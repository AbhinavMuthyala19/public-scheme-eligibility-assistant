"""Provider adapters behind one interface.

Adding a new provider (e.g. Gemini) = write one more subclass and register
it in PROVIDERS. Nothing else in the codebase changes.
"""

import json
import re
from abc import ABC, abstractmethod


def extract_json(text: str) -> dict:
    """Parse a JSON object out of an LLM reply, tolerating stray prose or
    ```json fences that a model might add."""
    text = (text or "").strip()

    # Strip ```json ... ``` fences if present
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()

    # Fallback: grab the first {...} block
    if not text.startswith("{"):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)

    return json.loads(text)


class LLMProvider(ABC):
    """One provider. Subclasses implement complete(); everyone gets
    complete_json() for free."""

    name: str = "base"

    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return the raw text reply for a system + user prompt."""
        raise NotImplementedError

    def complete_json(self, system: str, user: str) -> dict:
        return extract_json(self.complete(system, user))


class ClaudeProvider(LLMProvider):
    name = "claude"

    def __init__(self):
        from anthropic import Anthropic
        from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL

        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = ANTHROPIC_MODEL

    def complete(self, system: str, user: str) -> str:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            temperature=0,   # deterministic: same input -> same verdict
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self):
        from openai import OpenAI
        from config import OPENAI_API_KEY, OPENAI_MODEL

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL

    def complete(self, system: str, user: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0,   # deterministic: same input -> same verdict
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            # Forces valid JSON output. The prompt must mention "JSON"
            # (ours does) for this to be accepted by the API.
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content


# Registry — the ensemble builds providers from these names.
PROVIDERS = {
    "claude": ClaudeProvider,
    "openai": OpenAIProvider,
}


def build_providers(names):
    """Instantiate providers by name, e.g. ["claude", "openai"]."""
    return [PROVIDERS[n]() for n in names]
