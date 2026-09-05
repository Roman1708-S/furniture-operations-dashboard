"""Calculate direct profitability by furniture order.

The input workbook keeps materials and components separate. This script prices
each usage line using the matching inventory catalogue and produces one clean
row per order for the future Streamlit dashboard.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def price_usage(usage: pd.DataFrame, catalogue: pd.DataFrame, item_id: str, cost_name: str) -> pd.DataFrame:
    """Return direct cost per order, while failing clearly on unknown SKU IDs."""
    priced = usage.merge(
        catalogue[[item_id, "Unit Cost (C$)"]],
        how="left",
        on=item_id,
        validate="many_to_one",
    )
    missing = priced.loc[priced["Unit Cost (C$)"].isna(), item_id].unique().tolist()
    if missing:
        raise ValueError(f"Missing unit cost for {item_id}: {', '.join(missing)}")

    priced[cost_name] = priced["Quantity Used"] * priced["Unit Cost (C$)"]
    return priced.groupby("Order ID", as_index=False)[cost_name].sum()


def calculate(workbook_path: Path, output_path: Path) -> pd.DataFrame:
    # Row 3 contains the field names; rows 1–2 are the workbook title area.
    read_options = {"header": 2}
    orders = pd.read_excel(workbook_path, sheet_name="Orders", **read_options)
    materials = pd.read_excel(workbook_path, sheet_name="Materials", **read_options)
    components = pd.read_excel(workbook_path, sheet_name="Components", **read_options)
    labour_rates = pd.read_excel(workbook_path, sheet_name="Labour Rates", **read_options)
    material_usage = pd.read_excel(workbook_path, sheet_name="Material Usage", **read_options)
    component_usage = pd.read_excel(workbook_path, sheet_name="Component Usage", **read_options)

    material_cost = price_usage(material_usage, materials, "Material ID", "Material Cost (C$)")
    component_cost = price_usage(component_usage, components, "Component ID", "Component Cost (C$)")
    rates = labour_rates.set_index("Work Type")["Hourly Rate (C$)"].to_dict()
    required_rates = {"Production", "Installation"}
    if set(rates) != required_rates:
        missing = required_rates - set(rates)
        raise ValueError(f"Labour Rates must contain Production and Installation. Missing: {', '.join(missing)}")

    report = (
        orders.merge(material_cost, how="left", on="Order ID")
        .merge(component_cost, how="left", on="Order ID")
        .fillna({"Material Cost (C$)": 0, "Component Cost (C$)": 0})
    )
    report["Direct Cost (C$)"] = (
        report["Material Cost (C$)"]
        + report["Component Cost (C$)"]
        + report["Delivery Cost (C$)"]
    )
    report["Gross Profit Before Labour (C$)"] = report["Revenue (C$)"] - report["Direct Cost (C$)"]
    report["Direct Margin (%)"] = report["Gross Profit Before Labour (C$)"] / report["Revenue (C$)"]
    report["Production Labour Rate (C$/hr)"] = rates["Production"]
    report["Installation Labour Rate (C$/hr)"] = rates["Installation"]
    report["Production Labour Cost (C$)"] = report["Production Hrs"] * report["Production Labour Rate (C$/hr)"]
    report["Installation Labour Cost (C$)"] = report["Install Hrs"] * report["Installation Labour Rate (C$/hr)"]
    report["Total Labour Cost (C$)"] = report["Production Labour Cost (C$)"] + report["Installation Labour Cost (C$)"]
    report["Profit After Labour (before overhead) (C$)"] = report["Gross Profit Before Labour (C$)"] - report["Total Labour Cost (C$)"]
    report["Margin After Labour (%)"] = report["Profit After Labour (before overhead) (C$)"] / report["Revenue (C$)"]
    report["Total Work Hours"] = report["Production Hrs"] + report["Install Hrs"]
    report["Profit After Labour / Work Hour (C$)"] = (
        report["Profit After Labour (before overhead) (C$)"] / report["Total Work Hours"]
    )

    columns = [
        "Order ID", "Order Date", "City", "Product", "Status", "Revenue (C$)",
        "Material Cost (C$)", "Component Cost (C$)", "Delivery Cost (C$)",
        "Direct Cost (C$)", "Gross Profit Before Labour (C$)", "Direct Margin (%)",
        "Production Hrs", "Install Hrs", "Production Labour Rate (C$/hr)",
        "Installation Labour Rate (C$/hr)", "Production Labour Cost (C$)",
        "Installation Labour Cost (C$)", "Total Labour Cost (C$)",
        "Profit After Labour (before overhead) (C$)", "Margin After Labour (%)",
        "Total Work Hours", "Profit After Labour / Work Hour (C$)",
        "Repeat Visits", "Issue",
    ]
    report = report[columns].sort_values("Order ID")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(output_path, index=False, float_format="%.2f")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate furniture-order direct profitability.")
    parser.add_argument("workbook", type=Path, help="Path to furniture_operations_starter.xlsx")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/furniture_operations/order_profitability_report.csv"),
        help="Where to save the calculated report CSV.",
    )
    args = parser.parse_args()

    report = calculate(args.workbook, args.output)
    summary = report[["Revenue (C$)", "Direct Cost (C$)", "Total Labour Cost (C$)", "Profit After Labour (before overhead) (C$)"]].sum()
    print(f"Processed {len(report)} orders")
    print(f"Revenue: C${summary['Revenue (C$)']:,.2f}")
    print(f"Direct cost: C${summary['Direct Cost (C$)']:,.2f}")
    print(f"Labour cost: C${summary['Total Labour Cost (C$)']:,.2f}")
    print(f"Profit after labour (before overhead): C${summary['Profit After Labour (before overhead) (C$)']:,.2f}")
    print(f"Saved report: {args.output}")


if __name__ == "__main__":
    main()
