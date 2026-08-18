from agents.explanation_agent import ExplanationAgent
from models.schemas import (
    EligibilityResult,
    EligibilityStatus,
    ExplanationVerdict,
    SchemeDocument,
    UserProfile,
)


def _doc(doc_id: str) -> SchemeDocument:
    return SchemeDocument(
        id=doc_id,
        scheme_name="Scheme A",
        state="All",
        level="Central",
        ministry="Test Ministry",
        categories="Test",
        document="Benefits: loan up to 1 lakh",
        relevance_score=0.9,
    )


def test_run_builds_explanation_per_eligibility_result(mocker):
    mocker.patch(
        "agents.explanation_agent.chat_structured",
        return_value=ExplanationVerdict(explanation="You qualify for a low-interest loan."),
    )

    agent = ExplanationAgent()
    scheme = _doc("1")
    eligibility = [
        EligibilityResult(
            scheme_id="1",
            scheme_name="Scheme A",
            status=EligibilityStatus.ELIGIBLE,
            reasoning="Meets criteria.",
        )
    ]

    results = agent.run(UserProfile(age=25), {"1": scheme}, eligibility)

    assert len(results) == 1
    assert results[0].scheme_id == "1"
    assert "loan" in results[0].explanation
