from agents.eligibility_agent import EligibilityAgent
from models.schemas import EligibilityStatus, EligibilityVerdict, SchemeDocument, UserProfile
from utils.ollama_client import LLMResponseError


def _doc(doc_id: str, name: str) -> SchemeDocument:
    return SchemeDocument(
        id=doc_id,
        scheme_name=name,
        state="All",
        level="Central",
        ministry="Test Ministry",
        categories="Test",
        document="Eligibility: age >= 18",
        relevance_score=0.9,
    )


def test_run_maps_verdicts_onto_each_scheme(mocker):
    mocker.patch(
        "agents.eligibility_agent.chat_structured",
        return_value=EligibilityVerdict(
            status=EligibilityStatus.ELIGIBLE, reasoning="Meets age requirement."
        ),
    )

    agent = EligibilityAgent()
    schemes = [_doc("1", "Scheme A"), _doc("2", "Scheme B")]
    results = agent.run(UserProfile(age=25), schemes)

    assert [r.scheme_id for r in results] == ["1", "2"]
    assert all(r.status == EligibilityStatus.ELIGIBLE for r in results)
    assert results[0].scheme_name == "Scheme A"


def test_run_falls_back_to_insufficient_info_on_llm_error(mocker):
    mocker.patch(
        "agents.eligibility_agent.chat_structured",
        side_effect=LLMResponseError("bad output"),
    )

    agent = EligibilityAgent()
    results = agent.run(UserProfile(age=25), [_doc("1", "Scheme A")])

    assert results[0].status == EligibilityStatus.INSUFFICIENT_INFO
