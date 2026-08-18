from config import OLLAMA_MODEL
from models.schemas import (
    EligibilityResult,
    EligibilityStatus,
    EligibilityVerdict,
    SchemeDocument,
    UserProfile,
)
from prompts.eligibility_prompt import ELIGIBILITY_SYSTEM_PROMPT
from utils.formatting import format_profile, truncate
from utils.ollama_client import LLMResponseError, chat_structured

_MAX_DOCUMENT_CHARS = 3000


class EligibilityAgent:
    """Judges, scheme by scheme, whether a user profile meets the stated eligibility criteria."""

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model

    def run(
        self,
        profile: UserProfile,
        schemes: list[SchemeDocument],
    ) -> list[EligibilityResult]:
        return [self._evaluate(profile, scheme) for scheme in schemes]

    def _evaluate(self, profile: UserProfile, scheme: SchemeDocument) -> EligibilityResult:
        user_content = (
            f"User Profile:\n{format_profile(profile)}\n\n"
            f"Scheme:\n{truncate(scheme.document, _MAX_DOCUMENT_CHARS)}"
        )

        try:
            verdict = chat_structured(
                model=self.model,
                system_prompt=ELIGIBILITY_SYSTEM_PROMPT,
                user_content=user_content,
                schema=EligibilityVerdict,
            )
        except LLMResponseError:
            verdict = EligibilityVerdict(
                status=EligibilityStatus.INSUFFICIENT_INFO,
                reasoning="This scheme could not be evaluated automatically.",
            )

        return EligibilityResult(
            scheme_id=scheme.id,
            scheme_name=scheme.scheme_name,
            status=verdict.status,
            reasoning=verdict.reasoning,
        )
