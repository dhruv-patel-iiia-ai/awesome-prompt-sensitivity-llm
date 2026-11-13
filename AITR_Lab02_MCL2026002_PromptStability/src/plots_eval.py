"""Figures for the Prompt 13 evaluation (PNG + PDF).

Same palette as src/plots.py (dataviz reference palette). The three label
colours were run through the palette validator (light surface): CVD dE 9.2,
normal dE 27.6, PASS; aqua is below 3:1 contrast, so every segment that
fits carries a visible count label and the numbers are also in results.csv.
"""
from src.plots import _plt, _save, SURFACE, INK, INK_2, GRID

LABEL_COLOURS = {"yes": "#2a78d6", "no": "#eb6834", "maybe": "#1baf7a",
                 "invalid": "#8a8984"}
DOT = "#2a78d6"


def _clean_axes(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def accuracy_ci(rows, control, stem, title):
    """rows: [(method, acc, lo, hi)] top to bottom; control: (name, acc)."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(5.2, 0.45 * len(rows) + 1.0))
    ys = list(range(len(rows)))[::-1]
    for y, (name, a, lo, hi) in zip(ys, rows):
        ax.plot([lo, hi], [y, y], color=DOT, linewidth=2,
                solid_capstyle="round")
        ax.plot([a], [y], "o", color=DOT, markersize=8,
                markeredgecolor=SURFACE, markeredgewidth=2)
        ax.text(hi + 0.012, y, f"{a:.2f} [{lo:.2f}, {hi:.2f}]",
                va="center", fontsize=7.5, color=INK_2, zorder=3,
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1))
    cname, cval = control
    ax.axvline(cval, color=INK_2, linewidth=1, linestyle=(0, (3, 3)))
    ax.text(cval + 0.01, len(rows) - 0.45, f"{cname} {cval:.2f}",
            ha="left", va="center", fontsize=7.5, color=INK_2,
            bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1))
    ax.set_yticks(ys, [r[0] for r in rows])
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.6, len(rows) - 0.1)
    ax.set_xlabel("Accuracy vs expert label (95% bootstrap CI)")
    ax.set_title(title, fontsize=9, color=INK, loc="left")
    _clean_axes(ax)
    paths = _save(fig, stem)
    plt.close(fig)
    return paths


def label_mix(rows, stem, title):
    """rows: [(name, {label: count})] top to bottom; stacked bars."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(5.2, 0.45 * len(rows) + 1.2))
    ys = list(range(len(rows)))[::-1]
    total = max(sum(c.values()) for _, c in rows)
    for y, (_, counts) in zip(ys, rows):
        left = 0
        for lab, col in LABEL_COLOURS.items():
            v = counts.get(lab, 0)
            if not v:
                continue
            ax.barh(y, v, left=left, color=col, edgecolor=SURFACE,
                    linewidth=2, height=0.62)
            if v / total >= 0.06:
                ax.text(left + v / 2, y, str(v), ha="center", va="center",
                        fontsize=7.5, color="white")
            left += v
    ax.set_yticks(ys, [r[0] for r in rows])
    ax.set_xlim(0, total)
    ax.set_xlabel("Items")
    ax.set_title(title, fontsize=9, color=INK, loc="left", pad=22)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c)
               for c in LABEL_COLOURS.values()]
    ax.legend(handles, list(LABEL_COLOURS), frameon=False, fontsize=8,
              ncol=4, loc="lower left", bbox_to_anchor=(0, 1.0),
              borderaxespad=0.2, handlelength=1.0, columnspacing=1.0)
    _clean_axes(ax)
    paths = _save(fig, stem)
    plt.close(fig)
    return paths
