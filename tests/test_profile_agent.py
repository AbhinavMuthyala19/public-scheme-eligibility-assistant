from agents.profile_agent import ProfileAgent
from models.schemas import UserProfile
from utils.ollama_client import LLMResponseError


def test_run_extracts_profile_and_reports_missing_fields(mocker):
    mocker.patch(
        "agents.profile_agent.chat_structured",
        return_value=UserProfile(age=22, gender="female"),
    )

    agent = ProfileAgent()
    result = agent.run("I am a 22 year old woman.")

    assert result.profile.age == 22
    assert result.profile.gender == "female"
    assert result.missing_fields == ["state"]
    assert result.is_complete is False


def test_run_merges_with_existing_profile(mocker):
    mocker.patch(
        "agents.profile_agent.chat_structured",
        return_value=UserProfile(state="Himachal Pradesh"),
    )
    existing = UserProfile(age=22, gender="female")

    agent = ProfileAgent()
    result = agent.run("I live in Himachal Pradesh.", existing_profile=existing)

    assert result.profile.age == 22
    assert result.profile.gender == "female"
    assert result.profile.state == "Himachal Pradesh"
    assert result.is_complete is True


def test_run_falls_back_to_empty_profile_on_llm_error(mocker):
    mocker.patch(
        "agents.profile_agent.chat_structured",
        side_effect=LLMResponseError("bad output"),
    )

    agent = ProfileAgent()
    result = agent.run("gibberish")

    assert result.profile == UserProfile()
    assert result.is_complete is False
    assert set(result.missing_fields) == {"age", "gender", "state"}
