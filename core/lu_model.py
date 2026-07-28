"""
Lu et al. (2021) generalized N4 model, transcribed from
"N4 calculation_Lu et al 2021.xlsx" (sheet "Sheet1").

Unlike the Dell/Du-Stebbins model (core/dell_model.py), this model is
parameterized for arbitrary multicomponent oxide glasses: every network
former (SiO2, B2O3, Al2O3, P2O5, Fe2O3, TiO2, ZrO2, HfO2) and modifier
(alkalis, alkaline earths, La2O3, Y2O3, Bi2O3) contributes with its own
fixed weight (see core/oxides.py: LU2021_FORMER_COEFF /
LU2021_MODIFIER_COEFF - identical across all 4 fit variants below).

    K'' = x_SiO2 / sum(formerCoeff_i * x_i)
    R'' = (x_Na2O + sum(modifierCoeff_i * x_i)) / sum(formerCoeff_i * x_i)

Two functional forms, each fit in two flavours ("whole" = fit across the
whole multicomponent glass database in the paper; "borosilicate" = fit
restricted to borosilicate glasses):

  Modified Du & Stebbins (kind="ds"):
    Rmax = rmax_slope*K'' + rmax_const
    RD   = rd_slope*K''   + rd_const
    N4_raw = R''                                      if R'' <= Rmax
           = Rmax                                      if Rmax < R'' <= RD
           = Rmax - (R''-RD)*(8+K'')/(12*(2+K''))        otherwise

  Modified Bernstein (kind="bernstein"):
    Rmax = rmax_slope*K'' + rmax_const
    N4_raw = R''                                       if R'' < Rmax
           = a*(b+R'')*(c - R''/(d+e*K''))**5             otherwise

Both are then clamped to [0, 1] (matching the spreadsheet's
IF(N6<1, IF(N6>0, N6, 0), 1) logic exactly).

This model does not provide an NBO speciation breakdown (no NBO-Si /
NBO-B split) - the spreadsheet only computes N4.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .oxides import LU2021_FORMER_COEFF, LU2021_MODIFIER_COEFF

VARIANTS = {
    "ds_whole": {
        "label": "Modified Du & Stebbins (whole database)",
        "kind": "ds",
        "rmax_const": 0.59, "rmax_slope": 0.019,
        "rd_const": 0.096, "rd_slope": 0.502,
    },
    "ds_borosilicate": {
        "label": "Modified Du & Stebbins (borosilicate)",
        "kind": "ds",
        "rmax_const": 0.58, "rmax_slope": 0.022,
        "rd_const": 0.256, "rd_slope": 0.459,
    },
    "bernstein_whole": {
        "label": "Modified Bernstein (whole database)",
        "kind": "bernstein",
        "rmax_const": 0.43, "rmax_slope": 0.06,
        "a": 0.25, "b": 0.29, "c": 1.3, "d": 3.78, "e": 1.0,
    },
    "bernstein_borosilicate": {
        "label": "Modified Bernstein (borosilicate)",
        "kind": "bernstein",
        "rmax_const": 0.43, "rmax_slope": 0.06,
        "a": 0.71, "b": 0.4, "c": 1.03, "d": 5.47, "e": 1.19,
    },
}


def _weighted_sum(df: pd.DataFrame, coeffs: dict) -> np.ndarray:
    total = np.zeros(len(df), dtype=float)
    for oxide, coeff in coeffs.items():
        if coeff == 0:
            continue
        if oxide in df.columns:
            total = total + coeff * pd.to_numeric(df[oxide], errors="coerce").fillna(0.0).to_numpy()
    return total


def compute_rk(df: pd.DataFrame, formers: dict | None = None, modifiers: dict | None = None):
    """Return (R'', K'') arrays for the Lu et al. (2021) model."""
    formers = dict(LU2021_FORMER_COEFF if formers is None else formers)
    modifiers = dict(LU2021_MODIFIER_COEFF if modifiers is None else modifiers)

    n = len(df)
    na2o = pd.to_numeric(df.get("Na2O", pd.Series(np.zeros(n))), errors="coerce").fillna(0.0).to_numpy()
    sio2 = pd.to_numeric(df.get("SiO2", pd.Series(np.zeros(n))), errors="coerce").fillna(0.0).to_numpy()

    D = _weighted_sum(df, formers)
    with np.errstate(divide="ignore", invalid="ignore"):
        K = np.where(D > 0, sio2 / D, np.nan)
        Mnum = na2o + _weighted_sum(df, modifiers)
        R = np.where(D > 0, Mnum / D, np.nan)
    return R, K


def _n4_ds(R, K, params):
    Rmax = params["rmax_slope"] * K + params["rmax_const"]
    RD = params["rd_slope"] * K + params["rd_const"]
    with np.errstate(divide="ignore", invalid="ignore"):
        decline = Rmax - (R - RD) * (8 + K) / (12 * (2 + K))
    raw = np.where(R <= Rmax, R, np.where(R <= RD, Rmax, decline))
    return raw, Rmax, RD


def _n4_bernstein(R, K, params):
    Rmax = params["rmax_slope"] * K + params["rmax_const"]
    a, b, c, d, e = (params[k] for k in "abcde")
    with np.errstate(divide="ignore", invalid="ignore"):
        curve = a * (b + R) * (c - R / (d + e * K)) ** 5
    raw = np.where(R < Rmax, R, curve)
    return raw, Rmax, None


def compute_lu(
    df: pd.DataFrame,
    variant: str = "ds_whole",
    formers: dict | None = None,
    modifiers: dict | None = None,
    params: dict | None = None,
) -> pd.DataFrame:
    """Compute R'', K'' and N4 for each row under a chosen Lu et al. (2021)
    model variant ("ds_whole", "ds_borosilicate", "bernstein_whole",
    "bernstein_borosilicate"). ``params`` overrides the default regression
    constants for that variant (for user customization / sensitivity
    checks) - must contain the same keys as VARIANTS[variant].
    """
    if variant not in VARIANTS:
        raise ValueError(f"Unknown Lu et al. 2021 variant: {variant!r}")
    p = dict(VARIANTS[variant])
    if params:
        p.update(params)

    out = df.copy()
    R, K = compute_rk(df, formers, modifiers)

    if p["kind"] == "ds":
        raw, Rmax, RD = _n4_ds(R, K, p)
    else:
        raw, Rmax, RD = _n4_bernstein(R, K, p)

    N4 = np.clip(raw, 0.0, 1.0)
    N4 = np.where(np.isnan(raw), np.nan, N4)

    prefix = f"Lu_{variant}"
    out[f"{prefix}_R"] = R
    out[f"{prefix}_K"] = K
    out[f"{prefix}_Rmax"] = Rmax
    if RD is not None:
        out[f"{prefix}_RD"] = RD
    out[f"{prefix}_N4"] = N4
    return out


def compute_lu_all(df: pd.DataFrame, formers: dict | None = None, modifiers: dict | None = None) -> pd.DataFrame:
    """Compute N4 for all 4 Lu et al. (2021) variants at once (used when
    the user wants to compare/overlay all of them)."""
    out = df.copy()
    for variant in VARIANTS:
        res = compute_lu(df, variant=variant, formers=formers, modifiers=modifiers)
        prefix = f"Lu_{variant}"
        for col in res.columns:
            if col.startswith(prefix):
                out[col] = res[col]
    return out
