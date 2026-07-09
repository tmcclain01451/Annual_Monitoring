import re
import pandas as pd

def slugify(text):
    text = str(text).strip()
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text if text else "Unknown"

def build_species_status_counts(df):
    filtered = df[
        (df["Type_ID"] == 14)
        & (df["Status_2"] == "Live Occurrence")
    ].copy()

    if filtered.empty:
        return {}

    if "Feature_Count" in filtered.columns:
        filtered["_count"] = filtered["Feature_Count"].fillna(1)
    else:
        filtered["_count"] = 1

    grouped = filtered.groupby("Status_1")["_count"].sum()

    result = {}
    for status1, value in grouped.items():
        col_name = f"{slugify(status1)}_count"
        result[col_name] = value

    return result

summary_functions = {}
DYNAMIC_COLUMN_FUNC = build_species_status_counts

DISPLAY_NAME = "Other Live Occurrences"
FILE_PREFIX = "Other_Live_Wildlife"
