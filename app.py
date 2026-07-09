import pandas as pd
import streamlit as st

from config import DATA_PATH
from models.schemas import UserProfile
from agents.search_agent import SearchAgent
from agents.eligibility_agent import EligibilityAgent
from agents.explanation_agent import ExplanationAgent
from agents.action_agent import ActionAgent

# How many of the most relevant schemes to check (not shown to the user).
CANDIDATE_COUNT = 8

LANGUAGES = ["English", "Hindi", "Tamil", "Telugu", "Bengali", "Marathi",
             "Kannada", "Malayalam", "Gujarati", "Punjabi", "Odia"]
GENDERS = ["Female", "Male", "Other"]
AREAS = ["Rural", "Urban"]
CATEGORIES = ["General", "OBC", "SC", "ST", "EBC", "Minority"]
OCCUPATIONS = ["Farmer", "Student", "Daily wage laborer", "Self-employed / Business",
               "Salaried", "Unemployed", "Homemaker", "Artisan", "Senior citizen"]

NONE = "— select —"


@st.cache_resource
def load_agents():
    return {
        "search": SearchAgent(),
        "eligibility": EligibilityAgent(),
        "explanation": ExplanationAgent(),
        "action": ActionAgent(),
    }


@st.cache_data
def load_states():
    df = pd.read_csv(DATA_PATH)
    return sorted(s for s in df["state"].dropna().unique() if s != "All" and "," not in s)


st.set_page_config(page_title="Public Scheme Eligibility Assistant", page_icon="🇮🇳")
st.title("🇮🇳 Public Scheme Eligibility Assistant")
st.caption("Answer a few questions and we'll find government schemes you may qualify for.")

agents = load_agents()
states = load_states()

with st.form("profile_form"):
    language = st.selectbox("Language", LANGUAGES, index=0)

    c1, c2 = st.columns(2)
    age = c1.number_input("Age", min_value=0, max_value=120, value=30, step=1)
    gender = c2.selectbox("Gender", [NONE] + GENDERS)

    c3, c4 = st.columns(2)
    state = c3.selectbox("State", [NONE] + states)
    area = c4.selectbox("Region", [NONE] + AREAS)

    c5, c6 = st.columns(2)
    category = c5.selectbox("Category", [NONE] + CATEGORIES)
    occupation = c6.selectbox("Occupation", [NONE] + OCCUPATIONS)

    income = st.number_input(
        "Annual income (₹)",
        min_value=0,
        value=None,
        step=10000,
        placeholder="Enter the annual income",
    )

    submitted = st.form_submit_button("Find schemes")


def pick(value):
    return None if value == NONE else value


if submitted:
    profile = UserProfile(
        age=int(age) if age else None,
        gender=pick(gender),
        state=pick(state),
        area=pick(area),
        category=pick(category),
        occupation=pick(occupation),
        annual_income=float(income) if income else None,
    )

    with st.spinner("Searching schemes..."):
        candidates = agents["search"].run(profile, top_k=CANDIDATE_COUNT).candidates

    with st.spinner(f"Checking eligibility across {len(candidates)} schemes (Claude + GPT)..."):
        results = agents["eligibility"].run(profile, candidates).results

    # eligible first, then unclear, then not_eligible; higher confidence first
    order = {"eligible": 0, "unclear": 1, "not_eligible": 2}
    results.sort(key=lambda r: (order.get(r.verdict, 3), -r.confidence))

    # Show only schemes above 50% confidence, and never the ones they don't qualify for.
    shown = [
        r for r in results
        if r.confidence > 0.5 and r.verdict != "not_eligible"
    ]

    if not shown:
        st.warning(
            "No schemes matched with enough confidence. Try adding more details "
            "(category, occupation, income) and search again."
        )
        st.stop()

    n_eligible = sum(r.verdict == "eligible" for r in shown)
    n_review = sum(r.needs_review for r in shown)
    avg_conf = round(100 * sum(r.confidence for r in shown) / len(shown))

    m1, m2, m3 = st.columns(3)
    m1.metric("Eligible", n_eligible)
    m2.metric("Avg. confidence", f"{avg_conf}%")
    m3.metric("Needs review", n_review)

    with st.spinner("Writing your summary..."):
        explanation = agents["explanation"].run(profile, shown, language=language).explanation

    st.subheader("What this means for you")
    st.markdown(explanation)

    st.subheader("Scheme by scheme")
    st.caption(
        "**Confidence** = how strongly our two AI models (Claude + GPT) agree on the "
        "verdict. **🔎 Needs review** means the result isn't certain — usually the "
        "models agree they need more information from you to decide — so confirm on "
        "the official portal before applying. Only schemes above 50% confidence are shown."
    )
    actions = {i.scheme_id: i for i in agents["action"].run(shown).items}

    icons = {"eligible": "✅", "not_eligible": "❌", "unclear": "❓"}
    for r in shown:
        conf = f"{int(r.confidence * 100)}%"
        flag = " · 🔎 needs review" if r.needs_review else ""
        title = f"{icons.get(r.verdict, '•')} {r.scheme_name} — {r.verdict} · confidence {conf}{flag}"
        with st.expander(title):
            st.progress(r.confidence, text=f"Ensemble confidence: {conf}")
            if r.needs_review:
                st.info(
                    "🔎 **Needs review** — the models can't fully confirm this yet. "
                    "Check the 'Need to know' details below and verify on the official "
                    "portal before applying."
                )
            for reason in r.reasons:
                st.write("• " + reason)
            if r.required_documents:
                st.markdown("**Documents:** " + ", ".join(r.required_documents))
            if r.missing_info:
                st.markdown("**Need to know:** " + ", ".join(r.missing_info))

            item = actions.get(r.scheme_id)
            if item and item.apply_urls:
                st.markdown(
                    "**How to apply:** "
                    + "  ·  ".join(f"[Apply / info]({u})" for u in item.apply_urls)
                )
            if item and item.steps:
                st.caption("Next steps: " + item.steps)
