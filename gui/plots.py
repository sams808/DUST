"""
Matplotlib rendering for the two thesis-style figures:

  Fig A ("4.17-style"): K' vs R', background = Dell/Du-Stebbins N4(K',R')
         heatmap, data points overlaid.
  Fig B ("5.7-style"):   N4 vs R', background = 3 NBO-regime bands
         (No NBO / NBO-Si only / NBO-Si+NBO-B), iso-K' guide lines,
         data points overlaid (any combination of Dell and/or Lu et al.
         2021 model N4 series, so the user can compare predictions).

Both take a plain dataclass config so every visual choice (colors,
limits, labels, markers, fonts...) is a single field the GUI can bind
a widget to - "full customization" without hardcoding a look.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from core.dell_model import n4_grid, regime_grid


@dataclass
class SeriesStyle:
    column: str          # column in the working DataFrame holding N4 (or y) values
    label: str
    color: str = "black"
    marker: str = "o"
    size: float = 60.0
    edgecolor: str = "black"
    alpha: float = 1.0
    visible: bool = True


@dataclass
class FigAConfig:
    title: str = "K' vs R'"
    xlabel: str = "R'"
    ylabel: str = "K'"
    r_min: float = 0.0
    r_max: float = 5.0
    k_min: float = 0.0
    k_max: float = 6.0
    resolution: int = 250
    colormap: str = "viridis"
    show_colorbar: bool = True
    colorbar_label: str = "N$_4$"
    point_color_by: str | None = None   # column name, or None for flat color
    point_color: str = "black"
    point_size: float = 120.0
    point_marker: str = "+"
    point_edgecolor: str = "black"
    label_column: str | None = None     # optional per-point text labels
    show_legend: bool = False
    show_grid: bool = False
    font_size: float = 11.0


@dataclass
class FigBConfig:
    title: str = "N$_4$ vs R'"
    xlabel: str = "R'"
    ylabel: str = "N$_4$"
    r_min: float = 0.0
    r_max: float = 5.5
    n4_min: float = 0.0
    n4_max: float = 1.0
    resolution: int = 400
    region_colors: dict = field(default_factory=lambda: {
        1: "white", 2: "palegreen", 3: "cornflowerblue",
    })
    region_alpha: float = 0.45
    region_labels: dict = field(default_factory=lambda: {
        1: "No NBO", 2: "NBO-Si only (Q$^3$)", 3: "NBO-Si (Q$^2$&Q$^3$) + NBO-B",
    })
    show_region_legend: bool = True
    iso_k_values: tuple = (2, 3, 4, 5, 6, 7, 8)
    show_iso_k: bool = True
    iso_k_color: str = "black"
    iso_k_linewidth: float = 0.6
    series: list = field(default_factory=list)  # list[SeriesStyle]
    show_legend: bool = True
    show_grid: bool = False
    font_size: float = 11.0


def draw_fig_a(fig, df: pd.DataFrame, config: FigAConfig):
    # fig.clear() (not ax.clear()) so colorbar axes from the previous draw
    # are actually removed instead of accumulating on every redraw.
    fig.clear()
    ax = fig.add_subplot(111)
    k_values = np.linspace(config.k_min, config.k_max, config.resolution)
    r_values = np.linspace(config.r_min, config.r_max, config.resolution)
    n4 = n4_grid(k_values, r_values)

    mesh = ax.pcolormesh(r_values, k_values, n4, shading="auto", cmap=config.colormap,
                          vmin=0, vmax=1)
    if config.show_colorbar:
        cb = fig.colorbar(mesh, ax=ax)
        cb.set_label(config.colorbar_label, fontsize=config.font_size)

    if df is not None and len(df) and "Dell_R" in df.columns and "Dell_K" in df.columns:
        x = df["Dell_R"].to_numpy()
        y = df["Dell_K"].to_numpy()
        c = None
        if config.point_color_by and config.point_color_by in df.columns:
            c = df[config.point_color_by].to_numpy()
        sc = ax.scatter(
            x, y, c=c if c is not None else config.point_color,
            cmap=config.colormap if c is not None else None,
            s=config.point_size, marker=config.point_marker,
            edgecolors=config.point_edgecolor, linewidths=1.2,
        )
        if c is not None:
            cb2 = fig.colorbar(sc, ax=ax, pad=0.12)
            cb2.set_label(config.point_color_by, fontsize=config.font_size)
        if config.label_column and config.label_column in df.columns:
            for xi, yi, lbl in zip(x, y, df[config.label_column]):
                if pd.notna(xi) and pd.notna(yi) and pd.notna(lbl):
                    ax.annotate(str(lbl), (xi, yi), textcoords="offset points",
                                xytext=(6, 4), fontsize=config.font_size * 0.8)

    ax.set_xlabel(config.xlabel, fontsize=config.font_size)
    ax.set_ylabel(config.ylabel, fontsize=config.font_size)
    ax.set_title(config.title, fontsize=config.font_size * 1.1)
    ax.set_xlim(config.r_min, config.r_max)
    ax.set_ylim(config.k_min, config.k_max)
    ax.tick_params(labelsize=config.font_size * 0.9)
    if config.show_grid:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    return ax


def draw_fig_b(fig, df: pd.DataFrame, config: FigBConfig):
    fig.clear()
    ax = fig.add_subplot(111)
    r_values = np.linspace(max(config.r_min, 1e-6), config.r_max, config.resolution)
    n4_values = np.linspace(config.n4_min, config.n4_max, config.resolution)
    codes = regime_grid(r_values, n4_values)

    from matplotlib.colors import ListedColormap, BoundaryNorm
    cmap = ListedColormap([config.region_colors.get(i, "white") for i in (1, 2, 3)])
    norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5], cmap.N)
    ax.contourf(r_values, n4_values, codes, levels=[0.5, 1.5, 2.5, 3.5],
                cmap=cmap, norm=norm, alpha=config.region_alpha)
    # hatch the Q3-only band to match the thesis figure's texture
    ax.contourf(r_values, n4_values, codes, levels=[1.5, 2.5], colors="none",
                hatches=["//"], alpha=0)

    if config.show_iso_k:
        # Each iso-K' guide is the FULL N4(R') curve at fixed K' - rising
        # diagonal (N4=R', regime "No NBO"), flat plateau at Rmax (regime
        # "NBO-Si only"), then declining to 0 at RD3 (regime "NBO-Si+B") -
        # not just the declining tail. This is what the source figure
        # plots (and what EXAMPLES/DYB/DYB.ipynb draws as N4_values[idx, :]
        # for each fixed K row): the rising/flat parts of low-K' lines are
        # what make the whole fan of lines start near the origin instead
        # of appearing to begin partway across the plot.
        r_grid = np.linspace(max(config.r_min, 0.0), config.r_max, 400)
        for k in config.iso_k_values:
            rmax = 0.5 + k / 16.0
            rd1 = 0.5 + k / 4.0
            rd3 = k + 2.0
            n4_curve = np.where(
                r_grid < rmax, r_grid,
                np.where(r_grid < rd1, rmax,
                         np.where(r_grid < rd3,
                                  rmax - (r_grid - rd1) * (8 + k) / (12 * (2 + k)),
                                  np.nan)),
            )
            ax.plot(r_grid, n4_curve, color=config.iso_k_color, linewidth=config.iso_k_linewidth)

            # Label where the curve exits the visible axes - along the
            # right edge (R'=r_max) if it's still above n4_min there
            # (matches the source figure's stacked right-edge labels for
            # higher K'); at its own endpoint (RD3, 0) if it fully
            # depolymerizes before reaching r_max (lower K'); otherwise
            # wherever it crosses n4_min first, if that's tighter than both.
            if config.r_max < rd3:
                exit_r = config.r_max
                n4_at_exit = (
                    config.r_max if config.r_max < rmax
                    else rmax if config.r_max < rd1
                    else rmax - (config.r_max - rd1) * (8 + k) / (12 * (2 + k))
                )
            else:
                exit_r, n4_at_exit = rd3, 0.0  # curve ends here, not projected out to r_max
            if n4_at_exit >= config.n4_min:
                label_r, label_n4 = exit_r, n4_at_exit
            elif config.r_max > rd1:
                label_r = min(rd1 + (rmax - config.n4_min) * 12 * (2 + k) / (8 + k), rd3)
                label_n4 = config.n4_min
            else:
                continue  # this K' line never enters the visible (R', N4) window
            if label_n4 > config.n4_max:
                continue
            ax.annotate(f"K'={k:g}", (label_r, label_n4), fontsize=config.font_size * 0.75,
                        color=config.iso_k_color, alpha=0.9,
                        xytext=(-4, 4), textcoords="offset points", ha="right", va="bottom")

    if df is not None and len(df):
        x = df.get("Dell_R")
        for s in config.series:
            if not s.visible or s.column not in df.columns:
                continue
            y = df[s.column]
            ax.scatter(x, y, label=s.label, color=s.color, marker=s.marker,
                       s=s.size, edgecolors=s.edgecolor, alpha=s.alpha, zorder=5)

    if config.show_region_legend:
        from matplotlib.patches import Patch
        handles = [Patch(facecolor=config.region_colors.get(i, "white"),
                          alpha=config.region_alpha, label=config.region_labels.get(i, ""))
                   for i in (1, 2, 3)]
        # "lower right" collides with the iso-K' labels stacked along the
        # bottom/right edges (that's where low-K' lines exit the axes) -
        # "upper right" sits in the otherwise-empty top corner instead.
        leg1 = ax.legend(handles=handles, loc="upper right", fontsize=config.font_size * 0.75,
                          framealpha=0.9)
        ax.add_artist(leg1)

    if config.show_legend and config.series:
        ax.legend(loc="upper left", fontsize=config.font_size * 0.8)

    ax.set_xlabel(config.xlabel, fontsize=config.font_size)
    ax.set_ylabel(config.ylabel, fontsize=config.font_size)
    ax.set_title(config.title, fontsize=config.font_size * 1.1)
    ax.set_xlim(config.r_min, config.r_max)
    ax.set_ylim(config.n4_min, config.n4_max)
    ax.tick_params(labelsize=config.font_size * 0.9)
    if config.show_grid:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    return ax
