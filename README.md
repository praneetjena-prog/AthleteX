# AthleteX — Sports Performance Management System

AthleteX is a distributed sports performance intelligence platform built on CockroachDB Cloud and Streamlit. It provides real-time athlete directory browsing, training workload tracking, wearable telemetry insights, and multi-sport competition analytics.

---

## 🏅 Features & Dashboard Pages

- **Performance Overview**: Key counts (athletes, sports, training sessions, telemetry readings), athlete leaderboard, and medal distribution.
- **Athlete Directory**: Searchable roster with medal tallies, performance evaluations, and individual wearable telemetry time-series charts.
- **Training Workload**: Workload aggregation across athletes, total hours, calories burned, and top-workload bar charts.
- **Wearable Telemetry**: Daily biometric trends (heart rate, training intensity, speed) and automated threshold-based review alerts.
- **Competition & Sport Analytics**: Sport-by-sport athlete registrations, competition tallies, and medal distribution visualizations.

---

## 🛠️ Tech Stack & Requirements

- **Python**: 3.10+
- **Database**: CockroachDB Cloud (`athletex` database)
- **Frontend / UI**: Streamlit 1.38+, Plotly 5.23+
- **Database Driver**: `psycopg2-binary`
- **Data Manipulation**: `pandas`

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```powershell
git clone https://github.com/praneetjena-prog/AthleteX.git
cd AthleteX
```

### 2. Set Up Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```powershell
pip install -r streamlit_app/requirements.txt
```

### 4. Configure Database Credentials
1. Navigate to `streamlit_app/.streamlit/`.
2. Copy `secrets.toml.example` to `secrets.toml`:
   ```powershell
   cp streamlit_app/.streamlit/secrets.toml.example streamlit_app/.streamlit/secrets.toml
   ```
3. Open `secrets.toml` and configure your CockroachDB connection string:
   ```toml
   DATABASE_URL = "postgresql://USERNAME:PASSWORD@HOST:26257/athletex?sslmode=verify-full"
   ```

### 5. Launch the Dashboard
```powershell
cd streamlit_app
streamlit run app.py
```

---

## 🔒 Security
- Database connection strings containing passwords or tokens must never be committed to git.
- `.streamlit/secrets.toml` is ignored by `.gitignore`. Always use `.streamlit/secrets.toml.example` as a template.
