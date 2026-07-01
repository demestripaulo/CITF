#!/usr/bin/env python3
"""Build a floor-plan heat map + triaged feed from sensor data.

Reads data/sensor_events.json and data/sensor_incidents.json, aggregates per-door
frequency / open-duration / worst severity, and writes:
    viz/heatmap.svg   (the floor plan alone)
    viz/heatmap.html  (standalone page: floor plan + legend + triaged feed)

Uses a GENERIC/synthetic floor plan — never a real site plan. For an internal
deployment, swap in the authorized plan locally; keep this generic for anything
public.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from citf.sensors import DEFAULT_DOOR_CONFIG, DEFAULT_PIR_CONFIG  # noqa: E402

# Door label + (x, y) marker position on the 960x560 canvas.
LAYOUT = {
    "DOOR-01": (470, 505, "Main Lobby"),
    "DOOR-02": (480, 52, "Rear Entrance"),
    "DOOR-03": (760, 150, "Server Room"),
    "DOOR-04": (778, 378, "Records Room"),
    "DOOR-05": (162, 200, "Dormitory"),
    "DOOR-06": (160, 500, "Chapel"),
}
PIR_LAYOUT = {
    "PIR-01": (150, 290, "Library"),
    "PIR-02": (780, 290, "Admin Office"),
}

# Rooms: (x, y, w, h, label)
ROOMS = [
    (60, 60, 200, 130, "Dormitory"),
    (380, 60, 200, 80, "Rear Vestibule"),
    (700, 60, 120, 80, "Server Room"),
    (700, 150, 120, 40, "Network Closet"),
    (60, 210, 180, 140, "Library"),
    (300, 200, 320, 170, "Classroom Building"),
    (680, 210, 200, 130, "Administration"),
    (680, 360, 200, 130, "Records Room"),
    (60, 380, 200, 120, "Chapel"),
    (330, 400, 260, 100, "Main Lobby"),
]

# Emergency exits: (x, y)
EXITS = [(470, 516), (480, 44), (48, 300), (912, 300)]

SEV_COLOR = {"P1": "#f85149", "P2": "#e8833a", "P3": "#d4a72c", "P4": "#3fb950"}
SEV_RANK = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}


def _open_durations(events):
    """Return per-door (open_count, total_open_seconds)."""
    per_door = defaultdict(lambda: [0, 0.0])
    last_open = {}
    for e in sorted(events, key=lambda x: x.get("timestamp", "")):
        if e.get("state") == "open":
            per_door[e["door_id"]][0] += 1
            last_open[e["door_id"]] = datetime.fromisoformat(e["timestamp"])
        elif e.get("state") == "closed" and e["door_id"] in last_open:
            dt = (datetime.fromisoformat(e["timestamp"]) - last_open.pop(e["door_id"])).total_seconds()
            per_door[e["door_id"]][1] += max(dt, 0)
    return per_door


def _incident_stats(incidents):
    """Return per-(site, location) dict of counts and worst severity."""
    stats = defaultdict(lambda: {"AC-02": 0, "AC-05": 0, "worst": "P4", "count": 0})
    for r in incidents:
        key = (r["site_id"], r.get("_location", ""))
        s = stats[key]
        s["count"] += 1
        if r["category"] in ("AC-02", "AC-05"):
            s[r["category"]] += 1
        if SEV_RANK[r["severity"]] < SEV_RANK[s["worst"]]:
            s["worst"] = r["severity"]
    return stats


def build_svg(events, incidents):
    durations = _open_durations(events)
    istats = _incident_stats(incidents)

    parts = ['<svg viewBox="0 0 960 560" xmlns="http://www.w3.org/2000/svg" '
             'font-family="system-ui, sans-serif">']
    parts.append('<rect x="0" y="0" width="960" height="560" fill="#0d1117"/>')
    parts.append('<rect x="40" y="40" width="880" height="480" fill="none" '
                 'stroke="#30363d" stroke-width="3"/>')
    parts.append('<text x="56" y="30" fill="#c9d1d9" font-size="18" font-weight="700">'
                 'CITF — Door-Risk Heat Map (synthetic floor plan)</text>')

    for (x, y, w, h, label) in ROOMS:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#161b22" '
                     f'stroke="#30363d" stroke-width="1.5" rx="4"/>')
        parts.append(f'<text x="{x + 8}" y="{y + 18}" fill="#8b949e" font-size="11">{label}</text>')

    # Emergency exits
    for (x, y) in EXITS:
        parts.append(f'<rect x="{x - 16}" y="{y - 8}" width="32" height="16" rx="3" '
                     f'fill="#238636"/>')
        parts.append(f'<text x="{x}" y="{y + 4}" fill="#ffffff" font-size="9" '
                     f'font-weight="700" text-anchor="middle">EXIT</text>')

    # PIR sensors (small squares)
    for pir_id, (x, y, label) in PIR_LAYOUT.items():
        cfg = DEFAULT_PIR_CONFIG[pir_id]
        st = istats.get((cfg["site_id"], cfg["location"]))
        color = SEV_COLOR[st["worst"]] if st else "#3fb950"
        n = st["count"] if st else 0
        parts.append(f'<rect x="{x - 8}" y="{y - 8}" width="16" height="16" rx="2" '
                     f'fill="{color}" stroke="#0d1117" stroke-width="1.5">'
                     f'<title>{pir_id} · {label} · motion incidents: {n}</title></rect>')

    # Doors (circles sized by open-frequency, colored by worst severity)
    for door_id, (x, y, label) in LAYOUT.items():
        cfg = DEFAULT_DOOR_CONFIG[door_id]
        st = istats.get((cfg["site_id"], cfg["location"]))
        color = SEV_COLOR[st["worst"]] if st else "#3fb950"
        opens, secs = durations.get(door_id, [0, 0.0])
        propped = st["AC-02"] if st else 0
        afterh = st["AC-05"] if st else 0
        radius = 9 + min(opens, 60) / 6.0
        mins = round(secs / 60.0)
        tip = (f"{door_id} · {label}\\nopens: {opens} · total open: {mins} min\\n"
               f"propped(AC-02): {propped} · after-hours(AC-05): {afterh}\\n"
               f"worst: {st['worst'] if st else 'none'}")
        parts.append(f'<circle cx="{x}" cy="{y}" r="{radius:.1f}" fill="{color}" '
                     f'fill-opacity="0.85" stroke="#0d1117" stroke-width="2">'
                     f'<title>{tip}</title></circle>')
        parts.append(f'<text x="{x}" y="{y - radius - 5:.0f}" fill="#c9d1d9" font-size="10" '
                     f'text-anchor="middle">{door_id}</text>')

    # Legend
    lx, ly = 56, 540
    parts.append(f'<text x="{lx}" y="{ly - 6}" fill="#8b949e" font-size="11">Worst severity:</text>')
    for i, (sev, col) in enumerate(SEV_COLOR.items()):
        cx = lx + 110 + i * 90
        parts.append(f'<circle cx="{cx}" cy="{ly - 10}" r="7" fill="{col}"/>')
        parts.append(f'<text x="{cx + 12}" y="{ly - 6}" fill="#c9d1d9" font-size="11">{sev}</text>')

    parts.append('</svg>')
    return "\n".join(parts)


def build_html(svg, incidents):
    top = sorted(incidents, key=lambda r: (SEV_RANK[r["severity"]], r["timestamp"]))[:15]
    rows = []
    for r in top:
        col = SEV_COLOR[r["severity"]]
        rows.append(
            f'<tr><td><span class="pill" style="background:{col}">{r["severity"]}</span></td>'
            f'<td>{r["timestamp"][:16].replace("T", " ")}</td>'
            f'<td>{r["site_id"]} · {r.get("_location", "").replace("_", " ")}</td>'
            f'<td>{r["category"]}</td><td>{r["cyber_implication"]}</td></tr>')
    feed = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CITF Heat Map</title>
<style>
  body {{ margin:0; background:#0d1117; color:#c9d1d9; font-family:system-ui, sans-serif; }}
  .wrap {{ max-width:1000px; margin:0 auto; padding:24px; }}
  svg {{ width:100%; height:auto; border:1px solid #30363d; border-radius:8px; }}
  h2 {{ font-size:16px; margin:28px 0 10px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th, td {{ text-align:left; padding:8px 10px; border-bottom:1px solid #21262d; }}
  th {{ color:#8b949e; font-weight:600; }}
  .pill {{ color:#0d1117; font-weight:700; padding:2px 8px; border-radius:10px; font-size:12px; }}
  .note {{ color:#8b949e; font-size:12px; margin-top:16px; }}
</style></head>
<body><div class="wrap">
{svg}
<h2>Triaged incident feed (top 15 by priority)</h2>
<table><thead><tr><th>Priority</th><th>When</th><th>Where</th><th>Category</th><th>Cyber implication</th></tr></thead>
<tbody>
{feed}
</tbody></table>
<p class="note">Synthetic data. Generic floor plan — not a real site. Door size reflects open-frequency; color reflects worst incident severity at that door.</p>
</div></body></html>"""


def main():
    events = json.load(open("data/sensor_events.json", encoding="utf-8"))
    incidents = json.load(open("data/sensor_incidents.json", encoding="utf-8"))
    os.makedirs("viz", exist_ok=True)
    svg = build_svg(events, incidents)
    with open("viz/heatmap.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    with open("viz/heatmap.html", "w", encoding="utf-8") as f:
        f.write(build_html(svg, incidents))
    print("Wrote viz/heatmap.svg and viz/heatmap.html")


if __name__ == "__main__":
    main()
