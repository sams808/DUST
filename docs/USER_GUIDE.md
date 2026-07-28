# DUST user guide

The window is split in two: **left** is data + settings (4 tabs),
**right** is the two figures (2 tabs). Everything on the left updates
both figures live - there's no separate "plot" button.

## 1. The "Data" tab

An editable spreadsheet of glass compositions, in **mol%** oxide
columns plus two free-text columns:

| Column | Meaning |
|---|---|
| `Sample` | Point label, usable for on-plot annotation |
| `Label` | A second free-text field (e.g. reference/source) |
| oxide columns | mol% composition (`SiO2`, `Al2O3`, `B2O3`, `Na2O`, ...) |

Buttons along the top:

- **Add row** - appends a blank row (oxides default to 0).
- **Delete selected rows** - select cells/rows first (click a row
  number, or drag across cells), then delete.
- **Import CSV...** - see [CSV_IMPORT.md](CSV_IMPORT.md) for the full
  format/mapping guide. Short version: pick a file, confirm the column
  mapping DUST guesses, optionally check "convert wt% to mol%", and the
  rows are appended to whatever's already in the table.
- **Export CSV...** - saves the raw table (not the computed columns -
  use "Export results CSV..." on the Results tab for those).
- **Add oxide column...** - the table starts with the 10 most common
  oxides (SiO2, Al2O3, B2O3, Na2O, Li2O, K2O, CaO, MgO, BaO, Bi2O3);
  pick any other oxide from the canonical list to add its column.
  Right-click a column header and choose "Remove this oxide column" to
  drop one you don't need.

The app ships with 6 example rows loaded at startup (from
`sample_data/example_glasses.csv`) spanning all three NBO regimes, so
you always have something to look at immediately - just delete them
once you're working with your own data.

Missing/blank oxide cells are treated as 0, not as "unknown" - leave
oxides you don't have out or at 0.

## 2. The "Results" tab

A read-only view of every computed column for the current table:
R'/K' (Dell), NBO regime, N4 (Dell), the 3 %NBO-species columns, and
N4 from all 4 Lu et al. (2021) variants. This is the fastest way to
read off numbers without hovering over plot points. **"Export results
CSV..."** saves this - plus every other computed column not shown in
the table (Rmax/RD1/RD3/NBO mole fractions, R''/K'' for each Lu
variant, etc.) - to a CSV.

## 3. The "Formulas / Oxides" tab

Controls what R' and K' *mean* for the Dell/Du-Stebbins model - fully
editable, not fixed to one textbook definition. See
[CUSTOMIZATION.md](CUSTOMIZATION.md#rk-formula-editor) for the full
reference; short version:

- Two tables, **Formers** and **Modifiers** - each oxide has a
  checkbox (include/exclude) and a coefficient (weight).
  `K' = SiO2 / (checked formers, weighted sum)`,
  `R' = (checked modifiers, weighted sum) / (checked formers, weighted sum)`.
- **Preset** dropdown jumps to a few common starting points (Dell
  defaults, a bare-bones Na2O+CaO formula, the exact formulas behind
  thesis Figs 4.17 and 5.7, or the Lu et al. 2021 weighting scheme
  applied to this model). Editing any checkbox/coefficient after
  picking a preset switches the dropdown to "(custom)".
- **Save formula... / Load formula...** write/read the current
  formers+modifiers as JSON, so your own refined formula persists
  across sessions - hand a `.json` file to a labmate and they get your
  exact definition.
- **Reset to Dell defaults** - one click back to alkalis + alkaline
  earths + Bi2O3 over Al2O3+B2O3.

The Lu et al. (2021) model's own K''/R'' weighting is fixed to the
published fit (shown for reference at the bottom of this tab) and is
not affected by this editor - only the Dell/Du-Stebbins model's R'/K'
are customizable this way.

## 4. The "Appearance" tab

Every visual choice for both figures. See
[CUSTOMIZATION.md](CUSTOMIZATION.md) for the full field-by-field
reference. Grouped as:

- **Fig 4.17-style (K' vs R')**: title, colormap, R'/K' axis ranges,
  what column colors the data points (any numeric column, or a single
  flat color), point size/marker, optional point labels (from
  `Sample`), colorbar/grid toggles.
- **Fig 5.7-style (N4 vs R') - data series**: title, R'/N4 axis
  ranges, which iso-K' guide lines to draw, regime-legend/grid
  toggles, and a **per-model series table** - a Show checkbox, color,
  and marker for each of Dell/Du-Stebbins and the 4 Lu et al. (2021)
  variants. Tick more than one to overlay several models' N4
  predictions on the same axes for direct comparison.

Every change redraws both figures immediately.

## 5. The figure tabs

**"Fig 4.17-style: K' vs R'"** and **"Fig 5.7-style: N4 vs R'"**, each
with:

- The standard matplotlib toolbar (home/pan/zoom/save icon row) - use
  it to pan/zoom interactively or do a quick "save" via the disk icon.
- **Export DPI** + **Export figure...** - the app's own export, which
  respects your chosen DPI and lets you pick PNG/PDF/SVG. Prefer this
  over the toolbar's save icon for anything going into a manuscript.

## Typical workflows

**"I just want to drop my thesis data in and see where it falls"**
Data tab -> Import CSV (or type rows by hand) -> look at both figure
tabs. Defaults already match Fig 4.17/5.7's own R' definition family.

**"I want to compare Dell/Du-Stebbins vs. Lu et al. 2021 for my glasses"**
Appearance tab -> in the Fig 5.7-style series table, tick "Dell /
Du-Stebbins" and whichever Lu variant(s) you want -> switch to the Fig
5.7-style tab.

**"I use a different R' definition than the thesis"**
Formulas / Oxides tab -> either pick the closest preset and tweak it,
or start from "Reset to Dell defaults" and check/uncheck oxides and
edit their coefficients directly -> Save formula... once it's right,
so you don't have to redo it next time.

**"I need a publication-ready figure"**
Set everything up on the Appearance tab (colors, ranges, labels,
which series/regions to show) -> figure tab -> set Export DPI (300+
for print) -> Export figure... as PDF or SVG for vector output, PNG
for raster.
