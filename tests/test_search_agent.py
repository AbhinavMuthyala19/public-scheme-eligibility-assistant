import pytest

from agents.search_agent import SearchAgent
from models.schemas import SchemeDocument, UserProfile


def _doc(state: str, relevance_score: float = 0.5) -> SchemeDocument:
    return SchemeDocument(
        id="1",
        scheme_name="Test Scheme",
        state=state,
        level="Central",
        ministry="Test Ministry",
        categories="Test",
        document="doc",
        relevance_score=relevance_score,
    )


def test_boosted_score_favors_nationwide_schemes():
    profile = UserProfile(state="Kerala")
    all_states_doc = _doc("All")
    other_state_doc = _doc("Punjab")

    assert SearchAgent._boosted_score(all_states_doc, profile) > SearchAgent._boosted_score(
        other_state_doc, profile
    )


def test_boosted_score_favors_matching_state():
    profile = UserProfile(state="Kerala")
    matching_doc = _doc("Kerala")
    other_state_doc = _doc("Punjab")

    assert SearchAgent._boosted_score(matching_doc, profile) > SearchAgent._boosted_score(
        other_state_doc, profile
    )


def test_boosted_score_handles_comma_separated_states():
    profile = UserProfile(state="Assam")
    doc = _doc("Assam,Manipur,Nagaland")

    assert SearchAgent._boosted_score(doc, profile) > doc.relevance_score


@pytest.mark.integration
def test_run_returns_documents_from_real_chroma_db():
    pytest.importorskip("chromadb")
    from utils.vector_store import get_collection

    try:
        collection = get_collection()
        if collection.count() == 0:
            pytest.skip("chroma_db collection is empty; run src/build_vectordb.py first")
    except Exception:
        pytest.skip("chroma_db not available; run src/build_vectordb.py first")

    agent = SearchAgent(top_k=5)
    profile = UserProfile(age=22, gender="female", state="Himachal Pradesh", category="SC")

    results = agent.run(profile)

    assert 0 < len(results) <= 5
    assert all(isinstance(doc, SchemeDocument) for doc in results)
