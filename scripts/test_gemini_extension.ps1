<#
.SYNOPSIS
  End-to-end test for the Firestore Multimodal Gemini extension.

.DESCRIPTION
  Creates a test document in the configured collection (default: 'generate') and polls
  for the extension to populate the response field (default: 'output'). Saves artifacts
  (document path and logs) for later inspection.

.PARAMETER ProjectId
  GCP Project ID. Defaults to infinity-ai-5ec7c.

.PARAMETER Collection
  Firestore collection name the extension listens to. Defaults to 'generate'.

.PARAMETER ResponseField
  The field the extension writes the result to. Defaults to 'output'.

.PARAMETER Payload
  Optional hashtable of fields to include in the created Firestore document.
  Example: @{ engine_data = 'sample' }

.PARAMETER TimeoutSeconds
  How long to poll for a result before timing out. Defaults to 150 seconds.

.OUTPUTS
  Writes status to the console, and saves artifacts:
   - .\.last_extension_doc.txt: fully-qualified Firestore doc path
   - .\.last_extension_result.json: the full Firestore document JSON (when found)
   - .\.last_extension_generateText_logs.json: recent extension trigger logs (on timeout)

#>
[CmdletBinding()]
param(
  [string]$ProjectId = 'infinity-ai-5ec7c',
  [string]$Collection = 'generate',
  [string]$ResponseField = 'output',
  [hashtable]$Payload,
  [int]$TimeoutSeconds = 150
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-AccessToken {
  $t = (gcloud auth print-access-token).Trim()
  if ([string]::IsNullOrWhiteSpace($t)) { throw 'Failed to obtain gcloud access token' }
  return $t
}

function Convert-ToFirestoreJson([hashtable]$fields) {
  # Convert simple scalar fields to Firestore REST JSON shape
  $fs = @{}
  foreach ($k in $fields.Keys) {
    $v = $fields[$k]
    if ($v -is [string]) { $fs[$k] = @{ stringValue = $v } }
    elseif ($v -is [int] -or $v -is [long]) { $fs[$k] = @{ integerValue = [string]$v } }
    elseif ($v -is [double] -or $v -is [float] -or $v -is [decimal]) { $fs[$k] = @{ doubleValue = [double]$v } }
    elseif ($v -is [bool]) { $fs[$k] = @{ booleanValue = $v } }
    else {
      # Fallback to string
      $fs[$k] = @{ stringValue = ($v | ConvertTo-Json -Compress -Depth 10) }
    }
  }
  return @{ fields = $fs } | ConvertTo-Json -Depth 10 -Compress
}

function New-TestDocument {
  param(
    [string]$ProjectId,
    [string]$Collection,
    [hashtable]$Payload
  )
  $token = Get-AccessToken
  $headers = @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' }
  if (-not $Payload) { $Payload = @{ engine_data = 'No live engine feed; default test prompt.' } }
  $body = Convert-ToFirestoreJson -fields $Payload
  $url = "https://firestore.googleapis.com/v1/projects/$ProjectId/databases/(default)/documents/$Collection"
  $resp = Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $body
  if (-not $resp.name) { throw 'Firestore POST returned no document name' }
  return $resp.name
}

function Get-Document {
  param([string]$DocPath)
  $token = Get-AccessToken
  $headers = @{ Authorization = "Bearer $token" }
  $url = 'https://firestore.googleapis.com/v1/' + $DocPath
  return Invoke-RestMethod -Uri $url -Headers $headers -Method Get
}

function Save-LogsOnTimeout {
  param([string]$ProjectId)
  Write-Warning 'Result not populated within timeout. Fetching recent extension logs...'
  gcloud logging read "resource.type=cloud_function AND resource.labels.function_name=ext-firestore-multimodal-genai-generateText" --limit=50 --project=$ProjectId --format=json | Out-File -Encoding utf8 .\.last_extension_generateText_logs.json
  Write-Host 'Saved: .\.last_extension_generateText_logs.json'
}

Write-Host "Project: $ProjectId"
Write-Host "Collection: $Collection"
Write-Host "ResponseField: $ResponseField"

$docPath = New-TestDocument -ProjectId $ProjectId -Collection $Collection -Payload $Payload
Set-Content -Path .\.last_extension_doc.txt -Value $docPath
Write-Host ("Created doc: " + $docPath)

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$found = $false
do {
  Start-Sleep -Seconds 5
  try {
    $doc = Get-Document -DocPath $docPath
    $hasField = $null -ne $doc.fields[$ResponseField]
    $status = if ($hasField) { 'FOUND' } else { 'missing' }
    Write-Host ("Poll: $status; updateTime=" + $doc.updateTime)
    if ($hasField) {
      $found = $true
      $doc | ConvertTo-Json -Depth 20 | Out-File -Encoding utf8 .\.last_extension_result.json
      Write-Host 'Saved: .\.last_extension_result.json'
      break
    }
  } catch {
    Write-Warning ("Polling error: " + $_.Exception.Message)
  }
} while ((Get-Date) -lt $deadline)

if (-not $found) {
  Save-LogsOnTimeout -ProjectId $ProjectId
  exit 2
}

Write-Host 'Extension test completed successfully.' -ForegroundColor Green
exit 0
