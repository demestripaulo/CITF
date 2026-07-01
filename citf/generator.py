"""Synthetic incident dataset generator.

Produces a labeled dataset of fictional physical-security incident reports,
deliberately imbalanced toward routine property/safety events so that
cyber-relevant incidents form the meaningful minority a triage tool must surface.

Outputs (written to the chosen output directory):
  - incidents.json / incidents.csv          : full records WITH labels (ground truth)
  - incidents_input.json / incidents_input.csv : narratives only (what the tool sees)

Deterministic: a given --seed always yields the same dataset.
"""

import csv
import json
import os
import random
from datetime import datetime, timedelta

from . import taxonomy as T
from . import templates as TPL
from .triage import score_priority

# Schema field order (kept stable for CSV columns)
LABELED_FIELDS = [
    "incident_id", "timestamp", "site_id", "reporter_role", "narrative_text",
    "category", "severity", "cyber_nexus", "cyber_implication",
    "nist_csf_function", "pattern_flag", "_outcome", "_location",
]
INPUT_FIELDS = ["incident_id", "timestamp", "site_id", "reporter_role", "narrative_text"]

SITES = ["SITE-A", "SITE-B", "SITE-C", "SITE-D", "SITE-E", "SITE-F", "SITE-G"]
WINDOW_DAYS = 90
START = datetime(2026, 1, 6, 0, 0, 0)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _pick_location(rng, code):
    candidates = TPL.LOCATION_BIAS.get(code, T.ALL_LOCATIONS)
    return rng.choice(candidates)


def _pick_outcome(rng, code):
    return rng.choice(TPL.OUTCOME_BIAS.get(code, TPL.DEFAULT_OUTCOMES))


def _narrative(rng, code, location, ts):
    template = rng.choice(TPL.TEMPLATES[code])
    return template.format(location=location.replace("_", " "), time=ts.strftime("%H:%M"))


def _pick_group(rng):
    groups = list(TPL.GROUP_WEIGHTS.keys())
    weights = list(TPL.GROUP_WEIGHTS.values())
    return rng.choices(groups, weights=weights, k=1)[0]


def _build_record(rng, incident_id, code, site, ts, pattern_flag,
                  location=None, outcome=None):
    meta = T.meta(code)
    if location is None:
        location = _pick_location(rng, code)
    if outcome is None:
        outcome = _pick_outcome(rng, code)
    severity = score_priority(meta["nexus"], outcome, location, pattern_flag)
    return {
        "incident_id": incident_id,
        "timestamp": ts.isoformat(),
        "site_id": site,
        "reporter_role": rng.choice(TPL.REPORTER_ROLES),
        "narrative_text": _narrative(rng, code, location, ts),
        "category": code,
        "severity": severity,
        "cyber_nexus": meta["nexus"],
        "cyber_implication": meta["implication"],
        "nist_csf_function": meta["csf"],
        "pattern_flag": pattern_flag,
        "_outcome": outcome,
        "_location": location,
    }


def _rand_ts(rng):
    return START + timedelta(
        days=rng.randint(0, WINDOW_DAYS - 1),
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
    )


# --------------------------------------------------------------------------- #
# Pattern injection (Phase 1 §4)
# --------------------------------------------------------------------------- #

def _inject_patterns(rng, start_id):
    """Return a list of records that form deliberate, detectable patterns."""
    records = []
    nid = start_id

    # 3 recurrence sets: same site + same cyber-relevant category in a 7-day window
    recurrence_specs = [("SITE-B", "AC-02"), ("SITE-D", "VP-01"), ("SITE-A", "SV-01")]
    for site, code in recurrence_specs:
        base = _rand_ts(rng)
        for _ in range(rng.randint(3, 4)):
            ts = base + timedelta(days=rng.randint(0, 6), hours=rng.randint(0, 23),
                                  minutes=rng.randint(0, 59))
            records.append(_build_record(rng, f"INC-{nid:06d}", code, site, ts, True))
            nid += 1

    # 2 escalation sequences: recon -> attempt -> success, same site, ~10-day window
    escalation_specs = [
        ("SITE-C", ["SV-03", "AC-04", "AC-01"]),
        ("SITE-E", ["SV-03", "AC-04", "IN-01"]),
    ]
    for site, sequence in escalation_specs:
        base = _rand_ts(rng)
        offset = 0
        for code in sequence:
            ts = base + timedelta(days=offset, hours=rng.randint(8, 22))
            forced_outcome = "success" if code in ("AC-01", "IN-01") else (
                "attempt" if code == "AC-04" else "observation")
            loc = None
            if code == "IN-01":
                loc = rng.choice(["server_room", "network_closet"])
            records.append(_build_record(rng, f"INC-{nid:06d}", code, site, ts, True,
                                          location=loc, outcome=forced_outcome))
            nid += 1
            offset += rng.randint(2, 5)

    # 1 cross-site set: same category across 3 sites in a 5-day window
    cs_code = "VP-02"
    base = _rand_ts(rng)
    for site in ["SITE-A", "SITE-F", "SITE-G"]:
        ts = base + timedelta(days=rng.randint(0, 4), hours=rng.randint(8, 20))
        records.append(_build_record(rng, f"INC-{nid:06d}", cs_code, site, ts, True))
        nid += 1

    return records


# --------------------------------------------------------------------------- #
# Main generation
# --------------------------------------------------------------------------- #

def generate(count=600, seed=42):
    """Generate `count` random records plus injected pattern sets."""
    rng = random.Random(seed)
    records = []

    for i in range(count):
        group = _pick_group(rng)
        code = rng.choice(T.GROUPS[group])
        site = rng.choice(SITES)
        ts = _rand_ts(rng)
        records.append(_build_record(rng, f"INC-{i + 1:06d}", code, site, ts, False))

    records += _inject_patterns(rng, start_id=count + 1)

    # sort chronologically for realism
    records.sort(key=lambda r: r["timestamp"])

    # Apply the SAME recurrence rule used at runtime, so "pattern" has a single
    # definition across generation and triage (organic recurrences are labeled
    # too, on top of the deliberately injected escalation/cross-site seeds).
    from .patterns import flag_recurrences
    flag_recurrences(records, window_days=7, min_count=3)
    return records


def _write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fields})


def generate_and_write(count=600, seed=42, out_dir="data"):
    os.makedirs(out_dir, exist_ok=True)
    records = generate(count=count, seed=seed)

    # Full labeled dataset (ground truth)
    with open(os.path.join(out_dir, "incidents.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    _write_csv(os.path.join(out_dir, "incidents.csv"), records, LABELED_FIELDS)

    # Input-only view (what the runtime tool receives — no labels)
    inputs = [{k: r[k] for k in INPUT_FIELDS} for r in records]
    with open(os.path.join(out_dir, "incidents_input.json"), "w", encoding="utf-8") as f:
        json.dump(inputs, f, indent=2, ensure_ascii=False)
    _write_csv(os.path.join(out_dir, "incidents_input.csv"), inputs, INPUT_FIELDS)

    return records


def summarize(records):
    """Return a small summary dict for reporting."""
    from collections import Counter
    by_group = Counter(T.meta(r["category"])["group"] for r in records)
    by_sev = Counter(r["severity"] for r in records)
    by_nexus = Counter(r["cyber_nexus"] for r in records)
    patterns = sum(1 for r in records if r["pattern_flag"])
    return {
        "total": len(records),
        "by_group": dict(by_group),
        "by_severity": dict(sorted(by_sev.items())),
        "by_nexus": dict(by_nexus),
        "pattern_records": patterns,
    }
