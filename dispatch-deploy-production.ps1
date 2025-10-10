param(
    [string]$tag = "20251010-221305-fixed",
    [string]$ref = "main"
)

$workflow = "deploy-production.yml"
$repo = "raghu-1718/InfinityAI.Pro"

Write-Host "Triggering workflow '$workflow' on repository '$repo' at ref '$ref' with tag '$tag'"

gh workflow run $workflow --repo $repo --ref $ref -f image_tag=$tag
