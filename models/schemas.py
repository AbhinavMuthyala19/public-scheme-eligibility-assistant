from typing import Optional
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


class ProfileAgentResponse(BaseModel):
    profile: UserProfile
    missing_fields: list[str]
    is_complete: bool