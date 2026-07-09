import pandas as pd

# ==========================================================
# Helper Functions
# ==========================================================

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
# MFTL Metrics

def live_mftl_count(df):
    filtered = df[
        (df["Type_ID"] == 12) &
        (df["Status_1"] == "Live MFTL")
    ]
    return safe_feature_sum(filtered)

def unconfirmed_live_mftl_count(df):
    filtered = df[
        (df["Type_ID"] == 12) &
        (df["Status_1"] == "Possible live MFTL (species uncertain)")
    ]
    return safe_feature_sum(filtered)

def mftl_tracks_count(df):
    return (
	(df["Type_ID"] == 12) &
	(df["Status_2"] == "Tracks")
	).sum()
def mftl_scat_count(df):
    return (
	(df["Type_ID"] == 12) &
	(df["Status_2"] == "Scat")
	).sum()

#Dictionary of functions
summary_functions = {
    "live_mftl_count": live_mftl_count,
    "unconfirmed_live_mftl_count": unconfirmed_live_mftl_count,
    "mftl_tracks_count": mftl_tracks_count,
    "mftl_scat_count": mftl_scat_count,
    }

DISPLAY_NAME = "MFTL Summary"
FILE_PREFIX = "MFTL"


    
    
