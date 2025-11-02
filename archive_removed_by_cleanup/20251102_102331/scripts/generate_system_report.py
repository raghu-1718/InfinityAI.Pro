#!/usr/bin/env python3
"""
InfinityAI.Pro - Complete System Analysis Report Generator (Python)
Usage:
  python scripts/generate_system_report.py [--project <GCP_PROJECT_ID>] [--region <REGION>]

Notes:
  - Requires: gcloud CLI and (optionally) firebase CLI.
  - Cross-platform; good fallback when jq/awk are unavailable.
  - Writes markdown under ./system-reports/
"""
import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], check=False) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return out
    except subprocess.CalledProcessError as e:
        if check:
            raise
        return e.output or ""


def detect_project(provided: str | None) -> str:
    if provided:
        return provided
    out = run(["gcloud", "config", "get-value", "core/project"]) or ""
    out = out.strip()
    if not out:
        print("ERROR: GCP project not provided and not set in gcloud config.", file=sys.stderr)
        print("Use --project <ID> or 'gcloud config set project <ID>'", file=sys.stderr)
        sys.exit(1)
    return out


def write(lines: list[str], fp: Path):
    fp.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append(lines: list[str], fp: Path):
    with fp.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def section_divider(fp: Path):
    append(["", "---", ""], fp)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", dest="project", default=None)
    parser.add_argument("--region", dest="region", default="us-central1")
    args = parser.parse_args()

    project = detect_project(args.project)
    region = args.region

    reports_dir = Path("system-reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    report_file = reports_dir / f"{project}-full-report-{ts}.md"

    # Header
    write([
        "# InfinityAI.Pro - Complete System Analysis Report",
        "",
        f"**Generated:** {dt.datetime.now().isoformat(timespec='seconds')}",
        f"**Project ID:** {project}",
        f"**Region:** {region}",
        "",
        "## 📊 EXECUTIVE SUMMARY",
        "",
    ], report_file)

    # 1. Project overview
    append(["## 1️⃣ PROJECT OVERVIEW & CONFIGURATION", "", "### Project Information"], report_file)
    append([run(["gcloud", "config", "list"])], report_file)
    append(["", "### Active APIs & Services", run(["gcloud", "services", "list", "--enabled", f"--project={project}"])], report_file)

    # 2. Cloud Run services
    append(["## 2️⃣ CLOUD RUN SERVICES - COMPLETE ANALYSIS", "", "### All Deployed Services"], report_file)
    append([run(["gcloud", "run", "services", "list", "--platform", "managed", "--region", region, "--project", project])], report_file)

    services_raw = run(["gcloud", "run", "services", "list", "--platform", "managed", "--region", region, "--project", project, "--format=value(metadata.name)"]) or ""
    services = [s for s in (ln.strip() for ln in services_raw.splitlines()) if s]

    for svc in services:
        append([f"### 📦 Service: {svc}", "", "#### Service Details", run(["gcloud", "run", "services", "describe", svc, "--platform", "managed", "--region", region, "--project", project, "--format=yaml"])], report_file)
        append(["", "#### Resource Configuration", run(["gcloud", "run", "services", "describe", svc, "--platform", "managed", "--region", region, "--project", project, "--format=\"value(spec.template.spec.containers[0].resources)\""])], report_file)
        append(["", "#### Environment Variables", run(["gcloud", "run", "services", "describe", svc, "--platform", "managed", "--region", region, "--project", project, "--format=\"value(spec.template.spec.containers[0].env)\""])], report_file)
        append(["", "#### Service URL", run(["gcloud", "run", "services", "describe", svc, "--platform", "managed", "--region", region, "--project", project, "--format=\"value(status.url)\""])], report_file)
        section_divider(report_file)

    # 3. Firebase Functions
    append(["## 3️⃣ FIREBASE FUNCTIONS - COMPLETE ANALYSIS", "", "### All Deployed Functions"], report_file)
    fb_list = run(["firebase", "functions:list", "--project", project])
    if fb_list:
        append([fb_list, ""], report_file)
        fb_json = run(["firebase", "functions:list", "--project", project, "--json"]) or "[]"
        func_ids = []
        try:
            import json
            data = json.loads(fb_json)
            if isinstance(data, list):
                func_ids = [str(it.get("id", "")).strip() for it in data if isinstance(it, dict)]
        except Exception:
            pass
        for fn in func_ids:
            if not fn:
                continue
            append([f"### 🔧 Function: {fn}", "", "#### Function Configuration (gcloud describe v1/v2 best-effort)", run(["gcloud", "functions", "describe", fn, f"--region={region}", f"--project={project}", "--format=yaml"])], report_file)
            append(["", "#### Runtime & Resources", run(["gcloud", "functions", "describe", fn, f"--region={region}", f"--project={project}", "--format=value(runtime,availableMemoryMb,timeout,maxInstances)"])], report_file)
            append(["", "#### HTTPS Trigger (if any)", run(["gcloud", "functions", "describe", fn, f"--region={region}", f"--project={project}", "--format=value(httpsTrigger.url)"])], report_file)
            section_divider(report_file)
    else:
        append(["⚠️ firebase CLI not found or not logged in. Skipping detailed Firebase sections.", ""], report_file)

    # 4. Firebase & Firestore
    append(["## 4️⃣ FIREBASE CONFIGURATION & INTEGRATIONS", "", "### Firebase Project Info", run(["firebase", "projects:list"])], report_file)
    append(["", "### Firestore Database", run(["gcloud", "firestore", "databases", "list", f"--project={project}"])], report_file)

    # 5. AI/ML
    append(["## 5️⃣ AI/ML INTEGRATIONS & SERVICES", "", f"### Vertex AI Models (region {region})", run(["gcloud", "ai", "models", "list", "--region", region, "--project", project])], report_file)

    # 6. Secrets
    append(["## 6️⃣ SECRET MANAGER & SECURITY", "", "### All Secrets", run(["gcloud", "secrets", "list", f"--project={project}"])], report_file)
    secrets_raw = run(["gcloud", "secrets", "list", f"--project={project}", "--format=value(name)"]) or ""
    secrets = [s for s in (ln.strip() for ln in secrets_raw.splitlines()) if s]
    if secrets:
        append(["", "### Secret Access Permissions"], report_file)
        for sec in secrets:
            append([f"#### Secret: {sec}", run(["gcloud", "secrets", "get-iam-policy", sec, f"--project={project}"]) , ""], report_file)

    # 7. IAM
    append(["## 7️⃣ IAM ROLES & PERMISSIONS", "", "### Service Accounts", run(["gcloud", "iam", "service-accounts", "list", f"--project={project}"])], report_file)
    append(["", "### IAM Policy Bindings", run(["gcloud", "projects", "get-iam-policy", project])], report_file)

    # 8. Networking
    append(["## 8️⃣ NETWORKING & CONNECTIVITY", "", "### VPC Networks", run(["gcloud", "compute", "networks", "list", f"--project={project}"])], report_file)
    append(["", "### Firewall Rules", run(["gcloud", "compute", "firewall-rules", "list", f"--project={project}"])], report_file)

    # 9. Monitoring placeholder
    append(["## 9️⃣ MONITORING & LOGGING", "", "(Tip: Use Cloud Logging filters for deep dives.)", ""], report_file)

    # 10. Quotas
    append(["## 🔟 QUOTAS & RESOURCE LIMITS", "", "### Current Quota Usage", run(["gcloud", "compute", "project-info", "describe", f"--project={project}"])], report_file)

    # Footer
    append(["---", "", "## 🎯 REPORT GENERATION COMPLETE", f"Generated: {dt.datetime.now().isoformat(timespec='seconds')}", f"Report Location: {report_file}"], report_file)

    print("✅ Report generation complete!")
    print(f"📄 Report saved to: {report_file}")


if __name__ == "__main__":
    main()
