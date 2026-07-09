"""Run several providers on the same prompt, then compare their JSON outputs.

This is the "call both and compare" core:
  1. call every provider in parallel,
  2. parse each reply as JSON,
  3. score field-level agreement between the models,
  4. merge into one result and flag the fields they disagree on.
"""

from concurrent.futures import ThreadPoolExecutor

from config import ENSEMBLE_PROVIDERS
from llm.providers import build_providers


def _normalize(value):
    """Loose equality: 'Punjab' == 'punjab', 90000 == 90000.0."""
    if value is None:
        return None
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    return str(value).strip().lower()


def _call_provider(provider, system, user):
    try:
        data = provider.complete_json(system, user)
        return {"provider": provider.name, "ok": True, "data": data, "error": None}
    except Exception as e:  # noqa: BLE001 - we want to capture any provider failure
        return {"provider": provider.name, "ok": False, "data": None, "error": str(e)}


def run_json_ensemble(system: str, user: str, provider_names=None):
    """Call all configured providers in parallel and return their raw outputs."""
    provider_names = provider_names or ENSEMBLE_PROVIDERS
    providers = build_providers(provider_names)

    with ThreadPoolExecutor(max_workers=max(1, len(providers))) as pool:
        outputs = list(
            pool.map(lambda p: _call_provider(p, system, user), providers)
        )
    return outputs


def compare_json(outputs):
    """Field-level comparison across the successful provider outputs.

    Returns (merged, disagreements, agreement):
      merged        - one dict combining the models' answers
      disagreements - {field: {provider: value}} where they differ
      agreement     - fraction of fields all models agreed on (0..1)
    """
    ok_outputs = [o for o in outputs if o["ok"] and isinstance(o["data"], dict)]

    if not ok_outputs:
        return {}, {}, 0.0

    all_keys = set()
    for o in ok_outputs:
        all_keys.update(o["data"].keys())

    merged = {}
    disagreements = {}

    for key in all_keys:
        values = {o["provider"]: o["data"].get(key) for o in ok_outputs}
        distinct = {_normalize(v) for v in values.values()}

        if len(distinct) == 1:
            # all models agree
            merged[key] = next(iter(values.values()))
        else:
            disagreements[key] = values
            # tie-break: prefer the first non-null value
            non_null = [v for v in values.values() if v is not None]
            merged[key] = non_null[0] if non_null else None

    agreement = 1.0 - (len(disagreements) / len(all_keys)) if all_keys else 1.0
    return merged, disagreements, round(agreement, 3)
