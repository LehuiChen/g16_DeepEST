#!/bin/bash

set -euo pipefail

echo "======================================================"
echo "Generate Gaussian inputs for TS_work MACE/ORB workflow"
echo "Source layout: xyzdata/<reaction>/<category>/*.xyz"
echo "Output layout: <model_root>/<reaction>/<category>/<molecule>/"
echo "======================================================"

BASE_DIR="/share/home/Chenlehui/work/TS_work"
INPUT_ROOT="$BASE_DIR/xyzdata"

TARGET_REACTIONS=("4_2" "Butterfly_Mechanism" "Click_Reaction" "DA" "Nucleophilic_Addition")
MODELS=("mace" "orb")

NPROC=4
MEMORY="8GB"

cd "$BASE_DIR" || exit 1

for model in "${MODELS[@]}"; do
    case "$model" in
        mace)
            OUTPUT_ROOT="$BASE_DIR/MACE_Inputs_All"
            ext_cmd='external="g16-mlips-mace"'
            ;;
        orb)
            OUTPUT_ROOT="$BASE_DIR/ORB_Inputs_All"
            ext_cmd='external="g16-mlips-orb"'
            ;;
        *)
            echo "Unsupported model: $model"
            exit 1
            ;;
    esac

    mkdir -p "$OUTPUT_ROOT"
    echo "------------------------------------------------------"
    echo "Building inputs for model: $model"
    echo "Output root: $OUTPUT_ROOT"

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

            file_prefix="$molecule_dir/${base_name}_${model}"
            chk_name="${base_name}_${model}.chk"

            coords_tmp=$(mktemp)
            tail -n +3 "$xyz_file" > "$coords_tmp"

            cat <<EOT > "${file_prefix}_1_freq.com"
%chk=$chk_name
%nprocshared=$NPROC
%mem=$MEMORY
#p Freq $ext_cmd

Step 1: Hessian for $base_name ($model)

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
            echo "[$model][$task_label] $rel_path -> ${molecule_dir#"$BASE_DIR"/}"
        done < <(find "$reaction_path" -mindepth 2 -maxdepth 2 -type f -name "*.xyz" -print0 | sort -z)
    done
done

echo "======================================================"
echo "Input generation completed"
echo "Gaussian settings: 4 cores + 8GB"
echo "======================================================"
