"""
Regression tests: every expected value here was read directly (data_only)
from the reference spreadsheets, NOT recomputed by hand, so these tests
verify our transcription of the formulas matches the spreadsheets exactly:
  - "Copie de Dell1983 v2.xlsx" (sheets "K=1" and "Database Iodine")
  - "N4 calculation_Lu et al 2021.xlsx" (sheet "Sheet1", default example row)
"""
import math
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.dell_model import compute_dell, REGIME_NO_NBO, REGIME_SI_ONLY, REGIME_SI_AND_B, REGIME_INVALID
from core.lu_model import compute_lu, compute_lu_all, VARIANTS


def test_dell_regime4_matches_sheet_K1_row30():
    # "K=1" sheet, row 30: Na2O=2.9, Al2O3=0.1, B2O3=1.9, SiO2=2
    df = pd.DataFrame([{"Na2O": 2.9, "Al2O3": 0.1, "B2O3": 1.9, "SiO2": 2.0}])
    out = compute_dell(df)
    assert out["Dell_R"].iloc[0] == pytest.approx(1.45, abs=1e-9)
    assert out["Dell_K"].iloc[0] == pytest.approx(1.0, abs=1e-9)
    assert out["Dell_N4"].iloc[0] == pytest.approx(0.38749999999999996, abs=1e-9)
    assert out["Dell_regime"].iloc[0] == REGIME_SI_AND_B


@pytest.mark.parametrize(
    "na2o,al2o3,b2o3,sio2,expected_r,expected_n4",
    [
        (0.1, 0.1, 1.9, 2.0, 0.05, 0.05),      # row 2: regime 1, N4=R'
        (0.9, 0.1, 1.9, 2.0, 0.45, 0.45),      # row 10: regime 2, N4=R'
        (1.9, 0.1, 1.9, 2.0, 0.95, 0.5125),    # row 20: regime 4
        (3.9, 0.1, 1.9, 2.0, 1.95, 0.2625),    # row 40: regime 4
        (4.9, 0.1, 1.9, 2.0, 2.45, 0.13749999999999996),  # row 50: regime 4
    ],
)
def test_dell_K1_sheet_rows(na2o, al2o3, b2o3, sio2, expected_r, expected_n4):
    df = pd.DataFrame([{"Na2O": na2o, "Al2O3": al2o3, "B2O3": b2o3, "SiO2": sio2}])
    out = compute_dell(df)
    assert out["Dell_R"].iloc[0] == pytest.approx(expected_r, abs=1e-9)
    assert out["Dell_N4"].iloc[0] == pytest.approx(expected_n4, abs=1e-9)


def test_dell_no_nbo_regime_has_no_nbo():
    df = pd.DataFrame([{"Na2O": 0.1, "Al2O3": 0.1, "B2O3": 1.9, "SiO2": 2.0}])
    out = compute_dell(df)
    assert out["Dell_regime"].iloc[0] == REGIME_NO_NBO
    assert out["Dell_NBO_tot"].iloc[0] == pytest.approx(0.0, abs=1e-9)


def test_dell_database_iodine_ISG11():
    # "Database Iodine" sheet, row 2 (ISG 11): modifiers = Na2O+CaO+K2O
    df = pd.DataFrame([{"SiO2": 59.5, "Al2O3": 4.1, "B2O3": 15.3, "CaO": 5.7, "Na2O": 13.3, "K2O": 0.0}])
    out = compute_dell(df)
    assert out["Dell_R"].iloc[0] == pytest.approx(0.9793814432989691, abs=1e-9)
    assert out["Dell_K"].iloc[0] == pytest.approx(3.0670103092783507, abs=1e-9)
    assert out["Dell_Rmax"].iloc[0] == pytest.approx(0.6916881443298969, abs=1e-9)
    assert out["Dell_RD1"].iloc[0] == pytest.approx(1.2667525773195876, abs=1e-9)
    assert out["Dell_RD3"].iloc[0] == pytest.approx(5.06701030927835, abs=1e-9)
    assert out["Dell_N4"].iloc[0] == pytest.approx(0.6916881443298969, abs=1e-9)
    assert out["Dell_regime"].iloc[0] == REGIME_SI_ONLY


def test_dell_database_iodine_ISG12():
    df = pd.DataFrame([{"SiO2": 59.3, "Al2O3": 4.0, "B2O3": 15.7, "CaO": 5.6, "Na2O": 12.6, "K2O": 0.0}])
    out = compute_dell(df)
    assert out["Dell_R"].iloc[0] == pytest.approx(0.9238578680203046, abs=1e-9)
    assert out["Dell_K"].iloc[0] == pytest.approx(3.010152284263959, abs=1e-9)
    assert out["Dell_N4"].iloc[0] == pytest.approx(0.6881345177664975, abs=1e-9)
    assert out["Dell_regime"].iloc[0] == REGIME_SI_ONLY


