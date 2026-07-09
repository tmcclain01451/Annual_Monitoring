import os
import re
import pandas as pd
import shutil      
import tempfile     
import time         
# ==========================================================
# Preserve Name Extraction
# ==========================================================
def extract_preserve_from_package_id(package_id):
    """
    Extract preserve name from Package_ID.
    Strips trailing phase/unit suffixes like X, PH, PHI, PHII, PHIII.
    Example:
        'Mesa123'    -> 'Mesa'
        'CLPX45'     -> 'CLP'
        'KPPPHII001' -> 'KPP'
    """
    if pd.isna(package_id) or not isinstance(package_id, str):
        return "Unknown"

    match = re.search(r"\d", package_id)
    if match:
        preserve = package_id[:match.start()].strip()
    else:
        preserve = package_id.strip()

    preserve = re.sub(r"[^A-Za-z]", "", preserve)

    # Strip trailing phase/unit suffixes — longest first
    preserve = re.sub(r"(PHIII|PHII|PHI|PH|X)$", "", preserve, flags=re.IGNORECASE)

    return preserve if preserve else "Unknown"


# ==========================================================
# Validate Uploaded Dataset
# ==========================================================
def validate_columns(df):
    required = [
        "Package_ID",
        "Monitor_Year",
        "Type_ID",
        "Status_1",
        "Status_3",
        "Status_4",
        "Comments"
    ]
    missing = [c for c in required if c not in df.columns]
    return missing


# ==========================================================
# Per-Preserve History Saver 
# ==========================================================
def update_preserve_history_generic(row, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    new_df = pd.DataFrame([row])
    new_df["Monitor_Year"] = new_df["Monitor_Year"].astype(str)

    if os.path.exists(filename):
        try:
            old_df = pd.read_excel(filename)
            old_df["Monitor_Year"] = old_df["Monitor_Year"].astype(str)

            combined = pd.concat([old_df, new_df], ignore_index=True)
            combined["Monitor_Year"] = combined["Monitor_Year"].astype(str)

            combined = combined.drop_duplicates(
                subset=["Monitor_Year"],
                keep="last"
            )

            combined = combined.sort_values("Monitor_Year")

        except Exception as e:
            print(f"⚠️ Bad Excel file detected, rebuilding:")
            print(f"   {filename}")
            print(f"   Error: {e}")

            # Remove the bad file so it cannot block future runs
            os.remove(filename)

            combined = new_df

    else:
        combined = new_df

    combined.to_excel(filename, index=False)


# ==========================================================
# Generic Master Workbook Saver (works for ANY table type)
# ==========================================================
def update_master_summary_generic(summary_df, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    summary_df = summary_df.copy()
    summary_df["Monitor_Year"] = summary_df["Monitor_Year"].astype(str)

    if os.path.exists(filename):
        old = pd.read_excel(filename)
        old["Monitor_Year"] = old["Monitor_Year"].astype(str)

        combined = pd.concat([old, summary_df], ignore_index=True)
        combined["Monitor_Year"] = combined["Monitor_Year"].astype(str)
        combined = combined.drop_duplicates(subset=["Monitor_Year", "Preserve"], keep="last")
        combined = combined.sort_values(["Preserve", "Monitor_Year"])
    else:
        combined = summary_df

    combined.to_excel(filename, index=False)
    return combined
