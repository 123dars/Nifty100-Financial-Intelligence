-- =============================================================================
-- N100 FINANCIAL INTELLIGENCE PLATFORM — EXPLORATORY SQL QUERIES (DAY 05)
-- Database: nifty100.db / data/nifty100.db
-- Purpose: Ingestion audit, schema validation, and financial baseline inspection
-- =============================================================================

-- 1. Universe & Coverage Overview
SELECT COUNT(*) AS total_companies FROM companies;
SELECT COUNT(*) AS total_sectors FROM sectors;

-- 2. Sector Distribution of Nifty 100 Companies
SELECT 
    s.sector_name,
    COUNT(c.company_id) AS company_count,
    ROUND(COUNT(c.company_id) * 100.0 / (SELECT COUNT(*) FROM companies), 1) AS pct_of_index
FROM sectors s
LEFT JOIN companies c ON s.sector_name = c.sector
GROUP BY s.sector_name
ORDER BY company_count DESC;

-- 3. Ingestion Row Counts Audit Across Core Tables
SELECT 'companies' AS table_name, COUNT(*) AS row_count FROM companies
UNION ALL
SELECT 'sectors', COUNT(*) FROM sectors
UNION ALL
SELECT 'profitandloss', COUNT(*) FROM profitandloss
UNION ALL
SELECT 'balancesheet', COUNT(*) FROM balancesheet
UNION ALL
SELECT 'cashflow', COUNT(*) FROM cashflow
UNION ALL
SELECT 'financial_ratios', COUNT(*) FROM financial_ratios
UNION ALL
SELECT 'stock_prices', COUNT(*) FROM stock_prices
UNION ALL
SELECT 'documents', COUNT(*) FROM documents
UNION ALL
SELECT 'prosandcons', COUNT(*) FROM prosandcons
UNION ALL
SELECT 'peer_groups', COUNT(*) FROM peer_groups;

-- 4. Historical Year Coverage per Company in Profit & Loss
SELECT 
    c.ticker,
    c.company_name,
    c.sector,
    COUNT(p.year) AS years_of_pnl,
    MIN(p.year) AS earliest_year,
    MAX(p.year) AS latest_year
FROM companies c
LEFT JOIN profitandloss p ON c.company_id = p.company_id
GROUP BY c.company_id, c.ticker, c.company_name, c.sector
ORDER BY years_of_pnl ASC, c.ticker;

-- 5. Companies with Fewer than 5 Years of History (Limited Coverage Warning)
SELECT 
    c.ticker,
    c.company_name,
    COUNT(p.year) AS pnl_years
FROM companies c
JOIN profitandloss p ON c.company_id = p.company_id
GROUP BY c.company_id, c.ticker, c.company_name
HAVING COUNT(p.year) < 5;

-- 6. Top 10 Companies by FY2024 Revenue (in INR Crore)
SELECT 
    c.ticker,
    c.company_name,
    c.sector,
    p.sales AS revenue_fy24_cr,
    p.operating_profit AS ebitda_fy24_cr,
    p.opm_pct AS opm_fy24_pct,
    p.net_profit AS pat_fy24_cr
FROM companies c
JOIN profitandloss p ON c.company_id = p.company_id
WHERE p.year = 2024
ORDER BY p.sales DESC
LIMIT 10;

-- 7. Top 10 Most Profitable Companies by Net Profit Margin in FY2024
SELECT 
    c.ticker,
    c.company_name,
    c.sector,
    p.sales AS sales_cr,
    p.net_profit AS pat_cr,
    ROUND((p.net_profit * 100.0 / NULLIF(p.sales, 0)), 2) AS npm_calculated_pct
FROM companies c
JOIN profitandloss p ON c.company_id = p.company_id
WHERE p.year = 2024 AND p.sales > 500
ORDER BY npm_calculated_pct DESC
LIMIT 10;

-- 8. Balance Sheet Consistency Check (Total Assets Sanity)
SELECT 
    c.ticker,
    b.year,
    b.total_assets,
    b.equity,
    b.borrowings
FROM balancesheet b
JOIN companies c ON b.company_id = c.company_id
WHERE b.total_assets <= 0 OR b.total_assets IS NULL;

-- 9. Debt-Free Companies Screening (Zero Borrowings in FY2024)
SELECT 
    c.ticker,
    c.company_name,
    c.sector,
    b.borrowings AS debt_fy24_cr,
    b.total_assets AS assets_fy24_cr
FROM companies c
JOIN balancesheet b ON c.company_id = b.company_id
WHERE b.year = 2024 AND (b.borrowings = 0 OR b.borrowings IS NULL)
ORDER BY c.ticker;

-- 10. Cash Flow Conversion: CFO to EBITDA in FY2024
SELECT 
    c.ticker,
    c.company_name,
    p.operating_profit AS ebitda_cr,
    cf.cash_from_operating_activity AS cfo_cr,
    ROUND(cf.cash_from_operating_activity * 1.0 / NULLIF(p.operating_profit, 0), 2) AS cfo_to_ebitda_conversion
FROM companies c
JOIN profitandloss p ON c.company_id = p.company_id
JOIN cashflow cf ON c.company_id = cf.company_id AND p.year = cf.year
WHERE p.year = 2024 AND p.operating_profit > 100
ORDER BY cfo_to_ebitda_conversion DESC
LIMIT 15;

-- 11. Foreign Key Integrity Audit (Checking for Orphan Records)
SELECT 'pnl_orphans' AS check_name, COUNT(*) AS orphan_count 
FROM profitandloss WHERE company_id NOT IN (SELECT company_id FROM companies)
UNION ALL
SELECT 'bs_orphans', COUNT(*) 
FROM balancesheet WHERE company_id NOT IN (SELECT company_id FROM companies)
UNION ALL
SELECT 'cf_orphans', COUNT(*) 
FROM cashflow WHERE company_id NOT IN (SELECT company_id FROM companies)
UNION ALL
SELECT 'ratio_orphans', COUNT(*) 
FROM financial_ratios WHERE company_id NOT IN (SELECT company_id FROM companies);
