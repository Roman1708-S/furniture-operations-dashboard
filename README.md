# Furniture Operations Dashboard

A starter analytics project for a custom furniture business. It calculates direct profitability for every order while keeping **materials** and **components** as separate cost categories.

## What it does

- reads orders, inventory catalogues, labour rates, and item usage from an Excel workbook;
- calculates material, component, delivery, and labour costs per order;
- calculates direct margin, profit after labour, and profit per work hour;
- exports a clean CSV report that can later power a Streamlit dashboard.

## Project files

| File | Purpose |
| --- | --- |
| `furniture_operations_starter.xlsx` | Source model: orders, catalogues, labour rates, and usage records |
| `calculate_order_profitability.py` | Profitability calculation script |
| `order_profitability_report.csv` | Example output for January–April 2026 |

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python calculate_order_profitability.py furniture_operations_starter.xlsx --output outputs/order_profitability_report.csv
```

## Run the dashboard

```bash
streamlit run app.py
```

The dashboard includes filters for city, product, status, and date; KPI cards;
profitability charts; and an order-level review table.

## Current metrics

The included example report covers eight orders in the Vancouver area from January to April 2026. It includes revenue, direct cost, labour cost, profit after labour, margin, work hours, repeat visits, and delivery issues.

## Next step

Build a Streamlit interface to filter orders by city, product, status, and period; then add KPI cards and profitability charts.

> The figures in this repository are a sample operating model for learning and portfolio purposes.
