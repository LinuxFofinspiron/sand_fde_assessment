import gdown
import pandas as pd
import os

# Fetch the datasets from Google Drive

# Define the Google Drive file IDs and output file names
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

# Display the columns of the merged DataFrame
print(df.columns)

# Display column datatypes
print(df.dtypes)

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

# Create output directory for analytics results if it doesn't exist
os.makedirs("./analytics_output", exist_ok=True)
        
# Compute Analytics

## Top 10 facilities by patient volume per quarter
# Step 1: Aggregate total deliveries per facility per quarter
quarterly_deliveries = (
    df.groupby(['year_quarter', 'facility_id', 'facility_name', 'district', 'province'], as_index=False)
      .agg(total_deliveries_qtr=('total_deliveries', 'sum'))
)

# Step 2: Rank facilities within each quarter
quarterly_deliveries['facility_rank'] = (
    quarterly_deliveries
    .groupby('year_quarter')['total_deliveries_qtr']
    .rank(method='dense', ascending=False)
)

# Step 3: Filter to top 10 per quarter
top10_facilities = quarterly_deliveries[quarterly_deliveries['facility_rank'] <= 10]

# Step 4: Sort for bulletin display
top10_facilities = top10_facilities.sort_values(['year_quarter', 'facility_rank'])

# Display
top10_facilities.reset_index(drop=True, inplace=True)
print(top10_facilities)

# Save the top 10 facilities per quarter to a CSV file in the output directory
top10_facilities.to_csv("./analytics_output/top10_facilities_per_quarter.csv", index=False)

## maternal health indicators (ANCvisits, deliveries, complications)




# ----------------------------
# Ensure reporting_month is datetime
# ----------------------------
df['reporting_month'] = pd.to_datetime(
    df['reporting_month'], format='%Y-%m', errors='coerce'
)

# Create reporting_quarter (Q1–Q4)
df['reporting_quarter'] = 'Q' + df['reporting_month'].dt.quarter.astype(str)

# Create year_quarter (bulletin-ready key)
df['year_quarter'] = df['reporting_month'].dt.year.astype(str) + '_Q' + df['reporting_month'].dt.quarter.astype(str)

# ----------------------------
# 1. Top 10 Facilities by Patient Volume
# ----------------------------
# Aggregate total deliveries per facility per quarter
quarterly_deliveries = (
    df.groupby(['year_quarter', 'facility_id', 'facility_name', 'district', 'province'], as_index=False)
      .agg(total_deliveries_qtr=('total_deliveries', 'sum'))
)

# Rank facilities within each quarter
quarterly_deliveries['facility_rank'] = (
    quarterly_deliveries
    .groupby('year_quarter')['total_deliveries_qtr']
    .rank(method='dense', ascending=False)
)

# Filter top 10 facilities per quarter
top10_facilities = quarterly_deliveries[quarterly_deliveries['facility_rank'] <= 10].sort_values(
    ['year_quarter', 'facility_rank']
)

# ----------------------------
# 2. Maternal Health Indicators
# ----------------------------
# Aggregate per facility per quarter
maternal_indicators = df.groupby(
    ['year_quarter', 'facility_id', 'facility_name', 'district', 'province'], as_index=False
).agg(
    total_deliveries=('total_deliveries', 'sum'),
    # ANC Visits cannot be computed: no ANC field in current schema
    anc_visits=('total_deliveries', 'sum'),  # Placeholder column; replace with DHIS2 ANC data when available
    # Maternal complications cannot be computed: no maternal complication fields in current schema
    maternal_complications=('total_deliveries', lambda x: 0)  # Placeholder column
)

# Compute complication rate (will be zero due to placeholder)
maternal_indicators['complication_rate_pct'] = (
    maternal_indicators['maternal_complications'] / maternal_indicators['total_deliveries'] * 100
)

# ----------------------------
# 3. Facility Performance Scores
# ----------------------------
# Reporting completeness
# Convert hmis_reporting_completeness to numeric (if string like "95%")
maternal_indicators = maternal_indicators.merge(
    df.groupby(['year_quarter', 'facility_id'], as_index=False).agg(
        reporting_completeness=('hmis_reporting_completeness', 
                                lambda x: pd.to_numeric(x.str.rstrip('%'), errors='coerce').mean())
    ),
    on=['year_quarter', 'facility_id'],
    how='left'
)

# Reporting timeliness cannot be computed: no field in schema
# Composite performance score: only completeness is available
maternal_indicators['performance_score'] = maternal_indicators['reporting_completeness']  # Partial score

# ----------------------------
# 4. Trend Analysis vs Previous Quarter
# ----------------------------
# Example: compute QoQ change for total deliveries
maternal_indicators = maternal_indicators.sort_values(['facility_id', 'year_quarter'])
maternal_indicators['deliveries_qoq_change_pct'] = (
    maternal_indicators.groupby('facility_id')['total_deliveries']
    .pct_change() * 100
)

# ANC and maternal complications QoQ cannot be computed reliably without DHIS2 data

# ----------------------------
# 5. Merge Top 10 Facilities with Maternal Indicators
# ----------------------------
bulletin_df = top10_facilities.merge(
    maternal_indicators[['year_quarter','facility_id','anc_visits','maternal_complications',
                         'complication_rate_pct','reporting_completeness','performance_score',
                         'deliveries_qoq_change_pct']],
    on=['year_quarter','facility_id'],
    how='left'
)

# ----------------------------
# Bulletin-ready DataFrame
# ----------------------------
# Columns include:
# - year_quarter
# - facility_rank
# - facility_id, facility_name, district, province
# - total_deliveries_qtr
# - anc_visits (placeholder)
# - maternal_complications (placeholder)
# - complication_rate_pct (zero)
# - reporting_completeness
# - performance_score (partial)
# - deliveries_qoq_change_pct
bulletin_df.reset_index(drop=True, inplace=True)

# Display top 10 for first quarter as check
bulletin_df[bulletin_df['year_quarter'] == bulletin_df['year_quarter'].unique()[0]]

bulletin_df.to_csv("./analytics_output/bulletin_ready_top10_facilities.csv", index=False)