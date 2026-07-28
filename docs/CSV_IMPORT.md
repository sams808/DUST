# CSV import

*(Data tab -> "Import CSV...")*. Code: `core/io.py`.

## What it handles automatically

- **Delimiter**: comma, semicolon, or tab, auto-detected per file
  (handles files like `EXAMPLES/DYB/Si50P0-Bi0.csv`, which uses `;`).
- **Header matching**: column names are normalized before matching -
  case, surrounding whitespace, unit suffixes (`"Na2O (mol%)"`,
  `"Na2O_wt%"`, `"SiO2 mol %"`), and unicode subscripts (`Na₂O`) are
  all recognized as the plain oxide name.
- **BOM-safe reading**: files saved with a UTF-8 byte-order mark
  (common from Excel's "CSV UTF-8" export) are read correctly.

## The mapping dialog

After picking a file, DUST shows every column with a dropdown,
pre-filled with its best guess:

- **Ignore** - column is dropped.
- **Sample** / **Label** - kept as free text (for point
  labels/grouping), not parsed as a number.
- Any of the 22 canonical oxides - imported as mol% composition data.

Nothing imports silently without you seeing this dialog first, and
you can override any guess before confirming.

## wt% -> mol% conversion

If your CSV is in weight percent, check **"Values are wt% - convert
to mol% on import"** in the mapping dialog. Conversion uses standard
molar masses (`core/oxides.py:MOLAR_MASS`) and renormalizes each row
to sum to 100 mol% over the mapped oxide columns only - non-oxide
columns (Sample, Label) pass through unchanged.

## What happens on import

- New rows are **appended** to whatever's already in the table (import
  multiple files in a row to combine them).
- If your CSV has an oxide column DUST's table doesn't currently show
  (e.g. you import a `ZrO2` column for the first time), that column is
  added automatically - no need to "Add oxide column..." first.
- A confirmation dialog reports how many rows were imported.

## Column reference

Recognized oxide names (any capitalization/spacing/unit-suffix
variant of these): `SiO2, B2O3, Al2O3, P2O5, Fe2O3, TiO2, ZrO2, HfO2,
Na2O, Li2O, K2O, Cs2O, Rb2O, CaO, MgO, SrO, BaO, ZnO, PbO, La2O3, Y2O3,
Bi2O3`.

## Exporting

- **Data tab -> Export CSV...**: the raw table exactly as entered/imported.
- **Results tab -> Export results CSV...**: every computed column
  (R'/K', regime, N4 per model, %NBO per species, and the underlying
  Rmax/RD1/RD3/R''/K'' intermediates) alongside your original data -
  useful for further analysis outside DUST or for a supplementary
  data table in a paper.
