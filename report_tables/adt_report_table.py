from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import pandas as pd

# ==========================================================
# Which saved metrics table this report reads from
# (must match a metrics module's FILE_PREFIX)
# ==========================================================
SOURCE_FILE_PREFIX = "ADT_Trend_Table"

DISPLAY_NAME = "ADT Publication Table (PDF)"

# ==========================================================
# Column ordering rules
# ==========================================================
# Lower number = appears further left. Anything not matched
# falls into the last bucket (999) and is sorted alphabetically
# within that bucket, so new/unexpected columns just land at
# the end instead of breaking the layout.
def _column_sort_key(col):
    c = col.lower()

    if c == "live_adt_count":
        return (0, c)                          # Total Live Adt - always first
    if c.startswith("live_adt_"):
        return (1, c)                          # live adt age-class breakdown
    if c == "active_burrow_count":
        return (2, c)
    if c == "inactive_burrow_count":
        return (3, c)
    if c.startswith("ty_") and "scat" in c:
        return (4, c)                          # TY scat before NTY scat
    if "scat" in c:
        return (5, c)
    if "carcass" in c and "within_1yr" in c:
        return (6, c)
    if "carcass" in c:
        return (7, c)                          # older-than-1yr etc.
    if "egg" in c:
        return (8, c)                          # eggshell columns
    return (9, c)                              # everything else, alphabetical


# Special-case display names that don't follow the generic
# "underscore -> title case" rule.
_COLUMN_LABEL_OVERRIDES = {
    "live_adt_count": "Total Live Adt Count",
}


def _pretty_column_name(col):
    if col in _COLUMN_LABEL_OVERRIDES:
        return _COLUMN_LABEL_OVERRIDES[col]
    return col.replace("_", " ").title()


def build_pdf(history_df, preserve, output_path):
    """
    history_df: cumulative dataframe for ONE preserve, already loaded
                from {preserve}_{SOURCE_FILE_PREFIX}_summary.xlsx
    preserve:   preserve name, for the title
    output_path: full file path to write the .pdf to
    """
    history_df = history_df.sort_values("Monitor_Year").reset_index(drop=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=16,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=16,
    )

    doc = SimpleDocTemplate(
        output_path,
        pagesize=landscape(letter),
        leftMargin=0.2 * inch,
        rightMargin=0.2 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )

    story = []
    story.append(Paragraph(f"{preserve} — ADT Summary Table", title_style))
    story.append(Paragraph(
        f"Monitor years {int(history_df['Monitor_Year'].astype(float).min())}"
        f"–{int(history_df['Monitor_Year'].astype(float).max())}",
        subtitle_style
    ))

    # ------------------------------------------------------
    # Build column order: Monitor Year first, then everything
    # else sorted by the priority buckets above.
    # ------------------------------------------------------
    display_cols = list(history_df.columns)
    other_cols = [c for c in display_cols if c not in ("Monitor_Year", "Preserve")]
    other_cols_sorted = sorted(other_cols, key=_column_sort_key)
    ordered_cols = ["Monitor_Year"] + other_cols_sorted

    # ------------------------------------------------------
    # Header row - wrapped in Paragraphs so long headers wrap
    # onto multiple lines instead of forcing the table wider
    # than the page.
    # ------------------------------------------------------
    header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8.5,
        textColor=colors.white,
        alignment=1,  # center
    )
    header_row = [
        Paragraph("Monitor Year" if c == "Monitor_Year" else _pretty_column_name(c), header_style)
        for c in ordered_cols
    ]

    # ------------------------------------------------------
    # Data rows - NaN/missing values become "0", everything
    # else formatted as before.
    # ------------------------------------------------------
    data_rows = []
    for _, row in history_df.iterrows():
        formatted_row = []
        for c in ordered_cols:
            val = row[c]
            if c == "Monitor_Year":
                formatted_row.append(str(int(float(val))))
            elif pd.isna(val):
                formatted_row.append("0")
            else:
                try:
                    formatted_row.append(f"{float(val):,.0f}")
                except (ValueError, TypeError):
                    formatted_row.append(str(val))
        data_rows.append(formatted_row)

    table_data = [header_row] + data_rows

    # ------------------------------------------------------
    # Auto-fit: divide the full usable page width evenly across
    # all columns, and shrink body font size as column count grows,
    # so the table never runs off the left/right edge of the page.
    # ------------------------------------------------------
    usable_width = landscape(letter)[0] - doc.leftMargin - doc.rightMargin
    num_cols = len(ordered_cols)
    col_width = usable_width / num_cols
    col_widths = [col_width] * num_cols

    if num_cols <= 10:
        body_font_size = 8
    elif num_cols <= 16:
        body_font_size = 6.5
    else:
        body_font_size = 5.5

    table = Table(table_data, repeatRows=1, colWidths=col_widths)

    table.setStyle(TableStyle([
        # Header styling
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E4D32")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
        ("TOPPADDING", (0, 0), (-1, 0), 6),

        # Body styling
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), body_font_size),
        ("TOPPADDING", (0, 1), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),

        # Alternating row shading
        *[
            ("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F2F2F2"))
            for i in range(1, len(table_data)) if i % 2 == 0
        ],

        # Grid lines
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BBBBBB")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, colors.HexColor("#2E4D32")),
    ]))

    story.append(table)
    story.append(Spacer(1, 12))

    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#888888"),
    )
    story.append(Paragraph(
        "Active burrows represent Class 1 and 2 burrows, inactive burrows represent Class 3-5 as well as unknown. TY scat represents all scat from this year, NTY scat represents all older scat",
        footer_style
    ))

    doc.build(story)
    return output_path

