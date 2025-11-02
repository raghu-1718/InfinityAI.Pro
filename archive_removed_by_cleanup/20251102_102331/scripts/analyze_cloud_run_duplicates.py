#!/usr/bin/env python3
"""
Analyze Cloud Run services (including 2nd gen Cloud Functions) for potential duplicates
and overlapping functionality. Produces a JSON report and a short Markdown summary.

Usage:
  python scripts/analyze_cloud_run_duplicates.py [path_to_services.json]

Default input is services.json at repo root (exported via:
  gcloud run services list --platform=managed --region=us-central1 --format=json > services.json)
"""
import json
import sys
from collections import defaultdict
from typing import Any, Dict, List, DefaultDict, Tuple
from pathlib import Path
from datetime import datetime

DEFAULT_INPUT = Path("services.json")
REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(exist_ok=True)

# Heuristic overlaps map: Cloud Function name -> Engine endpoint it likely duplicates
OVERLAP_HINTS = {
    "getaisignals": {
        "engine": "engine-b",
        "endpoint": "/api/ai-signals",
        "note": "CF duplicates Engine B AI signals; prefer Engine B"
    },
    "getbatchaisignals": {
        "engine": "engine-b",
        "endpoint": "/api/batch-predict",
        "note": "CF duplicates Engine B batch predict; prefer Engine B"
    },
    "getenginebstatus": {
        "engine": "engine-b",
        "endpoint": "/health",
        "note": "CF mirrors Engine B health; prefer direct health"
    },
    "getgeminianalysis": {
        "engine": "engine-b",
        "endpoint": "/api/gemini/analyze",
        "note": "CF overlaps Gemini analysis now exposed via Engine B"
    },
}


def load_services(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize(s: str) -> str:
    return (s or "").strip().lower()


def analyze(services: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_name: Dict[str, Dict[str, Any]] = {}
    by_function_id: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    all_items: List[Dict[str, Any]] = []

    for item in services:
        meta = item.get("metadata", {})
        ann = meta.get("annotations", {})
        name = normalize(meta.get("name"))
        func_id = normalize(ann.get("cloudfunctions.googleapis.com/function-id"))
        service_type = "cloud-function" if func_id else "cloud-run-service"
        status = item.get("status", {})
        url = status.get("url") or (status.get("address", {}) or {}).get("url")
        urls_ann = ann.get("run.googleapis.com/urls")

        rec: Dict[str, Any] = {
            "name": name,
            "function_id": func_id or None,
            "type": service_type,
            "url": url,
            "urls": urls_ann,
        }
        all_items.append(rec)
        by_name[name] = rec
        if func_id:
            by_function_id[func_id].append(rec)

    duplicates: Dict[str, List[Dict[str, Any]]] = {
        fid: items for fid, items in by_function_id.items() if len(items) > 1
    }

    overlaps: List[Dict[str, Any]] = []
    for rec in all_items:
        key = rec["function_id"] or rec["name"]
        if key in OVERLAP_HINTS:
            hint = OVERLAP_HINTS[key]
            overlaps.append({
                "service": rec["name"],
                "type": rec["type"],
                "url": rec["url"],
                "hint": hint,
            })

    summary = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_services": len(all_items),
        "cloud_functions": sum(1 for r in all_items if r["type"] == "cloud-function"),
        "cloud_run_services": sum(1 for r in all_items if r["type"] == "cloud-run-service"),
        "duplicate_function_ids": list(duplicates.keys()),
        "overlaps_count": len(overlaps),
    }

    return {
        "summary": summary,
        "duplicates_by_function_id": duplicates,
        "overlaps": overlaps,
        "services": all_items,
    }


def write_reports(result: dict):
    json_path = REPORTS_DIR / "cloud_run_duplicates_report.json"
    md_path = REPORTS_DIR / "cloud_run_duplicates_report.md"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    s = result["summary"]
    lines = [
        "# Cloud Run Duplicates & Overlaps Report",
        "",
        f"Generated: {s['generated_at']}",
        f"Total services: {s['total_services']} (Cloud Functions: {s['cloud_functions']}, Cloud Run: {s['cloud_run_services']})",
        "",
    ]

    if result["duplicates_by_function_id"]:
        lines.append("## Duplicate Cloud Functions by function-id")
        for fid, items in result["duplicates_by_function_id"].items():
            lines.append(f"- {fid}:")
            for it in items:
                lines.append(f"  - {it['name']} -> {it.get('url')}")
        lines.append("")
    else:
        lines.append("No duplicate Cloud Function IDs detected.")
        lines.append("")

    if result["overlaps"]:
        lines.append("## Potential Overlaps with Engine Endpoints")
        for ov in result["overlaps"]:
            hint = ov["hint"]
            lines.append(
                f"- {ov['service']} ({ov['type']}) -> {ov['url']} | overlaps {hint['engine']} {hint['endpoint']} | {hint['note']}"
            )
        lines.append("")
    else:
        lines.append("No overlaps detected with known engine endpoints.")
        lines.append("")

    lines.append("## Recommendations")
    lines.append("- Prefer direct Engine endpoints from Frontend when equivalent exists.")
    lines.append("- Plan deprecation of overlapping Cloud Functions once Frontend is migrated.")
    lines.append("- Keep a runbook: which clients call which endpoints; remove unused after 14-30 days of no traffic.")

    with md_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return str(json_path), str(md_path)


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    if not path.exists():
        print(f"Input file not found: {path}")
        sys.exit(1)
    services = load_services(path)
    result = analyze(services)
    jp, mp = write_reports(result)
    print(f"Wrote: {jp}\nWrote: {mp}")


if __name__ == "__main__":
    main()
