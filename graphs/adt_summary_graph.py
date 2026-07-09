import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.cm as cm
import math
import hashlib

# ==========================================================
# Which saved metrics table this graph reads from
# (must match a metrics module's FILE_PREFIX)
# ==========================================================
SOURCE_FILE_PREFIX = "ADT_Trend_Table"

DISPLAY_NAME = "ADT Summary Graphs"

AGE_CLASS_PREFIX = "live_adt_"
AGE_CLASS_SUFFIX = "_count"
_PALETTE = [cm.tab10(i) for i in range(10)]


def _color_for_age_class(name):
    """Deterministic color per age-class name, stable across runs/years."""
    idx = int(hashlib.md5(name.encode()).hexdigest(), 16) % len(_PALETTE)
    return _PALETTE[idx]


def _age_class_label(col_name):
    """'live_adt_Sub_Adult_count' -> 'Sub Adult'"""
    core = col_name[len(AGE_CLASS_PREFIX):-len(AGE_CLASS_SUFFIX)]
    return core.replace("_", " ")


# ==========================================================
# Grouped panel definitions: each panel = one subplot,
# multiple lines (series) plotted together with a legend
# ==========================================================
GROUPED_PANELS = [
    {
        "title": "Live ADT by Age Class",
        "ylabel": "Individual Count",
        "series": [
            {"column": "live_adt_count", "label": "Total", "color": "#000000",
             "linestyle": "--", "linewidth": 2.5},
        ],
        "dynamic_age_classes": True,   # auto-add live_adt_<Class>_count lines
    },
    {
        "title": "Scat Occurrences",
        "ylabel": "Scat Count",
        "series": [
            {"column": "ty_scat_count", "label": "TY Scat", "color": "#1565C0"},
            {"column": "nty_scat_count", "label": "NTY Scat", "color": "#5E35B1"},
        ],
    },
    {
        "title": "Burrow Activity",
        "ylabel": "Burrow Count",
        "series": [
            {"column": "active_burrow_count", "label": "Active", "color": "#2E7D32"},
            {"column": "inactive_burrow_count", "label": "Inactive", "color": "#8D6E63"},
        ],
    },
    {
        "title": "Carcasses by Age",
        "ylabel": "Carcass Count",
        "series": [
            {"column": "carcass_within_1yr_count", "label": "0–1 YR", "color": "#D32F2F"},
            {"column": "carcass_older_than_1yr_count", "label": "1+ YR", "color": "#EF6C00"},
        ],
    },
]


def _resolve_panel_series(panel, history_df):
    """Build the actual list of (column, label, color, style-kwargs) to plot for a panel,
    including any dynamically-discovered age-class columns."""
    series_list = []

    for s in panel["series"]:
        if s["column"] in history_df.columns:
            series_list.append({
                "column": s["column"],
                "label": s["label"],
                "color": s["color"],
                "linestyle": s.get("linestyle", "-"),
                "linewidth": s.get("linewidth", 2),
            })

    if panel.get("dynamic_age_classes"):
        age_class_cols = sorted([
            c for c in history_df.columns
            if c.startswith(AGE_CLASS_PREFIX)
            and c.endswith(AGE_CLASS_SUFFIX)
            and c != "live_adt_count"
        ])
        for col in age_class_cols:
            series_list.append({
                "column": col,
                "label": _age_class_label(col),
                "color": _color_for_age_class(col),
                "linestyle": "-",
                "linewidth": 2,
            })

    return series_list


def build_graph(history_df, preserve):
    """
    history_df: cumulative dataframe for ONE preserve, already loaded
                from {preserve}_{SOURCE_FILE_PREFIX}_summary.xlsx
    preserve:   preserve name, for the title
    """
    history_df = history_df.sort_values("Monitor_Year")

    # Only build panels that have at least one matching series present
    active_panels = []
    for panel in GROUPED_PANELS:
        resolved = _resolve_panel_series(panel, history_df)
        if resolved:
            active_panels.append((panel, resolved))

    n_panels = len(active_panels)

    if n_panels == 0:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "No matching metric columns found", ha="center", va="center")
        ax.axis("off")
        return fig

    n_cols = 2 if n_panels > 1 else 1
    n_rows = math.ceil(n_panels / n_cols)

    fig, axes = plt.subplots(
        n_rows, n_cols,
        figsize=(7 * n_cols, 4 * n_rows),
        squeeze=False
    )
    axes_flat = axes.flatten()

    for i, (panel, series_list) in enumerate(active_panels):
        ax = axes_flat[i]

        for s in series_list:
            ax.plot(
                history_df["Monitor_Year"],
                history_df[s["column"]],
                marker="o",
                label=s["label"],
                color=s["color"],
                linestyle=s["linestyle"],
                linewidth=s["linewidth"],
            )

        ax.set_title(panel["title"], fontsize=12, fontweight="bold")
        ax.set_xlabel("Monitor Year", fontsize=9)
        ax.set_ylabel(panel["ylabel"], fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        ax.legend(loc="best", fontsize=8)

    for j in range(n_panels, len(axes_flat)):
        axes_flat[j].axis("off")

    fig.suptitle(f"{preserve} — {DISPLAY_NAME}", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    return fig
