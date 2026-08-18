from typing import Optional

from config import OLLAMA_MODEL
from models.schemas import ProfileAgentResponse, UserProfile
from prompts.profile_prompt import PROFILE_SYSTEM_PROMPT
from utils.ollama_client import LLMResponseError, chat_structured


class ProfileAgent:
    """Extracts a structured UserProfile from free-text user messages.

    Supports incremental extraction: pass the profile accumulated so far as
    `existing_profile` and newly-extracted fields are merged on top of it,
    so a multi-turn conversation can fill in missing fields one message at a time.
    """

    REQUIRED_FIELDS = [
        "age",
        "gender",
        "state",
    ]

    def __init__(self, model: str = OLLAMA_MODEL):
        self.model = model

    def run(
        self,
        user_input: str,
        existing_profile: Optional[UserProfile] = None,
    ) -> ProfileAgentResponse:
        try:
            extracted = chat_structured(
                model=self.model,
                system_prompt=PROFILE_SYSTEM_PROMPT,
                user_content=user_input,
                schema=UserProfile,
            )
        except LLMResponseError:
            extracted = UserProfile()

        profile = (
            existing_profile.merge(extracted)
            if existing_profile is not None
            else extracted
        )

        missing_fields = [
            field
            for field in self.REQUIRED_FIELDS
            if getattr(profile, field) is None
        ]

        return ProfileAgentResponse(
            profile=profile,
            missing_fields=missing_fields,
            is_complete=len(missing_fields) == 0,
        )
