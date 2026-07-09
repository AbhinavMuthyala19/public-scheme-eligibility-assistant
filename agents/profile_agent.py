from models.schemas import (
    UserProfile,
    ProfileAgentResponse,
    ProviderOutput,
    LLMComparison,
)
from prompts.profile_prompt import PROFILE_SYSTEM_PROMPT
from llm.ensemble import run_json_ensemble, compare_json


class ProfileAgent:
    """Extracts a structured user profile from free text by asking BOTH
    Claude and GPT, then merging and comparing their answers."""

    REQUIRED_FIELDS = ["age", "gender", "state"]

    def run(self, user_input: str) -> ProfileAgentResponse:
        # 1. Ask every configured provider in parallel.
        outputs = run_json_ensemble(PROFILE_SYSTEM_PROMPT, user_input)

        # 2. Merge their JSON and score how much they agreed.
        merged, disagreements, agreement = compare_json(outputs)

        # 3. Validate the merged result into a typed profile.
        profile = UserProfile.model_validate(merged)

        # 4. Which required fields are still missing?
        missing_fields = [
            field for field in self.REQUIRED_FIELDS
            if getattr(profile, field) is None
        ]

        comparison = LLMComparison(
            agreement=agreement,
            disagreements=disagreements,
            provider_outputs=[ProviderOutput(**o) for o in outputs],
        )

        return ProfileAgentResponse(
            profile=profile,
            missing_fields=missing_fields,
            is_complete=len(missing_fields) == 0,
            comparison=comparison,
        )
