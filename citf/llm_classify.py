"""Optional LLM classifier (Anthropic Claude).

This is an *optional* augmentation for messy, real-world narratives the
rule-based classifier struggles with. It is intentionally dependency-light and
degrades gracefully: if the `anthropic` package or an API key is missing, it
raises, and the pipeline falls back to the rule-based result.

Environment:
    ANTHROPIC_API_KEY   your API key
    CITF_LLM_MODEL      model id (defaults below; set to a current model)
"""

import json
import os

from .taxonomy import CATEGORIES

DEFAULT_MODEL = os.environ.get("CITF_LLM_MODEL", "claude-sonnet-4-6")

_CATEGORY_LINES = "\n".join(
    f"  {code}: {meta['name']}" for code, meta in CATEGORIES.items()
)

_SYSTEM = (
    "You classify short physical-security incident reports. "
    "Respond with ONLY a JSON object, no prose, no markdown fences. "
    "Keys: category (one of the codes below), outcome (success|attempt|observation), "
    "location (a short location phrase or empty string). "
    "Choose the single best category.\n\nCategories:\n" + _CATEGORY_LINES
)


def llm_classify(text, model=None):
    """Classify one narrative with Claude. Returns a dict or None. May raise if
    the client/key is unavailable (caller is expected to handle that)."""
    import anthropic  # optional dependency

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    resp = client.messages.create(
        model=model or DEFAULT_MODEL,
        max_tokens=200,
        system=_SYSTEM,
        messages=[{"role": "user", "content": text}],
    )
    raw = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
    raw = raw.strip().strip("`")
    if raw.startswith("json"):
        raw = raw[4:].strip()

    data = json.loads(raw)
    if data.get("category") not in CATEGORIES:
        return None
    return {
        "category": data["category"],
        "outcome": data.get("outcome", "observation"),
        "location": (data.get("location") or "").strip().lower().replace(" ", "_") or None,
        "confidence": 0.99,
    }
