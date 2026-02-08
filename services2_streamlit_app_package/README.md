# Services 2.0 Calculator (Streamlit)

This is a Streamlit app that reads your canonical **Services 2.0 Excel workbook** (the one with a `Data` sheet)
and provides:

- **City Demand & Build Plan**: enter home counts, compute total demand, pick one utility per service, get buildings needed + total cost.
- **Scenario Builder**: compare mixes by selecting service + utility + level + quantity (e.g. 3× Fusion L5 vs 2× Fusion L10).

## Quick start (local)

### 1) Create a virtualenv (recommended)
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Put your Excel file in /data (optional)
Place your canonical workbook at:
`data/Services_2_Calculator.xlsx`

Or just upload it in the UI after starting the app.

### 4) Run the app
```bash
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Push this folder to GitHub.
2. In Streamlit Cloud, select the repo and set the main file to `app.py`.
3. Either:
   - upload the workbook in the app UI each time, OR
   - commit the workbook into `data/Services_2_Calculator.xlsx` (only if you’re OK making it public).

## Notes
- The app expects the workbook to have a `Data` sheet with columns:
  `Service, Building, Level, Capacity, CumCost, MaxLevel`
- Costs are taken from `CumCost` (cumulative cost to reach that level).
