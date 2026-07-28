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
    # Set limits now (not at the end) so ax.transData is correct below when
    # computing on-screen line angles for the iso-K' labels.
    ax.set_xlim(config.r_min, config.r_max)
    ax.set_ylim(config.n4_min, config.n4_max)
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
        # The source figure only draws each iso-K' guide over the range
        # where it is actually informative about the NBO-Si+B regime: the
        # declining segment from (RD1, Rmax) to (RD3, 0) - confined to the
        # blue region. It does NOT extend the rising/flat portions into
        # the green/white regions (those would be redundant anyway: every
        # K's rising segment sits exactly on the same N4=R' diagonal).
        for k in config.iso_k_values:
            rmax = 0.5 + k / 16.0
            rd1 = 0.5 + k / 4.0
            rd3 = k + 2.0
            if rd1 > config.r_max or rd1 >= rd3:
                continue  # this K' line's blue-region segment isn't visible at all

            r_end = min(rd3, config.r_max)
            r_line = np.linspace(rd1, r_end, 100)
            n4_line = rmax - (r_line - rd1) * (8 + k) / (12 * (2 + k))
            # Bound by both axis edges - rmax can exceed n4_max for large
            # K' (e.g. K'>8 pushes Rmax=0.5+K'/16 above 1.0), in which case
            # the line starts above the visible window entirely.
            visible = (n4_line >= config.n4_min) & (n4_line <= config.n4_max)
            if not visible.any():
                continue
            r_line, n4_line = r_line[visible], n4_line[visible]
            ax.plot(r_line, n4_line, color=config.iso_k_color, linewidth=config.iso_k_linewidth)

            # Place the label ON the line, a bit before its visible end,
            # rotated to follow the line's on-screen angle (not the data
            # slope - the R'/N4 axes have very different scales, so those
            # differ) so it reads like a tilted inline label, matching the
            # source figure, instead of floating disconnected in a corner.
            # Skip the label (keep the line) if the visible stretch is too
            # short to anchor readable rotated text to, e.g. a line barely
            # clipping the corner of a zoomed-in axis range.
            span_r = r_line[-1] - r_line[0]
            if span_r < 0.05 * (config.r_max - config.r_min):
                continue
            t = 0.85
            label_r = r_line[0] + t * span_r
            label_n4 = n4_line[0] + t * (n4_line[-1] - n4_line[0])
            p0 = ax.transData.transform((r_line[0], n4_line[0]))
            p1 = ax.transData.transform((r_line[-1], n4_line[-1]))
            angle = np.degrees(np.arctan2(p1[1] - p0[1], p1[0] - p0[0]))
            ax.text(label_r, label_n4, f"K'={k:g}", fontsize=config.font_size * 0.75,
                    color=config.iso_k_color, alpha=0.95, rotation=angle,
                    ha="center", va="center", rotation_mode="anchor",
                    bbox=dict(boxstyle="round,pad=0.05", facecolor="white",
                              edgecolor="none", alpha=0.6))

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
    ax.tick_params(labelsize=config.font_size * 0.9)
    if config.show_grid:
        ax.grid(alpha=0.3)
    fig.tight_layout()
    return ax
