<div align="center">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Plotly-239120?style=for-the-badge&logo=plotly&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" />
</div>

<br />

<div align="center">
  <h1 align="center">Nifty 100 Financial Intelligence Platform</h1>
  <p align="center">
    <strong>An institutional-grade, highly optimized Streamlit dashboard for analyzing India's top 100 equities.</strong>
  </p>
</div>

---

## 🚀 Overview

The **Nifty 100 Financial Intelligence Platform** is a full-stack, automated financial analytics engine designed to parse, analyze, and visualize 10-year historical fundamental data for the NSE Nifty 100 universe.

Built entirely in Python, this platform synthesizes data from complex Excel models into a blazing-fast SQLite database, wrapped in a beautiful, enterprise-themed Streamlit UI. 

## ✨ Key Features

- **📊 Comprehensive Executive Dashboard:** Live KPI aggregates, Plotly donut charts for sector distributions, and auto-computed composite quality scores.
- **🏢 Deep-Dive Company Profiles:** Instant 10-year trend rendering (Revenue, Net Profit, ROE, ROCE) alongside dynamically generated qualitative Pros & Cons tags.
- **⚡ Lightning Fast Screener:** Filter all 100 companies instantly using 10 custom metrics and 6 algorithmic presets (e.g., *Debt-Free Blue Chip*, *Quality Compounder*).
- **👥 Peer Radar Comparisons:** Compare any stock against its sector benchmark using automated 8-axis Plotly radar charts and percentile-ranked KPI tables.
- **🧩 Capital Allocation Mapping:** Interactive treemap visualizing historical capital allocation patterns across the entire index.
- **💰 Algorithmic Valuation Module:** Standalone analytical engine to calculate FCF yields, EV/EBITDA, and automatically flag stocks trading at a premium or discount to their 5-year sector median.

## 📁 Repository Structure

```text
Nifty100-Financial-Intelligence/
├── data/                  # Raw and synthesized Excel models (Market Cap, Peer Groups)
├── output/                # Generated analytics (Capital Allocation, Valuation Flags)
├── src/
│   ├── analytics/         # Valuation and peer comparison engines
│   ├── dashboard/         # Streamlit frontend architecture
│   │   ├── app.py         # Main application entry point
│   │   ├── pages/         # 8 interactive dashboard screens
│   │   └── utils/db.py    # @st.cache_data optimized SQLite queries
│   └── screener/          # Core screening and composite score logic
├── tests/                 # 130+ Pytest unit and integration tests
├── nifty100.db            # Processed financial data warehouse
└── requirements.txt       # Cloud deployment dependencies
```

## 💻 Local Installation

To run this platform locally on your machine:

```bash
# 1. Clone the repository
git clone https://github.com/123dars/Nifty100-Financial-Intelligence.git
cd Nifty100-Financial-Intelligence

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the dashboard
python -m streamlit run src/dashboard/app.py
```
> *The platform will automatically launch in your browser at `http://localhost:8501`.*

## ☁️ Cloud Deployment

This repository is pre-configured for instant deployment on **Streamlit Community Cloud**. 
1. Log into [share.streamlit.io](https://share.streamlit.io/)
2. Create a new app pointing to this repository.
3. Set the Main file path to `src/dashboard/app.py`.
4. Click Deploy.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Development Team

This platform was architected and developed by:
- **Priya Singh**
- **Vinay Todkar**
- **Darshan B**
