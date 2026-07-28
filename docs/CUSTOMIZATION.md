# Customization reference

Field-by-field reference for the "Formulas / Oxides" and "Appearance"
tabs. Everything here updates both figures immediately - there is
nothing to "apply".

## R'/K' formula editor

*(Tab: "Formulas / Oxides")*

The Dell/Du-Stebbins model's R' and K' are built from two tables you
control directly - not a hardcoded formula:

```
K' = SiO2 / D            where D = sum(coefficient * value) over checked Formers
R' = M / D                where M = sum(coefficient * value) over checked Modifiers
```

Each row in the **Formers** and **Modifiers** tables has:

- **Include** checkbox - whether this oxide contributes at all.
- **Oxide** - fixed label, not editable.
- **Coefficient** - the weight it contributes with (0-20, 6 decimal
  places - enough for exact thirds like Lu et al. 2021's 1/3).

Formers candidates: Al2O3, B2O3, P2O5, Fe2O3, TiO2, ZrO2, HfO2 (SiO2 is
never a candidate here - it's always the fixed K' numerator).
Modifiers candidates: all alkalis, alkaline earths, and Bi2O3/La2O3/Y2O3.

### Presets

| Preset | Formers | Modifiers |
|---|---|---|
| Dell defaults | Al2O3, B2O3 (x1 each) | Na2O, Li2O, K2O, Cs2O, Rb2O, CaO, MgO, SrO, BaO, Bi2O3 (x1 each) |
| Simple (Na2O + CaO only) | Al2O3, B2O3 (x1) | Na2O, CaO (x1) |
| Thesis Fig 4.17 | Al2O3, B2O3 (x1) | Na2O, CaO, Bi2O3 (x1) |
| Thesis Fig 5.7 | Al2O3, B2O3 (x1) | Na2O (x1) |
| Lu et al. 2021 weighting scheme | B2O3 x1, Al2O3 x4, ZrO2 x3 | Na2O x1, alkalis x1, alkaline earths x0.5, La2O3/Y2O3/Bi2O3 x1/3 |

Picking a preset overwrites both tables. Editing any single
checkbox/coefficient afterward flips the dropdown to **"(custom)"** -
your edit is never silently reverted.

### Save / load your own formula

**Save formula...** writes the current Formers+Modifiers as a small
JSON file:

```json
{
  "formers": {"Al2O3": 1.0, "B2O3": 1.0},
  "modifiers": {"Na2O": 1.0, "CaO": 1.0, "Bi2O3": 1.0}
}
```

**Load formula...** reads one back. This is the mechanism for a
formula you refined for your own thesis/paper - save it once, reload
it in any future session, or share the `.json` with a labmate so they
use your exact definition.

**Reset to Dell defaults** is a shortcut equivalent to picking the
"Dell defaults" preset.

> The Lu et al. (2021) model's own R''/K'' weighting is fixed to the
> published fit (see [MODELS_REFERENCE.md](MODELS_REFERENCE.md#2-lu-et-al-2021))
> and is **not** affected by this editor.

## Appearance tab

### Fig 4.17-style (K' vs R')

| Field | Effect |
|---|---|
| Title | Plot title text |
| Colormap | Background N4 heatmap + (if used) point color-by scale. Any matplotlib-named colormap: viridis, plasma, magma, cividis, YlGnBu, coolwarm |
| R' range / K' range | Axis limits (also controls the resolution grid extent) |
| Color points by | `(single color)` or any numeric column currently in your data (oxide mol%, R', K', N4 from any model, %NBO columns...) - draws a second colorbar when active |
| Point color | Flat color used when "Color points by" is `(single color)` |
| Point size | Marker area |
| Point marker | `+ o s ^ x D v` |
| Point labels | `(none)` or `Sample` - draws the label as small text next to each point |
| Show colorbar | Toggles the background N4 colorbar |
| Show grid | Toggles axis gridlines |

### Fig 5.7-style (N4 vs R') - background & lines

| Field | Effect |
|---|---|
| Title | Plot title text |
| R' range / N4 range | Axis limits |
| Iso-K' values | Comma-separated list, e.g. `2, 3, 4, 5, 6, 7, 8` - draws and labels one guide line per value |
| Show iso-K' lines | Toggle |
| Show regime legend | Toggle the white/green/blue region legend box |
| Show grid | Toggle axis gridlines |

### Fig 5.7-style - data series table

One row per available N4 series - Dell/Du-Stebbins plus the 4 Lu et
al. (2021) variants:

| Column | Effect |
|---|---|
| Show | Whether this series is plotted at all - tick multiple to overlay/compare models |
| Model | Fixed label (Dell / Du-Stebbins, Lu 2021 - DS whole, etc.) |
| Color | Click the swatch to open a color picker |
| Marker | `o s ^ D v x +` |

All series share the same x-axis (Dell's R') - see
[MODELS_REFERENCE.md](MODELS_REFERENCE.md) for why: the background
regions and iso-K' lines are inherently defined in terms of the
Dell/Du-Stebbins R', and the thesis figure itself plots other models'
N4 against that same R' for direct comparison.

## Exporting figures

Each figure tab has its own **Export DPI** spinner (72-1200) and
**Export figure...** button, saving PNG/PDF/SVG at your chosen
resolution via a file dialog - independent of the matplotlib
toolbar's own quick-save icon, which always uses a fixed default.
