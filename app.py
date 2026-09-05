"""Interactive operating dashboard for furniture-order profitability."""

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


REPORT_PATH = Path(__file__).with_name("order_profitability_report.csv")


@st.cache_data
def load_report(path: Path) -> pd.DataFrame:
    """Load the order-level report and prepare dashboard fields."""
    report = pd.read_csv(path, parse_dates=["Order Date"])
    report["Issue"] = report["Issue"].fillna("").replace("", "No issue")
    report["Margin After Labour (%)"] = report["Margin After Labour (%)"].fillna(0)
    return report


def cad(value: float) -> str:
    return f"C${value:,.0f}"


def pct(value: float) -> str:
    return f"{value:.1%}"


st.set_page_config(page_title="Furniture Operations Dashboard", page_icon="📊", layout="wide")
st.title("📊 Furniture Operations Dashboard")
st.caption("Order profitability after direct material, component, delivery, and labour costs")

report = load_report(REPORT_PATH)

with st.sidebar:
    st.header("Filters")
    start_date, end_date = st.date_input(
        "Order date",
        value=(report["Order Date"].min().date(), report["Order Date"].max().date()),
        min_value=report["Order Date"].min().date(),
        max_value=report["Order Date"].max().date(),
    )
    cities = st.multiselect("City", sorted(report["City"].unique()), default=sorted(report["City"].unique()))
    products = st.multiselect("Product", sorted(report["Product"].unique()), default=sorted(report["Product"].unique()))
    statuses = st.multiselect("Status", sorted(report["Status"].unique()), default=sorted(report["Status"].unique()))

filtered = report.loc[
    report["Order Date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))
    & report["City"].isin(cities)
    & report["Product"].isin(products)
    & report["Status"].isin(statuses)
].copy()

if filtered.empty:
    st.warning("No orders match these filters. Try expanding the selection.")
    st.stop()

revenue = filtered["Revenue (C$)"].sum()
direct_cost = filtered["Direct Cost (C$)"].sum()
labour_cost = filtered["Total Labour Cost (C$)"].sum()
profit = filtered["Profit After Labour (before overhead) (C$)"].sum()
margin = profit / revenue if revenue else 0

first, second, third, fourth, fifth = st.columns(5)
first.metric("Revenue", cad(revenue))
second.metric("Direct cost", cad(direct_cost))
third.metric("Labour cost", cad(labour_cost))
fourth.metric("Profit after labour", cad(profit))
fifth.metric("Margin after labour", pct(margin))

st.subheader("Profitability overview")
left, right = st.columns(2)

with left:
    by_product = (
        filtered.groupby("Product", as_index=False)["Profit After Labour (before overhead) (C$)"]
        .sum()
        .sort_values("Profit After Labour (before overhead) (C$)", ascending=False)
    )
    product_chart = px.bar(
        by_product,
        x="Product",
        y="Profit After Labour (before overhead) (C$)",
        color="Profit After Labour (before overhead) (C$)",
        color_continuous_scale="Blues",
        title="Profit after labour by product",
        labels={"Profit After Labour (before overhead) (C$)": "Profit (C$)"},
    )
    product_chart.update_layout(coloraxis_showscale=False, yaxis_tickprefix="C$")
    st.plotly_chart(product_chart, width="stretch")

with right:
    by_city = filtered.groupby("City", as_index=False).agg(
        revenue=("Revenue (C$)", "sum"),
        profit=("Profit After Labour (before overhead) (C$)", "sum"),
    )
    by_city["Margin after labour"] = by_city["profit"] / by_city["revenue"]
    city_chart = px.bar(
        by_city.sort_values("Margin after labour", ascending=False),
        x="City",
        y="Margin after labour",
        color="Margin after labour",
        color_continuous_scale="Tealgrn",
        title="Margin after labour by city",
        labels={"Margin after labour": "Margin"},
    )
    city_chart.update_layout(coloraxis_showscale=False, yaxis_tickformat=".0%")
    st.plotly_chart(city_chart, width="stretch")

monthly = filtered.assign(Month=filtered["Order Date"].dt.to_period("M").astype(str)).groupby("Month", as_index=False).agg(
    Revenue=("Revenue (C$)", "sum"),
    Profit=("Profit After Labour (before overhead) (C$)", "sum"),
)
trend = monthly.melt(id_vars="Month", var_name="Metric", value_name="Amount (C$)")
trend_chart = px.line(
    trend,
    x="Month",
    y="Amount (C$)",
    color="Metric",
    markers=True,
    title="Monthly revenue and profit after labour",
)
trend_chart.update_layout(yaxis_tickprefix="C$")
st.plotly_chart(trend_chart, width="stretch")

st.subheader("Orders to review")
review = filtered.assign(
    **{"Margin after labour": filtered["Margin After Labour (%)"].map(pct)}
)[[
    "Order ID", "Order Date", "City", "Product", "Status", "Revenue (C$)",
    "Profit After Labour (before overhead) (C$)", "Margin after labour", "Repeat Visits", "Issue",
]].sort_values("Profit After Labour (before overhead) (C$)")
st.table(review)

st.caption("Source: order_profitability_report.csv. Values are a sample operating model for learning and portfolio purposes.")
