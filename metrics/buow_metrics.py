# BUOW metrics
import pandas as pd

# ==========================================================
# Helper Functions

def safe_feature_sum(filtered_df):
    """
    Sum Feature_Count, treating missing values as 1.
    If Feature_Count does not exist, count rows instead.
    """
    if filtered_df.empty:
        return 0

    if "Feature_Count" in filtered_df.columns:
        return filtered_df["Feature_Count"].fillna(1).sum()

    return len(filtered_df)


# ==========================================================
# BUOW summary functions

def live_BUOW_count(df):
    filtered = df[
        (df["Type_ID"] == 11) &
        (df["Status_1"] == "Live Owl(s)")
    ]
    return safe_feature_sum(filtered)


def active_BUOW_burrow_count(df):
    return (
        (df["Type_ID"] == 11) &
        (df["Status_2"] == "Active Owl Burrow (currently or within the last year)")
    ).sum()


def inactive_BUOW_burrow_count(df):
    return (
        (df["Type_ID"] == 11) &
        (df["Status_2"] == "Inactive Owl Burrow (not active within the last year)")
    ).sum()


def potential_BUOW_burrow_count(df):
    return (
        (df["Type_ID"] == 11) &
        (df["Status_2"] == "Potential or Suitable BUOW Burrow (no sign or unconfirmed species)")
    ).sum()


def BUOW_pellets_count(df):
    return (
        (df["Type_ID"] == 11) &
        (
            df["Status_2"].isin([
                "Pellet(s) only",
                "Pellet(s) and Whitewash"
            ])
        )
    ).sum()


def BUOW_whitewash_count(df):
    return (
        (df["Type_ID"] == 11) &
        (
            df["Status_2"].isin([
                "Whitewash only",
                "Pellet(s) and Whitewash"
            ])
        )
    ).sum()


def other_BUOW_sign_count(df):
    return (
        (df["Type_ID"] == 11) &
        (
            df["Status_4"] == "Feathers, carcass or other sign present (see comments)"
        )
    ).sum()


# ==========================================================
# Dictionary of summary functions

summary_functions = {
    "live_BUOW_count": live_BUOW_count,
    "active_BUOW_burrow_count": active_BUOW_burrow_count,
    "inactive_BUOW_burrow_count": inactive_BUOW_burrow_count,
    "potential_BUOW_burrow_count": potential_BUOW_burrow_count,
    "BUOW_pellets_count": BUOW_pellets_count,
    "BUOW_whitewash_count": BUOW_whitewash_count,
    "other_BUOW_sign_count": other_BUOW_sign_count,
}

DISPLAY_NAME = "BUOW Summary"
FILE_PREFIX = "BUOW"
        
