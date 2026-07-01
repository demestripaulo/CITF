#!/usr/bin/env python3
"""Triage free-text narratives into prioritized CITF incidents.

Usage:
    python3 scripts/triage_incidents.py --input data/incidents_input.json --out data
    python3 scripts/triage_incidents.py --input data/incidents_input.json --truth data/incidents.json
    python3 scripts/triage_incidents.py --input data/incidents_input.json --use-llm
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from citf.pipeline import triage_narratives           # noqa: E402
from citf.generator import LABELED_FIELDS              # noqa: E402

FIELDS = LABELED_FIELDS + ["_confidence"]


def _write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fields})


def _accuracy(records, truth_path):
    truth = {r["incident_id"]: r for r in json.load(open(truth_path, encoding="utf-8"))}
    cat_hits = sev_hits = n = 0
    for r in records:
        t = truth.get(r["incident_id"])
        if not t:
            continue
        n += 1
        cat_hits += (r["category"] == t["category"])
        sev_hits += (r["severity"] == t["severity"])
    if not n:
        return None
    return {"evaluated": n,
            "category_accuracy": round(cat_hits / n, 3),
            "severity_accuracy": round(sev_hits / n, 3)}


def main():
    parser = argparse.ArgumentParser(description="Triage narratives into CITF incidents.")
    parser.add_argument("--input", default="data/incidents_input.json")
    parser.add_argument("--truth", help="optional labeled file for a quick accuracy check")
    parser.add_argument("--use-llm", action="store_true", help="use LLM fallback for low-confidence cases")
    parser.add_argument("--out", default="data")
    args = parser.parse_args()

    items = json.load(open(args.input, encoding="utf-8"))
    records = triage_narratives(items, use_llm=args.use_llm)

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "triaged.json"), "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    _write_csv(os.path.join(args.out, "triaged.csv"), records, FIELDS)

    summary = {
        "input": len(items),
        "triaged": len(records),
        "by_severity": dict(sorted(Counter(r["severity"] for r in records).items())),
        "recurrence_flagged": sum(1 for r in records if r["pattern_flag"]),
    }
    if args.truth:
        summary["evaluation"] = _accuracy(records, args.truth)

    print(json.dumps(summary, indent=2))
    print(f"\nWritten to: {os.path.abspath(args.out)} (triaged.json / triaged.csv)")


if __name__ == "__main__":
    main()
