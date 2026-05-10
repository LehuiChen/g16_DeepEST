#!/usr/bin/env python3
"""DeePEST-OS backend built from GFN2-xTB baseline plus delta-MACE."""

from __future__ import absolute_import, division, print_function

import os

import numpy as np

if __package__ in (None, ""):
    from mlip_backends import BackendError, MACEEvaluator, _BackendBase, _numerical_hessian_from_forces
    from xtb_alpb_correction import XTBError, resolve_xtb_ncores, xtb_energy, xtb_engrad, xtb_hessian
else:
    from .mlip_backends import BackendError, MACEEvaluator, _BackendBase, _numerical_hessian_from_forces
    from .xtb_alpb_correction import XTBError, resolve_xtb_ncores, xtb_energy, xtb_engrad, xtb_hessian


_DEEPEST_VARIANTS = {
    "main": {
        "env": "DEEPEST_MODEL_PATH",
        "relpath": os.path.join("upstream", "DeePEST-OS", "models", "MACE_deltaL", "MACE_deltaL.model"),
    },
    "t1x": {
        "env": "DEEPEST_T1X_MODEL_PATH",
        "relpath": os.path.join("upstream", "DeePEST-OS", "models", "DeePEST-OS-T1x", "DeePEST-OS-T1x.model"),
    },
}


def _workspace_root():
    here = os.path.abspath(__file__)
    return os.path.dirname(os.path.dirname(os.path.dirname(here)))


def _resolve_variant_model_path(variant):
    key = str(variant or "main").strip().lower()
    if key not in _DEEPEST_VARIANTS:
        raise BackendError("Unsupported DeePEST variant '{}'. Choose from: main, t1x.".format(variant))

    spec = _DEEPEST_VARIANTS[key]
    env_path = os.getenv(spec["env"], "").strip()
    if env_path:
        return env_path
    return os.path.join(_workspace_root(), spec["relpath"])


def get_available_deepest_models():
    return [
        "auto",
        "main",
        "t1x",
        "<local_model_path>",
        "<https://...model>",
    ]


