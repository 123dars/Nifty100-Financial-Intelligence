import io
import os
import sqlite3

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Image,
    PageBreak,
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
        return f"₹{val / 10000:.1f}T" if val >= 0 else f"-₹{abs(val) / 10000:.1f}T"
    elif abs(val) >= 10:
        return f"₹{val:.0f}Cr" if val >= 0 else f"-₹{abs(val):.0f}Cr"
    return f"₹{val:.1f}Cr"


def create_bar_chart_rev_pat(df):
    plt.figure(figsize=(7, 3))
    x = df["year"]
    w = 0.35
    plt.bar(x - w / 2, df["sales"], width=w, label="Revenue", color="#1f77b4")
    plt.bar(x + w / 2, df["net_profit"], width=w, label="Net Profit", color="#ff7f0e")
    plt.title("10-Year Revenue & Net Profit (Cr)", fontsize=10)
    plt.legend(fontsize=8)
    plt.xticks(x, rotation=45, fontsize=8)
    plt.yticks(fontsize=8)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close()
    buf.seek(0)
    return buf


def create_line_chart_roe_roce(df):
    fig, ax1 = plt.subplots(figsize=(7, 3))
    x = df["year"]

    color = "tab:blue"
    ax1.set_xlabel("Year", fontsize=8)
    ax1.set_ylabel("ROE (%)", color=color, fontsize=8)
    l1 = ax1.plot(x, df["roe"], color=color, marker="o", label="ROE")
    ax1.tick_params(axis="y", labelcolor=color, labelsize=8)
    ax1.tick_params(axis="x", rotation=45, labelsize=8)
    ax1.set_xticks(x)

    ax2 = ax1.twinx()
    color = "tab:red"
    ax2.set_ylabel("ROCE (%)", color=color, fontsize=8)
    l2 = ax2.plot(x, df["roce"], color=color, marker="s", label="ROCE")
    ax2.tick_params(axis="y", labelcolor=color, labelsize=8)

    lns = l1 + l2
    labs = [l.get_label() for l in lns]
    ax1.legend(lns, labs, loc="upper left", fontsize=8)

    plt.title("ROE & ROCE Trend", fontsize=10)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close()
    buf.seek(0)
    return buf


def create_stacked_bar_bs(df):
    plt.figure(figsize=(7, 3))
    x = df["year"]
    equity = df["equity"]
    borrowings = df["borrowings"]
    other_liab = df["total_liabilities"] - df["equity"] - df["borrowings"]
    other_liab = other_liab.clip(lower=0)

    plt.bar(x, equity, label="Equity", color="#2ca02c")
    plt.bar(x, borrowings, bottom=equity, label="Borrowings", color="#d62728")
    plt.bar(
        x, other_liab, bottom=equity + borrowings, label="Other Liab", color="#7f7f7f"
    )

    plt.title("Balance Sheet Composition (Cr)", fontsize=10)
    plt.legend(fontsize=8)
    plt.xticks(x, rotation=45, fontsize=8)
    plt.yticks(fontsize=8)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close()
    buf.seek(0)
    return buf


def create_waterfall_cf(cf_row):
    plt.figure(figsize=(6, 3.5))
    labels = ["CFO", "CFI", "CFF", "Net"]
    cfo = cf_row["operating_cash_flow"] or 0
    cfi = cf_row["investing_cash_flow"] or 0
    cff = cf_row["financing_cash_flow"] or 0
    net = cfo + cfi + cff

    values = [cfo, cfi, cff, net]
    colors_list = ["g" if v > 0 else "r" for v in values[:-1]] + ["b"]

    starts = [0, cfo, cfo + cfi, 0]

    plt.bar(labels, values, bottom=starts, color=colors_list)
    for i, v in enumerate(values):
        plt.text(
            i,
            starts[i] + v / 2,
            f"{v:.0f}",
            ha="center",
            va="center",
            color="white",
            fontsize=8,
            fontweight="bold",
        )

    plt.title("Latest Year Cash Flow Waterfall (Cr)", fontsize=10)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close()
    buf.seek(0)
    return buf


