import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"figure.facecolor": "#FFF8F0", "axes.facecolor": "#FFF8F0"})
import matplotlib.ticker as ticker
import seaborn as sns
from matplotlib.figure import Figure

from storage import FLAVORS, FLAVOR_LABELS

# Welch's-inspired color palette (one per flavor, order matches FLAVORS list)
FLAVOR_COLORS = {
    "concord_grape": "#4A1A6B",
    "strawberry": "#E8334A",
    "white_grape_raspberry": "#C2185B",
    "orange": "#F4831F",
    "white_grape_peach": "#FFCA7A",
}


def _empty_figure(message: str) -> Figure:
    fig = Figure()
    ax = fig.add_subplot(111)
    ax.text(0.5, 0.5, message, ha="center", va="center")
    ax.axis("off")
    return fig


def _active_flavors(totals: dict) -> list[str]:
    """Return only flavors with at least one count."""
    return [f for f in FLAVORS if totals.get(f, 0) > 0]


def pie_chart(totals: dict) -> Figure:
    active = _active_flavors(totals)
    if not active:
        return _empty_figure("No data yet")

    values = [totals[f] for f in active]
    labels = [FLAVOR_LABELS[f] for f in active]
    colors = [FLAVOR_COLORS[f] for f in active]
    total = sum(values)

    fig = Figure(figsize=(7, 7))
    ax = fig.add_subplot(111)
    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,
        colors=colors,
        autopct=lambda pct: f"{pct:.1f}%\n({round(pct * total / 100)})",
        startangle=140,
        pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 1.5},
    )
    for at in autotexts:
        at.set_fontsize(9)

    ax.legend(
        wedges,
        [f"{FLAVOR_LABELS[f]} ({totals[f]})" for f in active],
        title="Flavor (count)",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=10,
    )
    ax.set_title(f"Flavor Distribution\n(Total: {total} pieces)", fontsize=13, pad=20)
    fig.tight_layout()
    return fig


def bar_chart(totals: dict) -> Figure:
    active = sorted(_active_flavors(totals), key=lambda f: totals[f], reverse=True)
    if not active:
        return _empty_figure("No data yet")

    total = sum(totals[f] for f in active)
    values = [totals[f] for f in active]
    pcts = [v / total * 100 for v in values]
    labels = [FLAVOR_LABELS[f] for f in active]
    colors = [FLAVOR_COLORS[f] for f in active]

    fig = Figure(figsize=(8, max(3, len(active) * 0.8)))
    ax = fig.add_subplot(111)
    bars = ax.barh(labels[::-1], values[::-1], color=colors[::-1], edgecolor="white")

    for bar, pct in zip(bars, pcts[::-1]):
        ax.text(
            bar.get_width() + 0.1,
            bar.get_y() + bar.get_height() / 2,
            f"{bar.get_width():.0f}  ({pct:.1f}%)",
            va="center",
            fontsize=9,
        )

    ax.set_xlabel("Count")
    ax.set_title("Flavor Counts", fontsize=13)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_xlim(0, max(values) * 1.25)
    sns.despine(ax=ax, left=True)
    fig.tight_layout()
    return fig


def history_chart(sessions: list) -> Figure:
    if not sessions:
        return _empty_figure("No sessions yet")

    labels = [s["id"][:10] + "\n" + s["id"][11:19] for s in sessions]
    colors = [FLAVOR_COLORS[f] for f in FLAVORS]

    fig = Figure(figsize=(max(6, len(sessions) * 1.2), 5))
    ax = fig.add_subplot(111)
    bottoms = [0] * len(sessions)

    for flavor, color in zip(FLAVORS, colors):
        values = [s["counts"].get(flavor, 0) for s in sessions]
        if any(v > 0 for v in values):
            ax.bar(
                range(len(sessions)),
                values,
                bottom=bottoms,
                color=color,
                label=FLAVOR_LABELS[flavor],
                edgecolor="white",
                width=0.6,
            )
            bottoms = [b + v for b, v in zip(bottoms, values)]

    ax.set_xticks(range(len(sessions)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Count")
    ax.set_title("Per-Session Flavor Breakdown", fontsize=13)
    ax.legend(loc="upper right", fontsize=9)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    sns.despine(ax=ax)
    fig.tight_layout()
    return fig
