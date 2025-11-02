param(
    [string[]]$KeepList = @('.git','.github','InfinityGT-Project','CONSOLIDATED_PROJECT.md','archive_removed_by_cleanup','scripts','.gitattributes','.gitignore','README.md')
)

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$archiveRoot = Join-Path -Path (Get-Location) -ChildPath "archive_removed_by_cleanup\$timestamp"
New-Item -ItemType Directory -Path $archiveRoot -Force | Out-Null

# Build keep set
$keepSet = @{}
foreach ($k in $KeepList) { $keepSet[$k.ToLower()] = $true }

$items = Get-ChildItem -Force | Where-Object { $true } | ForEach-Object { $_ }

$manifest = @()

foreach ($it in $items) {
    $name = $it.Name
    if ($keepSet.ContainsKey($name.ToLower())) {
        continue
    }
    if ($name -eq '.' -or $name -eq '..') { continue }
    # Do not move the archive we are creating
    if ($name -eq 'archive_removed_by_cleanup') { continue }

    $source = $it.FullName
    $destination = Join-Path -Path $archiveRoot -ChildPath $name
    try {
        Move-Item -LiteralPath $source -Destination $destination -Force
        $manifest += $name
        Write-Output "Moved: $name"
    } catch {
        Write-Warning ("Failed to move {0}: {1}" -f $name, $_.Exception.Message)
    }
}

# Write manifest
$manifestPath = Join-Path -Path $archiveRoot -ChildPath "manifest.txt"
$manifest | Out-File -FilePath $manifestPath -Encoding utf8

Write-Output "Consolidation complete. Archive: $archiveRoot"
Write-Output "Manifest written to: $manifestPath"
