"""LangGraph orchestration of the scheme-eligibility pipeline.

Flow:

    START -> profile -> (clarify | search)
                         search -> eligibility -> (no_matches | explanation)
                                                   explanation -> action -> END
    clarify -> END
    no_matches -> END

The two conditional edges are the "agentic" routing: a profile-completeness
gate and a no-results gate. Each node wraps one of the existing agents and
returns a partial state update.
"""

from typing import TypedDict, Optional, List

from langgraph.graph import StateGraph, START, END

from models.schemas import UserProfile

# Minimum info needed before a search is worthwhile.
REQUIRED_FIELDS = ["state"]
DEFAULT_TOP_K = 8


class PipelineState(TypedDict, total=False):
    user_text: Optional[str]
    profile: UserProfile
    language: str
    top_k: int
    missing_fields: List[str]
    candidates: list
    results: list
    shown: list
    explanation: str
    actions: list
    status: str          # "need_more_info" | "no_matches" | "done"


def _select(results):
    """Keep schemes above 50% confidence that aren't outright ineligible,
    ordered eligible -> unclear, highest confidence first."""
    # Show anything the user might qualify for (eligible or needs-more-info);
    # hide only schemes they clearly don't qualify for.
    shown = [r for r in results if r.verdict != "not_eligible"]
    order = {"eligible": 0, "unclear": 1}
    shown.sort(key=lambda r: (order.get(r.verdict, 2), -r.confidence))
    return shown


def build_graph(agents):
    """Compile the pipeline graph. `agents` is a dict of the agent instances
    (search, eligibility, explanation, action, and optionally profile)."""

    def profile_node(state: PipelineState):
        profile = state.get("profile")
        if profile is None and state.get("user_text"):
            profile = agents["profile"].run(state["user_text"]).profile
        missing = [
            f for f in REQUIRED_FIELDS
            if getattr(profile, f, None) in (None, "")
        ]
        return {"profile": profile, "missing_fields": missing}

    def search_node(state: PipelineState):
        top_k = state.get("top_k", DEFAULT_TOP_K)
        candidates = agents["search"].run(state["profile"], top_k=top_k).candidates
        return {"candidates": candidates}

    def eligibility_node(state: PipelineState):
        results = agents["eligibility"].run(state["profile"], state["candidates"]).results
        return {"results": results, "shown": _select(results)}

    def explanation_node(state: PipelineState):
        text = agents["explanation"].run(
            state["profile"], state["shown"],
            language=state.get("language", "English"),
        ).explanation
        return {"explanation": text}

    def action_node(state: PipelineState):
        items = agents["action"].run(state["shown"]).items
        return {"actions": items, "status": "done"}

    def clarify_node(state: PipelineState):
        return {"status": "need_more_info"}

    def no_match_node(state: PipelineState):
        return {"status": "no_matches"}

    def route_after_profile(state: PipelineState):
        return "clarify" if state.get("missing_fields") else "search"

    def route_after_eligibility(state: PipelineState):
        return "explanation" if state.get("shown") else "no_matches"

    g = StateGraph(PipelineState)
    g.add_node("profile", profile_node)
    g.add_node("search", search_node)
    g.add_node("eligibility", eligibility_node)
    g.add_node("explanation", explanation_node)
    g.add_node("action", action_node)
    g.add_node("clarify", clarify_node)
    g.add_node("no_matches", no_match_node)

    g.add_edge(START, "profile")
    g.add_conditional_edges(
        "profile", route_after_profile,
        {"clarify": "clarify", "search": "search"},
    )
    g.add_edge("search", "eligibility")
    g.add_conditional_edges(
        "eligibility", route_after_eligibility,
        {"explanation": "explanation", "no_matches": "no_matches"},
    )
    g.add_edge("explanation", "action")
    g.add_edge("action", END)
    g.add_edge("clarify", END)
    g.add_edge("no_matches", END)

    return g.compile()
