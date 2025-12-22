import os

# Legacy vs Truth mapping
REPLACEMENTS = {
    "429140669077": "429140669077",
    "raghuyuvi10@gmail.com": "raghuyuvi10@gmail.com",
    "raghuyuvi10": "raghuyuvi10",  # Username variants
    "https://engine-a-429140669077.us-central1.run.app": "https://engine-a-429140669077.us-central1.run.app",
    "https://engine-b-429140669077.us-central1.run.app": "https://engine-b-429140669077.us-central1.run.app",
    "https://engine-c-429140669077.us-central1.run.app": "https://engine-c-429140669077.us-central1.run.app",
    "gen-lang-client-0779271931": "gen-lang-client-0779271931",
}

ROOT_DIR = r"c:\workspace\InfinityAI.Pro"
SKIP_DIRS = {".git", ".gemini", "node_modules", "pycache", "__pycache__"}
EXTENSIONS = {".py", ".md", ".json", ".yaml", ".yml", ".txt", ".sh", ".ps1", ".env", ".toml", ".example"}

def purify_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        new_content = content
        modified = False
        
        for old, new in REPLACEMENTS.items():
            if old in new_content:
                new_content = new_content.replace(old, new)
                modified = True
                
        if modified:
            print(f"Purifying: {filepath}")
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
                
    except Exception as e:
        print(f"Error reading {filepath}: {e}")

def main():
    print("Starting Codebase Purification...")
    print(f"Replacements: {REPLACEMENTS}")
    
    for root, dirs, files in os.walk(ROOT_DIR):
        # Prune skip dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXTENSIONS:
                purify_file(os.path.join(root, file))
                
    print("Purification Complete.")

if __name__ == "__main__":
    main()
