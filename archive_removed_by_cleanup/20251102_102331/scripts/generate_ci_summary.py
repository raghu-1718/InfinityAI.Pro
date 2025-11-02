#!/usr/bin/env python3
import glob, os

def main():
    lines = [
        "# CI Pipeline Summary",
        "",
        "## Artifacts",
    ]
    for p in sorted(glob.glob('infinityai_verification_report_*.json')):
        lines.append(f"- Verifier Report: {p}")
    for p in ["gemini_primary_versions.json", "gemini_secondary_versions.json"]:
        if os.path.exists(p):
            lines.append(f"- {p}")
    with open('CI_PIPELINE_SUMMARY.md', 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    print("\n".join(lines))

if __name__ == '__main__':
    main()
