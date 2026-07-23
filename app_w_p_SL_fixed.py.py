import os
import io
import shutil
import tempfile
import zipfile
import importlib
import pkgutil
import pandas as pd
import streamlit as st

import metrics
import graphs
import report_tables

from utils_comb import (
    extract_preserve_from_package_id,
    validate_columns,
    update_preserve_history_generic,
    update_master_summary_generic,
)

# ==========================================================
# PAGE SETUP
# ==========================================================
st.set_page_config(page_title="Preserve Monitoring Tool", layout="wide")
st.title("Preserve Monitoring Summary Tool")

# ==========================================================
# RUN MODE
# ==========================================================
# Typed file paths only resolve against the disk of the machine actually
# running the Streamlit process. That's your computer when you run
# `streamlit run app.py` locally, but it is NOT your computer once this
# app is deployed somewhere else (Streamlit Cloud, a server, a container).
# In that case the only way to move files between your computer and the
# app is through the browser: st.file_uploader to send files in,
# st.download_button to bring results back out.
st.sidebar.subheader("Where is this app running?")
running_locally = st.sidebar.checkbox(
    "I'm running this with `streamlit run app.py` on my own computer",
    value=True,
    help=(
        "Check this ONLY if you launched the app yourself and are viewing it in a "
        "browser on the same machine. If this app was deployed (Streamlit Cloud, a "
        "server, shared with a link, etc.), leave this unchecked -- typed folder "
        "paths won't be reachable and you'll use uploads/downloads instead."
    ),
)

# ==========================================================
# UPLOAD CSV
# ==========================================================
uploaded_file = st.file_uploader("Upload Annual Monitoring CSV", type=["csv"])

if not uploaded_file:
    st.stop()

csv_df = pd.read_csv(uploaded_file, encoding="latin1")

missing = validate_columns(csv_df)
if missing:
    st.error("Missing columns:\n" + "\n".join(missing))
    st.stop()

csv_df["Preserve"] = csv_df["Package_ID"].apply(extract_preserve_from_package_id)

# ==========================================================
# WORKING / OUTPUT LOCATION
# ==========================================================
st.subheader("Output Location")

if running_locally:
    # Same behavior as before: a real folder on the machine running the app,
    # which in local mode is genuinely your computer.
    output_dir_input = st.text_input(
        "Output Folder (full path)",
        value=st.session_state.get("output_dir", ""),
    )
    if output_dir_input:
        output_dir_clean = output_dir_input.replace('"', '').replace("'", "").strip()
        output_dir_clean = os.path.normpath(output_dir_clean)
        st.session_state["output_dir"] = output_dir_clean

    output_dir = st.session_state.get("output_dir", None)

    if output_dir:
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                st.success(f"Created folder: {output_dir}")
            except OSError as e:
                st.error(f"Invalid folder path: {e}")
                output_dir = None
        else:
            st.success(output_dir)

    if not output_dir:
        st.info("Select an output folder to continue.")
        st.stop()

else:
    # Server-side scratch folder. Nothing here is visible on your computer
    # until you download it with the button that appears after the run.
    if "output_dir" not in st.session_state:
        st.session_state["output_dir"] = tempfile.mkdtemp(prefix="preserve_monitoring_")
    output_dir = st.session_state["output_dir"]

    st.caption(
        "This app is running remotely, so results are written to a temporary "
        "workspace on the server. You'll get a download button for a ZIP of "
        "everything once the analysis finishes."
    )

    with st.expander("Continue a previous run (optional)"):
        st.write(
            "If you have existing preserve history / master summary .xlsx files "
            "from an earlier run (e.g. downloaded last time), upload them here "
            "so this run updates them instead of starting fresh. Keep the same "
            "filenames and folder-per-preserve structure they had originally."
        )
        prior_files = st.file_uploader(
            "Existing output files (.xlsx)",
            type=["xlsx"],
            accept_multiple_files=True,
            key="prior_files",
        )
        if prior_files:
            for f in prior_files:
                # Preserve-specific files are named "<Preserve>_..._summary.xlsx";
                # master files start with "MASTER_". Route accordingly.
                if f.name.startswith("MASTER_"):
                    dest = os.path.join(output_dir, f.name)
                else:
                    preserve_name = f.name.split("_")[0]
                    preserve_dir = os.path.join(output_dir, preserve_name)
                    os.makedirs(preserve_dir, exist_ok=True)
                    dest = os.path.join(preserve_dir, f.name)
                with open(dest, "wb") as out:
                    out.write(f.getbuffer())
            st.success(f"Loaded {len(prior_files)} existing file(s) into the workspace.")

# ==========================================================
# PRECIPITATION DATA (optional)
# ==========================================================
st.subheader("Precipitation Data (optional)")

