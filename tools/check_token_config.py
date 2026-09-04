import os
import re
from pathlib import Path

print("🔍 Searching codebase for Dhan token storage patterns...")

# Directories to scan
search_dirs = [Path("backend"), Path("functions"), Path("scripts")]
keywords = ["access_token", "dhanAccessToken", "credentials", "set(", "update(", "firestore"]

found_matches = []

for d in search_dirs:
    if not d.exists():
        continue
    for file_path in d.rglob("*.py"):
        try:
            content = file_path.read_text(encoding="utf-8")
            if "dhan" in content.lower() and ("token" in content.lower() or "store" in content.lower()):
                found_matches.append(str(file_path))
        except Exception:
            pass

print(f"\n📂 Files handling Dhan tokens or credentials:")
for path in set(found_matches):
    print(f"  - {path}")

print("\n💡 Recommendation: Open one of these files (likely in your token renewal worker or background service) to see the exact Firestore collection path and encryption keys used.")
