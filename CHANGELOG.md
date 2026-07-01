# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/), and the
project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-01

### Added
- **Phase 1 — conceptual core**: incident taxonomy, P1–P4 triage rubric, and the
  physical-to-cyber crosswalk (`PHASE1_taxonomy_triage_crosswalk.md`).
- **Phase 2 — synthetic data engine**: deterministic dataset generator with a
  deliberate class imbalance and injected incident patterns (recurrence,
  escalation, cross-site).
- **Sensor ingestion adapter**: converts door-state and motion events into CITF
  incident records (`AC-02` propped/open door, `AC-05` after-hours).
- **Recurrence detection**: flags and re-scores recurring incidents over a stream.
- **Sensor simulator**: end-to-end testing without hardware.
- Test suites for the generator and the sensor adapter; MIT license; project docs.

[0.1.0]: https://github.com/demestripaulo/CITF/releases/tag/v0.1.0
