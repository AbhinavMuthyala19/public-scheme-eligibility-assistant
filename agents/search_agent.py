from config import TOP_K
from models.schemas import UserProfile, SchemeCandidate, SearchAgentResponse
from retrieval import SchemeRetriever


class SearchAgent:
    """Turns a user profile into a semantic query and retrieves the most
    relevant candidate schemes from the Chroma vector DB."""

    def __init__(self, retriever=None):
        # Loads the embedding model + Chroma collection once (reused per call).
        self.retriever = retriever or SchemeRetriever()

    def build_query(self, profile: UserProfile) -> str:
        """Compose a natural-language query from the filled profile fields."""
        bits = []
        if profile.age is not None:
            bits.append(f"{profile.age}-year-old")
        if profile.gender:
            bits.append(profile.gender)
        if profile.occupation:
            bits.append(profile.occupation)
        if profile.category:
            bits.append(f"{profile.category} category")
        if profile.area:
            bits.append(f"{profile.area} area")
        if profile.education:
            bits.append(f"with education {profile.education}")
        if profile.business_interest:
            bits.append(f"interested in {profile.business_interest}")
        if profile.disability:
            bits.append("person with disability")
        if profile.minority:
            bits.append("from a minority community")
        if profile.marital_status:
            bits.append(profile.marital_status)

        who = " ".join(bits) if bits else "citizen"
        where = f" in {profile.state}" if profile.state else ""
        income = (
            f" with annual income {int(profile.annual_income)}"
            if profile.annual_income is not None else ""
        )
        return f"Government welfare schemes for a {who}{where}{income}".strip()

    def build_where(self, profile: UserProfile):
        """Metadata filter: keep the user's own state plus nationally-available
        ("All") schemes, and drop other states' schemes they can't apply for."""
        if not profile.state:
            return None
        return {"state": {"$in": [profile.state, "All"]}}

    def run(self, profile: UserProfile, top_k: int = TOP_K) -> SearchAgentResponse:
        query = self.build_query(profile)
        where = self.build_where(profile)
        schemes = self.retriever.search_schemes(query, top_k=top_k, where=where)
        candidates = [SchemeCandidate(**s) for s in schemes]
        return SearchAgentResponse(query=query, candidates=candidates)