class DeePESTEvaluator(_BackendBase):
    """GFN2-xTB 基线 + delta-MACE 修正的 DeePEST 求值器。"""

    def __init__(
        self,
        model,
        variant,
        device,
        default_dtype,
        xtb_cmd="xtb",
        xtb_acc=0.2,
        xtb_workdir="tmp",
        xtb_keep_files=False,
        delta_hessian_step=1.0e-3,
        calc_kwargs=None,
    ):
        model_spec = str(model or "").strip()
        if model_spec.lower() in ("", "auto", "default", "main", "t1x"):
            alias = model_spec.lower() if model_spec.lower() in ("main", "t1x") else str(variant or "main").lower()
            model_spec = _resolve_variant_model_path(alias)

        self.model_path = str(model_spec)
        self.variant = str(variant or "main").strip().lower()
        self.xtb_cmd = str(xtb_cmd or "xtb")
        self.xtb_acc = float(xtb_acc)
        self.xtb_workdir = str(xtb_workdir or "tmp")
        self.xtb_keep_files = bool(xtb_keep_files)
        self.delta_hessian_step = float(delta_hessian_step)
        self.ncores = resolve_xtb_ncores()
        self._delta = MACEEvaluator(
            model=self.model_path,
            device=device,
            default_dtype=default_dtype,
            calc_kwargs=calc_kwargs,
        )

    def _xtb_energy(self, symbols, coords_ang, charge, multiplicity):
        try:
            return xtb_energy(
                symbols=symbols,
                coords_ang=coords_ang,
                charge=charge,
                multiplicity=multiplicity,
                solvent="none",
                xtb_cmd=self.xtb_cmd,
                xtb_acc=self.xtb_acc,
                xtb_workdir=self.xtb_workdir,
                xtb_keep_files=self.xtb_keep_files,
                ncores=self.ncores,
            )
        except XTBError as exc:
            raise BackendError("xTB baseline energy failed: {}".format(exc))

    def _xtb_energy_forces(self, symbols, coords_ang, charge, multiplicity):
        try:
            return xtb_engrad(
                symbols=symbols,
                coords_ang=coords_ang,
                charge=charge,
                multiplicity=multiplicity,
                solvent="none",
                xtb_cmd=self.xtb_cmd,
                xtb_acc=self.xtb_acc,
                xtb_workdir=self.xtb_workdir,
                xtb_keep_files=self.xtb_keep_files,
                ncores=self.ncores,
            )
        except XTBError as exc:
            raise BackendError("xTB baseline gradient failed: {}".format(exc))

    def _xtb_hessian(self, symbols, coords_ang, charge, multiplicity):
        try:
            return xtb_hessian(
                symbols=symbols,
                coords_ang=coords_ang,
                charge=charge,
                multiplicity=multiplicity,
                solvent="none",
                xtb_cmd=self.xtb_cmd,
                xtb_acc=self.xtb_acc,
                xtb_workdir=self.xtb_workdir,
                xtb_keep_files=self.xtb_keep_files,
                ncores=self.ncores,
            )
        except XTBError as exc:
            raise BackendError("xTB baseline Hessian failed: {}".format(exc))

    def _delta_energy_forces(self, symbols, coords_ang, charge, multiplicity):
        return self._delta.energy_forces(symbols, coords_ang, charge, multiplicity)

    def energy_forces(self, symbols, coords_ang, charge, multiplicity):
        coords = np.asarray(coords_ang, dtype=np.float64).reshape(-1, 3)
        xtb_e, xtb_f = self._xtb_energy_forces(symbols, coords, charge, multiplicity)
        delta_e, delta_f = self._delta_energy_forces(symbols, coords, charge, multiplicity)
        total_f = np.asarray(xtb_f, dtype=np.float64) + np.asarray(delta_f, dtype=np.float64)
        return float(xtb_e + delta_e), total_f

    def analytical_hessian(self, symbols, coords_ang, charge, multiplicity):
        coords = np.asarray(coords_ang, dtype=np.float64).reshape(-1, 3)
        xtb_h = self._xtb_hessian(symbols, coords, charge, multiplicity)
        delta_h = self._delta.analytical_hessian(symbols, coords, charge, multiplicity)
        return np.asarray(xtb_h, dtype=np.float64) + np.asarray(delta_h, dtype=np.float64)

    def evaluate(
        self,
        symbols,
        coords_ang,
        charge,
        multiplicity,
        need_forces,
        need_hessian,
        hessian_mode,
        hessian_step,
    ):
        coords = np.asarray(coords_ang, dtype=np.float64).reshape(-1, 3)

        if not need_hessian:
            if need_forces:
                total_e, total_f = self.energy_forces(symbols, coords, charge, multiplicity)
                return float(total_e), np.asarray(total_f, dtype=np.float64), None

            xtb_e = self._xtb_energy(symbols, coords, charge, multiplicity)
            delta_e, _ = self._delta_energy_forces(symbols, coords, charge, multiplicity)
            return float(xtb_e + delta_e), None, None

        # 中文说明：DeePEST 主模型是 delta-learning，H_total 必须由 xTB 基线与 delta-MACE 两部分相加。
        xtb_e, xtb_f = self._xtb_energy_forces(symbols, coords, charge, multiplicity)
        xtb_h = self._xtb_hessian(symbols, coords, charge, multiplicity)
        delta_e, delta_f = self._delta_energy_forces(symbols, coords, charge, multiplicity)

        mode = str(hessian_mode or "Analytical").strip().lower()
        use_analytical = mode.startswith("ana")
        delta_h = None
        if use_analytical:
            try:
                delta_h = self._delta.analytical_hessian(symbols, coords, charge, multiplicity)
            except Exception:
                delta_h = None

        if delta_h is None:
            # 中文说明：当 MACE 侧没有直接 Hessian 时，仅对 delta-force 做数值差分，
            # 这样可以保留 xTB 基线的解析 Hessian，避免把整个总势能面都降级成慢速数值 Hessian。
            _delta_e, _delta_f, delta_h = _numerical_hessian_from_forces(
                lambda xyz: self._delta_energy_forces(symbols, xyz, charge, multiplicity),
                coords,
                float(getattr(self, "delta_hessian_step", hessian_step)),
            )
            delta_e = _delta_e
            delta_f = _delta_f

        total_e = float(xtb_e + delta_e)
        total_f = np.asarray(xtb_f, dtype=np.float64) + np.asarray(delta_f, dtype=np.float64)
        total_h = np.asarray(xtb_h, dtype=np.float64) + np.asarray(delta_h, dtype=np.float64)
        return total_e, total_f, total_h
