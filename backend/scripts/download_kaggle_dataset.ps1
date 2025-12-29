# PowerShell helper: download and prepare a Kaggle recipe/image dataset
# Usage:
# 1) Install kaggle CLI and place your kaggle.json in %USERPROFILE%\.kaggle\kaggle.json
# 2) Run: .\download_kaggle_dataset.ps1 -Dataset "<owner/dataset>" -OutDir "..\data"
# 3) Adjust mapping steps below according to the dataset structure.

param(
    [Parameter(Mandatory=$true)]
    [string]$Dataset,

    [string]$OutDir = "..\data",

    [switch]$Unzip
)

Set-StrictMode -Version Latest

# Ensure backend\data directory exists
$fullOut = Join-Path -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) $OutDir
if (-not (Test-Path $fullOut)) { New-Item -ItemType Directory -Path $fullOut | Out-Null }

Write-Host "Downloading Kaggle dataset: $Dataset -> $fullOut"

# Download using kaggle CLI (requires kaggle.json to be configured)
# Use the call operator with argument array to avoid PowerShell parsing issues
# Try native 'kaggle' command first, fall back to 'python -m kaggle' if not on PATH
# Prevent accidental use of placeholder syntax like <owner/dataset>
if ($Dataset -match '[<>]') {
    Write-Error "Dataset id appears to contain angle brackets. Use the form 'owner/dataset' (no < >)."
    exit 1
}

$kaggleArgs = @('datasets','download','-d',$Dataset,'-p',$fullOut)

if (Get-Command kaggle -ErrorAction SilentlyContinue) {
    Write-Host "Running: kaggle $($kaggleArgs -join ' ')"
    try {
        & kaggle @kaggleArgs
    } catch {
        Write-Error "Failed to run kaggle CLI: $_"
        exit 1
    }
} else {
    # Try python -m kaggle as a fallback
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Host "'kaggle' not found; trying 'python -m kaggle'"
        $pyArgs = @('-m','kaggle') + $kaggleArgs
        Write-Host "Running: python $($pyArgs -join ' ')"
        try {
            & python @pyArgs
        } catch {
            Write-Error "Failed to run 'python -m kaggle': $_"
            Write-Error "Please ensure the kaggle package is installed and your Python Scripts folder is on PATH, or run: pip install kaggle"
            exit 1
        }
    } else {
        Write-Error "Neither 'kaggle' nor 'python' commands are available. Install Python and the kaggle package."
        exit 1
    }
}

if ($Unzip) {
    Get-ChildItem -Path $fullOut -Filter *.zip -Recurse | ForEach-Object {
        Write-Host "Unzipping $($_.FullName)"
        Expand-Archive -Path $_.FullName -DestinationPath $fullOut -Force
    }
}

# Prepare static images folder (Flask serves backend/static)
# Prepare static images folder (Flask serves from backend/static)
$staticImages = Join-Path -Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\static\images"
if (-not (Test-Path $staticImages)) {
    New-Item -ItemType Directory -Path $staticImages -Force | Out-Null
}
Write-Host "Static images folder: $staticImages"

Write-Host "Copied dataset files to: $fullOut"
Write-Host "You will likely need to map image filenames or URLs to recipes in your CSV."

Write-Host "Example next steps (manual):"
Write-Host " - Inspect CSVs in $fullOut for an image column or filename references."
Write-Host " - If the dataset includes image files, copy them into backend/static/images and set image_url to '/static/images/<filename>' in your CSV mapping."
Write-Host " - If the dataset provides external URLs, ensure they are accessible and that DataPreprocessor reads the 'image' column."

Write-Host "Example copy command (uncomment and adjust if dataset has an 'images' folder):"
Write-Host "# Copy-Item -Path (Join-Path $fullOut 'images\*') -Destination $staticImages -Recurse -Force"

Write-Host "Done. Edit the mapping/import logic as needed and run the DataPreprocessor to import recipes with image URLs."
