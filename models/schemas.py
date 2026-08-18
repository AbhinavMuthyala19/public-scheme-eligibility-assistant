from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Profile Agent
# ---------------------------------------------------------------------------

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

    def merge(self, other: "UserProfile") -> "UserProfile":
        """Return a new profile where `other`'s non-null fields override this profile's."""
        updates = {
            field: value
            for field, value in other.model_dump().items()
            if value is not None
        }
        return self.model_copy(update=updates)


class ProfileAgentResponse(BaseModel):
    profile: UserProfile
    missing_fields: list[str]
    is_complete: bool


# ---------------------------------------------------------------------------
# Search Agent
# ---------------------------------------------------------------------------

class SchemeDocument(BaseModel):
    id: str
    scheme_name: str
    state: str
    level: str
    ministry: str
    categories: str
    document: str
    relevance_score: float


# ---------------------------------------------------------------------------
# Eligibility Agent
# ---------------------------------------------------------------------------

class EligibilityStatus(str, Enum):
    ELIGIBLE = "eligible"
    LIKELY_ELIGIBLE = "likely_eligible"
    NOT_ELIGIBLE = "not_eligible"
    INSUFFICIENT_INFO = "insufficient_info"


class EligibilityVerdict(BaseModel):
    """Raw structured output requested from the LLM for a single scheme."""
    status: EligibilityStatus
    reasoning: str


class EligibilityResult(BaseModel):
    scheme_id: str
    scheme_name: str
    status: EligibilityStatus
    reasoning: str


# ---------------------------------------------------------------------------
# Explanation Agent
# ---------------------------------------------------------------------------

class ExplanationVerdict(BaseModel):
    """Raw structured output requested from the LLM for a single scheme."""
    explanation: str


class ExplanationResult(BaseModel):
    scheme_id: str
    explanation: str


# ---------------------------------------------------------------------------
# Action Agent
# ---------------------------------------------------------------------------

class ActionVerdict(BaseModel):
    """Raw structured output requested from the LLM for a single scheme."""
    steps: list[str]


class ActionResult(BaseModel):
    scheme_id: str
    steps: list[str]
    apply_link: Optional[str] = None


# ---------------------------------------------------------------------------
# Orchestration Agent
# ---------------------------------------------------------------------------

class SchemeRecommendation(BaseModel):
    """A single scheme's fully assembled result, combining every agent's output."""
    scheme_id: str
    scheme_name: str
    state: str
    level: str
    ministry: str
    status: EligibilityStatus
    reasoning: str
    explanation: str
    steps: list[str]
    apply_link: Optional[str] = None


class OrchestratorTurnResult(BaseModel):
    """What the orchestrator hands back to the UI after processing one user message."""
    profile: UserProfile
    is_complete: bool
    reply: str
    recommendations: list[SchemeRecommendation] = []
