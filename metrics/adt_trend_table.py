import re
import pandas as pd

# ==========================================================
# Helpers
# ==========================================================
def safe_feature_sum(filtered_df):
    if filtered_df.empty:
        return 0
    if "Feature_Count" in filtered_df.columns:
        return filtered_df["Feature_Count"].fillna(1).sum()
    return len(filtered_df)


def slugify(text):
    text = str(text).strip()
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text if text else "Unknown"


# ==========================================================
# Live ADT — total (kept for continuity/trend graphs)
# ==========================================================
def live_adt_count(df):
    filtered = df[df["Type_ID"].isin([5, 6])]
    return safe_feature_sum(filtered)


# ==========================================================
# Live ADT — broken out by age class (Status_2)
# ==========================================================
def build_live_adt_by_age_class(df):
    filtered = df[df["Type_ID"].isin([5, 6])].copy()

    if filtered.empty:
        return {}

    if "Feature_Count" in filtered.columns:
        filtered["_count"] = filtered["Feature_Count"].fillna(1)
    else:
        filtered["_count"] = 1

    grouped = filtered.groupby("Status_2")["_count"].sum()

    result = {}
    for age_class, value in grouped.items():
        col_name = f"live_adt_{slugify(age_class)}_count"
        result[col_name] = value

    return result


# ==========================================================
# Grouped Burrow Activity
# ==========================================================
def active_burrow_count(df):
    """Class 1 + Class 2 burrows."""
    return (
        (df["Type_ID"] == 6)
        | (
            (df["Type_ID"] == 7)
            & (df["Status_1"].isin(["Class 1", "Class 2"]))
        )
    ).sum()


def inactive_burrow_count(df):
    """Class 3 + 4 + 5 + unknown/undefined class burrows."""
    return (
        (df["Type_ID"] == 7)
        & (
            df["Status_1"].isin(
                [
                    "Class 3",
                    "Class 4",
                    "Class 5",
                    "Class unknown or not listed",
                ]
            )
        )
    ).sum()


# ==========================================================
# Scat
# ==========================================================
def ty_scat_count(df):
    return (
        df["Type_ID"].isin([6, 7, 8])
        & df["Status_3"].isin(["TY1", "TY2", "TY3"])
    ).sum()


def nty_scat_count(df):
    return (
        df["Type_ID"].isin([6, 7, 8])
        & df["Status_3"].str.contains("NTY", case=False, na=False)
    ).sum()


# ==========================================================
# Carcasses
# ==========================================================
def carcass_within_1yr_count(df):
    return (
        (df["Type_ID"] == 9)
        & (df["Status_1"] == "0-1 YR")
    ).sum()


def carcass_older_than_1yr_count(df):
    """1-2 YRS plus anything else not in the 0-1 YR bucket."""
    return (
        (df["Type_ID"] == 9)
        & (df["Status_1"] != "0-1 YR")
    ).sum()


# ==========================================================
# Registry info
# ==========================================================
summary_functions = {
    "live_adt_count": live_adt_count,
    "active_burrow_count": active_burrow_count,
    "inactive_burrow_count": inactive_burrow_count,
    "ty_scat_count": ty_scat_count,
    "nty_scat_count": nty_scat_count,
    "carcass_within_1yr_count": carcass_within_1yr_count,
    "carcass_older_than_1yr_count": carcass_older_than_1yr_count,
}

DYNAMIC_COLUMN_FUNC = build_live_adt_by_age_class   # NEW

DISPLAY_NAME = "ADT Trend Table"
FILE_PREFIX = "ADT_Trend_Table"
