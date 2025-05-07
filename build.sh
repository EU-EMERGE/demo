#!/bin/bash

# Exit on error
set -e

# Check and handle input argument
if [ "$1" == "touch" ]; then
    ENV_NAME="follow-touch-env"
    PYTHON_VERSION="3.8"
    REQUIREMENTS_PATH="follow-touch/requirements.txt"
elif [ "$1" == "neural" ]; then
    ENV_NAME="neural-model-env"
    PYTHON_VERSION="3.11"
    REQUIREMENTS_PATH="neural-model/requirements.txt"
else
    echo "❌ Error: Invalid argument. Use 'touch' or 'neural'."
    exit 1
fi

# Ensure conda is initialized in this shell
CONDA_BASE=$(conda info --base)
source "$CONDA_BASE/etc/profile.d/conda.sh"

# Create the environment if it doesn't exist
if ! conda info --envs | grep -q "^$ENV_NAME[[:space:]]"; then
    echo "Creating Conda environment: $ENV_NAME with Python $PYTHON_VERSION..."
    conda create -y -n "$ENV_NAME" python="$PYTHON_VERSION"
else
    echo "Conda environment '$ENV_NAME' already exists. Skipping creation."
fi

# Activate the environment
echo "Activating Conda environment: $ENV_NAME..."
conda activate "$ENV_NAME"

# Install dependencies
echo "Installing Python dependencies from $REQUIREMENTS_PATH..."
pip install -r "$REQUIREMENTS_PATH"

echo "✅ Environment setup complete."