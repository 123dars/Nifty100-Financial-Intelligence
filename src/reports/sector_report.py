import os
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def format_currency(val):
    if pd.isna(val):
        return "-"
    if abs(val) >= 10000:
        return f"Rs {val / 10000:.1f}T" if val >= 0 else f"-Rs {abs(val) / 10000:.1f}T"
    elif abs(val) >= 10:
        return f"Rs {val:.0f}Cr" if val >= 0 else f"-Rs {abs(val):.0f}Cr"
    return f"Rs {val:.1f}Cr"


def format_pct(val):
    if pd.isna(val):
        return "-"
    return f"{val:.1f}%"


def generate_sector_report(sector_name, comp_df, out_path):
    doc = SimpleDocTemplate(
        out_path,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.white,
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        alignment=1,
    )

    story = []

    # Header
    header_data = [[Paragraph(f"Sector Report: {sector_name}", title_style)]]
    t = Table(header_data, colWidths=[780], rowHeights=[40])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#004d40")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 20))

    # Median KPIs
    median_rev = comp_df["sales"].median()
    median_pat = comp_df["net_profit"].median()
    median_roe = comp_df["roe"].median()
    median_roce = comp_df["roce"].median()
    median_de = comp_df["debt_to_equity"].median()

    summary_data = [
        [
            "Total Companies",
            "Median Revenue",
            "Median Net Profit",
            "Median ROE",
            "Median ROCE",
            "Median D/E",
        ],
        [
            str(len(comp_df)),
            format_currency(median_rev),
            format_currency(median_pat),
            format_pct(median_roe),
            format_pct(median_roce),
            f"{median_de:.2f}x",
        ],
    ]
    summary_table = Table(summary_data, colWidths=[130] * 6)
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 30))

    # List of all companies
    story.append(Paragraph("Company Breakdown", subtitle_style))
    story.append(Spacer(1, 15))

    headers = [
        "Ticker",
        "Company Name",
        "Revenue",
        "Net Profit",
        "ROE",
        "ROCE",
        "D/E",
        "Current Ratio",
        "CapEx Intensity",
    ]
    comp_list = [headers]

    for _, row in comp_df.iterrows():
        comp_list.append(
            [
                row["ticker"],
                row["company_name"][:25] + "..."
                if len(row["company_name"]) > 28
                else row["company_name"],
                format_currency(row["sales"]),
                format_currency(row["net_profit"]),
                format_pct(row["roe"]),
                format_pct(row["roce"]),
                f"{row['debt_to_equity']:.2f}x"
                if pd.notna(row["debt_to_equity"])
                else "-",
                f"{row['current_ratio']:.2f}x"
                if pd.notna(row["current_ratio"])
                else "-",
                f"{row['capex_intensity_pct']:.1f}%"
                if pd.notna(row.get("capex_intensity_pct"))
                else "-",
            ]
        )

    comp_table = Table(comp_list, colWidths=[60, 160, 80, 80, 60, 60, 60, 70, 90])
    comp_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e0f2f1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("ALIGN", (1, 1), (1, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(comp_table)

    doc.build(story)


def main():
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    db_path = os.path.join(base_dir, "nifty100.db")
    out_dir = os.path.join(base_dir, "reports", "sector")
    cf_intel_xlsx = os.path.join(base_dir, "output", "cashflow_intelligence.xlsx")

    os.makedirs(out_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    companies = pd.read_sql_query(
        "SELECT company_id, ticker, company_name, sector FROM companies", conn
    )
    pl = pd.read_sql_query(
        "SELECT company_id, year, sales, net_profit FROM profitandloss", conn
    )
    frs = pd.read_sql_query(
        "SELECT company_id, year, roe, roce, debt_to_equity, current_ratio FROM financial_ratios_source",
        conn,
    )

    cf_intel_df = (
        pd.read_excel(cf_intel_xlsx)
        if os.path.exists(cf_intel_xlsx)
        else pd.DataFrame()
    )

    # Get latest year for each company
    latest_pl = pl.sort_values("year").groupby("company_id").tail(1)
    latest_frs = frs.sort_values("year").groupby("company_id").tail(1)

    df = companies.merge(latest_pl, on="company_id", how="left")
    df = df.merge(latest_frs, on="company_id", how="left", suffixes=("", "_frs"))

    if not cf_intel_df.empty:
        df = df.merge(
            cf_intel_df[["company_id", "capex_intensity_pct"]],
            on="company_id",
            how="left",
        )
    else:
        df["capex_intensity_pct"] = None

    sectors = df["sector"].dropna().unique()

    for sector in sectors:
        sector_df = df[df["sector"] == sector].sort_values("ticker")
        if sector_df.empty:
            continue

        # clean sector name for filename
        clean_name = sector.replace(" ", "_").replace("/", "_")
        out_path = os.path.join(out_dir, f"{clean_name}_report.pdf")
        generate_sector_report(sector, sector_df, out_path)

    print(f"Generated {len(sectors)} sector reports.")


if __name__ == "__main__":
    main()