def test_dell_beyond_validity_is_nan():
    # R' way past RD3 -> model shouldn't extrapolate
    df = pd.DataFrame([{"Na2O": 20.0, "Al2O3": 0.1, "B2O3": 1.9, "SiO2": 2.0}])
    out = compute_dell(df)
    assert out["Dell_regime"].iloc[0] == REGIME_INVALID
    assert math.isnan(out["Dell_N4"].iloc[0])


def test_dell_nbo_speciation_sums_to_total_and_percentages_sum_to_100():
    df = pd.DataFrame([{"Na2O": 2.9, "Al2O3": 0.1, "B2O3": 1.9, "SiO2": 2.0}])
    out = compute_dell(df)
    row = out.iloc[0]
    assert row["Dell_NBO_SiQ3"] + row["Dell_NBO_SiQ2"] + row["Dell_NBO_B"] == pytest.approx(row["Dell_NBO_tot"], abs=1e-12)
    pct_sum = row["Dell_pct_NBO_SiQ3"] + row["Dell_pct_NBO_SiQ2"] + row["Dell_pct_NBO_B"]
    assert pct_sum == pytest.approx(100.0, abs=1e-9)
    # hand-checked against the "Model Dell" sheet formulas (regime 4 branch)
    assert row["Dell_NBO_SiQ3"] == pytest.approx(0.275193798449612, abs=1e-9)
    assert row["Dell_NBO_SiQ2"] == pytest.approx(0.07838070628768304, abs=1e-9)
    assert row["Dell_NBO_B"] == pytest.approx(0.09646856158484064, abs=1e-9)


def test_dell_custom_formers_and_modifiers():
    # Figure 4.17-style R' = (Na2O+CaO+Bi2O3)/(Al2O3+B2O3)
    df = pd.DataFrame([{"SiO2": 60, "Al2O3": 5, "B2O3": 15, "Na2O": 10, "CaO": 5, "Bi2O3": 5}])
    modifiers = {"Na2O": 1.0, "CaO": 1.0, "Bi2O3": 1.0}
    out = compute_dell(df, modifiers=modifiers)
    assert out["Dell_R"].iloc[0] == pytest.approx(20 / 20, abs=1e-9)
    assert out["Dell_K"].iloc[0] == pytest.approx(60 / 20, abs=1e-9)


LU_EXAMPLE_ROW = {"SiO2": 30.0, "B2O3": 30.0, "Al2O3": 10.0, "CaO": 30.0}


@pytest.mark.parametrize(
    "variant,expected_rmax,expected_n4",
    [
        ("ds_whole", 0.5981428571428571, 0.21428571428571427),
        ("ds_borosilicate", 0.5894285714285714, 0.21428571428571427),
        ("bernstein_whole", 0.4557142857142857, 0.21428571428571427),
        ("bernstein_borosilicate", 0.4557142857142857, 0.21428571428571427),
    ],
)
def test_lu2021_default_example_row(variant, expected_rmax, expected_n4):
    df = pd.DataFrame([LU_EXAMPLE_ROW])
    out = compute_lu(df, variant=variant)
    prefix = f"Lu_{variant}"
    assert out[f"{prefix}_K"].iloc[0] == pytest.approx(0.42857142857142855, abs=1e-9)
    assert out[f"{prefix}_R"].iloc[0] == pytest.approx(0.21428571428571427, abs=1e-9)
    assert out[f"{prefix}_Rmax"].iloc[0] == pytest.approx(expected_rmax, abs=1e-9)
    assert out[f"{prefix}_N4"].iloc[0] == pytest.approx(expected_n4, abs=1e-9)


def test_lu2021_all_variants_together():
    df = pd.DataFrame([LU_EXAMPLE_ROW])
    out = compute_lu_all(df)
    for variant in VARIANTS:
        assert f"Lu_{variant}_N4" in out.columns


def test_lu2021_n4_clamped_to_unit_interval():
    # Extreme R'' should clamp, never go negative or above 1
    df = pd.DataFrame([{"SiO2": 5, "B2O3": 5, "Al2O3": 1, "Na2O": 80}])
    out = compute_lu_all(df)
    for variant in VARIANTS:
        n4 = out[f"Lu_{variant}_N4"].iloc[0]
        assert 0.0 <= n4 <= 1.0
