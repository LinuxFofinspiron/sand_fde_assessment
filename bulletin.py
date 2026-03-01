# dash_quarterly_health_bulletin_full_with_facility.py
import os # File and directory operations

import gdown # Downloading files from Google Drive
import pandas as pd # Data manipulation

from dash import Dash, dcc, html, dash_table # Dashboard Layout and Design
from dash.dependencies import Input, Output # Dashboard Interactivity

import plotly.express as px # Chart Design

# -------------------------------------------- Data Preparation Steps ------------------------------------------------------------
# If processed dataset already exists, skip data preparation steps
if os.path.exists("./processed/dhis2_flat.csv"):
    print("Processed dataset already exists. Skipping data preparation steps.")
else:
    # Fetch the datasets from Google Drive

    # Define the Google Drive file IDs and output file paths
    file_ids = {
        "clinical_neonatal": "1h9FDzHw6IXqV0ndq4ZAbhbQuRRK_pqE8",
        "facilities": "1_TeF2731LCDdjIJWHeNGnIiG1AS2vtSF",
        "governance": "1reVIu7yZp-grt1QqNVcZX2z-acRMUb4j",
        "healthcare_workers": "1qBX7fGyEoagkphBqJEHjk2G-vmPnwrLa",
        "operations": "14EouJuR5JJk6b0uTe_C4jWvC0AQ4jJi9"
    }

    output_files = {
        "clinical_neonatal": "./dataset/clinical_neonatal.csv",
        "facilities": "./dataset/facilities.csv",
        "governance": "./dataset/governance.csv",
        "healthcare_workers": "./dataset/healthcare_workers.csv",
        "operations": "./dataset/operations.csv"
    }

    # Create the dataset directory if it doesn't exist
    os.makedirs("./dataset", exist_ok=True)
    
    # Download the files using gdown if it doesn't exist
    for key in file_ids:
        if not os.path.exists(output_files[key]):
            gdown.download(f"https://drive.google.com/uc?id={file_ids[key]}", output_files[key], quiet=False)
    

    # Load the datasets
    clinicalNeonatalDf = pd.read_csv("./dataset/clinical_neonatal.csv")
    facilitiesDf = pd.read_csv("./dataset/facilities.csv")
    governanceDf = pd.read_csv("./dataset/governance.csv")
    healthcareworkersDf = pd.read_csv("./dataset/healthcare_workers.csv")
    operationsDf = pd.read_csv("./dataset/operations.csv")


    # Merge the datasets using the common column 'facility_id'
    df = facilitiesDf.merge(clinicalNeonatalDf, on="facility_id", how="left")
    df = df.merge(governanceDf, on="facility_id", how="left")
    df = df.merge(healthcareworkersDf, on="facility_id", how="left")
    df = df.merge(operationsDf, on="facility_id", how="left")

    # # Display the columns of the merged DataFrame
    # print(df.columns)

    # # Display column datatypes
    # print(df.dtypes)

    # Convert reporting_month to datetime
    df['reporting_month'] = pd.to_datetime(
        df['reporting_month'],
        format='%Y-%m',
        errors='coerce'  # prevents crash if bad format exists
    )

    # Create reporting_quarter (Q1–Q4)
    df['reporting_quarter'] = 'Q' + df['reporting_month'].dt.quarter.astype(str)

    # Create year_quarter (bulletin-safe key)
    df['year_quarter'] = (
        df['reporting_month'].dt.year.astype(str) +
        '_Q' +
        df['reporting_month'].dt.quarter.astype(str)
    )

    # Create processed directory if it doesn't exist
    os.makedirs("./processed", exist_ok=True)

    # Save the merged dataset to a new CSV file
    df.to_csv("./processed/dhis2_flat.csv", index=False)

    # export column names with corresponding datatypes to a text file
    with open("./processed/dhis2_columns.txt", "w") as f:
        for column in df.columns:
            f.write(f"{column}: {df[column].dtype}\n")


