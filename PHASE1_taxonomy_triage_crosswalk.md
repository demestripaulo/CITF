# Project #1 — Phase 1
## Incident Taxonomy, Triage Rubric & Physical-to-Cyber Crosswalk
**Draft v1 — conceptual core of the AI-assisted incident-triage framework**

### Purpose & integrity note
This document defines the conceptual core of the framework: (1) a **taxonomy** to classify physical-security incident reports, (2) a **rubric** to prioritize them, (3) a **crosswalk** that translates physical incidents into cyber-risk implications, and (4) the **data schema** used to generate the synthetic dataset in Phase 2.

**All data is synthetic.** No employer or client data is used. The tool is designed to be *source-agnostic* — it ingests a flat export (CSV/JSON), never a live connection to any production system. If an authorized employer pilot ever uses real data, the de-identification rules in §6 apply.

---

## 1. Incident Category Taxonomy

Each incident is assigned one primary category code. Categories are grouped by domain. The "narrative cue" column is what a human report typically contains — this is what the model reads.

### ACCESS — Access & Entry Control
| Code | Category | Typical narrative cue |
|---|---|---|
| AC-01 | Tailgating / piggybacking | "followed an authorized person through the door without badging" |
| AC-02 | Forced or propped door/gate | "found rear door propped open"; "lock appeared forced" |
| AC-03 | Credential anomaly | "badge belonging to former employee"; "two entries on one card" |
| AC-04 | Unauthorized access attempt (denied) | "attempted entry without authorization, turned away" |
| AC-05 | After-hours / unexpected presence | "individual on site outside authorized hours" |

### VISITOR — Visitor, Vendor & Personnel
| Code | Category | Typical narrative cue |
|---|---|---|
| VP-01 | Unverified visitor / refused identification | "declined to provide ID"; "no record of appointment" |
| VP-02 | Vendor/contractor impersonation | "claimed to be IT vendor, could not confirm work order" |
| VP-03 | Social engineering / pretexting at post | "asked guard to let them in 'just this once'"; urgency/authority pressure |
| VP-04 | Delivery / parcel anomaly | "unexpected package addressed to no known recipient" |

### DEVICE — Devices & Media
| Code | Category | Typical narrative cue |
|---|---|---|
| DV-01 | Unattended/unknown removable media | "USB drive found in parking lot/lobby" |
| DV-02 | Unauthorized device connected | "unknown laptop plugged into network jack / guard PC" |
| DV-03 | Unauthorized photography/recording | "observed photographing access points / server room" |

### INFRA — Critical Infrastructure & IT Spaces
| Code | Category | Typical narrative cue |
|---|---|---|
| IN-01 | Access to server/network/telecom space | "person in IT closet without escort" |
| IN-02 | Utility/HVAC/power event affecting systems | "power event in comms room"; "AC failure in server room" |
| IN-03 | Cabling / network port tampering | "patch cable disconnected"; "open network port in public area" |

### SURVEIL — Surveillance & Detection Systems
| Code | Category | Typical narrative cue |
|---|---|---|
| SV-01 | Camera/sensor tampering or outage | "camera repositioned / lens obscured / offline" |
| SV-02 | Blind-spot exploitation | "movement through known camera gap" |
| SV-03 | Suspected reconnaissance / casing | "repeatedly observing entrances, photographing layout" |

### INFO — Information Handling
| Code | Category | Typical narrative cue |
|---|---|---|
| IF-01 | Sensitive documents exposed/unsecured | "confidential files left on desk overnight" |
| IF-02 | Improper disposal of sensitive material | "documents with PII in open trash" |
| IF-03 | Shoulder-surfing / screen exposure | "unauthorized person viewing workstation screen" |

### PROPERTY — Property & Safety (baseline, low cyber-nexus)
*Included deliberately so the model learns to discriminate genuine cyber-relevant events from routine physical events.*
| Code | Category | Typical narrative cue |
|---|---|---|
| PR-01 | Theft / attempted theft | "missing item from common area" |
| PR-02 | Vandalism | "graffiti on exterior wall" |
| PR-03 | Trespassing / perimeter breach | "individual climbed perimeter fence" |
| PR-04 | Safety / medical / fire event | "slip-and-fall in lobby"; "fire alarm activation" |

---

## 2. Severity / Priority Rubric

Each incident receives a priority P1–P4. Priority is a function of five factors:

1. **Cyber-nexus strength** — how directly the event maps to a cyber-risk (see §3).
2. **Asset/location sensitivity** — server/comms space and credential systems rank highest.
3. **Outcome** — successful breach vs. attempt vs. observation.
4. **Recurrence/pattern** — repeated or escalating events at the same site (see §4).
5. **Intent indicators** — evasion, pretexting, reconnaissance, concealment.

