# g16-deepest

Gaussian 16 `External` backend for DeePEST-OS.

This package keeps the `g16-mlips` Gaussian External framework, but replaces
the backend with the published DeePEST-OS inference definition:

- baseline: `GFN2-xTB`
- delta model: `MACE_deltaL.model`
- total PES: `E_total = E_xtb + ΔE_mace`

## Layout

- package root: `g16-deepest/`
- upstream weights: `../upstream/DeePEST-OS/models/`
- environment file: `../deepest_g16.yaml`
- install script: `../setup_deepest_g16.sh`

## Install

On the Linux cluster, create the dedicated environment first:

```bash
cd /path/to/DeePEST
bash setup_deepest_g16.sh
conda activate deepest_g16
```

The install script uses editable mode, so the default published model paths can
still resolve back to the current workspace.

## Commands

```bash
g16-mlips-deepest --help
deepest --list-models
```

Supported published variants:

- `main`: 10-element `MACE_deltaL.model` (default)
- `t1x`: CHON `DeePEST-OS-T1x.model`

You can also pass a local model path explicitly:

```bash
g16-mlips-deepest --model /abs/path/to/model.model
```

## Gaussian Example

```text
%nprocshared=8
%mem=32GB
%chk=ts_ext.chk
#p external="g16-mlips-deepest" opt(ts,readfc,nomicro)

DeePEST TS optimization

0 1
...
```

Use `freq` first to populate the checkpoint Hessian, then `opt(readfc,nomicro)`
or `irc(readfc,nomicro)` in the same way as the existing MACE/ORB workflow.

## Runtime Notes

- `DEEPEST_MODEL_PATH` can override the default main checkpoint path.
- `DEEPEST_T1X_MODEL_PATH` can override the `t1x` checkpoint path.
- `xtb` must be available on `PATH`.
- The current implementation keeps the Gaussian External resident server mode
  from `g16-mlips` for faster repeated calls during optimization.
