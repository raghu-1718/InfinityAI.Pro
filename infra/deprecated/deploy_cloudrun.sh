#!/usr/bin/env bash
set -euo pipefail

# deploy_cloudrun.sh <local_image> <target_image> <service_name> <region> <gcp_project> <dry_run>
# Example (dry run):
# bash scripts/deploy_cloudrun.sh my-image:latest us-central1-docker.pkg.dev/my-project/my-repo/my-service:latest my-service us-central1 my-project true

if [ "$#" -lt 6 ]; then
  echo "Usage: $0 <local_image> <target_image> <service_name> <region> <gcp_project> <dry_run>"
  exit 2
fi

LOCAL_IMAGE="$1"
TARGET_IMAGE="$2"
SERVICE="$3"
REGION="$4"
GCP_PROJECT="$5"
DRY_RUN="$6"

echo "deploy_cloudrun.sh called with:
  LOCAL_IMAGE=$LOCAL_IMAGE
  TARGET_IMAGE=$TARGET_IMAGE
  SERVICE=$SERVICE
  REGION=$REGION
  GCP_PROJECT=$GCP_PROJECT
  DRY_RUN=$DRY_RUN"

if [ "$DRY_RUN" = "true" ] || [ "$DRY_RUN" = "dry" ]; then
  echo "[DRY RUN] would tag ${LOCAL_IMAGE} -> ${TARGET_IMAGE} and push, then deploy to Cloud Run service ${SERVICE} in ${GCP_PROJECT}/${REGION}"
  exit 0
fi

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud is required to deploy to Cloud Run. Please install and authenticate gcloud." >&2
  exit 6
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker is required to tag/push images. Please install docker." >&2
  exit 7
fi

echo "Authenticating Docker for Artifact Registry (${REGION}-docker.pkg.dev)"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet || true

echo "Tagging image: ${LOCAL_IMAGE} -> ${TARGET_IMAGE}"
docker tag "${LOCAL_IMAGE}" "${TARGET_IMAGE}"

echo "Pushing image to Artifact Registry: ${TARGET_IMAGE}"
docker push "${TARGET_IMAGE}"

echo "Deploying to Cloud Run: service=${SERVICE}, region=${REGION}, project=${GCP_PROJECT}"
gcloud run deploy "${SERVICE}" --image "${TARGET_IMAGE}" --region "${REGION}" --platform managed --project "${GCP_PROJECT}" --quiet

echo "Cloud Run deploy complete"