if running_locally:
    precip_path_input = st.text_input(
        "Precip Master Workbook Path (optional -- enables precip overlay on graphs)",
        value=st.session_state.get("precip_master_path", ""),
    )
    if precip_path_input:
        precip_path_clean = precip_path_input.replace('"', '').replace("'", "").strip()
        precip_path_clean = os.path.normpath(precip_path_clean)
        st.session_state["precip_master_path"] = precip_path_clean

    precip_master_path = st.session_state.get("precip_master_path", None)

    if precip_master_path:
        if os.path.exists(precip_master_path):
            st.success(f"Precip data found: {precip_master_path}")
        else:
            st.warning(
                f"Path doesn't exist yet -- overlay will be skipped until it's available: "
                f"{precip_master_path}"
            )

else:
    precip_upload = st.file_uploader(
        "Upload Precip Master Workbook (optional -- enables precip overlay on graphs)",
        type=["xlsx", "xls"],
    )
    if precip_upload:
        # Save the uploaded workbook to the server-side workspace so the rest
        # of the pipeline can keep treating precip_master_path as a normal path.
        precip_master_path = os.path.join(output_dir, "_precip_master" + os.path.splitext(precip_upload.name)[1])
        with open(precip_master_path, "wb") as out:
            out.write(precip_upload.getbuffer())
        st.session_state["precip_master_path"] = precip_master_path
        st.success(f"Precip data loaded: {precip_upload.name}")
    else:
        precip_master_path = st.session_state.get("precip_master_path", None)

# ==========================================================
# YEAR SELECTION
# ==========================================================
years = sorted(csv_df["Monitor_Year"].dropna().unique())
selected_year = st.selectbox("Select Monitor Year", years)
csv_df = csv_df[csv_df["Monitor_Year"] == selected_year]

st.caption(f"Preserves found for {selected_year}: {', '.join(sorted(csv_df['Preserve'].unique()))}")

# ==========================================================
# BUILD METRICS TABLE REGISTRY (auto-discovers metrics/ files)
# ==========================================================
def build_table_registry():
    registry = {}
    for _, module_name, _ in pkgutil.iter_modules(metrics.__path__):
        module = importlib.import_module(f"metrics.{module_name}")
        if hasattr(module, "summary_functions"):
            label = getattr(module, "DISPLAY_NAME", module_name)
            registry[label] = module
    return registry

TABLE_REGISTRY = build_table_registry()

if not TABLE_REGISTRY:
    st.error("No valid metrics modules found in the metrics/ folder.")
    st.stop()

# ==========================================================
# BUILD GRAPH REGISTRY (auto-discovers graphs/ files)
# ==========================================================
def build_graph_registry():
    registry = {}
    for _, module_name, _ in pkgutil.iter_modules(graphs.__path__):
        module = importlib.import_module(f"graphs.{module_name}")
        if hasattr(module, "build_graph"):
            label = getattr(module, "DISPLAY_NAME", module_name)
            registry[label] = module
    return registry

GRAPH_REGISTRY = build_graph_registry()

# ==========================================================
# BUILD REPORT (PDF) REGISTRY (auto-discovers reports/ files)
# ==========================================================
def build_report_registry():
    registry = {}
    for _, module_name, _ in pkgutil.iter_modules(report_tables.__path__):
        module = importlib.import_module(f"report_tables.{module_name}")
        if hasattr(module, "build_pdf"):
            label = getattr(module, "DISPLAY_NAME", module_name)
            registry[label] = module
    return registry

REPORT_REGISTRY = build_report_registry()

# ==========================================================
# USER SELECTIONS
# ==========================================================
st.subheader("Select Tables to Generate")
selected_tables = st.multiselect(
    "Choose which summary tables to create for each preserve:",
    options=list(TABLE_REGISTRY.keys()),
    default=list(TABLE_REGISTRY.keys())
)

if GRAPH_REGISTRY:
    st.subheader("Select Graphs to Display")
    selected_graphs = st.multiselect(
        "Choose which graphs to generate per preserve:",
        options=list(GRAPH_REGISTRY.keys()),
        default=[]
    )
else:
    selected_graphs = []

if REPORT_REGISTRY:
    st.subheader("Select Publication-Ready PDF Tables")
    selected_reports = st.multiselect(
        "Choose which PDF tables to generate per preserve:",
        options=list(REPORT_REGISTRY.keys()),
        default=[]
    )
else:
    selected_reports = []

if not selected_tables:
    st.info("Select at least one table type to generate.")
    st.stop()

