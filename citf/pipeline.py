"""End-to-end triage pipeline: free-text narratives -> triaged CITF records.

Uses the rule-based classifier by default. If use_llm=True and the optional LLM
classifier is available, low-confidence narratives are re-classified with it.
"""

from .classify import classify_narrative
from .taxonomy import meta
from .triage import score_priority
from .patterns import flag_recurrences

# Fallback category for narratives the classifier cannot place (low cyber-nexus).
UNKNOWN_FALLBACK = "PR-04"


def triage_narratives(items, use_llm=False, llm_threshold=0.34):
    """items: list of dicts with at least incident_id, timestamp, site_id,
    reporter_role, narrative_text. Returns triaged records in the CITF schema."""
    records = []
    for it in items:
        pred = classify_narrative(it["narrative_text"])

        if use_llm and (pred["category"] is None or pred["confidence"] < llm_threshold):
            try:
                from .llm_classify import llm_classify
                llm = llm_classify(it["narrative_text"])
                if llm and llm.get("category"):
                    pred = {**pred, **llm}
            except Exception:
                pass  # LLM optional; fall back to rule-based result silently

        category = pred["category"] or UNKNOWN_FALLBACK
        m = meta(category)
        outcome = pred.get("outcome", "observation")
        location = pred.get("location") or ""

        records.append({
            "incident_id": it["incident_id"],
            "timestamp": it["timestamp"],
            "site_id": it["site_id"],
            "reporter_role": it.get("reporter_role", ""),
            "narrative_text": it["narrative_text"],
            "category": category,
            "severity": score_priority(m["nexus"], outcome, location, False),
            "cyber_nexus": m["nexus"],
            "cyber_implication": m["implication"],
            "nist_csf_function": m["csf"],
            "pattern_flag": False,
            "_outcome": outcome,
            "_location": location,
            "_confidence": pred.get("confidence", 0.0),
        })

    flag_recurrences(records, window_days=7, min_count=3)
    return records
