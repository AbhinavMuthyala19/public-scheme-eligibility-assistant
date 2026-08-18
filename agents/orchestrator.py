from typing import Optional

from config import MAX_RECOMMENDATIONS
from models.schemas import (
    EligibilityStatus,
    OrchestratorTurnResult,
    SchemeDocument,
    SchemeRecommendation,
    UserProfile,
)
from agents.action_agent import ActionAgent
from agents.eligibility_agent import EligibilityAgent
from agents.explanation_agent import ExplanationAgent
from agents.profile_agent import ProfileAgent
from agents.search_agent import SearchAgent

_FIELD_QUESTIONS = {
    "age": "How old are you?",
    "gender": "What is your gender?",
    "state": "Which state or union territory do you live in?",
}

# Statuses worth showing to the user, ranked best-first.
_RELEVANT_STATUSES = [EligibilityStatus.ELIGIBLE, EligibilityStatus.LIKELY_ELIGIBLE]
_STATUS_RANK = {status: rank for rank, status in enumerate(_RELEVANT_STATUSES)}


class Orchestrator:
    """Top-level coordinator: routes each user message through Profile Agent,
    and once the profile is complete, runs Search -> Eligibility -> Explanation -> Action.
    """

    def __init__(
        self,
        profile_agent: Optional[ProfileAgent] = None,
        search_agent: Optional[SearchAgent] = None,
        eligibility_agent: Optional[EligibilityAgent] = None,
        explanation_agent: Optional[ExplanationAgent] = None,
        action_agent: Optional[ActionAgent] = None,
    ):
        self.profile_agent = profile_agent or ProfileAgent()
        self.search_agent = search_agent or SearchAgent()
        self.eligibility_agent = eligibility_agent or EligibilityAgent()
        self.explanation_agent = explanation_agent or ExplanationAgent()
        self.action_agent = action_agent or ActionAgent()

    def handle_turn(
        self,
        user_input: str,
        profile: Optional[UserProfile] = None,
    ) -> OrchestratorTurnResult:
        profile_response = self.profile_agent.run(user_input, existing_profile=profile)

        if not profile_response.is_complete:
            return OrchestratorTurnResult(
                profile=profile_response.profile,
                is_complete=False,
                reply=self._follow_up_question(profile_response.missing_fields),
                recommendations=[],
            )

        recommendations = self._run_pipeline(profile_response.profile)

        return OrchestratorTurnResult(
            profile=profile_response.profile,
            is_complete=True,
            reply=self._summary_reply(recommendations),
            recommendations=recommendations,
        )

    def _run_pipeline(self, profile: UserProfile) -> list[SchemeRecommendation]:
        candidates = self.search_agent.run(profile)
        if not candidates:
            return []

        schemes_by_id: dict[str, SchemeDocument] = {doc.id: doc for doc in candidates}

        eligibility_results = self.eligibility_agent.run(profile, candidates)
        relevant = [r for r in eligibility_results if r.status in _RELEVANT_STATUSES]
        relevant.sort(key=lambda r: _STATUS_RANK[r.status])
        relevant = relevant[:MAX_RECOMMENDATIONS]

        if not relevant:
            return []

        shortlisted_docs = [schemes_by_id[r.scheme_id] for r in relevant]
        explanations = {
            e.scheme_id: e.explanation
            for e in self.explanation_agent.run(profile, schemes_by_id, relevant)
        }
        actions = {
            a.scheme_id: a
            for a in self.action_agent.run(shortlisted_docs)
        }

        recommendations = []
        for result in relevant:
            scheme = schemes_by_id[result.scheme_id]
            action = actions[result.scheme_id]
            recommendations.append(
                SchemeRecommendation(
                    scheme_id=scheme.id,
                    scheme_name=scheme.scheme_name,
                    state=scheme.state,
                    level=scheme.level,
                    ministry=scheme.ministry,
                    status=result.status,
                    reasoning=result.reasoning,
                    explanation=explanations[result.scheme_id],
                    steps=action.steps,
                    apply_link=action.apply_link,
                )
            )
        return recommendations

    @staticmethod
    def _follow_up_question(missing_fields: list[str]) -> str:
        field = missing_fields[0]
        question = _FIELD_QUESTIONS.get(field, f"Could you tell me your {field}?")
        return f"Thanks! {question}"

    @staticmethod
    def _summary_reply(recommendations: list[SchemeRecommendation]) -> str:
        if not recommendations:
            return (
                "I couldn't find any schemes you're clearly eligible for based on your "
                "profile. Try sharing more details, such as your occupation, category, "
                "income, or education."
            )
        return (
            f"Based on your profile, I found {len(recommendations)} scheme(s) you may be "
            "eligible for. See the details below."
        )
