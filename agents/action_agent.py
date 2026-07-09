import re

from models.schemas import ActionItem, ActionAgentResponse
from scheme_store import SchemeStore

URL_RE = re.compile(r"https?://[^\s\]\)>\"]+")


def _clean(text: str) -> str:
    """Turn the markdown-ish application text into a plain, readable snippet."""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # [label](url) -> label
    text = re.sub(r"[#*_`>]+", " ", text)                 # drop markdown symbols
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class ActionAgent:
    """Deterministically assembles the 'what to do next' for each scheme:
    the real apply URLs and a short how-to-apply snippet from the data."""

    def __init__(self, store=None):
        self.store = store or SchemeStore()

    def build_item(self, verdict) -> ActionItem:
        scheme = self.store.get(verdict.scheme_id)
        app_text = scheme.get("application_process_text") or ""

        urls = []
        for u in URL_RE.findall(app_text):
            u = u.rstrip(".,);]")
            if u not in urls:
                urls.append(u)

        steps = _clean(app_text)
        if len(steps) > 400:
            steps = steps[:400].rsplit(" ", 1)[0] + "..."

        return ActionItem(
            scheme_id=verdict.scheme_id,
            scheme_name=verdict.scheme_name,
            apply_urls=urls[:5],
            documents=verdict.required_documents,
            steps=steps or None,
        )

    def run(self, results) -> ActionAgentResponse:
        return ActionAgentResponse(items=[self.build_item(r) for r in results])
