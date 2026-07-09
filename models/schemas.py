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
