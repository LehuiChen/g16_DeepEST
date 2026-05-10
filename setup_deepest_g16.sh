#!/bin/bash

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV_FILE="$SCRIPT_DIR/deepest_g16.yaml"
ENV_NAME="deepest_g16"

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif command -v conda >/dev/null 2>&1; then
    :
else
    echo "Cannot find conda. Please source your conda.sh before running this script."
    exit 1
fi

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
    conda env update -n "$ENV_NAME" -f "$ENV_FILE"
else
    conda env create -f "$ENV_FILE"
fi

conda activate "$ENV_NAME"

pip install -e "$SCRIPT_DIR/g16-deepest"

if ! command -v xtb >/dev/null 2>&1; then
    echo "xtb executable is not available in environment '$ENV_NAME'."
    exit 1
fi

if ! command -v g16-mlips-deepest >/dev/null 2>&1; then
    echo "g16-mlips-deepest command is not available after installation."
    exit 1
fi

echo "Environment '$ENV_NAME' is ready."
