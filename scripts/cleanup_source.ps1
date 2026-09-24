[CmdletBinding()]
param(
    [string]$RepositoryRoot
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($RepositoryRoot)) {
    $RepositoryRoot = Split-Path -Parent $PSScriptRoot
}

$cleanRepositoryRoot = $RepositoryRoot.Trim().Trim([char]34)
if ([string]::IsNullOrWhiteSpace($cleanRepositoryRoot)) {
    Write-Host "[ERROR] Repository path is empty." -ForegroundColor Red
    exit 1
}

$repository = [System.IO.Path]::GetFullPath($cleanRepositoryRoot)
$sourceRoot = Join-Path $repository "source"
$compiledRoot = Join-Path $repository "compiled"

if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) {
    Write-Host "[ERROR] Source directory does not exist: $sourceRoot" -ForegroundColor Red
    exit 1
}

Write-Host "Scanning only: $sourceRoot"
Write-Host "Targets: History and Project Outputs for ..."
Write-Host ""

$targets = @(
    Get-ChildItem -LiteralPath $sourceRoot -Directory -Recurse -Force |
        Where-Object {
            $_.Name -ieq "History" -or
            $_.Name -ilike "Project Outputs for *"
        } |
        Sort-Object { $_.FullName.Length } -Descending
)

if ($targets.Count -eq 0) {
    Write-Host "Nothing to remove." -ForegroundColor Green
    exit 0
}

$removed = 0
$skipped = 0

foreach ($directory in $targets) {
    if (-not (Test-Path -LiteralPath $directory.FullName -PathType Container)) {
        continue
    }

    if (($directory.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        Write-Host "[SAFEGUARD] Skipped link or junction: $($directory.FullName)" -ForegroundColor Yellow
        $skipped++
        continue
    }

    $isOutputDirectory = $directory.Name -ilike "Project Outputs for *"
    if ($isOutputDirectory) {
        $libraries = @(
            Get-ChildItem -LiteralPath $directory.FullName -File -Recurse -Force |
                Where-Object { $_.Extension -ieq ".IntLib" }
        )
        $outputIsSynchronized = $true

        foreach ($library in $libraries) {
            $compiledLibrary = Join-Path $compiledRoot $library.Name
            if (-not (Test-Path -LiteralPath $compiledLibrary -PathType Leaf)) {
                Write-Host "[SAFEGUARD] Compiled copy is missing for: $($library.FullName)" -ForegroundColor Yellow
                $outputIsSynchronized = $false
                continue
            }

            $sourceHash = (Get-FileHash -LiteralPath $library.FullName -Algorithm SHA256).Hash
            $compiledHash = (Get-FileHash -LiteralPath $compiledLibrary -Algorithm SHA256).Hash
            if ($sourceHash -ne $compiledHash) {
                Write-Host "[SAFEGUARD] Compiled copy differs from: $($library.FullName)" -ForegroundColor Yellow
                $outputIsSynchronized = $false
            }
        }

        if (-not $outputIsSynchronized) {
            Write-Host "[KEEP] Unsynchronized output directory: $($directory.FullName)" -ForegroundColor Yellow
            Write-Host "       Push it first or run: python scripts/update_repository.py" -ForegroundColor Yellow
            $skipped++
            continue
        }
    }

    Write-Host "[REMOVE] $($directory.FullName)"
    Remove-Item -LiteralPath $directory.FullName -Recurse -Force
    $removed++
}

Write-Host ""
Write-Host "Removed directories: $removed" -ForegroundColor Green

if ($skipped -gt 0) {
    Write-Host "Directories kept by safeguards: $skipped" -ForegroundColor Yellow
    exit 2
}

exit 0
