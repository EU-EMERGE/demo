# Exit on error
$ErrorActionPreference = "Stop"

# Get argument
param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("touch", "neural")]
    [string]$Target
)

# Set environment based on input
switch ($Target) {
    "touch" {
        $ENV_NAME = "follow-touch-env"
        $PYTHON_VERSION = "3.8"
        $REQUIREMENTS_PATH = "follow-touch/requirements.txt"
    }
    "neural" {
        $ENV_NAME = "neural-model-env"
        $PYTHON_VERSION = "3.11"
        $REQUIREMENTS_PATH = "neural-model/requirements.txt"
    }
}

# Initialize Conda
$condaBase = (conda info --base).Trim()
. "$condaBase/etc/profile.d/conda.ps1"

# Create environment if it doesn't exist
$envExists = conda info --envs | Select-String -Pattern "^$ENV_NAME\s"
if (-not $envExists) {
    Write-Host "Creating Conda environment: $ENV_NAME with Python $PYTHON_VERSION..."
    conda create -y -n $ENV_NAME python=$PYTHON_VERSION
} else {
    Write-Host "Conda environment '$ENV_NAME' already exists. Skipping creation."
}

# Activate environment
Write-Host "Activating Conda environment: $ENV_NAME..."
conda activate $ENV_NAME

# Install dependencies
Write-Host "Installing Python dependencies from $REQUIREMENTS_PATH..."
pip install -r $REQUIREMENTS_PATH

Write-Host "✅ Environment setup complete."