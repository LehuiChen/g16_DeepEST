# DeePEST Gaussian External

This repository provides a Gaussian 16 `External` workflow around DeePEST for PBS batch runs.

## Upstream

- Original project: [DeePEST-OS (kaipai-ren)](https://github.com/kaipai-ren/DeePEST-OS)

## Repository Layout

- `g16-deepest/`: core package (`g16-mlips-deepest`)
- `deepest_scripts/`: input generation and PBS submission scripts
- `upstream/DeePEST-OS/`: minimal upstream reference files kept in this repo
- `deepest_g16.yaml`: conda environment definition
- `setup_deepest_g16.sh`: local installation helper

## Notes

- Legacy `mace&orb` scripts were removed.
- The paper PDF is intentionally not tracked in this Git repository.
- DeePEST model weights should stay local/server-side and should not be committed.

## Quick Start (Linux Cluster)

```bash
bash setup_deepest_g16.sh
conda activate deepest_g16
bash deepest_scripts/generate_all_inputs.sh
qsub -v NODE_ID=1,INPUT_ROOT=DEEPEST_Inputs_All deepest_scripts/submit_all_models.pbs
```
