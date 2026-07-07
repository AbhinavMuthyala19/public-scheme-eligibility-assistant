import json
import ollama

from config import OLLAMA_MODEL
from models.schemas import UserProfile, ProfileAgentResponse
from prompts.profile_prompt import PROFILE_SYSTEM_PROMPT


class ProfileAgent:

    REQUIRED_FIELDS = [
        "age",
        "gender",
        "state"
    ]

    def __init__(self):
        self.model = OLLAMA_MODEL

    def run(self, user_input: str) -> ProfileAgentResponse:

        response = ollama.chat(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": PROFILE_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ]
        )

        profile_json = json.loads(
            response["message"]["content"]
        )

        profile = UserProfile.model_validate(
            profile_json
        )

        missing_fields = []

        for field in self.REQUIRED_FIELDS:
            if getattr(profile, field) is None:
                missing_fields.append(field)

        return ProfileAgentResponse(
            profile=profile,
            missing_fields=missing_fields,
            is_complete=len(missing_fields) == 0
        )