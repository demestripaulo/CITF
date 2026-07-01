"""Sanity checks for the narrative classifier and triage pipeline.
Run: python3 tests/test_classify.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from citf.classify import classify_narrative
from citf.pipeline import triage_narratives


def test_classifies_core_cases():
    cases = {
        "A USB flash drive was found unattended in the main lobby at 21:10.": "DV-01",
        "Found the rear entrance door propped open with a wedge at 02:31.": "AC-02",
        "Person observed inside the server room at 23:40 without escort.": "IN-01",
        "Graffiti was found on the exterior wall near the chapel at 15:00.": "PR-02",
        "Individual attempted entry at the library at 10:00 and was turned away.": "AC-04",
    }
    for text, expected in cases.items():
        pred = classify_narrative(text)
        assert pred["category"] == expected, f"{text!r} -> {pred['category']} (expected {expected})"


def test_outcome_extraction():
    assert classify_narrative("attempted entry and was turned away")["outcome"] == "attempt"
    assert classify_narrative("door was held open with a wedge")["outcome"] == "success"


def test_pipeline_produces_schema():
    items = [{
        "incident_id": "T-1", "timestamp": "2026-03-02T02:31:00",
        "site_id": "SITE-B", "reporter_role": "guard",
        "narrative_text": "Found the rear entrance door propped open at 02:31.",
    }]
    recs = triage_narratives(items)
    r = recs[0]
    assert r["category"] == "AC-02"
    assert r["severity"] in {"P1", "P2", "P3", "P4"}
    assert r["cyber_nexus"] == "high"


if __name__ == "__main__":
    test_classifies_core_cases()
    test_outcome_extraction()
    test_pipeline_produces_schema()
    print("All classifier sanity checks passed.")
