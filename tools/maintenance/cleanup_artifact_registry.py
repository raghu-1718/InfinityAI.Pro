import subprocess
import json
import concurrent.futures

REPO = "asia-south1-docker.pkg.dev/project-841b7f97-5ee3-4fbe-920/infinityai"

def list_untagged_images():
    print(f"Fetchting images from {REPO}...")
    cmd = [
        "gcloud", "artifacts", "docker", "images", "list",
        REPO, "--include-tags", "--format=json"
    ]
    # On Windows, shell=True is often needed for batch files like gcloud.cmd if not using full path
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print(f"Error listing images: {result.stderr}")
        return []
    
    images = json.loads(result.stdout)
    untagged = []
    for img in images:
        if not img.get("tags"):
            untagged.append(img)
    
    return untagged

def delete_image(package, version):
    full_image_path = f"{package}@{version}"
    print(f"Deleting {full_image_path}...")
    cmd = [
        "gcloud", "artifacts", "docker", "images", "delete",
        full_image_path, "--quiet", "--delete-tags"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        return True
    else:
        print(f"Failed to delete {version}: {result.stderr}")
        return False

def main():
    untagged_images = list_untagged_images()
    print(f"Found {len(untagged_images)} untagged images.")
    
    if not untagged_images:
        print("No untagged images found. Cleanup complete.")
        return

    # Delete in parallel to speed up
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for img in untagged_images:
            version = img.get('version')
            package = img.get('package')
            if version and package:
                futures.append(executor.submit(delete_image, package, version))
        
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
    print(f"Successfully deleted {results.count(True)} images.")

if __name__ == "__main__":
    main()
