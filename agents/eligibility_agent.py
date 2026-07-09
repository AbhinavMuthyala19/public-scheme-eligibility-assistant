from collections import Counter

from models.schemas import (
    UserProfile,
    EligibilityVerdict,
    EligibilityAgentResponse,
)
from prompts.eligibility_prompt import ELIGIBILITY_SYSTEM_PROMPT
from llm.ensemble import run_json_ensemble
from scheme_store import SchemeStore

VALID_VERDICTS = {"eligible", "not_eligible", "unclear"}


def _norm_verdict(value):
    if value is None:
        return None
    v = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    return v if v in VALID_VERDICTS else None


def _dedupe(items):
    seen, out = set(), []
    for item in items or []:
        key = str(item).strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


class EligibilityAgent:
    """Checks a user's profile against each candidate scheme's eligibility
    TEXT using the multi-LLM ensemble, grounded strictly in that text."""

    def __init__(self, store=None):
        self.store = store or SchemeStore()

    def _build_user_prompt(self, profile: UserProfile, scheme: dict) -> str:
        return (
            "USER PROFILE (JSON):\n"
            f"{profile.model_dump_json()}\n\n"
            f"SCHEME NAME: {scheme['scheme_name']}\n\n"
            "ELIGIBILITY CRITERIA (use ONLY this text):\n"
            f"{scheme['eligibility']}\n\n"
            "APPLICATION / DOCUMENTS TEXT:\n"
            f"{scheme['application_process_text']}"
        )

    def check_one(self, profile: UserProfile, scheme_id) -> EligibilityVerdict:
        scheme = self.store.get(scheme_id)
        user_prompt = self._build_user_prompt(profile, scheme)

        outputs = run_json_ensemble(ELIGIBILITY_SYSTEM_PROMPT, user_prompt)
        ok = [o for o in outputs if o["ok"] and isinstance(o["data"], dict)]

        verdicts = [_norm_verdict(o["data"].get("verdict")) for o in ok]
        valid = [v for v in verdicts if v is not None]

        # Reconcile via majority vote; confidence = share of the winning verdict.
        if not valid:
            verdict, confidence, needs_review = "unclear", 0.0, True
        else:
            counts = Counter(valid)
            top_verdict, top_n = counts.most_common(1)[0]
            confidence = round(top_n / len(valid), 2)
            tie = list(counts.values()).count(top_n) > 1
            if tie:
                verdict, needs_review = "unclear", True
            else:
                verdict = top_verdict
                needs_review = (verdict == "unclear") or (confidence < 1.0)

        reasons, docs, missing = [], [], []
        for o in ok:
            reasons += o["data"].get("reasons") or []
            docs += o["data"].get("required_documents") or []
            missing += o["data"].get("missing_info") or []

        return EligibilityVerdict(
            scheme_id=str(scheme_id),
            scheme_name=scheme["scheme_name"],
            verdict=verdict,
            reasons=_dedupe(reasons),
            required_documents=_dedupe(docs),
            missing_info=_dedupe(missing),
            confidence=confidence,
            needs_review=needs_review,
        )

    def run(self, profile: UserProfile, candidates) -> EligibilityAgentResponse:
        results = [self.check_one(profile, c.scheme_id) for c in candidates]
        return EligibilityAgentResponse(results=results)