# ------------------------------------------------------------ Analytics Steps ------------------------------------------------------------
# -----------------------------
# Load processed flat dataset
# -----------------------------
df = pd.read_csv("./processed/dhis2_flat.csv")


# -----------------------------
# Compute Top 10 Facilities by Total Deliveries per Quarter
# -----------------------------
quarterly_deliveries = (
    df.groupby(['year_quarter', 'facility_id', 'facility_name', 'district', 'province'], as_index=False)
      .agg(total_deliveries_qtr=('total_deliveries', 'sum'))
)

quarterly_deliveries['facility_rank'] = (
    quarterly_deliveries.groupby('year_quarter')['total_deliveries_qtr']
    .rank(method='dense', ascending=False)
)

top10_facilities = quarterly_deliveries[quarterly_deliveries['facility_rank'] <= 10].sort_values(['year_quarter', 'facility_rank'])

# -----------------------------
# Facility performance (reporting completeness)
# -----------------------------
df['hmis_reporting_completeness_num'] = pd.to_numeric(df['hmis_reporting_completeness'].str.rstrip('%'), errors='coerce')

performance_scores = (
    df.groupby(['year_quarter', 'facility_id'], as_index=False)
      .agg(reporting_completeness=('hmis_reporting_completeness_num', 'mean'))
)

top10_facilities = top10_facilities.merge(performance_scores, on=['year_quarter','facility_id'], how='left')

# -----------------------------
# Compute QoQ trend
# -----------------------------
top10_facilities = top10_facilities.sort_values(['facility_id','year_quarter'])
top10_facilities['deliveries_qoq_change_pct'] = (
    top10_facilities.groupby('facility_id')['total_deliveries_qtr'].pct_change() * 100
)
top10_facilities['deliveries_qoq_change_pct'] = top10_facilities['deliveries_qoq_change_pct'].round(2)
top10_facilities['reporting_completeness'] = top10_facilities['reporting_completeness'].round(2)

#------------------------------ Visualization and Dashboard Building Steps -----------------------------

# -----------------------------
# Build Dash App
# -----------------------------
app = Dash(__name__)
app.title = "MoH Quarterly Health Bulletin"

# -----------------------------
# Layout
# -----------------------------

app.layout = html.Div([
    
    html.Div([
    html.H1("Quarterly Health Bulletin for Ministry of Health", style={'textAlign':'center', 'color':'#2c3e50'}),
    
    # html.Hr(style={'borderColor':'#2c3e50'}),
        
    # Filters
    html.Div([
        html.Label("Select Year-Quarter:"),
        dcc.Dropdown(
            id='quarter-dropdown',
            options=[{'label': q, 'value': q} for q in sorted(top10_facilities['year_quarter'].unique())],
            value=sorted(top10_facilities['year_quarter'].unique())[-1]
        ),
    ], style={'width':'30%', 'margin':'10px', 'display':'inline-block'}),
    
    html.Div([
        html.Label("Select Province:"),
        dcc.Dropdown(
            id='province-dropdown',
            options=[{'label': p, 'value': p} for p in sorted(top10_facilities['province'].unique())],
            value=None,
            placeholder="All Provinces",
        ),
    ], style={'width':'30%', 'margin':'10px', 'display':'inline-block'}),
    
    html.Div([
        html.Label("Select Facility:"),
        dcc.Dropdown(
            id='facility-dropdown',
            options=[{'label': f, 'value': f} for f in sorted(top10_facilities['facility_name'].unique())],
            value=None,
            placeholder="All Facilities"
        ),
    ], style={'width':'30%', 'margin':'10px', 'display':'inline-block'})
       
    ], 
    style={'border':'1px solid #2c3e50', 'padding':'10px', 'borderRadius':'5px', 'backgroundColor':'#ecf0f1', 'textAlign':'center', 'font-weight':'bold', 'position':'sticky', 'top':'0', 'zIndex':'1000'}),
     
    # html.Hr(style={'borderColor':'#2c3e50'}),   
    
    # Top 10 Bar Chart
    dcc.Graph(id='top10-bar-chart'),

    # Trend Line Chart
    dcc.Graph(id='deliveries-trend-line'),

    # KPI Table
    dash_table.DataTable(
        id='kpi-table',
        columns=[
            {'name':'Facility Rank','id':'facility_rank'},
            {'name':'Facility Name','id':'facility_name'},
            {'name':'District','id':'district'},
            {'name':'Province','id':'province'},
            {'name':'Total Deliveries','id':'total_deliveries_qtr'},
            {'name':'Reporting Completeness (%)','id':'reporting_completeness'},
            {'name':'QoQ Change (%)','id':'deliveries_qoq_change_pct'},
        ],
        style_table={'overflowX':'auto',},
        style_cell={'textAlign':'center'},
        style_header={'backgroundColor':'#2c3e50', 'color':'white', 'fontWeight':'bold'},
        page_size=10
    ),

    # Note on missing KPIs
    html.Div([
        html.P("Note: ANC visits, maternal complications, and reporting timeliness are not included because they are not present in the dataset schema.", style={'color':'red'})
    ], style={'marginTop':'20px', 'textAlign':'center'}),
    html.Footer("Data Source: DHIS2 Files | Author: Mohamed Fofanah for SandTech FDE Assessment", 
                style={'textAlign':'center', 'color':'white','background-color':'darkgray' ,'marginTop':'20px','font-family':'Arial, sans-serif', 'padding':'10px','position':'relative', 'bottom':'0', 'width':'100%'})
])

