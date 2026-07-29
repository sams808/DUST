# Customization reference

Field-by-field reference for the "Formulas / Oxides" and "Appearance"
tabs. Everything here updates both figures immediately - there is
nothing to "apply".

## R'/K' formula editor

*(Tab: "Formulas / Oxides")*

The Dell/Du-Stebbins model's R' and K' are built from one table you
control directly - not a hardcoded formula, and not limited to a
pre-picked list of "former" vs. "modifier" oxides:

```
K' = SiO2 / D            where D = sum(coefficient * value) over oxides set to Former
R' = M / D                where M = sum(coefficient * value) over oxides set to Modifier
```

Every oxide DUST recognizes (the full list in `core/oxides.py` -
covers common network formers/modifiers plus transition metals, rare
earths and actinide oxides relevant to complex multicomponent glasses)
gets one row with:

- **Oxide** - fixed label, not editable.
- **Role** - `Ignore` / `Former` / `Modifier`. SiO2 itself never
  appears here - it's always the fixed K' numerator.
- **Coefficient** - the weight it contributes with (0-20, 6 decimal
  places - enough for exact thirds like Lu et al. 2021's 1/3).

Nothing restricts an oxide to one role - assign any oxide to Former,
Modifier, or leave it at Ignore, however your own charge-balancing
scheme works.

### Presets

| Preset | Formers | Modifiers |
|---|---|---|
| Dell defaults | Al2O3, B2O3 (x1 each) | Na2O, Li2O, K2O, Cs2O, Rb2O, CaO, MgO, SrO, BaO (x1 each) |
| Simple (Na2O + CaO only) | Al2O3, B2O3 (x1) | Na2O, CaO (x1) |
| Na2O + CaO + Bi2O3 | Al2O3, B2O3 (x1) | Na2O, CaO, Bi2O3 (x1) |
| Na2O only | Al2O3, B2O3 (x1) | Na2O (x1) |
| Lu et al. 2021 weighting scheme | B2O3 x1, Al2O3 x4, ZrO2 x3 | Na2O x1, alkalis x1, alkaline earths x0.5, La2O3/Y2O3/Bi2O3 x1/3 |

Note Bi2O3 is not part of the Dell-defaults preset - its role as an
NBO-forming modifier in the Dell/Du-Stebbins sense isn't settled (see
docs/MODELS_REFERENCE.md), so it's opt-in rather than assumed.

Picking a preset sets every oxide's role/coefficient at once. Editing
any single row afterward flips the dropdown to **"(custom)"** - your
edit is never silently reverted.

### Save / load your own formula

**Save formula...** writes the current role assignments as a small
JSON file (two dicts - one per role that has any oxides in it):

```json
{
  "formers": {"Al2O3": 1.0, "B2O3": 1.0},
  "modifiers": {"Na2O": 1.0, "CaO": 1.0, "Bi2O3": 1.0}
}
```

**Load formula...** reads one back. This is the mechanism for a
formula you've refined for your own compositions - save it once,
reload it in any future session, or share the `.json` with a labmate
so they use your exact definition.

**Reset to Dell defaults** is a shortcut equivalent to picking the
"Dell defaults" preset.

> The Lu et al. (2021) model's own R''/K'' weighting is fixed to the
> published fit (see [MODELS_REFERENCE.md](MODELS_REFERENCE.md#2-lu-et-al-2021))
> and is **not** affected by this editor. Any oxide outside that fit's
> coefficient table is simply excluded from R''/K'' rather than
> raising an error.

## Appearance tab

### K' vs R'

| Field | Effect |
|---|---|
| Title | Plot title text |
| Colormap | Background N4 heatmap + (if used) point color-by scale. Any matplotlib-named colormap: viridis, plasma, magma, cividis, YlGnBu, coolwarm |
| R' range / K' range | Axis limits (also controls the resolution grid extent) |
| Color points by | `(single color)` or any numeric column currently in your data (oxide mol%, R', K', N4 from any model, %NBO columns...) - draws a second colorbar when active |
| Point color | Flat color used when "Color points by" is `(single color)` |
| Point size | Marker area |
| Point marker | `+ o s ^ x D v` |
| Point labels | `(none)` or `Sample` - draws the label next to each point, automatically repositioned (with a thin leader line) to avoid overlapping nearby labels |
| Show colorbar | Toggles the background N4 colorbar |
| Show grid | Toggles axis gridlines |

### N4 vs R' - regions and lines

| Field | Effect |
|---|---|
| Title | Plot title text |
| R' range / N4 range | Axis limits |
| Iso-K' values | Comma-separated list, e.g. `2, 3, 4, 5, 6, 7, 8` - draws and labels one guide line per value |
| Show iso-K' lines | Toggle |
| Show regime legend | Toggle the region-color legend box |
| Region color: No NBO / NBO-Si only (Q3) / NBO-Si (Q2&Q3)+NBO-B | Click each swatch to recolor that regime's background fill |
| Show grid | Toggle axis gridlines |

### N4 vs R' - data series table

One row per available N4 series - Dell/Du-Stebbins plus the 4 Lu et
al. (2021) variants:

| Column | Effect |
|---|---|
| Show | Whether this series is plotted at all - tick multiple to overlay/compare models |
| Model | Fixed label (Dell / Du-Stebbins, Lu 2021 - DS whole, etc.) |
| Color | Click the swatch to open a color picker |
| Marker | `o s ^ D v x +` |

All series share the same x-axis position (Dell's R'), because the
background regions and iso-K' lines are inherently defined in terms of
that R'. When any Lu et al. (2021) series is shown, the axis label
switches from "R'" to "R' or R''" as a reminder that a Lu-series
point's x-position is Dell's R', not the R'' that actually fed its own
N4 - see [MODELS_REFERENCE.md](MODELS_REFERENCE.md) for the full
reasoning.

## Exporting figures

Each figure tab has its own **Export DPI** spinner (72-1200) and
**Export figure...** button, saving PNG/PDF/SVG at your chosen
resolution via a file dialog - independent of the matplotlib
toolbar's own quick-save icon, which always uses a fixed default.
