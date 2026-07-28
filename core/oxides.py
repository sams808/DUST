"""
Oxide reference data: canonical names, molar masses, and default
former/modifier classifications for the two N4 models.

Coefficients below are transcribed directly from the user's reference
spreadsheets so the app reproduces those numbers exactly:
  - Dell (1983) / Du & Stebbins (2005a) model:
      "Copie de Dell1983 v2.xlsx" (sheet "Model Dell")
      "Copie de RnKp Dell1983 10-10-2023.xlsx" (identical "Model Dell" sheet)
  - Lu et al. (2021) model:
      "N4 calculation_Lu et al 2021.xlsx" (sheet "Sheet1")

All coefficients are exposed as plain dicts so the GUI can let the user
edit them (per-oxide include/exclude + weight) without touching this file.
"""
from __future__ import annotations

# Canonical oxide order used throughout the app (mol% basis).
CANONICAL_OXIDES = [
    "SiO2", "B2O3", "Al2O3", "P2O5", "Fe2O3", "TiO2", "ZrO2", "HfO2",
    "Na2O", "Li2O", "K2O", "Cs2O", "Rb2O",
    "CaO", "MgO", "SrO", "BaO", "ZnO", "PbO",
    "La2O3", "Y2O3", "Bi2O3",
]

# Standard molar masses (g/mol) - used only for the optional wt% -> mol%
# conversion offered at CSV import time.
MOLAR_MASS = {
    "SiO2": 60.084, "B2O3": 69.620, "Al2O3": 101.961, "P2O5": 141.945,
    "Fe2O3": 159.688, "TiO2": 79.866, "ZrO2": 123.218, "HfO2": 210.49,
    "Na2O": 61.979, "Li2O": 29.881, "K2O": 94.196, "Cs2O": 281.810,
    "Rb2O": 186.935,
    "CaO": 56.077, "MgO": 40.304, "SrO": 103.619, "BaO": 153.326,
    "ZnO": 81.379, "PbO": 223.199,
    "La2O3": 325.809, "Y2O3": 225.810, "Bi2O3": 465.958,
}

# ---------------------------------------------------------------------
# Dell (1983) / Du & Stebbins (2005a) model - default classification.
# R' = (sum modifier oxides) / (Al2O3 + B2O3); K' = SiO2 / (Al2O3 + B2O3)
# Every entry is (oxide -> coefficient). Formers make up the shared
# denominator; modifiers make up the R' numerator. Fully editable in the
# GUI; these are just sensible starting defaults (alkalis + alkaline
# earths + Bi2O3, coefficient 1, matching thesis Figs 4.17/5.7).
# ---------------------------------------------------------------------
DELL_DEFAULT_FORMERS = {"Al2O3": 1.0, "B2O3": 1.0}
DELL_DEFAULT_MODIFIERS = {
    "Na2O": 1.0, "Li2O": 1.0, "K2O": 1.0, "Cs2O": 1.0, "Rb2O": 1.0,
    "CaO": 1.0, "MgO": 1.0, "SrO": 1.0, "BaO": 1.0,
    "Bi2O3": 1.0,
}
# Available but off by default (rarer / less certain as charge
# compensators) - user can flip these on in the customization panel.
DELL_OPTIONAL_MODIFIERS = {"ZnO": 1.0, "PbO": 1.0, "La2O3": 1.0, "Y2O3": 1.0}

# ---------------------------------------------------------------------
# Lu et al. (2021) model - fixed network-former / charge-compensator
# weights as given in "N4 calculation_Lu et al 2021.xlsx" (columns D-I).
# These weights are identical across all 4 fit variants; only the
# regression constants (below, in core/lu_model.py) differ.
# ---------------------------------------------------------------------
LU2021_FORMER_COEFF = {
    "B2O3": 1.0, "Al2O3": 4.0, "P2O5": 0.0, "Fe2O3": 0.0,
    "TiO2": 0.0, "ZrO2": 3.0, "HfO2": 0.0,
}
LU2021_MODIFIER_COEFF = {
    # Na2O is the base of R'' (added with implicit coefficient 1 in the
    # spreadsheet, cell $B$10) - always included, not user-toggleable.
    "Li2O": 1.0, "K2O": 1.0, "Cs2O": 1.0, "Rb2O": 1.0,
    "CaO": 0.5, "MgO": 0.5, "SrO": 0.5, "BaO": 0.5, "ZnO": 0.5, "PbO": 0.5,
    "La2O3": 1.0 / 3.0, "Y2O3": 1.0 / 3.0, "Bi2O3": 1.0 / 3.0,
}
