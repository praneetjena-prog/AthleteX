# AthleteX Streamlit Dashboard

A Streamlit dashboard for the AthleteX sports performance database.

## Pages
- **Overview:** key counts, athlete leaderboard, medal distribution
- **Athletes:** searchable directory and selected-athlete telemetry
- **Training:** training workload table and chart
- **Telemetry:** daily trends and threshold-based review flags
- **Competitions:** sport-wise registration and medal analytics

## Requirements
- Python 3.10+
- CockroachDB Cloud connection URL for database `athletex`
- Existing AthleteX schema, `athlete_performance_summary` view, and `competition_sport` table

## Setup (Windows PowerShell)

1. Extract this ZIP and open PowerShell in the `AthleteX_Streamlit_Dashboard` folder.
2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install packages:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. In `.streamlit`, copy `secrets.toml.example` to `secrets.toml`.
5. In CockroachDB Cloud, open `athletex-db` → **Connect**. Choose the Python/psycopg2 connection option or copy the general connection URL. Paste the full URL into `DATABASE_URL` in `secrets.toml`. Preserve the SSL settings and certificate path supplied by Cloud.
6. Start the app:

   ```powershell
   streamlit run app.py
   ```

## Security
Do not share your password or connection URL in chat, commit `secrets.toml`, or disable SSL verification to work around certificate errors.

## Data note
Telemetry is synthetic project data. Threshold flags demonstrate SQL logic and are not medical assessments.