| Priority | Definition | Response expectation |
|---|---|---|
| **P1 — Critical** | Successful or imminent compromise with a strong cyber-nexus (e.g., unknown device connected to network; unescorted access to server room). | Immediate escalation + notification. |
| **P2 — High** | Credible cyber-relevant event, attempt or strong indicator (e.g., tailgating into a sensitive area; pretexting against the guard). | Same-shift escalation + documentation. |
| **P3 — Moderate** | Cyber-relevant but low immediacy, or single low-severity event (e.g., propped door in low-sensitivity area). | Logged, reviewed, pattern-monitored. |
| **P4 — Informational** | Little/no cyber-nexus; routine physical/safety event. | Logged for record and pattern baseline. |

**Simple scoring guide (for the synthetic labels and the tool's default logic):** start from the crosswalk's default nexus level (§3), then raise priority one level for each of: success (not attempt), sensitive location, or active pattern; lower one level if clearly isolated and non-sensitive.

---

## 3. Physical-to-Cyber Crosswalk *(the differentiating contribution)*

This is what log-based tools (SIEM) and camera-integration platforms (PSIM) do **not** do: read a human-authored physical incident and surface its cyber-risk meaning. NIST CSF references are given at the **function** level; exact CSF 2.0 *category* codes should be confirmed against the current framework before publication.

| Category | Cyber-risk implication | NIST CSF function | Default nexus |
|---|---|---|---|
| AC-01 Tailgating | Unauthorized physical access to endpoints, network jacks, credentials | Protect | High |
| AC-02 Forced/propped door | Physical access path bypassing controls | Protect / Detect | High |
| AC-03 Credential anomaly | Credential misuse / cloning / orphaned access | Protect | High |
| VP-02 Vendor impersonation | Pretext for access to systems/spaces (supply-chain/physical) | Protect / Identify | High |
| VP-03 Social engineering at post | Front-line pretexting → access or info disclosure | Protect (awareness) | High |
| DV-01 Unknown removable media | Malware / BadUSB introduction vector | Protect / Detect | High |
| DV-02 Unauthorized device connected | Direct network/endpoint compromise | Detect / Protect | Critical |
| IN-01 Server/network space access | Direct infrastructure compromise | Protect | Critical |
| IN-03 Port/cabling tampering | Network tap / unauthorized connectivity | Detect | High |
| SV-01 Camera/sensor tampering | Defeating detection to cover later intrusion | Detect | High |
| SV-03 Reconnaissance / casing | Pre-attack intelligence gathering | Identify / Detect | Moderate |
| IF-01/02 Info exposure/disposal | Sensitive data / PII disclosure | Protect | Moderate |
| IF-03 Shoulder-surfing | Credential/info disclosure | Protect | Moderate |
| PR-01..04 Property/safety | Minimal or no cyber-nexus (discrimination baseline) | — | Low/None |

---

## 4. Pattern & Anomaly Signals (beyond single-incident triage)

The framework adds value not just per-incident but across the stream:

- **Recurrence rule:** same site + same category within a rolling window (e.g., 3× AC-02 in 7 days) → raise priority and flag.
- **Escalation sequence:** reconnaissance (SV-03) → access attempt (AC-04) → success (AC-01/IN-01) at the same site → flag as a developing pattern.
- **Cross-site correlation:** the same anomaly across multiple client sites in a short window → possible coordinated activity.

---

## 5. Data Schema (bridge to Phase 2)

Each synthetic record carries both the raw narrative (model input) and the labels (ground truth for evaluation):

```json
{
  "incident_id": "string (uuid)",
  "timestamp": "ISO-8601",
  "site_id": "string (synthetic, e.g., SITE-A through SITE-G)",
  "reporter_role": "guard | supervisor | account_manager",
  "narrative_text": "free-text incident report (synthetic)",
  "category": "taxonomy code (e.g., AC-01)  [label]",
  "severity": "P1 | P2 | P3 | P4  [label]",
  "cyber_nexus": "critical | high | moderate | low | none  [label]",
  "cyber_implication": "short phrase from crosswalk  [label]",
  "nist_csf_function": "Identify | Protect | Detect | Respond | Recover  [label]",
  "pattern_flag": "boolean (true if part of a recurrence/escalation set)"
}
```

**Phase 2 generation targets:** ~500–1,000 records; realistic class balance (PROPERTY/safety should be the majority, as in real operations, with cyber-relevant categories as the meaningful minority the tool must surface); include deliberate recurrence/escalation sets so §4 logic can be demonstrated and evaluated.

---

## 6. Scope & integrity rules

- **Synthetic-first.** Public dataset and repo use only generated data, clearly labeled synthetic.
- **Source-agnostic ingestion.** The tool reads CSV/JSON exports; it never connects live to any production or employer system and never uses work credentials against a legacy system.
- **De-identification (only if an authorized pilot uses real data):** strip names, unit/apartment numbers, exact addresses, license plates, badge IDs, and any free-text PII; replace site identifiers with neutral codes; aggregate timestamps to the hour. Authorization in writing from the employer is a precondition.
