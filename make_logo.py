"""
make_logo.py -- generates DUST's brand assets into assets/:
  dust_logo.png   (512x512, window/taskbar icon source)
  dust_splash.png (720x420, startup splash)
  dust.ico        (multi-size Windows icon, for the exe + title bar)

Design: a tetrahedral network unit (the SiO4/BO4 coordination the app's
N4 calculations are all about) with one edge coming apart into drifting
"dust" motes -- a network former breaking into a non-bridging oxygen as
a modifier cation moves in. Also a quiet nod to the two names DUST is
named after (Du & Stebbins) and to "R'"/"K'" as fine, drifting grains
of composition data. Regenerate any time: python make_logo.py
"""
from __future__ import annotations

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch

ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")

INK = "#161a23"          # dark charcoal-navy background
EDGE = "#2dd4bf"          # teal - intact network bonds
EDGE_BREAK = "#3a4658"    # faded slate - the one bond coming apart
NODE = "#67e8d4"          # bright teal - former nodes (Si/B)
NODE_CENTER = "#f8fafc"   # near-white - the front/center coordinating node
DUST = "#f5b942"          # warm amber - drifting modifier "dust"
DUST_SOFT = "#fbd487"

# Tetrahedron vertices (2D projection: apex, two back-base, one front-base)
APEX = (5.0, 8.15)
BACK_L = (2.35, 3.35)
BACK_R = (7.65, 3.35)
FRONT = (5.15, 1.55)

EDGES_INTACT = [(APEX, BACK_L), (APEX, BACK_R), (APEX, FRONT), (BACK_L, BACK_R), (BACK_L, FRONT)]
EDGE_BROKEN = (BACK_R, FRONT)

DUST_MOTES = [
    # (x, y, radius, color, alpha)
    (8.55, 2.55, 0.34, DUST, 0.95),
    (9.35, 3.15, 0.22, DUST_SOFT, 0.9),
    (9.75, 1.95, 0.16, DUST, 0.75),
    (8.95, 1.35, 0.13, DUST_SOFT, 0.7),
    (9.55, 4.05, 0.11, DUST, 0.55),
]


def _draw_mark(ax) -> None:
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_aspect("equal")
    ax.axis("off")

    # the one bond that's breaking apart, faded/dashed
    (x0, y0), (x1, y1) = EDGE_BROKEN
    ax.plot([x0, x1], [y0, y1], color=EDGE_BREAK, lw=5.5, solid_capstyle="round",
            linestyle=(0, (1.2, 1.6)), alpha=0.85, zorder=1)

    # intact edges
    for (x0, y0), (x1, y1) in EDGES_INTACT:
        ax.plot([x0, x1], [y0, y1], color=EDGE, lw=6.2, solid_capstyle="round", zorder=2)

    # drifting dust motes (the modifier cation pulling the bond apart)
    for x, y, r, color, alpha in DUST_MOTES:
        ax.add_patch(Circle((x, y), r, facecolor=color, edgecolor="none", alpha=alpha, zorder=3))

    # vertices on top
    for pt in (APEX, BACK_L, BACK_R):
        ax.add_patch(Circle(pt, 0.62, facecolor=NODE, edgecolor=INK, lw=2.2, zorder=4))
    ax.add_patch(Circle(FRONT, 0.72, facecolor=NODE_CENTER, edgecolor=INK, lw=2.4, zorder=5))


def make_logo(path: str, px: int = 512) -> None:
    fig = plt.figure(figsize=(px / 100, px / 100), dpi=100)
    ax = fig.add_axes([0, 0, 1, 1])
    bg = FancyBboxPatch(
        (0.25, 0.25), 9.5, 9.5, boxstyle="round,pad=0.02,rounding_size=1.6",
        facecolor=INK, edgecolor="none",
    )
    ax.add_patch(bg)
    _draw_mark(ax)
    fig.savefig(path, transparent=True)
    plt.close(fig)


def make_splash(path: str, w: int = 720, h: int = 420) -> None:
    fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
    fig.patch.set_facecolor(INK)
    ax = fig.add_axes([0.02, 0.16, 0.5, 0.82])
    _draw_mark(ax)
    fig.text(0.55, 0.62, "DUST", color="white", fontsize=56, fontweight="bold",
              family="DejaVu Sans", va="center")
    fig.text(0.55, 0.44, "N4 / NBO speciation for\naluminoborosilicate glasses",
              color="#9fb0c8", fontsize=14, va="center")
    fig.text(0.05, 0.07, "Dell (1983) / Du & Stebbins (2005a) · Lu et al. (2021)",
              color="#5d6b80", fontsize=10.5)
    fig.savefig(path, facecolor=INK)
    plt.close(fig)


def make_ico(png_path: str, ico_path: str) -> None:
    from PIL import Image
    img = Image.open(png_path)
    img.save(ico_path, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    logo = os.path.join(ASSETS, "dust_logo.png")
    make_logo(logo)
    make_splash(os.path.join(ASSETS, "dust_splash.png"))
    make_ico(logo, os.path.join(ASSETS, "dust.ico"))
    print("assets written to", ASSETS)
