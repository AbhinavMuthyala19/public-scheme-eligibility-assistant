import streamlit as st

from agents.orchestrator import Orchestrator
from models.schemas import EligibilityStatus, SchemeRecommendation, UserProfile

st.set_page_config(
    page_title="Public Scheme Eligibility Assistant",
    page_icon="\U0001F3DB️",
    layout="wide",
)

_STATUS_BADGE = {
    EligibilityStatus.ELIGIBLE: "✅ Eligible",
    EligibilityStatus.LIKELY_ELIGIBLE: "\U0001F7E1 Likely Eligible",
    EligibilityStatus.NOT_ELIGIBLE: "❌ Not Eligible",
    EligibilityStatus.INSUFFICIENT_INFO: "❓ Insufficient Info",
}


@st.cache_resource
def get_orchestrator() -> Orchestrator:
    return Orchestrator()


def _init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi! I'm your Government Scheme Eligibility Assistant. "
                    "Tell me a bit about yourself — your age, gender, state, occupation, "
                    "category, income, or what kind of support you're looking for — "
                    "and I'll find schemes you may be eligible for."
                ),
            }
        ]
    if "profile" not in st.session_state:
        st.session_state.profile = UserProfile()
    if "recommendations" not in st.session_state:
        st.session_state.recommendations = []


def _reset_conversation() -> None:
    for key in ("messages", "profile", "recommendations"):
        st.session_state.pop(key, None)


def _render_sidebar(profile: UserProfile) -> None:
    with st.sidebar:
        st.header("Your Profile")
        known_fields = {
            k: v for k, v in profile.model_dump().items() if v is not None
        }
        if known_fields:
            for field, value in known_fields.items():
                st.markdown(f"**{field.replace('_', ' ').title()}:** {value}")
        else:
            st.caption("Nothing captured yet — start chatting below.")

        st.divider()
        if st.button("Start Over", use_container_width=True):
            _reset_conversation()
            st.rerun()


def _render_recommendation(rec: SchemeRecommendation) -> None:
    badge = _STATUS_BADGE.get(rec.status, rec.status.value)
    with st.expander(f"{badge}  —  {rec.scheme_name}"):
        st.caption(f"{rec.level} scheme · {rec.ministry} · Applicable in: {rec.state}")

        st.markdown("**Why this result:**")
        st.write(rec.explanation)

        if rec.steps:
            st.markdown("**How to apply:**")
            for i, step in enumerate(rec.steps, start=1):
                st.markdown(f"{i}. {step}")

        if rec.apply_link:
            st.link_button("Open official link", rec.apply_link)


def main() -> None:
    _init_session_state()
    orchestrator = get_orchestrator()

    _render_sidebar(st.session_state.profile)

    st.title("Public Scheme Eligibility Assistant")
    st.caption(
        "An agentic RAG assistant that recommends Indian Government schemes "
        "based on your profile."
    )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    if st.session_state.recommendations:
        st.subheader("Recommended Schemes")
        for rec in st.session_state.recommendations:
            _render_recommendation(rec)

    user_input = st.chat_input("Tell me about yourself...")
    if not user_input:
        return

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = orchestrator.handle_turn(
                    user_input, profile=st.session_state.profile
                )
            except Exception as exc:  # noqa: BLE001 - surface any failure to the user
                error_message = (
                    "Something went wrong while talking to the local Ollama model. "
                    "Make sure Ollama is running (`ollama serve`) and that the model "
                    f"in `config.py` has been pulled.\n\nDetails: {exc}"
                )
                st.error(error_message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_message}
                )
                return

        st.session_state.profile = result.profile
        st.session_state.recommendations = result.recommendations
        st.write(result.reply)

    st.session_state.messages.append({"role": "assistant", "content": result.reply})
    st.rerun()


if __name__ == "__main__":
    main()
