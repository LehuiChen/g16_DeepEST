#!/bin/bash

set -euo pipefail

echo "========================================================"
echo "Generate Gaussian inputs for TS_work DeePEST workflow"
echo "Source layout: xyzdata/<reaction>/<category>/*.xyz"
echo "Output layout: DEEPEST_Inputs_All/<reaction>/<category>/<molecule>/"
echo "========================================================"

BASE_DIR="/share/home/Chenlehui/work/TS_work"
INPUT_ROOT="$BASE_DIR/xyzdata"
OUTPUT_ROOT="$BASE_DIR/DEEPEST_Inputs_All"

TARGET_REACTIONS=("4_2" "Butterfly_Mechanism" "Click_Reaction" "DA" "Nucleophilic_Addition")
NPROC=4
MEMORY="8GB"

variant_flag=""
if [ "${DEEPEST_VARIANT:-main}" = "t1x" ]; then
    variant_flag=' --variant t1x'
fi
ext_cmd="external=\"g16-mlips-deepest${variant_flag}\""

cd "$BASE_DIR" || exit 1
mkdir -p "$OUTPUT_ROOT"

for reaction in "${TARGET_REACTIONS[@]}"; do
    reaction_path="$INPUT_ROOT/$reaction"
    if [ ! -d "$reaction_path" ]; then
        echo "Skip missing reaction directory: $reaction_path"
        continue
    fi

    while IFS= read -r -d '' xyz_file; do
        rel_path="${xyz_file#"$INPUT_ROOT"/}"
        rel_dir=$(dirname "$rel_path")
        category=$(basename "$rel_dir")
        base_name=$(basename "$xyz_file" .xyz)
        molecule_dir="$OUTPUT_ROOT/$rel_dir/$base_name"

        if [ "${category^^}" = "TS" ]; then
            task_label="TS"
            opt_keywords="Opt=(TS,ReadFC,NoMicro,NoEigen,MaxStep=20,MaxCycles=1000)"
        else
            task_label="Reactant"
            opt_keywords="Opt=(ReadFC,NoMicro,Loose,MaxStep=20,MaxCycles=1000)"
        fi

        mkdir -p "$molecule_dir"

        file_prefix="$molecule_dir/${base_name}_deepest"
        chk_name="${base_name}_deepest.chk"

        coords_tmp=$(mktemp)
        tail -n +3 "$xyz_file" > "$coords_tmp"

        cat <<EOT > "${file_prefix}_1_freq.com"
%chk=$chk_name
%nprocshared=$NPROC
%mem=$MEMORY
#p Freq $ext_cmd

Step 1: Hessian for $base_name (deepest)

0 1
$(cat "$coords_tmp")

EOT

        cat <<EOT > "${file_prefix}_2_opt.com"
%chk=$chk_name
%nprocshared=$NPROC
%mem=$MEMORY
#p $opt_keywords Geom=AllCheck $ext_cmd

EOT

        cat <<EOT > "${file_prefix}_3_freq.com"
%chk=$chk_name
%nprocshared=$NPROC
%mem=$MEMORY
#p Freq Geom=AllCheck $ext_cmd

EOT

        rm -f "$coords_tmp"
        echo "[deepest][$task_label] $rel_path -> ${molecule_dir#"$BASE_DIR"/}"
    done < <(find "$reaction_path" -mindepth 2 -maxdepth 2 -type f -name "*.xyz" -print0 | sort -z)
done

echo "========================================================"
echo "Input generation completed"
echo "Gaussian settings: 4 cores + 8GB"
echo "========================================================"
