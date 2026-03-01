# SandTech Forward Deployed Engineer Role Assessment
This entails source code and setup/run instructions for the Sandtech FDE Role Recruitment Assessment for Sierra Leone by Mohamed Fofanah


# Quarterly Health Bulletin Dashboard

This repository contains a **Dash-based interactive dashboard** for the **Ministry of Health Quarterly Health Bulletin**
as the Sandtech FDE Role Recruitment Assessment for Sierra Leone by Mohamed Fofanah. The dashboard provides insights into:

* Top 10 facilities by patient volume
* Facility performance (reporting completeness)
* QoQ trends for deliveries
* Interactive filters by Year-Quarter, Province, and Facility
* KPI table for bulletin-ready reporting

> **Note:** ANC visits, maternal complications, and reporting timeliness are not included due to dataset schema limitations.

---

## 📦 Requirements

* Python 3.10
* Pip (or virtual environment tool of your choice)

The required Python packages are listed in `requirements.txt`.

---

## ⚙️ Setup Instructions

1. **Clone the repository**

```bash
git clone https://github.com/LinuxFofinspiron/sand_fde_assessment.git
cd sand_fde_assessment
```

2. **Create a virtual environment** (optional but recommended)

```bash
python3.10 -m venv venv
```

3. **Activate the virtual environment**

* **Linux / macOS:**

```bash
source venv/bin/activate
```

* **Windows:**

```bash
venv\Scripts\activate
```

4. **Install dependencies**

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🚀 Running the Dashboard

The main entry point for the dashboard is `bulletin.py`.

Run the Dash app with:

```bash
python bulletin.py
```

By default, the dashboard will start on:

```
http://127.0.0.1:1997
```

Open this URL in your web browser to interact with the dashboard.

---

## 📝 Features

* **Interactive Filters**: Year-Quarter, Province, Facility
* **Top 10 Bar Chart**: Facility ranking by deliveries
* **Trend Line Chart**: Total deliveries over the last 4 quarters
* **KPI Table**: Displays deliveries, reporting completeness, QoQ change
* **Missing KPIs Note**: Clearly indicates KPIs not included

---

## 📄 File Structure

```text
quarterly-health-bulletin/
│
├─ bulletin.py             # Main Dash app entrypoint
├─ requirements.txt        # Python dependencies
└─ README.md
```

---

## 🔧 Notes

* Developed with **Python 3.10**.
* Ensure all dependencies in `requirements.txt` are installed.
* Script Auto-downloads csv files from Google Drive into dataset folder which is created automatically.
* Datasets are merged and formatted using Pandas. 
* Dataset preprocessing with `year_quarter` column as `YYYY_QX` done with Pandas date manipulation methods.
* Preprocessed flat file after merging and formatting is saved as dhis2_flat.csv in processed folder
* Analytics are being computed against the merged DHIS2 flat file
* Dash app is fully interactive; filters will update charts and table dynamically.

---

## 🧾 Future Enhancements
* Fully fledged ETL pipeline with job scheduling using Crontab or Apache Airflow
* Leverage a traditional RDBMS or Big Data as the system scales
* Add **downloadable Excel/PDF** export for automated bulletin generation.
* Include additional KPIs when the dataset is updated (ANC visits, maternal complications, reporting timeliness).
* Dockerize Build
* Utilize Apache Superset or Metabase for Dashboard

`Author: Ing. Mohamed Fofanah`