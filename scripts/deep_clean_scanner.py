import os
import re

ROOT_DIR = r"c:\workspace\InfinityAI.Pro"

# Patterns indicating STALE or INCORRECT values
FORBIDDEN_PATTERNS = {
    # Legacy Project Info
    r"573866363_?639": "Legacy Project Number (573...)",
    r"raghu42620": "Legacy Username (raghu42620)",
    
    # Generic Placeholders (Flag for review, might be valid in docs)
    r"your-project-id": "Placeholder 'your-project-id'",
    r"INSERT_API_KEY": "Placeholder 'INSERT_API_KEY'",
    
    # Specific Hardcoded Demos/Mocks in PROD code (heuristic)
    # r"mock_": "Mock Data (Check context)", 
}

# Whitelist (Files to ignore)
IGNORE_DIRS = {
    ".git", ".gemini", "node_modules", "pycache", "__pycache__", ".next", ".firebase", "venv", "env"
}
IGNORE_FILES = {
    "package-lock.json", "yarn.lock", "purify_codebase.py", "deep_clean_scanner.py", 
    "PURIFICATION_REPORT.md", "CLOUD_CENSUS_REPORT.md", "task.md"
}

def scan_workspace():
    print(f"Scanning {ROOT_DIR} for forbidden patterns...")
    dirty_files = {}

    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
                
            filepath = os.path.join(root, file)
            
            # Skip large binary files or typically binary extensions
            if file.endswith(('.png', '.jpg', '.pyc', '.exe', '.dll', '.so', '.webp')):
                continue

            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern_regex, label in FORBIDDEN_PATTERNS.items():
                    if re.search(pattern_regex, content, re.IGNORECASE):
                        if filepath not in dirty_files:
                            dirty_files[filepath] = []
                        dirty_files[filepath].append(label)

            except Exception as e:
                # print(f"Skipping {filepath}: {e}")
                pass

    # Report
    if dirty_files:
        print(f"\n FOUND {len(dirty_files)} FILES WITH ISSUES:")
        for fp, issues in dirty_files.items():
            print(f"[{', '.join(issues)}] {fp}")
    else:
        print("\n[CLEAN] SCAN. No forbidden patterns found.")

if __name__ == "__main__":
    scan_workspace()
