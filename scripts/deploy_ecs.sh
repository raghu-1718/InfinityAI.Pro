#!/usr/bin/env bash
set -euo pipefail
IMAGE="$1"
CLUSTER="$2"
SERVICE="$3"
#!/usr/bin/env bash
set -euo pipefail

# deploy_ecs.sh <image_uri> <cluster> <service> <task_def_template_json> <dry_run>
# Example (dry run):
# bash scripts/deploy_ecs.sh 123456789012.dkr.ecr.us-east-1.amazonaws.com/my-app:latest my-cluster my-service taskdef.template.json true

if [ "$#" -lt 5 ]; then
  echo "Usage: $0 <image_uri> <cluster> <service> <task_def_template_json> <dry_run>"
  exit 2
fi

IMAGE_URI="$1"
CLUSTER="$2"
SERVICE="$3"
TASKDEF_TEMPLATE="$4"
DRY_RUN="$5"

echo "deploy_ecs.sh called with:
  IMAGE_URI=$IMAGE_URI
  CLUSTER=$CLUSTER
  SERVICE=$SERVICE
  TASKDEF_TEMPLATE=$TASKDEF_TEMPLATE
  DRY_RUN=$DRY_RUN"

if [ "$DRY_RUN" = "true" ] || [ "$DRY_RUN" = "dry" ]; then
  echo "[DRY RUN] would render task definition from ${TASKDEF_TEMPLATE}, replace image with ${IMAGE_URI}, register task and update service ${SERVICE} in cluster ${CLUSTER}"
  exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to render task definition JSON. Please install jq." >&2
  exit 3
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "aws CLI is required to register task definitions and update services. Please install/configure AWS CLI." >&2
  exit 5
fi

if [ ! -f "$TASKDEF_TEMPLATE" ]; then
  echo "Task definition template $TASKDEF_TEMPLATE not found" >&2
  exit 4
fi

TMP_TASKDEF=$(mktemp /tmp/taskdef.XXXX.json)
trap 'rm -f "$TMP_TASKDEF"' EXIT

echo "Rendering and sanitizing task definition into $TMP_TASKDEF"
# Set the image on all container definitions and remove optional keys when they're null
# (AWS CLI / boto3 expects optional params to be omitted rather than null)
jq --arg image "$IMAGE_URI" '
  # set image for every container definition
  .containerDefinitions |= map(.image = $image) |
  # remove top-level optional keys when null
  (if .tags == null then del(.tags) else . end) |
  (if .pidMode == null then del(.pidMode) else . end) |
  (if .ipcMode == null then del(.ipcMode) else . end) |
  (if .proxyConfiguration == null then del(.proxyConfiguration) else . end) |
  (if .inferenceAccelerators == null then del(.inferenceAccelerators) else . end) |
  (if .volumes == null then del(.volumes) else . end) |
  (if .placementConstraints == null then del(.placementConstraints) else . end) |
  (if .requiresCompatibilities == null then del(.requiresCompatibilities) else . end) |
  (if .cpu == null then del(.cpu) else . end) |
  (if .memory == null then del(.memory) else . end) |
  # within each container definition, remove optional keys that may be null
  .containerDefinitions |= map(
    (if .logConfiguration == null then del(.logConfiguration) else . end) |
    (if .healthCheck == null then del(.healthCheck) else . end) |
    (if .linuxParameters == null then del(.linuxParameters) else . end) |
    (if .resourceRequirements == null then del(.resourceRequirements) else . end) |
    (if .dependsOn == null then del(.dependsOn) else . end) |
    (if .secrets == null then del(.secrets) else . end) |
    .
  )' "$TASKDEF_TEMPLATE" > "$TMP_TASKDEF"

echo "Registering task definition"
REG_OUT=$(aws ecs register-task-definition --cli-input-json file://"$TMP_TASKDEF" || true)
if [ -z "$REG_OUT" ]; then
  echo "aws ecs register-task-definition returned empty response" >&2
  echo "--- Task definition (sanitized) ---"
  cat "$TMP_TASKDEF" >&2
  exit 6
fi
TASK_FAMILY=$(echo "$REG_OUT" | jq -r '.taskDefinition.family // empty')
REVISION=$(echo "$REG_OUT" | jq -r '.taskDefinition.revision // empty')
TASK_DEF_ARN=$(echo "$REG_OUT" | jq -r '.taskDefinition.taskDefinitionArn // empty')
if [ -z "$TASK_DEF_ARN" ]; then
  echo "Failed to register task definition, aws output: $REG_OUT" >&2
  exit 7
fi

echo "Updating service $SERVICE on cluster $CLUSTER to use task definition $TASK_FAMILY:$REVISION"
aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --force-new-deployment --task-definition "$TASK_DEF_ARN"

echo "ECS deploy complete"

