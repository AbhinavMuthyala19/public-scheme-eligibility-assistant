"""Small text-formatting helpers shared by the agent prompts."""

from __future__ import annotations

from models.schemas import UserProfile

_FIELD_LABELS: dict[str, str] = {
    "age": "Age",
    "gender": "Gender",
    "state": "State",
    "occupation": "Occupation",
    "category": "Social Category",
    "annual_income": "Annual Income",
    "education": "Education",
    "business_interest": "Business Interest",
    "disability": "Disability",
    "minority": "Minority",
    "marital_status": "Marital Status",
}


def format_profile(profile: UserProfile) -> str:
    """Render the known (non-null) fields of a profile as readable "Label: value" lines."""
    lines = []
    for field, label in _FIELD_LABELS.items():
        value = getattr(profile, field)
        if value is not None:
            lines.append(f"{label}: {value}")
    return "\n".join(lines) if lines else "No profile information available."


def truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0] + " ..."
