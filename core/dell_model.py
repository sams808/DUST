"""
Dell (1983) / Du & Stebbins (2005a) N4 and NBO-speciation model, as
generalized to aluminoborosilicate glasses and used to draw thesis
Figures 4.17 and 5.7 (see EXAMPLES/DYB/DYB.ipynb and
"Copie de Dell1983 v2.xlsx" / "Copie de RnKp Dell1983 10-10-2023.xlsx",
sheet "Model Dell").

Definitions (R', K' in mol% ratios; formers/modifiers are user-editable
oxide -> coefficient dicts, see core/oxides.py for defaults):

    D     = sum(coeff_i * x_i) over "former" oxides   (default Al2O3+B2O3)
    K'    = x_SiO2 / D
    R'    = sum(coeff_i * x_i) over "modifier" oxides / D
    Rmax  = 0.5 + K'/16
    RD1   = 0.5 + K'/4
    RD3   = K' + 2

Three NBO regimes (boundaries exactly as stated in the thesis text,
section 5.1.4, and reproduced in Fig. 4.17B / 5.7):
    R' < Rmax            -> "No NBO"
    Rmax <= R' < RD1      -> "NBO-Si only (Q3)"
    RD1 <= R' < RD3        -> "NBO-Si (Q2 & Q3) + NBO-B"
    R' >= RD3               -> "Beyond model validity" (N4 undefined)

N4 (fraction of 4-coordinated boron):
    R' < Rmax  : N4 = R'
    Rmax<=R'<RD1: N4 = Rmax
    RD1<=R'<RD3 : N4 = Rmax - (R'-RD1)*(8+K')/(12*(2+K'))
    R'>=RD3      : N4 = NaN

NBO speciation (mole fraction of NBO per formula unit, matching the
"NBO-Si1"/"NBO-Si2"/"NBO-B" columns of the "Model Dell" sheet exactly):
    U = (R'-RD1)*(8-K')/4/(K'+2)
    V = (R'-RD1)*5*K'/4/(K'+2)
    NBO_Si_Q3 = 2*(R'-Rmax)/(3+2K'+R')              [R' >= Rmax]
    NBO_Si_Q2 = (2/15)*13*V/(3+2K'+R')              [R' >= RD1]
    NBO_B     = 4/3*(U + V/5)/(3+2K'+R')            [R' >= RD1]
    NBO_tot   = NBO_Si_Q3 + NBO_Si_Q2 + NBO_B

"Percentage of NBO on each species" = each term / NBO_tot * 100, i.e.
the speciation of the total non-bridging-oxygen population - not
defined once NBO_tot == 0 (the "No NBO" regime).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .oxides import DELL_DEFAULT_FORMERS, DELL_DEFAULT_MODIFIERS

REGIME_NO_NBO = "No NBO"
REGIME_SI_ONLY = "NBO-Si only (Q3)"
REGIME_SI_AND_B = "NBO-Si (Q2 & Q3) + NBO-B"
REGIME_INVALID = "Beyond model validity"


def _weighted_sum(df: pd.DataFrame, coeffs: dict) -> np.ndarray:
    total = np.zeros(len(df), dtype=float)
    for oxide, coeff in coeffs.items():
        if coeff == 0:
            continue
        if oxide in df.columns:
            total = total + coeff * pd.to_numeric(df[oxide], errors="coerce").fillna(0.0).to_numpy()
    return total


def compute_dell(
    df: pd.DataFrame,
    formers: dict | None = None,
    modifiers: dict | None = None,
) -> pd.DataFrame:
    """Compute R', K', N4, NBO regime and NBO speciation for each row.

    ``df`` must contain oxide columns in mol% (canonical names, e.g.
    'SiO2', 'Na2O', ...). Missing oxide columns are treated as 0.
    Returns a new DataFrame with the added columns; input is not mutated.
    """
    formers = dict(DELL_DEFAULT_FORMERS if formers is None else formers)
    modifiers = dict(DELL_DEFAULT_MODIFIERS if modifiers is None else modifiers)

    out = df.copy()
    n = len(df)
    sio2 = pd.to_numeric(df.get("SiO2", pd.Series(np.zeros(n))), errors="coerce").fillna(0.0).to_numpy()

    D = _weighted_sum(df, formers)
    with np.errstate(divide="ignore", invalid="ignore"):
        K = np.where(D > 0, sio2 / D, np.nan)
        Mnum = _weighted_sum(df, modifiers)
        R = np.where(D > 0, Mnum / D, np.nan)

    Rmax = 0.5 + K / 16.0
    RD1 = 0.5 + K / 4.0
    RD3 = K + 2.0

    valid = R < RD3
    N4 = np.where(
        ~valid, np.nan,
        np.where(R < Rmax, R,
                 np.where(R < RD1, Rmax,
                          Rmax - (R - RD1) * (8 + K) / (12 * (2 + K)))),
    )

    regime = np.select(
        [~valid, R < Rmax, R < RD1, R < RD3],
        [REGIME_INVALID, REGIME_NO_NBO, REGIME_SI_ONLY, REGIME_SI_AND_B],
        default=REGIME_INVALID,
    )

    denom = 3 + 2 * K + R
    with np.errstate(divide="ignore", invalid="ignore"):
        U = (R - RD1) * (8 - K) / 4.0 / (K + 2)
        V = (R - RD1) * 5 * K / 4.0 / (K + 2)
        nbo_si_q3 = np.where(valid & (R >= Rmax), 2 * (R - Rmax) / denom, 0.0)
        nbo_si_q2 = np.where(valid & (R >= RD1), (2.0 / 15.0) * 13 * V / denom, 0.0)
        nbo_b = np.where(valid & (R >= RD1), (4.0 / 3.0) * (U + V / 5.0) / denom, 0.0)
    nbo_si_q3 = np.where(valid, nbo_si_q3, np.nan)
    nbo_si_q2 = np.where(valid, nbo_si_q2, np.nan)
    nbo_b = np.where(valid, nbo_b, np.nan)
    nbo_tot = nbo_si_q3 + nbo_si_q2 + nbo_b

    with np.errstate(divide="ignore", invalid="ignore"):
        pct_si_q3 = np.where(nbo_tot > 0, 100 * nbo_si_q3 / nbo_tot, 0.0)
        pct_si_q2 = np.where(nbo_tot > 0, 100 * nbo_si_q2 / nbo_tot, 0.0)
        pct_b = np.where(nbo_tot > 0, 100 * nbo_b / nbo_tot, 0.0)
    pct_si_q3 = np.where(valid, pct_si_q3, np.nan)
    pct_si_q2 = np.where(valid, pct_si_q2, np.nan)
    pct_b = np.where(valid, pct_b, np.nan)

    out["Dell_R"] = R
    out["Dell_K"] = K
    out["Dell_Rmax"] = Rmax
    out["Dell_RD1"] = RD1
    out["Dell_RD3"] = RD3
    out["Dell_N4"] = N4
    out["Dell_regime"] = regime
    out["Dell_NBO_SiQ3"] = nbo_si_q3
    out["Dell_NBO_SiQ2"] = nbo_si_q2
    out["Dell_NBO_B"] = nbo_b
    out["Dell_NBO_tot"] = nbo_tot
    out["Dell_pct_NBO_SiQ3"] = pct_si_q3
    out["Dell_pct_NBO_SiQ2"] = pct_si_q2
    out["Dell_pct_NBO_B"] = pct_b
    return out


def n4_grid(k_values: np.ndarray, r_values: np.ndarray) -> np.ndarray:
    """N4(K', R') evaluated on a full grid, for background heatmaps.

    Returns an array of shape (len(k_values), len(r_values)).
    """
    K, R = np.meshgrid(k_values, r_values, indexing="ij")
    Rmax = 0.5 + K / 16.0
    RD1 = 0.5 + K / 4.0
    RD3 = K + 2.0
    valid = R < RD3
    N4 = np.where(
        ~valid, np.nan,
        np.where(R < Rmax, R,
                 np.where(R < RD1, Rmax,
                          Rmax - (R - RD1) * (8 + K) / (12 * (2 + K)))),
    )
    return N4


def regime_grid(r_values: np.ndarray, n4_values: np.ndarray) -> np.ndarray:
    """Classify each (R', N4) grid cell for the Fig. 4.17B / 5.7 style
    background, independent of any single K' value (K' only appears as
    the iso-K' guide lines overlaid on top).

    The two boundary curves are exact, not empirical fits: at the
    "No NBO"/"Q3-only" transition (R'=Rmax(K')), both regime formulas
    agree that N4=Rmax(K')=R', for *every* K' - so that boundary is
    simply the diagonal N4=R'.  At the "Q3-only"/"Q3+Q2+B" transition
    (R'=RD1(K'), N4=Rmax(K')), eliminating K' between
    R'=0.5+K'/4 and N4=0.5+K'/16 gives N4 = R'/4 + 0.375. (This matches
    EXAMPLES/DYB/DYB.ipynb's "model_db" construction, confirmed here by
    direct algebraic derivation rather than just copied.)  Below that
    second boundary, every K' large enough has RD3=K'+2 further out
    than the plotted R', so the "Q3+Q2+B" region legitimately extends
    down to N4=0 for all plotted R' - no 4th "invalid" state is needed
    in this 2D projection.

    Returns an integer code array of shape (len(n4_values), len(r_values)):
    1 = No NBO, 2 = NBO-Si only (Q3), 3 = NBO-Si (Q2 & Q3) + NBO-B.
    """
    R = r_values[np.newaxis, :]
    N4 = n4_values[:, np.newaxis]
    upper = R  # No NBO / Q3-only boundary: N4 = R'
    lower = 0.25 * R + 0.375  # Q3-only / Q3+Q2+B boundary
    codes = np.where(N4 >= upper, 1, np.where(N4 > lower, 2, 3))
    return codes.astype(int)
