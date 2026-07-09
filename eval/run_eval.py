"""Run the golden test profiles through the LangGraph pipeline and report
structural pass/fail. Requires .env keys and a built chroma_db.

    python3 eval/run_eval.py
"""

import os
import sys
import time

# Make the project root importable.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import UserProfile
from scheme_store import SchemeStore
from graph import build_graph
from agents.profile_agent import ProfileAgent
from agents.search_agent import SearchAgent
from agents.eligibility_agent import EligibilityAgent
from agents.explanation_agent import ExplanationAgent
from agents.action_agent import ActionAgent

from cases import CASES


def build():
    agents = {
        "profile": ProfileAgent(),
        "search": SearchAgent(),
        "eligibility": EligibilityAgent(),
        "explanation": ExplanationAgent(),
        "action": ActionAgent(),
    }
    return build_graph(agents), SchemeStore()


def check(case, final, store):
    problems = []
    status = final.get("status")

    if case["expect"] == "need_more_info":
        if status != "need_more_info":
            problems.append(f"expected need_more_info, got '{status}'")
        return problems

    # A normal run should finish (or legitimately find nothing).
    if status not in ("done", "no_matches"):
        problems.append(f"unexpected status '{status}'")

    user_state = case["profile"].get("state")
    for r in final.get("shown", []):
        if r.verdict == "not_eligible":
            problems.append(f"ineligible scheme shown: {r.scheme_name}")
        if not (0.0 <= r.confidence <= 1.0):
            problems.append(f"bad confidence {r.confidence}: {r.scheme_name}")
        scheme_state = store.get(r.scheme_id)["state"]
        if user_state and scheme_state not in (user_state, "All"):
            problems.append(
                f"state filter leak: '{r.scheme_name}' is {scheme_state}, user in {user_state}"
            )
    return problems


def main():
    graph, store = build()
    passed = 0

    for case in CASES:
        profile = UserProfile(**case["profile"])
        t0 = time.time()
        final = graph.invoke({"profile": profile, "language": "English", "top_k": 6})
        dt = time.time() - t0

        problems = check(case, final, store)
        shown = len(final.get("shown", []))
        if problems:
            print(f"FAIL  {case['name']}  ({dt:.1f}s, {shown} shown)")
            for p in problems:
                print(f"        - {p}")
        else:
            print(f"PASS  {case['name']}  ({dt:.1f}s, {shown} shown, status={final.get('status')})")
            passed += 1

    print(f"\n{passed}/{len(CASES)} cases passed.")
    sys.exit(0 if passed == len(CASES) else 1)


if __name__ == "__main__":
    main()
