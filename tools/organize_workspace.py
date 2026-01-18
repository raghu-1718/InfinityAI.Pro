import os
import shutil
import glob

def safe_makedirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

# 1. Define Structure
base_dir = r"c:\workspace\InfinityAI.Pro"
destinations = {
    "docs/reports": [
        "*_REPORT.md", "*_GUIDE.md", "*_SUMMARY.md", "*_COMPLETE.md", 
        "BACKTEST_*.md", "DEPLOYMENT_*.md", "VERIFICATION_*.md", "LIVE_*.md"
    ],
    "docs/archive": ["*.txt", "analysis_*.txt"],
    "tools/verification": ["tools/check_*.py", "tools/verify_*.py", "tools/test_*.py"],
    "tools/data": ["tools/ingest_*.py", "tools/fetch_*.py"],
    "tools/maintenance": ["tools/clean_*.py", "tools/optimize_*.py", "tools/setup_*.py"],
    "tools/scripts": ["*.py", "*.ps1", "*.sh"] # Root scripts moves to tools/scripts, EXCEPT critical ones
}

# Critical files to KEEP in Root
EXCLUDE_ROOT = [
    "deploy-stack.ps1", "deploy-fresh.ps1", "requirements.txt", 
    "setup.py", "main.py", "monitor-engine-c-24h.sh"
]

def organize():
    print("Starting Workspace Organization...")
    
    # Create Dirs
    for folder in destinations.keys():
        safe_makedirs(os.path.join(base_dir, folder))

    # Move Files
    for dest, patterns in destinations.items():
        dest_path = os.path.join(base_dir, dest)
        for pattern in patterns:
            # Handle root vs subdir patterns
            if "/" in pattern:
                # Subdir like tools/check_*.py
                search_path = os.path.join(base_dir, pattern.replace("/", os.sep))
            else:
                # Root like *.py
                search_path = os.path.join(base_dir, pattern)
                
            files = glob.glob(search_path)
            for f in files:
                filename = os.path.basename(f)
                
                # Check Exclusions for Root files
                if dest == "tools/scripts" and filename in EXCLUDE_ROOT:
                    continue
                if "comprehensive_verification_suite.py" in filename: # Keep this one handy or move? Move is fine.
                    pass
                
                # specific rule: don't move tools/organize_workspace.py if it's running
                if "organize_workspace.py" in filename:
                    continue

                try:
                    shutil.move(f, os.path.join(dest_path, filename))
                    print(f"Moved {filename} -> {dest}")
                except Exception as e:
                    print(f"Failed to move {filename}: {e}")

if __name__ == "__main__":
    organize()
