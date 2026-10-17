import os
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def get_trend_arrow(val_latest, val_prev):
    if pd.isna(val_latest) or pd.isna(val_prev):
        return "-"
    if val_prev == 0:
        return "↑" if val_latest > 0 else "↓"
    change = (val_latest - val_prev) / abs(val_prev)
    if change > 0.02:
        return "<font color='green'>↑</font>"
    elif change < -0.02:
        return "<font color='red'>↓</font>"
    else:
        return "<font color='grey'>→</font>"


def format_currency(val):
    if pd.isna(val):
        return "-"
    if abs(val) >= 10000:
        return f"Rs {val / 10000:.1f}T" if val >= 0 else f"-Rs {abs(val) / 10000:.1f}T"
    elif abs(val) >= 10:
        return f"Rs {val:.0f}Cr" if val >= 0 else f"-Rs {abs(val):.0f}Cr"
    return f"Rs {val:.1f}Cr"


def main():
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    db_path = os.path.join(base_dir, "nifty100.db")
    out_dir = os.path.join(base_dir, "reports", "portfolio")
    out_path = os.path.join(out_dir, "portfolio_summary.pdf")

    os.makedirs(out_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    companies = pd.read_sql_query("SELECT * FROM companies ORDER BY ticker", conn)
    pl = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    frs = pd.read_sql_query("SELECT * FROM financial_ratios_source", conn)

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=50,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        alignment=1,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=14,
        alignment=1,
        textColor=colors.dimgrey,
    )
    kpi_name_style = ParagraphStyle(
        "KPIName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        alignment=1,
    )
    kpi_val_style = ParagraphStyle(
        "KPIVal",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=14,
        alignment=1,
    )

    story = []

    # Title Page
    story.append(Spacer(1, 200))
    story.append(Paragraph("Portfolio Summary Report", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph("N100 Financial Intelligence", subtitle_style))
    story.append(PageBreak())

    for _, company in companies.iterrows():
        cid = company["company_id"]
        ticker = company["ticker"]
        c_name = company["company_name"]
        sector = company["sector"]

        c_pl = pl[pl["company_id"] == cid].sort_values("year")
        c_bs = bs[bs["company_id"] == cid].sort_values("year")
        c_frs = frs[frs["company_id"] == cid].sort_values("year")

        if len(c_pl) < 2 or len(c_bs) < 2 or len(c_frs) < 2:
            continue

        pl_curr = c_pl.iloc[-1]
        pl_prev = c_pl.iloc[-2]
        bs_curr = c_bs.iloc[-1]
        bs_prev = c_bs.iloc[-2]
        frs_curr = c_frs.iloc[-1]
        frs_prev = c_frs.iloc[-2]

        # Header
        story.append(Paragraph(f"<b>{c_name} ({ticker})</b>", title_style))
        story.append(Spacer(1, 10))
        story.append(Paragraph(f"Sector: {sector}", subtitle_style))
        story.append(Spacer(1, 40))

        # 6 KPIs with Trends
        kpis = [
            (
                "Revenue",
                format_currency(pl_curr["sales"]),
                get_trend_arrow(pl_curr["sales"], pl_prev["sales"]),
            ),
            (
                "Net Profit",
                format_currency(pl_curr["net_profit"]),
                get_trend_arrow(pl_curr["net_profit"], pl_prev["net_profit"]),
            ),
            (
                "Equity",
                format_currency(bs_curr["equity"]),
                get_trend_arrow(bs_curr["equity"], bs_prev["equity"]),
            ),
            (
                "ROE",
                f"{frs_curr['roe']:.1f}%" if pd.notna(frs_curr.get("roe")) else "-",
                get_trend_arrow(frs_curr["roe"], frs_prev["roe"]),
            ),
            (
                "ROCE",
                f"{frs_curr['roce']:.1f}%" if pd.notna(frs_curr.get("roce")) else "-",
                get_trend_arrow(frs_curr["roce"], frs_prev["roce"]),
            ),
            (
                "D/E",
                f"{frs_curr['debt_to_equity']:.2f}x"
                if pd.notna(frs_curr.get("debt_to_equity"))
                else "-",
                get_trend_arrow(frs_curr["debt_to_equity"], frs_prev["debt_to_equity"]),
            ),
        ]

        # Format as 3 rows of 2 KPIs for better layout
        table_data = []
        for i in range(0, 6, 2):
            k1 = kpis[i]
            k2 = kpis[i + 1]
            table_data.append(
                [
                    Paragraph(k1[0], kpi_name_style),
                    Paragraph(f"{k1[1]} {k1[2]}", kpi_val_style),
                    Paragraph(k2[0], kpi_name_style),
                    Paragraph(f"{k2[1]} {k2[2]}", kpi_val_style),
                ]
            )

        t = Table(table_data, colWidths=[120, 130, 120, 130], rowHeights=[60] * 3)
        t.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f0f0f0")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f0f0f0")),
                ]
            )
        )

        story.append(t)
        story.append(PageBreak())

    doc.build(story)
    print("Generated portfolio_summary.pdf")


if __name__ == "__main__":
    main()
