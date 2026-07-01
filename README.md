# Converged Incident Triage Framework (CITF)

[![tests](https://github.com/demestripaulo/CITF/actions/workflows/tests.yml/badge.svg)](https://github.com/demestripaulo/CITF/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)

A source-agnostic framework for classifying **physical-security incident reports**,
prioritizing them, and surfacing their **cyber-risk implications** — aimed at
small and mid-sized, security-dependent organizations that do not run a Security
Operations Center or enterprise monitoring tools.

Log-based tools (SIEM) and camera-integration platforms (PSIM) do not read the
human-authored narratives a security officer writes ("found the rear door
propped open," "a USB drive was left in the lobby"). CITF focuses on exactly
that layer: turning free-text physical incidents into prioritized, cyber-aware
signal.

> **All bundled data is synthetic.** This repository contains no real, employer,
> or client data. The generator produces fictional incident reports for research,
> development, and evaluation.

## Why this exists

Most security-awareness and monitoring tooling targets enterprise IT and office
knowledge workers. The front-line physical-security workforce — and the small
organizations it protects — sit in a gap: real cyber-relevant events (tailgating,
propped doors, unknown devices, pretexting at reception) are reported in plain
language and never translated into cyber-risk terms. CITF is a practical bridge
for that gap.

## What's here (Phase 1 + Phase 2)

- **Phase 1 — conceptual core** (`PHASE1_taxonomy_triage_crosswalk.md`):
  the incident taxonomy, the P1–P4 triage rubric, and the physical-to-cyber
  crosswalk.
- **Phase 2 — synthetic data engine** (`citf/`, `scripts/`):
  a deterministic generator that produces a labeled dataset built from the
  Phase 1 taxonomy, with realistic class imbalance and deliberate incident
  patterns (recurrence, escalation, cross-site).

```
citf/
  taxonomy.py    # categories + physical->cyber crosswalk + severity config (single source of truth)
  triage.py      # transparent P1-P4 priority engine (also powers the runtime tool)
  templates.py   # narrative templates and generation biases
  generator.py   # dataset generation + pattern injection
  sensors.py     # sensor ingestion adapter (door-state / motion events -> incidents)
  patterns.py    # recurrence detection over an incident stream (Phase 1 §4)
  sensor_sim.py  # synthetic sensor-event simulator (no hardware required)
scripts/
  generate_dataset.py       # CLI: synthetic narrative dataset
  simulate_sensors.py       # CLI: simulate sensors -> incidents (+ recurrence)
  ingest_sensor_events.py   # CLI: ingest REAL exported sensor events
tests/
  test_generator.py         # determinism / schema / pattern sanity checks
  test_sensors.py           # sensor adapter + recurrence checks
```

## Quick start

No external dependencies (Python 3.9+):

```bash
python3 scripts/generate_dataset.py --count 600 --seed 42 --out data
```

This writes to `data/`:

| File | Contents |
|---|---|
| `incidents.json` / `incidents.csv` | full records **with labels** (ground truth) |
| `incidents_input.json` / `incidents_input.csv` | narratives only (what the tool sees) |

The `input` files separate the model's input from the ground-truth labels so a
classifier can be evaluated honestly in later phases.

## Record schema

```json
{
  "incident_id": "INC-000123",
  "timestamp": "2026-02-14T02:31:00",
  "site_id": "SITE-B",
  "reporter_role": "guard",
  "narrative_text": "Found the rear entrance door propped open with a wedge at 02:31; no personnel present.",
  "category": "AC-02",
  "severity": "P2",
  "cyber_nexus": "high",
  "cyber_implication": "Physical access path bypassing controls",
  "nist_csf_function": "Protect",
  "pattern_flag": true
}
```
(The labeled files also include `_outcome` and `_location`, the two derived
features the triage engine uses; these are kept for transparency and evaluation.)

## Design notes

- **Deliberate class imbalance.** Routine property/safety events are the
  majority; cyber-relevant incidents are the minority the tool must surface —
  mirroring real operations.
- **Explainable priority.** Severity is a transparent rule (see `triage.py`),
  not a black box, because it must be defensible to a security manager.
- **Source-agnostic.** The design ingests flat exports (CSV/JSON). It never
  connects live to a production system and never uses operational credentials
  against a legacy platform.
- **NIST CSF references** are at the function level; exact CSF 2.0 category
  codes should be confirmed against the current framework before formal use.

## Sensor ingestion (live data source)

Physical sensors become just another producer of incident records. A door-contact
sensor that reports a should-be-closed door held open beyond a threshold yields an
`AC-02` (propped/open door) incident; an after-hours door opening or motion event
yields an `AC-05` (after-hours presence) incident. These flow through the same
taxonomy, crosswalk, and triage engine as everything else, and the recurrence
detector escalates chronic issues (a door propped repeatedly climbs from P3 to P1).

Test the full path without any hardware:

```bash
python3 scripts/simulate_sensors.py --days 14 --seed 7 --out data
```

This writes `sensor_events.json` (raw stream) and `sensor_incidents.json` / `.csv`
(triaged CITF incidents). For a real deployment, export door/motion events to JSON
and run `scripts/ingest_sensor_events.py --events <file> --doors <config>` — the
adapter reads exports and never connects live to a production system.

**Scope & privacy for a real deployment:** keep to door-state and aggregate counts;
avoid tracking individuals. Use the site's authorized floor plan only for the
internal deployment; use a generic/synthetic plan for any public or portfolio
version. Obtain written authorization, an IP/ownership agreement, and a
de-identification policy before ingesting any real operational data.

## Triage pipeline (Phase 3)

Free-text incident narratives are classified and prioritized end to end:

```bash
python3 scripts/triage_incidents.py --input data/incidents_input.json --truth data/incidents.json
```

- `citf/classify.py` — a transparent, rule-based classifier that infers
  `category`, `outcome`, and `location` from free text with a confidence score.
- `citf/pipeline.py` — narrative → classify → crosswalk → triage → recurrence,
  producing records in the CITF schema.
- `citf/llm_classify.py` — optional Claude-based classifier for messy real-world
  phrasing; the pipeline falls back to the rule-based result if it is unavailable.

On the bundled synthetic set, category accuracy is high (~0.98). Severity is a
*derived* quantity — it depends on whether the narrative explicitly states the
outcome — so its accuracy is lower and honestly bounded by how much the text
says. Sensor-derived incidents carry an exact outcome, so their severity is
exact. Making generated outcomes fully consistent with the narrative text is a
Phase 4 refinement.

## Heat map & triaged feed (Phase 3)

```bash
python3 scripts/build_heatmap.py
```

Writes `viz/heatmap.svg` and a standalone `viz/heatmap.html`: a floor plan whose
doors are colored by worst incident severity and sized by open-frequency, plus a
triaged incident feed. The plan is **generic/synthetic** — swap in an authorized
site plan only for a private, internal deployment.

## Roadmap

- **Phase 4** — evaluation & refinement: precision/recall by category, calibrate
  triage against outcomes made text-consistent, and measure triage-time impact.
- A lightweight capture UI (mobile-friendly) for officers to file narratives that
  enter the same pipeline.

## License

MIT © 2026 Paulo Demestri. See [LICENSE](LICENSE).