# -----------------------------
# Callback for all charts and table
# -----------------------------
@app.callback(
    [Output('top10-bar-chart', 'figure'),
     Output('deliveries-trend-line', 'figure'),
     Output('kpi-table', 'data')],
    [Input('quarter-dropdown', 'value'),
     Input('province-dropdown', 'value'),
     Input('facility-dropdown', 'value')]
)
def update_dashboard(selected_quarter, selected_province, selected_facility):
    filtered = top10_facilities[top10_facilities['year_quarter']==selected_quarter]
    
    if selected_province:
        filtered = filtered[filtered['province']==selected_province]
    
    if selected_facility:
        filtered = filtered[filtered['facility_name']==selected_facility]

    # Top 10 Bar Chart
    bar_fig = px.bar(
        filtered,
        x='facility_name',
        y='total_deliveries_qtr',
        color='facility_rank',
        text='total_deliveries_qtr',
        hover_data=['reporting_completeness','deliveries_qoq_change_pct'],
        labels={'total_deliveries_qtr':'Total Deliveries','facility_name':'Facility'},
        title=f"Top Facilities by Patient Volume - {selected_quarter}"
    )
    bar_fig.update_layout(xaxis_tickangle=-45)

    # Trend Line Chart - last 4 quarters
    last_4_quarters = sorted(top10_facilities['year_quarter'].unique())[-4:]
    trend_filtered = top10_facilities[top10_facilities['year_quarter'].isin(last_4_quarters)]
    
    if selected_province:
        trend_filtered = trend_filtered[trend_filtered['province']==selected_province]
    if selected_facility:
        trend_filtered = trend_filtered[trend_filtered['facility_name']==selected_facility]

    trend_fig = px.line(
        trend_filtered,
        x='year_quarter',
        y='total_deliveries_qtr',
        color='facility_name',
        markers=True,
        labels={'year_quarter':'Year-Quarter','total_deliveries_qtr':'Total Deliveries','facility_name':'Facility'},
        title=f"Total Deliveries Trend - Last 4 Quarters"
    )
    trend_fig.update_layout(xaxis_tickangle=-45)

    # Table data
    table_data = filtered.to_dict('records')
    
    return bar_fig, trend_fig, table_data

# -----------------------------
# Run app
# -----------------------------
if __name__ == '__main__':
    app.run(debug=True)