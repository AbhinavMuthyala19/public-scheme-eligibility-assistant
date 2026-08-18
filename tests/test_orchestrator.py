from agents.orchestrator import Orchestrator
from models.schemas import (
    ActionResult,
    EligibilityResult,
    EligibilityStatus,
    ExplanationResult,
    ProfileAgentResponse,
    SchemeDocument,
    UserProfile,
)


class _StubProfileAgent:
    def __init__(self, response: ProfileAgentResponse):
        self.response = response

    def run(self, user_input, existing_profile=None):
        return self.response


class _StubSearchAgent:
    def __init__(self, docs: list[SchemeDocument]):
        self.docs = docs

    def run(self, profile):
        return self.docs


class _StubEligibilityAgent:
    def __init__(self, results: list[EligibilityResult]):
        self.results = results

    def run(self, profile, schemes):
        return self.results


class _StubExplanationAgent:
    def run(self, profile, schemes_by_id, eligibility_results):
        return [
            ExplanationResult(scheme_id=r.scheme_id, explanation=f"Explanation for {r.scheme_id}")
            for r in eligibility_results
        ]


class _StubActionAgent:
    def run(self, schemes):
        return [
            ActionResult(scheme_id=doc.id, steps=["Step 1"], apply_link=None)
            for doc in schemes
        ]


def _doc(doc_id: str) -> SchemeDocument:
    return SchemeDocument(
        id=doc_id,
        scheme_name=f"Scheme {doc_id}",
        state="All",
        level="Central",
        ministry="Test Ministry",
        categories="Test",
        document="doc",
        relevance_score=0.9,
    )


def _eligibility(scheme_id: str, status: EligibilityStatus) -> EligibilityResult:
    return EligibilityResult(
        scheme_id=scheme_id, scheme_name=f"Scheme {scheme_id}", status=status, reasoning="because"
    )


def test_incomplete_profile_asks_follow_up_without_running_pipeline():
    profile_response = ProfileAgentResponse(
        profile=UserProfile(age=22),
        missing_fields=["gender", "state"],
        is_complete=False,
    )

    orchestrator = Orchestrator(
        profile_agent=_StubProfileAgent(profile_response),
        search_agent=_StubSearchAgent([]),
    )

    result = orchestrator.handle_turn("I am 22.")

    assert result.is_complete is False
    assert result.recommendations == []
    assert "gender" in result.reply.lower()


def test_complete_profile_runs_full_pipeline_and_filters_by_status():
    profile_response = ProfileAgentResponse(
        profile=UserProfile(age=22, gender="female", state="Kerala"),
        missing_fields=[],
        is_complete=True,
    )
    docs = [_doc("1"), _doc("2"), _doc("3")]
    eligibility_results = [
        _eligibility("1", EligibilityStatus.ELIGIBLE),
        _eligibility("2", EligibilityStatus.NOT_ELIGIBLE),
        _eligibility("3", EligibilityStatus.LIKELY_ELIGIBLE),
    ]

    orchestrator = Orchestrator(
        profile_agent=_StubProfileAgent(profile_response),
        search_agent=_StubSearchAgent(docs),
        eligibility_agent=_StubEligibilityAgent(eligibility_results),
        explanation_agent=_StubExplanationAgent(),
        action_agent=_StubActionAgent(),
    )

    result = orchestrator.handle_turn("I am a 22 year old woman from Kerala.")

    assert result.is_complete is True
    # scheme 2 (not_eligible) is filtered out; eligible ranks before likely_eligible
    assert [r.scheme_id for r in result.recommendations] == ["1", "3"]
    assert all(r.explanation for r in result.recommendations)
    assert all(r.steps for r in result.recommendations)


def test_no_relevant_schemes_yields_empty_recommendations():
    profile_response = ProfileAgentResponse(
        profile=UserProfile(age=22, gender="female", state="Kerala"),
        missing_fields=[],
        is_complete=True,
    )
    docs = [_doc("1")]
    eligibility_results = [_eligibility("1", EligibilityStatus.NOT_ELIGIBLE)]

    orchestrator = Orchestrator(
        profile_agent=_StubProfileAgent(profile_response),
        search_agent=_StubSearchAgent(docs),
        eligibility_agent=_StubEligibilityAgent(eligibility_results),
        explanation_agent=_StubExplanationAgent(),
        action_agent=_StubActionAgent(),
    )

    result = orchestrator.handle_turn("I am a 22 year old woman from Kerala.")

    assert result.recommendations == []
    assert "couldn't find" in result.reply.lower()
