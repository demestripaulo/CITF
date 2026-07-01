"""Rule-based narrative classifier.

Reads a free-text incident narrative and infers:
  - category  (a taxonomy code)
  - outcome   (success | attempt | observation)
  - location  (a known location, if named)
plus a simple confidence score.

This is a transparent baseline. It scores each category by matched signal terms
and picks the best. It performs very well on well-formed narratives and is the
honest floor for the system; the optional LLM classifier (llm_classify.py)
exists to generalize to messy, real-world phrasing that these keywords miss.
"""

import re

from .taxonomy import ALL_LOCATIONS, CATEGORIES

# Distinctive signal terms per category. Weighted by specificity (longer/rarer
# phrases score higher). Deliberately signal-based, not copies of the templates.
SIGNALS = {
    "AC-01": [("tailgat", 3), ("piggyback", 3), ("without badging", 3),
              ("did not badge", 3), ("behind a badged", 3), ("followed", 1)],
    "AC-02": [("propped", 3), ("held open", 3), ("wedge", 3), ("standing open", 2),
              ("latch appeared forced", 3), ("designated closed", 2), ("forced", 1)],
    "AC-03": [("no longer affiliated", 3), ("former employee", 3), ("same credential", 3),
              ("two entries", 2), ("credential", 1), ("badge", 1)],
    "AC-04": [("turned away", 3), ("access denied", 3), ("attempted entry", 3),
              ("tried badging", 3), ("without authorization", 2)],
    "AC-05": [("outside operating hours", 3), ("outside authorized hours", 3),
              ("no scheduled activity", 3), ("after hours", 2), ("outside authorized", 2)],
    "VP-01": [("declined to provide id", 3), ("no record of appointment", 3),
              ("could not be verified", 3), ("visitor log", 2), ("refused to provide", 2)],
    "VP-02": [("work order", 3), ("could not produce", 2), ("claimed to be an it vendor", 3),
              ("contractor", 2), ("vendor", 2), ("maintenance contractor", 2)],
    "VP-03": [("just this once", 3), ("time pressure", 3), ("talk past", 3),
              ("claimed authority", 3), ("pressured", 2), ("pretext", 2)],
    "VP-04": [("no known recipient", 3), ("no manifest", 3), ("unexpected parcel", 3),
              ("unscheduled delivery", 3), ("parcel", 1), ("package", 1)],
    "DV-01": [("usb", 3), ("flash drive", 3), ("removable drive", 3), ("unlabeled", 2)],
    "DV-02": [("unknown laptop", 3), ("plugged into equipment", 3),
              ("connected to a network port", 3), ("unrecognized device", 3),
              ("unknown device", 2)],
    "DV-03": [("photographing access points", 3), ("recording the", 2),
              ("on a phone", 2), ("photographing", 1)],
    "IN-01": [("without escort", 3), ("unlocked and occupied", 3), ("it closet", 2),
              ("inside the server room", 3), ("inside the network closet", 3)],
    "IN-02": [("power fluctuation", 3), ("cooling failure", 3), ("hvac", 3),
              ("affecting equipment", 2)],
    "IN-03": [("patch cable", 3), ("open and active network port", 3),
              ("disconnected", 2), ("cabling", 2)],
    "SV-01": [("repositioned away", 3), ("feed was offline", 3), ("lens obscured", 3),
              ("camera", 1), ("offline", 1)],
    "SV-02": [("camera gap", 3), ("blind spot", 3), ("avoids camera", 3),
              ("camera coverage", 2)],
    "SV-03": [("photographing the layout", 3), ("noting access points", 3),
              ("repeatedly observing", 3), ("lingered near", 2), ("casing", 3)],
    "IF-01": [("confidential files", 3), ("left unattended on a desk", 3),
              ("marked sensitive", 3), ("exposed", 1)],
    "IF-02": [("open trash", 3), ("unsecured disposal", 3), ("improper disposal", 3),
              ("in disposal", 2)],
    "IF-03": [("workstation screen", 3), ("logged-in screen", 3), ("shoulder", 2),
              ("viewing a staff", 2)],
    "PR-01": [("suspected theft", 3), ("reported missing", 3), ("theft", 1), ("missing", 1)],
    "PR-02": [("graffiti", 3), ("vandalism", 3)],
    "PR-03": [("perimeter fence", 3), ("climbing the perimeter", 3), ("trespasser", 3),
              ("crossing into the grounds", 3), ("perimeter", 1)],
    "PR-04": [("slip-and-fall", 3), ("first aid", 3), ("fire alarm", 3), ("medical", 2)],
}

OUTCOME_SIGNALS = {
    "attempt": ["turned away", "access denied", "attempted", "tried", "declined",
                "refused", "without authorization"],
    "success": ["propped", "held open", "followed", "entered via", "connected",
                "occupied", "plugged into", "gained", "standing open"],
}

_LOC_LOOKUP = {loc.replace("_", " "): loc for loc in ALL_LOCATIONS}


def _extract_location(text_lower):
    for phrase, canonical in _LOC_LOOKUP.items():
        if phrase in text_lower:
            return canonical
    return None


def _extract_outcome(text_lower):
    for term in OUTCOME_SIGNALS["attempt"]:
        if term in text_lower:
            return "attempt"
    for term in OUTCOME_SIGNALS["success"]:
        if term in text_lower:
            return "success"
    return "observation"


def classify_narrative(text):
    """Return {'category', 'outcome', 'location', 'confidence', 'scores'}."""
    t = text.lower()

    scores = {}
    for code, terms in SIGNALS.items():
        s = sum(weight for term, weight in terms if term in t)
        if s:
            scores[code] = s

    if not scores:
        return {"category": None, "outcome": _extract_outcome(t),
                "location": _extract_location(t), "confidence": 0.0, "scores": {}}

    best = max(scores, key=scores.get)
    total = sum(scores.values())
    confidence = round(scores[best] / total, 2) if total else 0.0

    return {
        "category": best,
        "outcome": _extract_outcome(t),
        "location": _extract_location(t),
        "confidence": confidence,
        "scores": scores,
    }
