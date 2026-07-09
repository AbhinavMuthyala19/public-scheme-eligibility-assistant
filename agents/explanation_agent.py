from models.schemas import UserProfile, ExplanationAgentResponse
from prompts.explanation_prompt import EXPLANATION_SYSTEM_PROMPT
from llm.providers import build_providers


class ExplanationAgent:
    """Turns eligibility verdicts into a friendly, plain-language summary,
    optionally in another language. Uses a single provider (prose, not a
    structured decision, so ensemble comparison adds little)."""

    def __init__(self, provider_name: str = "claude", provider=None):
        self.provider = provider or build_providers([provider_name])[0]

    def _format_results(self, results) -> str:
        lines = []
        for r in results:
            lines.append(f"SCHEME: {r.scheme_name}  [verdict: {r.verdict}]")
            for reason in r.reasons:
                lines.append(f"  - reason: {reason}")
            if r.required_documents:
                lines.append(f"  - documents: {', '.join(r.required_documents)}")
            if r.missing_info:
                lines.append(f"  - missing: {', '.join(r.missing_info)}")
            if r.needs_review:
                lines.append("  - note: flagged for human review (models disagreed)")
            lines.append("")
        return "\n".join(lines).strip()

    def run(self, profile: UserProfile, results, language: str = "English") -> ExplanationAgentResponse:
        system = EXPLANATION_SYSTEM_PROMPT.format(language=language)
        user = (
            "USER PROFILE (JSON):\n"
            f"{profile.model_dump_json()}\n\n"
            "SCHEME ELIGIBILITY RESULTS:\n"
            f"{self._format_results(results)}"
        )
        text = self.provider.complete(system, user)
        return ExplanationAgentResponse(language=language, explanation=text.strip())
