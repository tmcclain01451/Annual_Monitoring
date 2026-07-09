import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import math

# ==========================================================
# Which saved metrics table this graph reads from
# (must match a metrics module's FILE_PREFIX)
# ==========================================================
SOURCE_FILE_PREFIX = "ADT_Trend_Table"

# ==========================================================
# Metric config: column name -> (panel title, y-axis label, color)
# ==========================================================
METRIC_CONFIG = {
    "live_adt_count": {
        "title": "Live ADT",
        "ylabel": "Individual Count",
        "color": "#00838F",
    },
    "active_burrow_count": {
        "title": "Active Burrows",
        "ylabel": "Burrow Count",
        "color": "#2E7D32",
    },
    "inactive_burrow_count": {
        "title": "Inactive Burrows",
        "ylabel": "Burrow Count",
        "color": "#8D6E63",
    },
    "ty_scat_count": {
        "title": "TY Scat",
        "ylabel": "Scat Count",
        "color": "#1565C0",
    },
    "nty_scat_count": {
        "title": "NTY Scat",
        "ylabel": "Scat Count",
        "color": "#5E35B1",
    },
    "carcass_within_1yr_count": {
        "title": "Carcasses (0–1 YR)",
        "ylabel": "Carcass Count",
        "color": "#D32F2F",
    },
    "carcass_older_than_1yr_count": {
        "title": "Carcasses (1+ YR)",
        "ylabel": "Carcass Count",
        "color": "#EF6C00",
    },
}

METRICS_TO_PLOT = list(METRIC_CONFIG.keys())

DISPLAY_NAME = "ADT Summary Graphs"


def build_graph(history_df, preserve):
    """
    history_df: cumulative dataframe for ONE preserve, already loaded
                from {preserve}_{SOURCE_FILE_PREFIX}_summary.xlsx
    preserve:   preserve name, for the title
    
    """
    history_df = history_df.sort_values("Monitor_Year")

    metrics_present = [m for m in METRICS_TO_PLOT if m in history_df.columns]
    n_metrics = len(metrics_present)

    if n_metrics == 0:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.text(0.5, 0.5, "No matching metric columns found", ha="center", va="center")
        ax.axis("off")
        return fig

    n_cols = 2 if n_metrics > 1 else 1
    n_rows = math.ceil(n_metrics / n_cols)

    fig, axes = plt.subplots(
        n_rows, n_cols,
        figsize=(6 * n_cols, 3.5 * n_rows),
        squeeze=False
    )
    axes_flat = axes.flatten()

    for i, metric in enumerate(metrics_present):
        ax = axes_flat[i]
        config = METRIC_CONFIG[metric]

        ax.plot(
            history_df["Monitor_Year"],
            history_df[metric],
            marker="o",
            color=config["color"],
            linewidth=2,
        )

        ax.set_title(config["title"], fontsize=11, fontweight="bold")
        ax.set_xlabel("Monitor Year", fontsize=9)
        ax.set_ylabel(config["ylabel"], fontsize=9)
        ax.grid(True, alpha=0.3)

        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

        ax.tick_params(axis="x", rotation=45, labelsize=8)

    for j in range(n_metrics, len(axes_flat)):
        axes_flat[j].axis("off")

    fig.suptitle(f"{preserve} — {DISPLAY_NAME}", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    return fig

