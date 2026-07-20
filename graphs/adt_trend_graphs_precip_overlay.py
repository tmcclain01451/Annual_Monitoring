#Will need to change build_graph() call in app_py first b4 can run
#precip sheet pulling from must have following namings:
#PRECIP_SHEET_NAME = "PreservePrecip"   
#PRECIP_PRESERVE_COL = "preserve_clean"    
#PRECIP_YEAR_COL = "year"   

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.cm as cm
import math
import hashlib
import os
import pandas as pd

# ==========================================================
# Which saved metrics table this graph reads from
# (must match a metrics module's FILE_PREFIX)
# ==========================================================
SOURCE_FILE_PREFIX = "ADT_Trend_Table"

DISPLAY_NAME = "ADT Summary Graphs P"

# ==========================================================
# PRECIP OVERLAY CONFIG
# ==========================================================
# To turn the precip overlay OFF later, just set this to False.
# No other code changes needed -- every panel will render as a
# normal single-axis chart again.
SHOW_PRECIP_OVERLAY = True

# Path to the master workbook produced by the separate PRISM precip tool
# (prism_core.py -> upsert_master_workbook). Update this if that file moves.
PRECIP_MASTER_PATH = ""  # fallback only -- normally supplied by the app's text input
PRECIP_SHEET_NAME = "PreservePrecip"
PRECIP_PRESERVE_COL = "preserve_clean"
PRECIP_YEAR_COL = "year"

# Which precip columns to plot, and how.
# Rendered as shaded fill (not lines) on a twin y-axis. Colors picked so
# winter (dark blue) and annual (light blue) both stay visible when they
# overlap -- alpha is intentionally < 1 on each so neither fully hides
# the other regardless of which series is higher.
PRECIP_SERIES = [
    {"column": "annual_mean_precip", "label": "Annual Precip", "color": "#90CAF9", "alpha": 0.35},
    {"column": "winter_mean_precip", "label": "Winter Precip (Oct-Mar)", "color": "#0D47A1", "alpha": 0.35},
]
PRECIP_YLABEL = "Precipitation (mm)"  # NOTE: assumes raw PRISM units (mm); change if converted to inches


def _load_precip_for_preserve(preserve, precip_master_path=None):
    """Load and filter the precip master workbook to one preserve. Returns
    an empty DataFrame (not an error) if the file or preserve isn't found,
    so a missing precip file never breaks the ADT graphs.

    precip_master_path: path supplied by the app (e.g. from a Streamlit
    text input). Falls back to the PRECIP_MASTER_PATH constant below if
    not provided, so this still works if called directly without the app.
    """
    if not SHOW_PRECIP_OVERLAY:
        return pd.DataFrame()

    path_to_use = precip_master_path or PRECIP_MASTER_PATH

    if not path_to_use or not os.path.exists(path_to_use):
        return pd.DataFrame()

    try:
        precip_df = pd.read_excel(path_to_use, sheet_name=PRECIP_SHEET_NAME)
    except Exception:
        return pd.DataFrame()

    precip_df = precip_df[precip_df[PRECIP_PRESERVE_COL] == preserve].copy()
    if precip_df.empty:
        return precip_df

    precip_df[PRECIP_YEAR_COL] = pd.to_numeric(precip_df[PRECIP_YEAR_COL], errors="coerce")
    precip_df = precip_df.dropna(subset=[PRECIP_YEAR_COL])
    precip_df[PRECIP_YEAR_COL] = precip_df[PRECIP_YEAR_COL].astype(int)
    precip_df = precip_df.sort_values(PRECIP_YEAR_COL)

    return precip_df


def _add_precip_overlay(ax, precip_df):
    """Adds a twin y-axis to `ax` with the configured precip series drawn
    as semi-transparent shaded fills (rather than lines) from the axis
    baseline up to each series' value. Returns the (handles, labels) for
    the precip fills so they can be merged into the panel's combined
    legend."""
    if precip_df.empty:
        return [], []

    ax2 = ax.twinx()
    handles, labels = [], []

    for s in PRECIP_SERIES:
        if s["column"] not in precip_df.columns:
            continue
        fill = ax2.fill_between(
            precip_df[PRECIP_YEAR_COL],
            precip_df[s["column"]],
            0,
            color=s["color"],
            alpha=s.get("alpha", 0.35),
            linewidth=0,
            label=s["label"],
        )
        handles.append(fill)
        labels.append(s["label"])

    ax2.set_ylabel(PRECIP_YLABEL, fontsize=9)
    ax2.tick_params(axis="y", labelsize=8)
    ax2.yaxis.set_major_locator(mticker.MaxNLocator(nbins=5))
    ax2.set_ylim(bottom=0)

    return handles, labels


AGE_CLASS_PREFIX = "live_adt_"
AGE_CLASS_SUFFIX = "_count"

# Dynamic age-class colors are auto-assigned from tab10. Blue (tab:blue,
# index 0) and cyan (tab:cyan, index 9) are excluded so no auto-assigned
# data line ever ends up blue -- that's reserved visually for the precip
# shading only.
_PALETTE = [cm.tab10(i) for i in range(10) if i not in (0, 9)]


def _color_for_age_class(name):
    idx = int(hashlib.md5(name.encode()).hexdigest(), 16) % len(_PALETTE)
    return _PALETTE[idx]


def _age_class_label(col_name):
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
             "linestyle": "-", "linewidth": 2.5},
        ],
        "dynamic_age_classes": True,
    },
    {
        "title": "Scat Occurrences",
        "ylabel": "Scat Count",
        "series": [
            {"column": "ty_scat_count", "label": "TY Scat", "color": "#EF6C00"},
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
            {"column": "carcass_within_1yr_count", "label": "0-1 YR", "color": "#D32F2F"},
            {"column": "carcass_older_than_1yr_count", "label": "1+ YR", "color": "#EF6C00"},
        ],
    },
]


def _resolve_panel_series(panel, history_df):
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


def build_graph(history_df, preserve, precip_master_path=None, **kwargs):
    """
    history_df: cumulative dataframe for ONE preserve, already loaded
                from {preserve}_{SOURCE_FILE_PREFIX}_summary.xlsx
    preserve:   preserve name, for the title
    """
    history_df = history_df.sort_values("Monitor_Year").copy()
    history_df["Monitor_Year"] = pd.to_numeric(history_df["Monitor_Year"], errors="coerce")

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

    precip_df = _load_precip_for_preserve(preserve, precip_master_path)

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

        # Draw precip shading first so it sits behind the data lines.
        precip_handles, precip_labels = _add_precip_overlay(ax, precip_df)

        primary_handles = []
        primary_labels = []

        for s in series_list:
            line, = ax.plot(
                history_df["Monitor_Year"],
                history_df[s["column"]],
                marker="o",
                label=s["label"],
                color=s["color"],
                linestyle=s["linestyle"],
                linewidth=s["linewidth"],
                zorder=3,
            )
            primary_handles.append(line)
            primary_labels.append(s["label"])

        ax.set_title(panel["title"], fontsize=12, fontweight="bold")
        ax.set_xlabel("Monitor Year", fontsize=9)
        ax.set_ylabel(panel["ylabel"], fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_zorder(3)
        ax.patch.set_visible(False)
        ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
        ax.tick_params(axis="x", rotation=45, labelsize=8)

        all_handles = primary_handles + precip_handles
        all_labels = primary_labels + precip_labels
        ax.legend(all_handles, all_labels, loc="best", fontsize=7)

    for j in range(n_panels, len(axes_flat)):
        axes_flat[j].axis("off")

    fig.suptitle(f"{preserve} — {DISPLAY_NAME}", fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    return fig
