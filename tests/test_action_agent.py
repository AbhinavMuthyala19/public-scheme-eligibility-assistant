from agents.action_agent import ActionAgent
from models.schemas import ActionVerdict, SchemeDocument


def _doc(document: str) -> SchemeDocument:
    return SchemeDocument(
        id="1",
        scheme_name="Scheme A",
        state="All",
        level="Central",
        ministry="Test Ministry",
        categories="Test",
        document=document,
        relevance_score=0.9,
    )


def test_run_extracts_link_when_present(mocker):
    mocker.patch(
        "agents.action_agent.chat_structured",
        return_value=ActionVerdict(steps=["Visit the portal.", "Submit documents."]),
    )

    agent = ActionAgent()
    doc = _doc("Application Process: Apply at https://example.gov.in/apply for details.")

    results = agent.run([doc])

    assert results[0].apply_link == "https://example.gov.in/apply"
    assert results[0].steps == ["Visit the portal.", "Submit documents."]


def test_run_returns_no_link_when_absent(mocker):
    mocker.patch(
        "agents.action_agent.chat_structured",
        return_value=ActionVerdict(steps=["Visit your nearest office."]),
    )

    agent = ActionAgent()
    doc = _doc("Application Process: Visit your nearest government office.")

    results = agent.run([doc])

    assert results[0].apply_link is None


def test_run_falls_back_to_default_steps_on_empty_verdict(mocker):
    mocker.patch(
        "agents.action_agent.chat_structured",
        return_value=ActionVerdict(steps=[]),
    )

    agent = ActionAgent()
    results = agent.run([_doc("Application Process: unclear.")])

    assert len(results[0].steps) > 0
