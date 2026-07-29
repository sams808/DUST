# Models reference

Full formulas, sources, and the calculation-check findings for both
N4 models DUST implements. Code: `core/dell_model.py`, `core/lu_model.py`.
Regression tests pinning every number here to a source value:
`tests/test_models.py` (18 tests).

## 1. Dell (1983) / Du & Stebbins (2005a)

**Sources**: `bib/Dell1983_11B_NMR_glass_modeling.pdf`,
`bib/Du_and_stebbins2005_Network_connectivity_borosilicate_glasses.pdf`,
cross-checked against **"Copie de Dell1983 v2.xlsx"** and
**"Copie de RnKp Dell1983 10-10-2023.xlsx"** (sheet "Model Dell",
byte-identical in both files).

### R' and K' - fully customizable

Unlike a single textbook formula, R' and K' are built from whatever
oxides you tick in the "Formulas / Oxides" tab, each with its own
weight:

    D    = sum(coefficient_i * x_i)   over checked "former" oxides
    K'   = x_SiO2 / D
    R'   = sum(coefficient_i * x_i) / D   over checked "modifier" oxides

Default: formers = {Al2O3: 1, B2O3: 1}; modifiers = alkalis + alkaline
earths, all at weight 1 (Bi2O3 is deliberately not in this default -
its role as an NBO-forming modifier in the Dell/Du-Stebbins sense
isn't settled, see "Bi2O3" below). Any oxide in `core/oxides.py`'s
CANONICAL_OXIDES list - not just alkalis/alkaline earths, but
transition metals, rare earths and actinide oxides too, for complex
multicomponent glasses - can be assigned as a former, a modifier, or
ignored, each with its own coefficient. A few one-click presets are
included (Na2O+CaO+Bi2O3, Na2O only, a Lu-et-al.-2021-style weighted
scheme applied to this model), plus a save/load mechanism for your own
refined formula.

#### Bi2O3

Bismuth is not believed to act as a conventional alkali/alkaline-earth
charge compensator - it can also exist as Bi5+ rather than only Bi3+,
and its impact on network depolymerization is not settled the way the
alkali-derived Dell/Du-Stebbins model's own charge compensators are.
It is available as a modifier (full weight or your own custom weight)
but excluded from the default preset for that reason - include it
deliberately, not by default.

### Regime boundaries

    Rmax = 0.5 + K'/16
    RD1  = 0.5 + K'/4
    RD3  = K' + 2

### N4 (fraction of 4-coordinated boron)

    N4 = R'                                     if R' < Rmax
       = Rmax                                   if Rmax <= R' < RD1
       = Rmax - (R'-RD1)*(8+K')/(12*(2+K'))         if RD1 <= R' < RD3
       = undefined (NaN)                         if R' >= RD3

`RD3` is not an arbitrary cutoff: plugging R'=RD3 into the third
branch gives exactly N4=0 for any K' (verified symbolically) - it's
where the model predicts full depolymerization of the borate network,
so extrapolating past it would go unphysically negative.

### NBO regime classification

Three regimes (colors customizable in the Appearance tab; defaults
white/green/blue below):

| Regime | Condition | Meaning |
|---|---|---|
| "No NBO" | R' < Rmax | fully polymerized network |
| "NBO-Si only (Q3)" | Rmax <= R' < RD1 | NBOs only on SiO4 tetrahedra, forming Q3 |
| "NBO-Si (Q2 & Q3) + NBO-B" | RD1 <= R' < RD3 | NBOs on both SiO4 (Q3 and Q2) and BO3 |
| "Beyond model validity" | R' >= RD3 | outside the model's range; N4 undefined |

### NBO speciation ("percentage of NBO on each species")

Mole fraction of NBO per formula unit, split by which structural unit
carries it:

    U = (R'-RD1)*(8-K')/4/(K'+2)
    V = (R'-RD1)*5*K'/4/(K'+2)

    NBO-Si(Q3) = 2*(R'-Rmax)/(3+2K'+R')            [R' >= Rmax, else 0]
    NBO-Si(Q2) = (2/15)*13*V/(3+2K'+R')            [R' >= RD1, else 0]
    NBO-B      = 4/3*(U + V/5)/(3+2K'+R')          [R' >= RD1, else 0]
    NBO_tot    = NBO-Si(Q3) + NBO-Si(Q2) + NBO-B

    %NBO-Si(Q3) = 100 * NBO-Si(Q3) / NBO_tot   (and likewise for the other two)

These are undefined (NaN) once R' >= RD3 and 0/0 (reported as 0%) when
NBO_tot = 0 (the "No NBO" regime).

### N4-vs-R' region background - derived, not fitted

The N4-vs-R' background (white/green/blue regions) is drawn purely
from R' and N4, independent of any single K' (K' only appears as the
iso-K' guide lines). The two boundary curves are **exact algebraic
identities**, not an empirical fit:

- **"No NBO" / "NBO-Si only" boundary**: at R'=Rmax(K'), both regime
  formulas agree N4 = Rmax(K') = R' - true for *every* K'. So this
  boundary is simply the diagonal **N4 = R'**.
- **"NBO-Si only" / "NBO-Si+NBO-B" boundary**: at the transition point,
  R'=RD1(K')=0.5+K'/4 and N4=Rmax(K')=0.5+K'/16 simultaneously.
  Eliminating K' between those two equations gives
  **N4 = R'/4 + 0.375**.

(`core/dell_model.py:regime_grid` has the full derivation in its
docstring.) These two curves match the ones used in
`EXAMPLES/DYB/DYB.ipynb` - confirmed independently here by algebra
rather than assumed from that notebook.

### Iso-K' guide lines

Each guide line is the real N4(R') shape at that fixed K' - not just
the declining tail: a flat plateau at N4=Rmax(K') from R'=Rmax(K') to
R'=RD1(K') (inside the "NBO-Si only" region), continuing into the
declining segment from (RD1, Rmax) down to (RD3, 0) (inside the
"NBO-Si+NBO-B" region, where the "K'=n" label is placed). The rising
diagonal below R'=Rmax(K') is not drawn separately since it's
identical for every K' - it's already the region boundary itself.

### Displaying Lu et al. (2021) N4 against R' or R''?

All series in the N4-vs-R' plot share the same x-position: Dell's R',
not each series' own R'-equivalent. For the Dell/Du-Stebbins series
that's exactly right by construction. For a Lu et al. (2021) series,
it means the point is plotted at Dell's R' even though its N4 value
was actually computed from Lu's own R'' (a different weighted formula
- see below) - a deliberate choice, not an oversight, because the
background regions and iso-K' lines are inherently defined in terms of
Dell's R'/K', so that's the only x-axis they're meaningful against.
The app flags this on the axis label itself: it reads "R' or R''"
whenever a Lu series is shown, instead of implying the Lu points sit
at their own R''.

## 2. Lu et al. (2021)

**Source**: `N4 calculation_Lu et al 2021.xlsx` (sheet "Sheet1").

Generalized to arbitrary multicomponent oxide glasses - more network
formers and modifiers than the Dell model, each with a *fixed* weight
(not user-editable, unlike the Dell model's formula editor - this
matches exactly what the spreadsheet publishes as the fitted model):

    K'' = x_SiO2 / sum(formerCoeff_i * x_i)
    R'' = (x_Na2O + sum(modifierCoeff_i * x_i)) / sum(formerCoeff_i * x_i)

| Formers | Coeff | Modifiers | Coeff |
|---|---|---|---|
| B2O3 | 1 | Na2O | 1 (base of R'', always included) |
| Al2O3 | 4 | Li2O, K2O, Cs2O, Rb2O | 1 |
| ZrO2 | 3 | CaO, MgO, SrO, BaO, ZnO, PbO | 0.5 |
| P2O5, Fe2O3, TiO2, HfO2 | 0 (present in the sheet, not yet calibrated) | La2O3, Y2O3, Bi2O3 | 1/3 |

Four fit variants, chosen in the Appearance tab's N4-vs-R' data series
list:

**Modified Du & Stebbins** ("ds_whole" / "ds_borosilicate"):

    Rmax = rmax_slope*K'' + rmax_const
    RD   = rd_slope*K''   + rd_const
    N4_raw = R''                                       if R'' <= Rmax
           = Rmax                                        if Rmax < R'' <= RD
           = Rmax - (R''-RD)*(8+K'')/(12*(2+K''))           otherwise

| Variant | rmax_const | rmax_slope | rd_const | rd_slope |
|---|---|---|---|---|
| whole database | 0.59 | 0.019 | 0.096 | 0.502 |
| borosilicate only | 0.58 | 0.022 | 0.256 | 0.459 |

**Modified Bernstein** ("bernstein_whole" / "bernstein_borosilicate"):

    Rmax = rmax_slope*K'' + rmax_const     (rmax_const=0.43, rmax_slope=0.06 for both)
    N4_raw = R''                                        if R'' < Rmax
           = a*(b+R'')*(c - R''/(d+e*K''))^5              otherwise

| Variant | a | b | c | d | e |
|---|---|---|---|---|---|
| whole database | 0.25 | 0.29 | 1.3 | 3.78 | 1.0 |
| borosilicate only | 0.71 | 0.4 | 1.03 | 5.47 | 1.19 |

All 4 variants clamp `N4_raw` to `[0, 1]` (matching the spreadsheet's
`IF(N<1, IF(N>0, N, 0), 1)` exactly).

This model reports **N4 only** - the spreadsheet has no NBO-Si/NBO-B
speciation breakdown, so DUST's %NBO-species columns are Dell-model-only.

## Calculation check

Both source spreadsheets were checked against the published papers
they implement, not just transcribed blindly:

- `Copie de Dell1983 v2.xlsx` and `Copie de RnKp Dell1983 10-10-2023.xlsx`
  have a **byte-identical** "Model Dell" sheet.
- Every regime boundary and NBO formula matches the published
  regime-boundary definitions and the Du & Stebbins (2005a) paper.
- The spreadsheet's 4-branch `IF` classification ladder (R'<=0.5 /
  0.5<R'<Rmax / Rmax<=R'<RD1 / RD1<=R'<RD3) has no gaps or overlaps;
  R'<=0.5 always falls under R'<Rmax too (since Rmax>=0.5 for K'>=0),
  so DUST's simplified 2-way test (`R' < Rmax`) is provably equivalent,
  not a shortcut that changes behavior.
- NBO speciation formulas were independently re-derived with exact
  fraction arithmetic (Python `fractions.Fraction`, zero floating-point
  rounding) and matched the app's output to 15 significant figures.
- The Lu et al. 2021 spreadsheet's default worked example (SiO2=30,
  B2O3=30, Al2O3=10, CaO=30 mol%) reproduces K''=0.42857142857142855,
  R''=0.21428571428571427, and every variant's Rmax/RD/N4 to full
  float precision.

**No calculation errors were found in either spreadsheet** - both are
correct, internally consistent implementations of their respective
published models. The 18 tests in `tests/test_models.py` pin these
reference values so future edits to the code can't silently drift from
them.
