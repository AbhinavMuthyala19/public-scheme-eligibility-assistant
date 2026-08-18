from config import SEARCH_POOL_SIZE, TOP_K
from models.schemas import SchemeDocument, UserProfile
from utils.formatting import format_profile
from utils.vector_store import query_schemes

# Boosts applied on top of raw semantic relevance so nationwide and
# state-matching schemes are favored over same-scored schemes for other states.
_ALL_STATE_BOOST = 0.15
_STATE_MATCH_BOOST = 0.15


class SearchAgent:
    """Retrieves candidate schemes from ChromaDB using semantic search over the user profile.

    Retrieval is purely embedding-based (no LLM call). Results are re-ranked with a
    small boost for schemes available nationwide ("All") or in the user's own state,
    since Chroma's metadata filter can't reliably match comma-separated state lists.
    """

    def __init__(self, top_k: int = TOP_K, pool_size: int = SEARCH_POOL_SIZE):
        self.top_k = top_k
        self.pool_size = pool_size

    def run(self, profile: UserProfile) -> list[SchemeDocument]:
        query_text = format_profile(profile)
        raw = query_schemes(query_text, n_results=self.pool_size)

        candidates = self._to_documents(raw)
        candidates.sort(key=lambda doc: self._boosted_score(doc, profile), reverse=True)

        return candidates[: self.top_k]

    @staticmethod
    def _to_documents(raw: dict) -> list[SchemeDocument]:
        ids = raw["ids"][0]
        documents = raw["documents"][0]
        metadatas = raw["metadatas"][0]
        distances = raw["distances"][0]

        results = []
        for doc_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            results.append(
                SchemeDocument(
                    id=doc_id,
                    scheme_name=metadata.get("scheme_name", ""),
                    state=metadata.get("state", ""),
                    level=metadata.get("level", ""),
                    ministry=metadata.get("ministry", ""),
                    categories=metadata.get("categories", ""),
                    document=document,
                    relevance_score=1.0 / (1.0 + distance),
                )
            )
        return results

    @staticmethod
    def _boosted_score(doc: SchemeDocument, profile: UserProfile) -> float:
        score = doc.relevance_score
        scheme_states = [s.strip() for s in doc.state.split(",")]

        if "All" in scheme_states:
            score += _ALL_STATE_BOOST
        elif profile.state and profile.state.strip() in scheme_states:
            score += _STATE_MATCH_BOOST

        return score