def generate_tearsheet(company, pl, bs, cf, frs, pros_cons, cap_alloc, output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.white,
        alignment=1,
    )
    kpi_style = ParagraphStyle(
        "KPI",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        alignment=1,
    )
    bullet_green = ParagraphStyle(
        "Pros",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.green,
        spaceAfter=5,
    )
    bullet_red = ParagraphStyle(
        "Cons",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        textColor=colors.red,
        spaceAfter=5,
    )

    story = []

    # Page 1 Header
    header_data = [
        [Paragraph(f"{company['company_name']} ({company['ticker']})", title_style)]
    ]
    t = Table(header_data, colWidths=[530], rowHeights=[40])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#000080")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 20))

    # 6 KPIs
    latest_pl = pl.iloc[-1]
    latest_bs = bs.iloc[-1]
    latest_frs = frs.iloc[-1] if not frs.empty else None

    kpis = [
        [
            Paragraph("Revenue", kpi_style),
            Paragraph("Net Profit", kpi_style),
            Paragraph("Total Equity", kpi_style),
        ],
        [
            format_currency(latest_pl["sales"]),
            format_currency(latest_pl["net_profit"]),
            format_currency(latest_bs["equity"]),
        ],
        [
            Paragraph("ROE", kpi_style),
            Paragraph("ROCE", kpi_style),
            Paragraph("D/E", kpi_style),
        ],
        [
            f"{latest_frs['roe']:.1f}%"
            if latest_frs is not None and pd.notna(latest_frs.get("roe"))
            else "-",
            f"{latest_frs['roce']:.1f}%"
            if latest_frs is not None and pd.notna(latest_frs.get("roce"))
            else "-",
            f"{latest_frs['debt_to_equity']:.2f}x"
            if latest_frs is not None and pd.notna(latest_frs.get("debt_to_equity"))
            else "-",
        ],
    ]

    kpi_table = Table(kpis, colWidths=[176, 176, 176])
    kpi_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("BACKGROUND", (0, 2), (-1, 2), colors.lightgrey),
                ("FONTSIZE", (0, 1), (-1, 1), 12),
                ("FONTSIZE", (0, 3), (-1, 3), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(kpi_table)
    story.append(Spacer(1, 20))

    # Charts Page 1
    buf_bar = create_bar_chart_rev_pat(pl)
    buf_line = create_line_chart_roe_roce(frs)

    chart_data = [
        [Image(buf_bar, width=250, height=120), Image(buf_line, width=250, height=120)]
    ]
    chart_table = Table(chart_data, colWidths=[265, 265])
    chart_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(chart_table)

    story.append(PageBreak())

    # Page 2 Charts
    buf_bs = create_stacked_bar_bs(bs)
    buf_wf = create_waterfall_cf(cf.iloc[-1])

    chart_data2 = [
        [Image(buf_bs, width=250, height=120), Image(buf_wf, width=250, height=120)]
    ]
    chart_table2 = Table(chart_data2, colWidths=[265, 265])
    chart_table2.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(chart_table2)
    story.append(Spacer(1, 20))

    # Pros & Cons
    pros = pros_cons[pros_cons["type"] == "pro"]
    cons = pros_cons[pros_cons["type"] == "con"]

    pros_list = [
        Paragraph(f"• {row['text']} (Conf: {row['confidence_pct']}%)", bullet_green)
        for _, row in pros.iterrows()
    ]
    cons_list = [
        Paragraph(f"• {row['text']} (Conf: {row['confidence_pct']}%)", bullet_red)
        for _, row in cons.iterrows()
    ]

    pc_data = [
        [
            Paragraph("<b>Pros</b>", styles["Normal"]),
            Paragraph("<b>Cons</b>", styles["Normal"]),
        ],
        [pros_list, cons_list],
    ]
    pc_table = Table(pc_data, colWidths=[265, 265])
    pc_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#e6f2e6")),
                ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#f2e6e6")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    story.append(pc_table)
    story.append(Spacer(1, 20))

    # Capital Allocation Badge
    badge_style = ParagraphStyle(
        "Badge",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.white,
        alignment=1,
    )
    badge_data = [[Paragraph(f"Capital Allocation Pattern: {cap_alloc}", badge_style)]]
    badge_table = Table(badge_data, colWidths=[530], rowHeights=[30])
    badge_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#4a86e8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(badge_table)

    doc.build(story)


def main():
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    db_path = os.path.join(base_dir, "nifty100.db")
    out_dir = os.path.join(base_dir, "reports", "tearsheets")
    skipped_csv = os.path.join(base_dir, "output", "skipped_tearsheets.csv")
    pros_cons_csv = os.path.join(base_dir, "output", "pros_cons_generated.csv")
    cf_intel_xlsx = os.path.join(base_dir, "output", "cashflow_intelligence.xlsx")

    os.makedirs(out_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    companies = pd.read_sql_query("SELECT * FROM companies", conn)
    pl_all = pd.read_sql_query("SELECT * FROM profitandloss", conn)
    bs_all = pd.read_sql_query("SELECT * FROM balancesheet", conn)
    cf_all = pd.read_sql_query("SELECT * FROM cashflow", conn)
    frs_all = pd.read_sql_query("SELECT * FROM financial_ratios_source", conn)

    pros_cons_df = (
        pd.read_csv(pros_cons_csv) if os.path.exists(pros_cons_csv) else pd.DataFrame()
    )
    cf_intel_df = (
        pd.read_excel(cf_intel_xlsx)
        if os.path.exists(cf_intel_xlsx)
        else pd.DataFrame()
    )

    skipped = []

    for _, company in companies.iterrows():
        cid = company["company_id"]
        ticker = company["ticker"]

        pl = pl_all[pl_all["company_id"] == cid].sort_values("year")
        if len(pl) < 3:
            skipped.append(
                {"ticker": ticker, "reason": f"Only {len(pl)} years of data"}
            )
            continue

        bs = bs_all[bs_all["company_id"] == cid].sort_values("year")
        cf = cf_all[cf_all["company_id"] == cid].sort_values("year")
        frs = frs_all[frs_all["company_id"] == cid].sort_values("year")

        # fallback if some tables are empty
        if bs.empty or cf.empty:
            skipped.append({"ticker": ticker, "reason": "Missing BS or CF data"})
            continue

        pc = (
            pros_cons_df[pros_cons_df["company_id"] == cid]
            if not pros_cons_df.empty
            else pd.DataFrame()
        )

        cap_alloc = "Unknown"
        if not cf_intel_df.empty:
            c_intel = cf_intel_df[cf_intel_df["company_id"] == cid]
            if not c_intel.empty:
                cap_alloc = c_intel.iloc[0]["capital_allocation_label"]

        out_path = os.path.join(out_dir, f"{ticker}_tearsheet.pdf")

        try:
            generate_tearsheet(company, pl, bs, cf, frs, pc, cap_alloc, out_path)
        except Exception as e:
            print(f"Error generating {ticker}: {e}")
            skipped.append({"ticker": ticker, "reason": str(e)})

    pd.DataFrame(skipped).to_csv(skipped_csv, index=False)
    print(f"Generated tearsheets. Skipped {len(skipped)} companies.")


if __name__ == "__main__":
    main()
