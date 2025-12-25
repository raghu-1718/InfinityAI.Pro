import json
import os

def load_json(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def main():
    base_dir = "infra_snapshot"
    
    # Load raw data
    cloudrun = load_json(os.path.join(base_dir, "cloudrun.json"))
    fb_projects = load_json(os.path.join(base_dir, "firebase_projects.json"))
    fb_hosting = load_json(os.path.join(base_dir, "firebase_hosting.json"))
    fb_functions = load_json(os.path.join(base_dir, "firebase_functions.json"))
    
    # Construct truth object
    truth = {
        "cloudrun": cloudrun,
        "firebase_projects": fb_projects,
        "firebase_hosting": fb_hosting,
        "firebase_functions": fb_functions
    }
    
    # Write to file
    with open(os.path.join(base_dir, "infra_truth.json"), 'w') as f:
        json.dump(truth, f, indent=2)

    print("✅ Normalized infra_truth.json created.")

if __name__ == "__main__":
    main()
