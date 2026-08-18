import re

from config import OLLAMA_MODEL
from models.schemas import ActionResult, ActionVerdict, SchemeDocument
from prompts.action_prompt import ACTION_SYSTEM_PROMPT
from utils.formatting import truncate
from utils.ollama_client import LLMResponseError, chat_structured

_MAX_DOCUMENT_CHARS = 3000
_URL_RE = re.compile(r"https?://[^\s\]\)]+")

_FALLBACK_STEPS = [
    "Visit the official website or nearest government office for this scheme.",
    "Check the detailed eligibility and required documents before applying.",
]


class ActionAgent:
    """Summarizes a scheme's application process into concrete next steps.

    The apply link is extracted deterministically with a regex (the source text
    reliably contains a URL when one exists); the LLM is only used to turn the
    unstructured process description into a short numbered list of steps.
    """

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model

    def run(self, schemes: list[SchemeDocument]) -> list[ActionResult]:
        return [self._plan(scheme) for scheme in schemes]

    def _plan(self, scheme: SchemeDocument) -> ActionResult:
        try:
            verdict = chat_structured(
                model=self.model,
                system_prompt=ACTION_SYSTEM_PROMPT,
                user_content=truncate(scheme.document, _MAX_DOCUMENT_CHARS),
                schema=ActionVerdict,
            )
            steps = verdict.steps or _FALLBACK_STEPS
        except LLMResponseError:
            steps = _FALLBACK_STEPS

        return ActionResult(
            scheme_id=scheme.id,
            steps=steps,
            apply_link=self._extract_link(scheme.document),
        )

    @staticmethod
    def _extract_link(document: str) -> str | None:
        match = _URL_RE.search(document)
        return match.group(0).rstrip(".,") if match else None
