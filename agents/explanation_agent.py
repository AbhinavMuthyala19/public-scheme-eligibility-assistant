from config import OLLAMA_MODEL
from models.schemas import (
    EligibilityResult,
    ExplanationResult,
    ExplanationVerdict,
    SchemeDocument,
    UserProfile,
)
from prompts.explanation_prompt import EXPLANATION_SYSTEM_PROMPT
from utils.formatting import format_profile, truncate
from utils.ollama_client import LLMResponseError, chat_structured

_MAX_DOCUMENT_CHARS = 3000


class ExplanationAgent:
    """Turns a raw eligibility verdict into a short, user-friendly explanation."""

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model

    def run(
        self,
        profile: UserProfile,
        schemes_by_id: dict[str, SchemeDocument],
        eligibility_results: list[EligibilityResult],
    ) -> list[ExplanationResult]:
        return [
            self._explain(profile, schemes_by_id[result.scheme_id], result)
            for result in eligibility_results
        ]

    def _explain(
        self,
        profile: UserProfile,
        scheme: SchemeDocument,
        eligibility: EligibilityResult,
    ) -> ExplanationResult:
        user_content = (
            f"User Profile:\n{format_profile(profile)}\n\n"
            f"Scheme:\n{truncate(scheme.document, _MAX_DOCUMENT_CHARS)}\n\n"
            f"Eligibility Status: {eligibility.status.value}\n"
            f"Eligibility Reasoning: {eligibility.reasoning}"
        )

        try:
            verdict = chat_structured(
                model=self.model,
                system_prompt=EXPLANATION_SYSTEM_PROMPT,
                user_content=user_content,
                schema=ExplanationVerdict,
            )
        except LLMResponseError:
            verdict = ExplanationVerdict(explanation=eligibility.reasoning)

        return ExplanationResult(
            scheme_id=scheme.id,
            explanation=verdict.explanation,
        )
