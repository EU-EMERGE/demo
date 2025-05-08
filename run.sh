#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Ensure conda is available
source "$(conda info --base)/etc/profile.d/conda.sh"

if [ "$1" == "touch" ]; then
    echo "Starting follow-touch application..."
    conda activate follow-touch-env
    python -u follow-touch/app.py 2>&1 | tee follow-touch.log
elif [ "$1" == "neural" ]; then
    echo "Starting neural-model application..."
    conda activate neural-model-env
    python -u -m streamlit run neural-model/app.py | tee neural-model.log
else
    echo "❌ Error: Invalid argument. Use 'touch' or 'neural'."
    exit 1
fi
