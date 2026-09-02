"""
Pre-Commit Secret Scanner for InfinityAI.Pro
Fails build/commit if any literal credential, API key, or private token is detected.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Prohibited secret patterns
SECRET_PATTERNS = [
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "Google / Gemini API Key"),
    (re.compile(r"-----BEGIN\s+(?:RSA|EC|OPENSSH|PRIVATE)\s+KEY-----"), "Private Key Block"),
    (re.compile(r"""(?:DHAN_API_SECRET|DHAN_ACCESS_TOKEN)\s*=\s*["'][a-zA-Z0-9_\-]{20,}["']"""), "Hardcoded DhanHQ Credential"),
    (re.compile(r"""USER_CREDENTIALS_KEY\s*=\s*["'][0-9a-fA-F]{64}["']"""), "Hardcoded 64-char AES Key Literal"),
    (re.compile(r"""AKIA[0-9A-Z]{16}"""), "AWS Access Key ID"),
    (re.compile(r"""ghp_[0-9a-zA-Z]{36}"""), "GitHub Personal Access Token"),
]

# Paths to ignore
IGNORE_PATHS = [
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".next",
    "out",
    "dist",
    "build",
    "data",
    "ml_data_local",
    "catboost_info",
    "semgrep_rules.yaml",
    "check_secrets.py",  # Ignore scanner regex definitions itself
    "test_secrets_vault.py",  # Ignore test case asserting detection
]


def scan_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """Scan a single file for secret patterns. Returns list of (line_no, pattern_name, line_text)."""
    findings = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                # Skip comments explaining rules or placeholder tokens
                if "placeholder" in line.lower() or "your-" in line.lower():
                    continue
                for pattern, name in SECRET_PATTERNS:
                    if pattern.search(line):
                        findings.append((line_no, name, line.strip()))
    except Exception:
        pass
    return findings


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def scan_codebase(root_dir: Path) -> int:
    """Scan codebase and return number of secret violations."""
    total_violations = 0
    print(f"[INFO] Scanning codebase at {root_dir} for secret leaks...")

    for root, dirs, files in os.walk(root_dir):
        # Prune ignored directories in-place so os.walk does not recurse into them
        dirs[:] = [d for d in dirs if d not in IGNORE_PATHS and not d.startswith(".")]

        for file_name in files:
            if file_name in IGNORE_PATHS:
                continue
            path = Path(root) / file_name
            if path.suffix not in [".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml", ".env", ".sh"]:
                continue

            findings = scan_file(path)
            if findings:
                for line_no, pattern_name, snippet in findings:
                    print(f"[SECRET DETECTED] {path}:{line_no} - {pattern_name}")
                    print(f"   Snippet: {snippet[:60]}...")
                    total_violations += 1

    if total_violations > 0:
        print(f"\n[BUILD FAILED] Found {total_violations} hardcoded secret violation(s)!")
        return 1

    print("[SUCCESS] Pre-commit secrets scan passed: Zero hardcoded secrets detected.")
    return 0


if __name__ == "__main__":
    exit_code = scan_codebase(PROJECT_ROOT)
    sys.exit(exit_code)
