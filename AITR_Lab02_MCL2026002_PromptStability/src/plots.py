"""Basic result figures (PNG + PDF). Colours: reference palette, validated for colour-vision deficiency
(slot 1 blue / slot 2 orange; sequential blue ramp). Text uses ink colours, never series colours."""
from pathlib import Path

LABELS_GOLD = ("yes", "no", "maybe")
LABELS_PRED = ("yes", "no", "maybe", "invalid")
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SERIES = ("#2a78d6", "#eb6834")
BLUE_RAMP = ("#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b")


def _plt():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK_2, "axes.labelcolor": INK, "xtick.color": INK_2,
                         "ytick.color": INK_2, "text.color": INK, "figure.facecolor": SURFACE,
                         "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})
    return plt


def _save(fig, stem):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".png"), dpi=200, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    return [str(stem.with_suffix(".png")), str(stem.with_suffix(".pdf"))]


def confusion_heatmap(confusion, stem, title):
    """confusion: {gold: {pred: count}}. Cells shaded by row share (sequential blue), labelled with count and %."""
    plt = _plt()
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list("blue_seq", BLUE_RAMP)
    rows = [[confusion[g][p] for p in LABELS_PRED] for g in LABELS_GOLD]
    share = [[v / max(sum(r), 1) for v in r] for r in rows]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    ax.imshow(share, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            ax.text(j, i, f"{v}\n{share[i][j]:.0%}", ha="center", va="center", fontsize=8,
                    color="white" if share[i][j] > 0.55 else INK)
    ax.set_xticks(range(len(LABELS_PRED)), LABELS_PRED)
    ax.set_yticks(range(len(LABELS_GOLD)), LABELS_GOLD)
    ax.set_xlabel("Predicted label")
    ax.set_ylabel("Gold label")
    ax.set_title(title, fontsize=9, color=INK, loc="left")
    ax.set_xticks([x - 0.5 for x in range(1, len(LABELS_PRED))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(LABELS_GOLD))], minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="both", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    paths = _save(fig, stem)
    plt.close(fig)
    return paths


def label_distribution(gold_counts, pred_counts, stem, title):
    """Grouped bars: gold vs predicted label counts, with a legend and value labels."""
    plt = _plt()
    fig, ax = plt.subplots(figsize=(4.6, 2.8))
    x = range(len(LABELS_PRED))
    w = 0.38
    g = [gold_counts.get(c, 0) for c in LABELS_PRED]
    p = [pred_counts.get(c, 0) for c in LABELS_PRED]
    bg = ax.bar([i - w / 2 for i in x], g, w, color=SERIES[0], edgecolor=SURFACE, linewidth=2, label="Gold (expert)")
    bp = ax.bar([i + w / 2 for i in x], p, w, color=SERIES[1], edgecolor=SURFACE, linewidth=2, label="Predicted")
    for bars in (bg, bp):
        for b in bars:
            if b.get_height() > 0:
                ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{int(b.get_height())}", ha="center",
                        va="bottom", fontsize=7.5, color=INK_2)
    ax.set_xticks(list(x), LABELS_PRED)
    ax.set_ylabel("Items")
    ax.set_title(title, fontsize=9, color=INK, loc="left")
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    paths = _save(fig, stem)
    plt.close(fig)
    return paths
