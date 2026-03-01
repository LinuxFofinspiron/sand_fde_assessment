# app.py

import pandas as pd
import dash
from dash import html, dcc
import plotly.express as px

# ----------------------------
# 1. Load Data
# ----------------------------
data_file = "./dataset/operations.csv"
df = pd.read_csv(data_file)

# ----------------------------
# 2. Validate Required Fields
# ----------------------------
required_fields = [
    "facility_id",
    "avg_referral_time_hrs",
    "referrals_out_monthly",
    "referrals_in_monthly",
    "oxygen_cylinders_available",
    "oxygen_concentrators",
    "oxygen_plant",
    "ambulance_available",
    "kangaroo_care_practiced",
    "essential_drugs_stockouts_days",
    "antibiotics_available",
    "surfactant_available",
    "referral_feedback_rate"
]

for col in required_fields:
    if col not in df.columns:
        raise ValueError(f"Dataset missing required field: {col}")

# ----------------------------
# 3. Data Cleaning
# ----------------------------

# Columns expected to be numeric
numeric_columns = [
    "avg_referral_time_hrs",
    "referrals_out_monthly",
    "referrals_in_monthly",
    "oxygen_cylinders_available",
    "oxygen_concentrators",
    "oxygen_plant",
    "essential_drugs_stockouts_days",
    "referral_feedback_rate"
]

for col in numeric_columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace("%", "", regex=False)
        .str.strip()
    )
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Convert Yes/No columns to binary
binary_columns = [
    "ambulance_available",
    "kangaroo_care_practiced",
    "antibiotics_available",
    "surfactant_available"
]

for col in binary_columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"yes": 1, "no": 0})
    )

# ----------------------------
# 4. Compute Dashboard Metrics
# ----------------------------

# Top 10 referral facilities
top_referrals = df.sort_values(
    by="referrals_out_monthly", ascending=False
).head(10)

# Oxygen capacity totals
oxygen_summary = df[
    ["oxygen_cylinders_available",
     "oxygen_concentrators",
     "oxygen_plant"]
].sum().reset_index()

oxygen_summary.columns = ["Resource", "Total"]

# Referral performance averages
referral_performance = df[
    ["avg_referral_time_hrs",
     "referral_feedback_rate"]
].mean().reset_index()

referral_performance.columns = ["Metric", "Average"]

# Binary availability averages (converted to %)
binary_summary = df[binary_columns].mean() * 100
binary_summary = binary_summary.reset_index()
binary_summary.columns = ["Metric", "Percent (%)"]

# Drug stockout average
stockout_avg = df[["essential_drugs_stockouts_days"]].mean().reset_index()
stockout_avg.columns = ["Metric", "Average Days"]

# ----------------------------
# 5. Build Dash App
# ----------------------------

app = dash.Dash(__name__)
app.title = "MoH Operational Bulletin"

app.layout = html.Div([

    html.H1("Quarterly Operational Bulletin - MoH",
            style={'textAlign': 'center'}),

    # ----------------------------
    # Top Referral Facilities
    # ----------------------------
    html.H2("Top 10 Facilities by Outgoing Referrals"),
    dcc.Graph(
        figure=px.bar(
            top_referrals,
            x="facility_id",
            y="referrals_out_monthly",
            text="referrals_out_monthly",
            labels={
                "facility_id": "Facility ID",
                "referrals_out_monthly": "Monthly Referrals Out"
            },
            title="Top Referral Facilities"
        )
    ),

    # ----------------------------
    # Oxygen Capacity
    # ----------------------------
    html.H2("National Oxygen Capacity Overview"),
    dcc.Graph(
        figure=px.bar(
            oxygen_summary,
            x="Resource",
            y="Total",
            text="Total",
            title="Oxygen & Plant Capacity"
        )
    ),

    # ----------------------------
    # Referral Performance
    # ----------------------------
    html.H2("Referral System Performance"),
    dcc.Graph(
        figure=px.bar(
            referral_performance,
            x="Metric",
            y="Average",
            text="Average",
            title="Average Referral Time & Feedback Rate"
        )
    ),

    # ----------------------------
    # Service Availability
    # ----------------------------
    html.H2("Service & Commodity Availability (%)"),
    dcc.Graph(
        figure=px.bar(
            binary_summary,
            x="Metric",
            y="Percent (%)",
            text="Percent (%)",
            title="Percentage of Facilities with Services"
        )
    ),

    # ----------------------------
    # Drug Stockouts
    # ----------------------------
    html.H2("Average Essential Drug Stockout Days"),
    dcc.Graph(
        figure=px.bar(
            stockout_avg,
            x="Metric",
            y="Average Days",
            text="Average Days",
            title="Average Stockout Duration"
        )
    )

])

# ----------------------------
# 6. Run Server
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)