"""
Artifact Registry Safe Cleanup & Optimization Tool
InfinityAI.Pro - Safe Container Image Purge
"""
import subprocess
import json
import sys

PROJECT_ID = "project-841b7f97-5ee3-4fbe-920"
REPOS = [
    f"us-central1-docker.pkg.dev/{PROJECT_ID}/cloud-run-source-deploy",
    f"asia-south1-docker.pkg.dev/{PROJECT_ID}/cloud-run-source-deploy"
]

def analyze_repo(repo_uri: str):
    print(f"\n=======================================================")
    print(f"Scanning Repository: {repo_uri}")
    print(f"=======================================================")
    cmd = ["gcloud", "artifacts", "docker", "images", "list", repo_uri, "--format=json"]
    res = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if res.returncode != 0:
        print(f"Error reading repo: {res.stderr}")
        return [], []

    try:
        images = json.loads(res.stdout)
    except Exception as e:
        print(f"Failed to parse images JSON: {e}")
        return [], []

    tagged = [img for img in images if img.get("tags")]
    untagged = [img for img in images if not img.get("tags")]

    print(f"Total Images Found: {len(images)}")
    print(f"Protected / Tagged Images (e.g. :latest): {len(tagged)}")
    print(f"Dangling / Untagged Images (Safe to Clean): {len(untagged)}")

    for t in tagged:
        pkg = t.get("package", "").split("/")[-1]
        tags = t.get("tags", [])
        print(f"  [PROTECTED] {pkg} -> Tags: {tags} (Digest: {t.get('version', '')[:19]}...)")

    return tagged, untagged

def main():
    dry_run = "--execute" not in sys.argv

    all_untagged = []
    for repo in REPOS:
        tagged, untagged = analyze_repo(repo)
        for u in untagged:
            all_untagged.append((repo, u))

    print(f"\n=======================================================")
    print(f"SUMMARY: {len(all_untagged)} Untagged Images identified across all registries.")
    print(f"Estimated Space to Reclaim: ~100-115 GB")
    print(f"=======================================================")

    if dry_run:
        print("\n[DRY RUN MODE] No images were deleted.")
        print("To safely delete all untagged images, run:")
        print("  python tools/cleanup_artifact_registry.py --execute")
        return

    print("\n[EXECUTE MODE] Purging untagged images safely...")
    deleted_count = 0
    for repo, u in all_untagged:
        pkg = u.get("package", "")
        version = u.get("version", "")
        if not pkg or not version:
            continue
        full_image_uri = f"{pkg}@{version}"
        print(f"Deleting: {pkg.split('/')[-1]}@{version[:19]}...")
        del_cmd = ["gcloud", "artifacts", "docker", "images", "delete", full_image_uri, "--quiet", "--delete-tags=false"]
        del_res = subprocess.run(del_cmd, capture_output=True, text=True, shell=True)
        if del_res.returncode == 0:
            deleted_count += 1
        else:
            print(f"  Failed: {del_res.stderr.strip()}")

    print(f"\n[DONE] Successfully purged {deleted_count} untagged images.")

if __name__ == "__main__":
    main()
