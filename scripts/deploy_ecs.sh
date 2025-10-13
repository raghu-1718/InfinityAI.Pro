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

echo "Rendering task definition into $TMP_TASKDEF"
jq --arg image "$IMAGE_URI" '.containerDefinitions[0].image = $image' "$TASKDEF_TEMPLATE" > "$TMP_TASKDEF"

echo "Registering task definition"
REG_OUT=$(aws ecs register-task-definition --cli-input-json file://"$TMP_TASKDEF")
TASK_FAMILY=$(echo "$REG_OUT" | jq -r '.taskDefinition.family')
REVISION=$(echo "$REG_OUT" | jq -r '.taskDefinition.revision')
TASK_DEF_ARN=$(echo "$REG_OUT" | jq -r '.taskDefinition.taskDefinitionArn')

echo "Updating service $SERVICE on cluster $CLUSTER to use task definition $TASK_FAMILY:$REVISION"
aws ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --force-new-deployment --task-definition "$TASK_DEF_ARN"

echo "ECS deploy complete"

