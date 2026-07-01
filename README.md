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

## Roadmap

- **Phase 3** — narrative classifier: extract `category` / `cyber_nexus` /
  outcome from free text (rule-based baseline + optional LLM augmentation),
  then derive priority via `triage.py`. A floor-plan "heat map" view of
  door-open frequency/duration and a triaged incident feed.
- **Phase 4** — evaluation: measure classification against the ground-truth
  labels; report precision/recall and triage-time impact.

## License

MIT © 2026 Paulo Demestri. See [LICENSE](LICENSE).
