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
    # Start follow-touch in background
    echo "Starting follow-touch application..."
    conda run -n follow-touch-env python follow-touch/app.py
elif [ "$1" == "neural" ]; then
    # Start neural-model in foreground
    echo "Starting neural-model application..."
    conda run -n neural-model-env streamlit run neural-model/app.py
else
    echo "❌ Error: Invalid argument. Use 'touch' or 'neural'."
    exit 1
fi
