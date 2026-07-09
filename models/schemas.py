from typing import Optional, Any
from pydantic import BaseModel


class UserProfile(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    occupation: Optional[str] = None

    category: Optional[str] = None
    annual_income: Optional[float] = None
    education: Optional[str] = None

    business_interest: Optional[str] = None

    disability: Optional[bool] = None
    minority: Optional[bool] = None
    marital_status: Optional[str] = None
    area: Optional[str] = None            # e.g. Rural / Urban


class ProviderOutput(BaseModel):
    """Raw result from one LLM provider in the ensemble."""
    provider: str
    ok: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class LLMComparison(BaseModel):
    """How the providers compared on a single request."""
    agreement: float                      # 0..1, fraction of fields all models agreed on
    disagreements: dict[str, Any]         # field -> {provider: value}
    provider_outputs: list[ProviderOutput]


class ProfileAgentResponse(BaseModel):
    profile: UserProfile
    missing_fields: list[str]
    is_complete: bool
    comparison: Optional[LLMComparison] = None


class SchemeCandidate(BaseModel):
    """One scheme returned by the Search Agent."""
    scheme_id: str
    slug: Optional[str] = None
    scheme_name: Optional[str] = None
    state: Optional[str] = None
    level: Optional[str] = None
    categories: Optional[str] = None
    ministry: Optional[str] = None
    distance: float                       # lower = more relevant
    best_chunk: Optional[str] = None      # the closest-matching text chunk


class SearchAgentResponse(BaseModel):
    query: str                            # the query built from the profile
    candidates: list[SchemeCandidate]


class EligibilityVerdict(BaseModel):
    """The eligibility outcome for one scheme."""
    scheme_id: str
    scheme_name: Optional[str] = None
    verdict: str                          # "eligible" | "not_eligible" | "unclear"
    reasons: list[str] = []
    required_documents: list[str] = []
    missing_info: list[str] = []
    confidence: float = 0.0               # LLM ensemble confidence in the verdict (0..1)
    needs_review: bool = False            # flagged when they disagree or it's unclear


class EligibilityAgentResponse(BaseModel):
    results: list[EligibilityVerdict]


class ExplanationAgentResponse(BaseModel):
    language: str
    explanation: str


class ActionItem(BaseModel):
    scheme_id: str
    scheme_name: Optional[str] = None
    apply_urls: list[str] = []
    documents: list[str] = []
    steps: Optional[str] = None


class ActionAgentResponse(BaseModel):
    items: list[ActionItem]