# ==========================================================
# RUN ANALYSIS
# ==========================================================
if st.button("Run Analysis"):

    # ------------------------------------------------------
    # 1) Generate & save each selected table type
    # ------------------------------------------------------
    for table_label in selected_tables:
        module = TABLE_REGISTRY[table_label]
        summary_functions = module.summary_functions
        file_prefix = getattr(module, "FILE_PREFIX", table_label.replace(" ", "_"))

        rows = []
        for preserve, df_p in csv_df.groupby("Preserve"):
            row = {
                "Monitor_Year": df_p["Monitor_Year"].iloc[0],
                "Preserve": preserve
            }
            for name, func in summary_functions.items():
                row[name] = func(df_p)

            if hasattr(module, "DYNAMIC_COLUMN_FUNC"):
                dynamic_cols = module.DYNAMIC_COLUMN_FUNC(df_p)
                row.update(dynamic_cols)

            rows.append(row)

        result_df = pd.DataFrame(rows)

        id_cols = ["Monitor_Year", "Preserve"]
        value_cols = [c for c in result_df.columns if c not in id_cols]
        result_df[value_cols] = result_df[value_cols].fillna(0)

        st.subheader(f"{table_label} -- All Preserves")
        st.dataframe(result_df, use_container_width=True)

        for _, row in result_df.iterrows():
            preserve = row["Preserve"]
            preserve_dir = os.path.join(output_dir, preserve)
            preserve_filename = os.path.join(
                preserve_dir,
                f"{preserve}_{file_prefix}_summary.xlsx"
            )
            try:
                update_preserve_history_generic(row, preserve_filename)
            except PermissionError as e:
                st.error(
                    f"Could not update {preserve} ({table_label}): "
                    f"file may be open in Excel. Skipping and continuing."
                )
            except Exception as e:
                st.error(
                    f"Unexpected error updating {preserve} ({table_label}): {e}"
                )

        master_filename = os.path.join(
            output_dir,
            f"MASTER_{file_prefix}_SUMMARY.xlsx"
        )
        try:
            update_master_summary_generic(result_df, master_filename)
            st.caption(f"Master file updated: {master_filename}")
        except PermissionError as e:
            st.error(
                f"Could not update master file for {table_label}: "
                f"file may be open in Excel. Skipping and continuing."
            )
        except Exception as e:
            st.error(
                f"Unexpected error updating master file for {table_label}: {e}"
            )

    st.success("Analysis complete for all selected tables!")

    # ------------------------------------------------------
    # 2) Generate and display graphs
    # ------------------------------------------------------
    for graph_label in selected_graphs:
        module = GRAPH_REGISTRY[graph_label]
        source_prefix = module.SOURCE_FILE_PREFIX

        st.subheader(graph_label)

        for preserve in sorted(csv_df["Preserve"].unique()):
            history_file = os.path.join(
                output_dir, preserve, f"{preserve}_{source_prefix}_summary.xlsx"
            )
            if os.path.exists(history_file):
                history_df = pd.read_excel(history_file)
                fig = module.build_graph(history_df, preserve, precip_master_path=precip_master_path)
                st.pyplot(fig)

                preserve_dir = os.path.join(output_dir, preserve)
                os.makedirs(preserve_dir, exist_ok=True)
                graph_filename = os.path.join(
                    preserve_dir,
                    f"{preserve}_{source_prefix}_graph.png"
                )
                fig.savefig(graph_filename, dpi=150, bbox_inches="tight")
                st.caption(f"Graph saved to: {graph_filename}")

            else:
                st.caption(
                    f"No history file yet for {preserve} ({source_prefix}) -- "
                    f"run that table type first."
                )

    # ------------------------------------------------------
    # 3) Generate publication-ready PDF tables
    # ------------------------------------------------------
    for report_label in selected_reports:
        module = REPORT_REGISTRY[report_label]
        source_prefix = module.SOURCE_FILE_PREFIX

        st.subheader(report_label)

        for preserve in sorted(csv_df["Preserve"].unique()):
            history_file = os.path.join(
                output_dir, preserve, f"{preserve}_{source_prefix}_summary.xlsx"
            )
            if os.path.exists(history_file):
                history_df = pd.read_excel(history_file)
                pdf_filename = os.path.join(
                    output_dir, preserve, f"{preserve}_{source_prefix}_report.pdf"
                )
                try:
                    module.build_pdf(history_df, preserve, pdf_filename)
                    st.caption(f"Report saved to: {pdf_filename}")
                except Exception as e:
                    st.error(f"Could not generate PDF for {preserve} ({report_label}): {e}")
            else:
                st.caption(
                    f"No history file yet for {preserve} ({source_prefix}) -- "
                    f"run that table type first."
                )

    # ------------------------------------------------------
    # 4) Remote mode: package everything for download
    # ------------------------------------------------------
    if not running_locally:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(output_dir):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    arcname = os.path.relpath(fpath, output_dir)
                    zf.write(fpath, arcname)
        zip_buffer.seek(0)

        st.subheader("Download Results")
        st.download_button(
            label="Download all results (.zip)",
            data=zip_buffer,
            file_name=f"preserve_monitoring_results_{selected_year}.zip",
            mime="application/zip",
        )
        st.caption(
            "Save this ZIP somewhere on your computer. Next time you run the app, "
            "upload the .xlsx files from inside it under 'Continue a previous run' "
            "so history keeps accumulating."
        )
