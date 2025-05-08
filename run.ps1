# Exit on error
$ErrorActionPreference = "Stop"

# Get argument
param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("touch", "neural")]
    [string]$Target
)

# Load environment variables from .env
if (Test-Path ".env") {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^\s*#') { return }
        $parts = $_ -split '=', 2
        if ($parts.Length -eq 2) {
            $key = $parts[0].Trim()
            $value = $parts[1].Trim()
            [System.Environment]::SetEnvironmentVariable($key, $value)
        }
    }
}

# Initialize Conda
$condaBase = (conda info --base).Trim()
. "$condaBase/etc/profile.d/conda.ps1"


switch ($Target) {
    "touch" {
        # Start follow-touch in foreground
        Write-Host "Starting follow-touch application in foreground..."
        conda activate follow-touch-env
        python -u follow-touch/app.py 2>&1 | tee follow-touch.log
    }
    "neural" {
        # Start neural-model in foreground
        Write-Host "Starting neural-model application in foreground..."
        conda activate neural-model-env
        python -u -m streamlit run neural-model/app.py | tee neural-model.log
    }
}