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
# NTS / Fence summary functions

def ok_nts_count(df):
    return (
        (df["Type_ID"] == 16) &
        (df["Status_1"] == "OK")
    ).sum()


def new_sign_nts_count(df):
    return (
        (df["Type_ID"] == 16) &
        (df["Status_1"] == "New Sign")
    ).sum()


def replaced_nts_count(df):
    return (
        (df["Type_ID"] == 16) &
        (df["Status_1"] == "Replaced")
    ).sum()


def needs_rep_nts_count(df):
    return (
        (df["Type_ID"] == 16) &
        (df["Status_1"] == "Needs Replacement")
    ).sum()


def unknown_nts_count(df):
    return (
        (df["Type_ID"] == 16) &
        (df["Status_2"].isin([
            "Unknown",
            "Not Surveyed (skipped)"
        ]))
    ).sum()


def suggested_location_count(df):
    return (
        (df["Type_ID"] == 16) &
        (df["Status_2"] == "Suggested location for new sign")
    ).sum()


def fence_install_count(df):
    return (
        (df["Type_ID"] == 15) &
        (df["Status_1"] == "Documentation of Installation")
    ).sum()


def fence_damage_count(df):
    return (
        (df["Type_ID"] == 15) &
        (df["Status_1"] == "Observation of Damaged Fencing")
    ).sum()


def fence_repaired_count(df):
    return (
        (df["Type_ID"] == 15) &
        (df["Status_1"] == "Completed Repair of Damaged Fencing")
    ).sum()


def fence_suggested_locations_count(df):
    return (
        (df["Type_ID"] == 15) &
        (df["Status_1"] == "Suggested location for new fencing")
    ).sum()


# ==========================================================
# Function dictionary

summary_functions = {
    "ok_nts_count": ok_nts_count,
    "new_sign_nts_count": new_sign_nts_count,
    "replaced_nts_count": replaced_nts_count,
    "needs_rep_nts_count": needs_rep_nts_count,
    "unknown_nts_count": unknown_nts_count,
    "suggested_location_count": suggested_location_count,
    "fence_install_count": fence_install_count,
    "fence_damage_count": fence_damage_count,
    "fence_repaired_count": fence_repaired_count,
    "fence_suggested_locations_count": fence_suggested_locations_count,
}

DISPLAY_NAME = "Fence and Sign Summary"
FILE_PREFIX = "Fence_Sign"
