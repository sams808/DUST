"""
Oxide reference data: canonical names, molar masses, and default
former/modifier classifications for the two N4 models.

Coefficients below are transcribed directly from the reference
spreadsheets so the app reproduces those numbers exactly:
  - Dell (1983) / Du & Stebbins (2005a) model: "Copie de Dell1983
    v2.xlsx" and "Copie de RnKp Dell1983 10-10-2023.xlsx" (identical
    "Model Dell" sheet in both).
  - Lu et al. (2021) model: "N4 calculation_Lu et al 2021.xlsx".

All coefficients are exposed as plain dicts so the GUI can let the user
edit them (per-oxide include/exclude + weight, and for the Dell model
which role - former or modifier - each oxide plays) without touching
this file. CANONICAL_OXIDES deliberately covers more than the classic
Na2O-Al2O3-B2O3-SiO2 borosilicate system - complex multicomponent
glasses (e.g. nuclear waste borosilicates) commonly carry transition
metals, rare earths and even actinide oxides, and any oxide not
recognized by the Lu et al. (2021) weighting scheme is simply excluded
from that model's R''/K'' (it only sums oxides it has a coefficient
for) rather than raising an error.
"""
from __future__ import annotations

# Canonical oxide order used throughout the app (mol% basis). Grouped
# by role for readability; the app itself treats this as one flat list.
CANONICAL_OXIDES = [
    # network formers / intermediates
    "SiO2", "B2O3", "Al2O3", "P2O5", "GeO2", "TeO2", "As2O5", "Sb2O3",
    "Fe2O3", "Cr2O3", "TiO2", "ZrO2", "HfO2", "Nb2O5", "Ta2O5",
    "WO3", "MoO3", "V2O5", "SO3", "SnO2",
    # alkali modifiers
    "Na2O", "Li2O", "K2O", "Cs2O", "Rb2O",
    # alkaline earth modifiers
    "CaO", "MgO", "SrO", "BaO", "BeO",
    # divalent / transition-metal modifiers
    "ZnO", "PbO", "CdO", "MnO", "NiO", "CoO", "CuO",
    # trivalent modifiers, including rare earths
    "La2O3", "Y2O3", "Bi2O3", "CeO2", "Nd2O3", "Sm2O3", "Gd2O3",
    "In2O3", "Ga2O3", "Sc2O3",
    # nuclear-waste-relevant actinides
    "ThO2", "UO3", "NpO2", "PuO2",
]

# Standard molar masses (g/mol) - used only for the optional wt% -> mol%
# conversion offered at CSV import time.
MOLAR_MASS = {
    "SiO2": 60.084, "B2O3": 69.620, "Al2O3": 101.961, "P2O5": 141.945,
    "GeO2": 104.613, "TeO2": 159.600, "As2O5": 229.841, "Sb2O3": 291.518,
    "Fe2O3": 159.688, "Cr2O3": 151.990, "TiO2": 79.866, "ZrO2": 123.218,
    "HfO2": 210.490, "Nb2O5": 265.810, "Ta2O5": 441.893,
    "WO3": 231.837, "MoO3": 143.940, "V2O5": 181.880, "SO3": 80.058,
    "SnO2": 150.708,
    "Na2O": 61.979, "Li2O": 29.881, "K2O": 94.196, "Cs2O": 281.810,
    "Rb2O": 186.935,
    "CaO": 56.077, "MgO": 40.304, "SrO": 103.619, "BaO": 153.326,
    "BeO": 25.012,
    "ZnO": 81.379, "PbO": 223.199, "CdO": 128.410, "MnO": 70.937,
    "NiO": 74.693, "CoO": 74.933, "CuO": 79.545,
    "La2O3": 325.809, "Y2O3": 225.810, "Bi2O3": 465.958, "CeO2": 172.115,
    "Nd2O3": 336.478, "Sm2O3": 348.718, "Gd2O3": 362.498,
    "In2O3": 277.638, "Ga2O3": 187.444, "Sc2O3": 137.910,
    "ThO2": 264.037, "UO3": 286.027, "NpO2": 269.047, "PuO2": 276.063,
}

# ---------------------------------------------------------------------
# Dell (1983) / Du & Stebbins (2005a) model - default classification.
# R' = (sum modifier oxides) / (Al2O3 + B2O3); K' = SiO2 / (Al2O3 + B2O3)
# Every entry is (oxide -> coefficient). Formers make up the shared
# denominator; modifiers make up the R' numerator. Every oxide in
# CANONICAL_OXIDES can be assigned to either role (or left out) in the
# GUI's formula editor - these are just the starting defaults (alkalis
# + alkaline earths at coefficient 1; no Bi2O3 by default, since its
# role as an NBO-forming modifier in the Dell/Du-Stebbins sense is
# uncertain rather than settled - see docs/MODELS_REFERENCE.md).
# ---------------------------------------------------------------------
DELL_DEFAULT_FORMERS = {"Al2O3": 1.0, "B2O3": 1.0}
DELL_DEFAULT_MODIFIERS = {
    "Na2O": 1.0, "Li2O": 1.0, "K2O": 1.0, "Cs2O": 1.0, "Rb2O": 1.0,
    "CaO": 1.0, "MgO": 1.0, "SrO": 1.0, "BaO": 1.0,
}

# ---------------------------------------------------------------------
# Lu et al. (2021) model - fixed network-former / charge-compensator
# weights as given in "N4 calculation_Lu et al 2021.xlsx" (columns D-I).
# These weights are identical across all 4 fit variants; only the
# regression constants (below, in core/lu_model.py) differ. Any oxide
# present in a user's data but absent from these dicts (e.g. one of the
# rare earths/actinides added for complex glasses above) simply doesn't
# contribute to R''/K'' - core/lu_model.py only sums oxides it has a
# coefficient for.
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
