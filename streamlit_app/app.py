import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

st.set_page_config(page_title="AthleteX | Sports Performance", page_icon="🏅", layout="wide")
st.markdown("""
<style>
:root {
    --ax-ink: #183247;
    --ax-muted: #667b8c;
    --ax-teal: #087f8c;
    --ax-teal-soft: #e6f6f5;
    --ax-border: #dce6ed;
    --ax-canvas: #f5f8fb;
}
.stApp {
    background: #f5f8fb;
    color: var(--ax-ink);
}
.block-container {
    padding-top: 1.35rem;
    padding-bottom: 2.25rem;
    max-width: 1500px;
}
h1, h2, h3 {
    color: #183247;
    letter-spacing: -0.02em;
}
h1 { font-weight: 750; }
h2, h3 { font-weight: 650; }
[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid #e0e8ee;
}
[data-testid="stSidebar"] * {
    color: #183247;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: #718596;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: .42rem .55rem;
    border-radius: 9px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: #eef7f8;
}
[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #dce6ed;
    border-radius: 13px;
    padding: 14px 16px;
    box-shadow: 0 3px 12px rgba(24,50,71,.04);
}
[data-testid="stMetricLabel"] {
    color: #667b8c;
    font-weight: 600;
}
[data-testid="stMetricValue"] {
    color: #183247;
    font-weight: 750;
}
div[data-testid="stDataFrame"], div[data-testid="stTable"] {
    border: 1px solid #dce6ed;
    border-radius: 10px;
    overflow: hidden;
}
.stButton > button {
    border-radius: 9px;
    border: 1px solid #cbd9e3;
    font-weight: 600;
    background: #ffffff;
    color: #183247;
}
.stButton > button[kind="primary"] {
    background: #087f8c;
    border-color: #087f8c;
    color: #ffffff;
}
hr { border-color: #dce6ed; }
.ax-status { display:inline-block; padding:5px 10px; border-radius:999px; background:#e6f6f0; color:#116149; border:1px solid #b8e3d3; font-size:12px; font-weight:700; }
.ax-alert { padding:14px 16px; border-radius:12px; background:#fff7ed; border:1px solid #fed7aa; color:#9a3412; margin:8px 0 16px 0; }
.ax-subtle { color:#667b8c; font-size:13px; }

</style>
""", unsafe_allow_html=True)
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = ["#087f8c","#4776a8","#d99a2b","#d96b62","#7b72b2"]

def compact_fig(fig, height=320, top=42):
    fig.update_layout(height=height, margin=dict(l=24, r=18, t=top, b=28), font=dict(size=12))
    return fig

def friendly_columns(df, mapping):
    return df.rename(columns=mapping)

def database_url():
    try:
        secret = st.secrets.get("DATABASE_URL", "")
    except Exception:
        secret = ""
    return secret or os.getenv("DATABASE_URL", "")

@st.cache_resource
def connection(url):
    conn = psycopg2.connect(url, connect_timeout=10)
    conn.autocommit = True
    return conn

def query(sql, params=None):
    url = database_url()
    if not url:
        st.error("Database connection is not configured. Add DATABASE_URL to .streamlit/secrets.toml.")
        st.stop()
    try:
        conn = connection(url)
        # Validate cached connections before use; reconnect once after an idle disconnect.
        try:
            with conn.cursor() as health_cursor:
                health_cursor.execute("SELECT 1")
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            st.cache_resource.clear()
            conn = connection(url)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return pd.DataFrame(cur.fetchall() if cur.description else [])
    except Exception as exc:
        st.error("Could not query CockroachDB. Check the connection URL, SSL settings, and database permissions.")
        with st.expander("Technical details"):
            st.code(str(exc))
        st.stop()

def scalar(sql):
    df = query(sql)
    return 0 if df.empty or pd.isna(df.iloc[0, 0]) else df.iloc[0, 0]

st.sidebar.markdown("## 🏅 AthleteX")
st.sidebar.caption("SPORTS PERFORMANCE INTELLIGENCE")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navigate", ["Overview", "Athletes", "Training", "Telemetry", "Competitions"])
st.sidebar.divider()
st.sidebar.caption("CockroachDB Cloud · athletex")
if st.sidebar.button("Refresh data", use_container_width=True):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

header_left, header_right = st.columns([4, 1.5])
with header_left:
    st.title("AthleteX")
    st.caption("Distributed Sports Performance Management System · Sports performance intelligence")
status = query("SELECT current_database() AS database_name, now() AS server_time")
with header_right:
    st.markdown("<div style='text-align:right;padding-top:14px'><span class='ax-status'>● CockroachDB Cloud · Connected</span><div class='ax-subtle' style='margin-top:6px'>Cluster region: asia-south1 · connection verified</div></div>", unsafe_allow_html=True)
st.sidebar.success(f"Connected · {status.iloc[0]['database_name']}")

if page == "Overview":
    st.subheader("Performance overview")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Athletes", int(scalar("SELECT COUNT(*) FROM athletex.public.athlete")))
    c2.metric("Sports", int(scalar("SELECT COUNT(*) FROM athletex.public.sport")))
    c3.metric("Training sessions", int(scalar("SELECT COUNT(*) FROM athletex.public.training_session")))
    c4.metric("Telemetry readings", f"{int(scalar('SELECT COUNT(*) FROM athletex.public.telemetry')):,}")
    left, right = st.columns([1.2, 1])
    with left:
        st.markdown("#### Athlete leaderboard")
        df = query("""
            SELECT full_name, competitions, gold_medals, silver_medals, bronze_medals,
                   avg_competition_score, best_evaluation_score
            FROM athletex.public.athlete_performance_summary
            ORDER BY gold_medals DESC, avg_competition_score DESC NULLS LAST, full_name
            LIMIT 10
        """)
        df["avg_competition_score"] = pd.to_numeric(df["avg_competition_score"], errors="coerce")
        df["best_evaluation_score"] = pd.to_numeric(df["best_evaluation_score"], errors="coerce")
        df["Podium"] = df.apply(lambda r: f"🥇 {int(r['gold_medals'] or 0)}  ·  🥈 {int(r['silver_medals'] or 0)}  ·  🥉 {int(r['bronze_medals'] or 0)}", axis=1)
        df["Athlete"] = df["full_name"].map(lambda x: f"🏃 {x}")
        leaderboard = df[["Athlete", "competitions", "Podium", "avg_competition_score", "best_evaluation_score"]].rename(columns={"competitions":"Competitions", "avg_competition_score":"Avg. score", "best_evaluation_score":"Best evaluation"})
        st.dataframe(leaderboard, use_container_width=True, hide_index=True, height=360,
            column_config={"Avg. score": st.column_config.ProgressColumn("Avg. score", min_value=0, max_value=100, format="%.1f"),
                           "Best evaluation": st.column_config.NumberColumn("Best evaluation", format="⭐ %.2f")})
    with right:
        st.markdown("#### Medal distribution")
        medals = query("""
            SELECT COALESCE(SUM(gold_medals), 0) AS Gold,
                   COALESCE(SUM(silver_medals), 0) AS Silver,
                   COALESCE(SUM(bronze_medals), 0) AS Bronze
            FROM athletex.public.athlete_performance_summary
        """)
        if not medals.empty:
            long = medals.melt(var_name="Medal", value_name="Count")
            long["Count"] = pd.to_numeric(long["Count"], errors="coerce").fillna(0)
            long = long[long["Count"] > 0]
            if long.empty:
                st.info("No medals have been recorded yet.")
            else:
                fig = px.pie(long, names="Medal", values="Count", hole=0.60,
                    color="Medal", color_discrete_map={"Gold":"#d99a2b", "Silver":"#8fa1b0", "Bronze":"#b36b39"})
                fig.update_traces(textinfo="percent", hovertemplate="%{label}<br>Medals: %{value}<br>Share: %{percent}<extra></extra>")
                fig.update_layout(legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5))
                compact_fig(fig, height=340, top=18)
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
    st.caption(f"Database server time: {status.iloc[0]['server_time']}")

elif page == "Athletes":
    st.subheader("Athletes & biometrics")
    directory_tab, biometrics_tab = st.tabs(["👥 Athlete directory", "📈 Individual biometrics"])
    with directory_tab:
        athletes = query("""
            SELECT a.athlete_id, a.full_name,
                   COALESCE(ps.competitions, 0) AS competitions,
                   COALESCE(ps.gold_medals, 0) AS gold_medals,
                   COALESCE(ps.silver_medals, 0) AS silver_medals,
                   COALESCE(ps.bronze_medals, 0) AS bronze_medals,
                   ps.avg_competition_score, ps.best_evaluation_score
            FROM athletex.public.athlete a
            LEFT JOIN athletex.public.athlete_performance_summary ps ON ps.athlete_id = a.athlete_id
            ORDER BY a.full_name
        """)
        term = st.text_input("Search athlete by name")
        if term:
            athletes = athletes[athletes["full_name"].str.contains(term, case=False, na=False)]
        athlete_display = friendly_columns(athletes, {"full_name":"Athlete","competitions":"Competitions","gold_medals":"Gold","silver_medals":"Silver","bronze_medals":"Bronze","avg_competition_score":"Avg. score","best_evaluation_score":"Best evaluation"}).drop(columns=["athlete_id"], errors="ignore")
        st.dataframe(athlete_display, use_container_width=True, hide_index=True, height=340)

    with biometrics_tab:
        athlete_choices = query("SELECT athlete_id, full_name FROM athletex.public.athlete ORDER BY full_name")
        if not athlete_choices.empty:
            name = st.selectbox("Choose athlete", athlete_choices["full_name"].tolist(), key="biometric_athlete")
            athlete_id = athlete_choices.loc[athlete_choices["full_name"] == name, "athlete_id"].iloc[0]
            readings = query("""
                SELECT recorded_at, heart_rate, training_intensity, speed_kmh, distance_km
                FROM athletex.public.telemetry WHERE athlete_id = %s
                ORDER BY recorded_at DESC LIMIT 120
            """, (str(athlete_id),))
            if not readings.empty:
                readings = readings.sort_values("recorded_at")
                st.markdown(f"#### Recent telemetry — {name}")
                for col in ["heart_rate", "training_intensity", "speed_kmh", "distance_km"]:
                    readings[col] = pd.to_numeric(readings[col], errors="coerce")
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Max heart rate", f"{readings['heart_rate'].max():.0f} BPM" if readings['heart_rate'].notna().any() else "—")
                k2.metric("Avg. intensity", f"{readings['training_intensity'].mean():.1f}/10" if readings['training_intensity'].notna().any() else "—")
                k3.metric("Max distance logged", f"{readings['distance_km'].max():.2f} km" if readings['distance_km'].notna().any() else "—")
                k4.metric("Readings shown", f"{len(readings):,}")
                fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.12, subplot_titles=("Heart rate · BPM", "Speed · km/h and training intensity · /10"))
                fig.add_trace(go.Scatter(x=readings["recorded_at"], y=readings["heart_rate"], name="Heart rate (BPM)", mode="lines+markers", line=dict(color="#087f8c", width=2)), row=1, col=1)
                fig.add_hline(y=160, line_dash="dash", line_color="#dc2626", annotation_text="160 BPM review threshold", annotation_position="top left", row=1, col=1)
                fig.add_trace(go.Scatter(x=readings["recorded_at"], y=readings["speed_kmh"], name="Speed (km/h)", mode="lines", line=dict(color="#4776a8", width=2)), row=2, col=1)
                fig.add_trace(go.Scatter(x=readings["recorded_at"], y=readings["training_intensity"], name="Intensity (/10)", mode="lines", line=dict(color="#d99a2b", width=2, dash="dot")), row=2, col=1)
                fig.update_layout(hovermode="x unified", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), height=520, margin=dict(l=20,r=20,t=65,b=25), font=dict(size=12))
                fig.update_xaxes(title_text="Recorded at", row=2, col=1)
                fig.update_yaxes(title_text="BPM", row=1, col=1)
                fig.update_yaxes(title_text="Value", row=2, col=1)
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
            else:
                st.info("No telemetry readings are linked to this athlete.")
        else:
            st.info("No athletes found in the database.")

elif page == "Training":
    st.subheader("Training workload")
    df = query("""
        SELECT a.full_name, COUNT(ts.session_id) AS total_sessions,
               COALESCE(SUM(ts.duration_minutes), 0) AS total_minutes,
               ROUND(COALESCE(SUM(ts.duration_minutes), 0) / 60.0, 2) AS total_hours,
               COALESCE(SUM(ts.calories_burned), 0) AS total_calories,
               ROUND(AVG(ts.duration_minutes), 2) AS avg_session_minutes
        FROM athletex.public.athlete a
        LEFT JOIN athletex.public.training_plan tp ON tp.athlete_id = a.athlete_id
        LEFT JOIN athletex.public.training_session ts ON ts.plan_id = tp.plan_id
        GROUP BY a.athlete_id, a.full_name
        ORDER BY total_minutes DESC, a.full_name
    """)
    for col in ["total_sessions", "total_minutes", "total_hours", "total_calories", "avg_session_minutes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    total_hours = df["total_minutes"].sum() / 60
    total_sessions = int(df["total_sessions"].sum())
    total_calories = int(df["total_calories"].sum())
    avg_session = (df["total_minutes"].sum() / total_sessions) if total_sessions else 0
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Team training hours", f"{total_hours:,.1f} hrs")
    k2.metric("Sessions logged", f"{total_sessions:,}")
    k3.metric("Calories burned", f"{total_calories:,} kcal")
    k4.metric("Avg. session time", f"{avg_session:.0f} min")
    st.markdown("#### Athlete workload")
    training_display = friendly_columns(df, {"full_name":"Athlete","total_sessions":"Sessions","total_minutes":"Training minutes","total_hours":"Training hours","total_calories":"Calories burned","avg_session_minutes":"Avg. session (min)"})
    st.dataframe(training_display, use_container_width=True, hide_index=True, height=300,
        column_config={"Training hours": st.column_config.NumberColumn(format="%.1f"), "Calories burned": st.column_config.NumberColumn(format="%d kcal"), "Avg. session (min)": st.column_config.NumberColumn(format="%.1f min")})
    if not df.empty:
        sort_by = st.radio("Rank workload by", options=["Training minutes", "Calories burned"], horizontal=True)
        metric_col = "total_minutes" if sort_by == "Training minutes" else "total_calories"
        chart_df = df.nlargest(10, metric_col).sort_values(metric_col, ascending=True)
        fig = px.bar(chart_df, x=metric_col, y="full_name", orientation="h", labels={metric_col:sort_by,"full_name":"Athlete"}, title=f"Top 10 athletes by {sort_by.lower()}")
        fig.update_traces(marker_color="#087f8c", hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>")
        fig.update_layout(yaxis_title=None, xaxis_title=sort_by)
        compact_fig(fig, height=360, top=42)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

elif page == "Telemetry":
    st.subheader("Telemetry & review center")
    fleet_tab, alert_tab = st.tabs(["📈 Fleet trends", "⚠️ Anomaly / review flags"])
    with fleet_tab:
        st.subheader("Wearable telemetry")
        daily = query("""
            SELECT DATE_TRUNC('day', recorded_at) AS reading_day, COUNT(*) AS total_readings,
                   ROUND(AVG(heart_rate), 2) AS avg_heart_rate,
                   MIN(heart_rate) AS min_heart_rate, MAX(heart_rate) AS max_heart_rate,
                   ROUND(AVG(training_intensity), 2) AS avg_training_intensity,
                   ROUND(AVG(speed_kmh), 2) AS avg_speed_kmh
            FROM athletex.public.telemetry
            GROUP BY DATE_TRUNC('day', recorded_at) ORDER BY reading_day
        """)
        if not daily.empty:
            for col in ["total_readings", "avg_heart_rate", "min_heart_rate", "max_heart_rate", "avg_training_intensity", "avg_speed_kmh"]:
                daily[col] = pd.to_numeric(daily[col], errors="coerce")
            c1, c2 = st.columns(2)
            with c1:
                fig_hr = px.line(daily, x="reading_day", y="avg_heart_rate", markers=True, title="Average heart rate by day", labels={"reading_day":"Date","avg_heart_rate":"Avg. heart rate (bpm)"})
                fig_hr.update_yaxes(title=None)
                compact_fig(fig_hr, height=300, top=48)
                st.plotly_chart(fig_hr, use_container_width=True, config={"displaylogo": False})
            with c2:
                fig_intensity = px.line(daily, x="reading_day", y="avg_training_intensity", markers=True, title="Average training intensity by day", labels={"reading_day":"Date","avg_training_intensity":"Avg. intensity"})
                fig_intensity.update_yaxes(title=None)
                compact_fig(fig_intensity, height=300, top=48)
                st.plotly_chart(fig_intensity, use_container_width=True, config={"displaylogo": False})
            st.markdown("#### Daily data")
            daily_display = friendly_columns(daily, {"reading_day":"Date","total_readings":"Readings","avg_heart_rate":"Avg. heart rate (bpm)","min_heart_rate":"Min heart rate","max_heart_rate":"Max heart rate","avg_training_intensity":"Avg. intensity","avg_speed_kmh":"Avg. speed (km/h)"})
            st.dataframe(daily_display, use_container_width=True, hide_index=True, height=300)

    with alert_tab:
        st.markdown("#### Threshold-based review flags")
        alerts = query("""
            SELECT a.full_name, COUNT(t.telemetry_id) AS flagged_readings,
                   ROUND(AVG(t.heart_rate), 2) AS avg_heart_rate,
                   ROUND(AVG(t.training_intensity), 2) AS avg_intensity,
                   MAX(t.heart_rate) AS max_heart_rate
            FROM athletex.public.athlete a
            JOIN athletex.public.telemetry t ON t.athlete_id = a.athlete_id
            WHERE t.heart_rate >= 160 AND t.training_intensity >= 8
            GROUP BY a.athlete_id, a.full_name
            HAVING COUNT(t.telemetry_id) >= 5
            ORDER BY flagged_readings DESC
        """)
        count_flagged = len(alerts)
        if count_flagged:
            st.markdown(f"<div class='ax-alert'><b>⚠️ {count_flagged} athletes meet the review rule</b><br>Heart rate ≥ 160 BPM and training intensity ≥ 8/10 across at least 5 readings.</div>", unsafe_allow_html=True)
            alerts["Priority"] = alerts["flagged_readings"].apply(lambda n: "🔴 High" if int(n) >= 10 else "🟠 Review")
            alerts["flagged_readings"] = pd.to_numeric(alerts["flagged_readings"], errors="coerce").fillna(0).astype(int)
            for col in ["avg_heart_rate", "avg_intensity", "max_heart_rate"]:
                alerts[col] = pd.to_numeric(alerts[col], errors="coerce")
            alerts_display = friendly_columns(alerts, {"full_name":"Athlete","flagged_readings":"Flagged readings","avg_heart_rate":"Avg. heart rate (bpm)","avg_intensity":"Avg. intensity","max_heart_rate":"Max heart rate (bpm)"})
            st.dataframe(alerts_display, use_container_width=True, hide_index=True, height=300,
                column_config={"Priority": st.column_config.TextColumn("Priority"), "Avg. heart rate (bpm)": st.column_config.NumberColumn(format="%.1f BPM"), "Avg. intensity": st.column_config.NumberColumn(format="%.1f/10"), "Max heart rate (bpm)": st.column_config.NumberColumn(format="%.0f BPM")})
        else:
            st.success("No athletes currently meet the configured review rule.")
        st.caption("Rule-based review of synthetic demonstration data only. This is not a medical diagnosis or clinically validated risk score.")

elif page == "Competitions":
    st.subheader("Competition and sport analytics")
    df = query("""
        WITH registration_stats AS (
            SELECT sport_id, COUNT(DISTINCT athlete_id) AS registered_athletes
            FROM athletex.public.athlete_sport GROUP BY sport_id
        ), result_stats AS (
            SELECT cs.sport_id, COUNT(DISTINCT cs.competition_id) AS total_competitions,
                   SUM(CASE WHEN cr.medal = 'Gold' THEN 1 ELSE 0 END) AS gold_medals,
                   SUM(CASE WHEN cr.medal = 'Silver' THEN 1 ELSE 0 END) AS silver_medals,
                   SUM(CASE WHEN cr.medal = 'Bronze' THEN 1 ELSE 0 END) AS bronze_medals,
                   ROUND(AVG(cr.score), 2) AS avg_competition_score
            FROM athletex.public.competition_sport cs
            LEFT JOIN athletex.public.competition_result cr
              ON cr.competition_id = cs.competition_id AND cr.sport_id = cs.sport_id
            GROUP BY cs.sport_id
        )
        SELECT s.sport_name, COALESCE(r.registered_athletes, 0) AS registered_athletes,
               COALESCE(rs.total_competitions, 0) AS total_competitions,
               COALESCE(rs.gold_medals, 0) AS gold_medals,
               COALESCE(rs.silver_medals, 0) AS silver_medals,
               COALESCE(rs.bronze_medals, 0) AS bronze_medals,
               rs.avg_competition_score
        FROM athletex.public.sport s
        LEFT JOIN registration_stats r ON r.sport_id = s.sport_id
        LEFT JOIN result_stats rs ON rs.sport_id = s.sport_id
        ORDER BY gold_medals DESC, avg_competition_score DESC NULLS LAST
    """)
    for col in ["registered_athletes", "total_competitions", "gold_medals", "silver_medals", "bronze_medals", "avg_competition_score"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    total_medals = int(df[["gold_medals", "silver_medals", "bronze_medals"]].sum().sum()) if not df.empty else 0
    total_competitions_overall = int(scalar("SELECT COUNT(*) FROM athletex.public.competition"))
    leading_sport = df.sort_values(["gold_medals", "avg_competition_score"], ascending=False).iloc[0]["sport_name"] if not df.empty else "—"
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Sports", f"{df['sport_name'].nunique():,}")
    k2.metric("Total competitions", f"{total_competitions_overall:,}")
    k3.metric("Medals distributed", f"{total_medals:,}")
    k4.metric("Leading sport", leading_sport)
    competition_display = friendly_columns(df, {"sport_name":"Sport","registered_athletes":"Registered athletes","total_competitions":"Competitions","gold_medals":"Gold","silver_medals":"Silver","bronze_medals":"Bronze","avg_competition_score":"Avg. score"})
    st.dataframe(competition_display, use_container_width=True, hide_index=True, height=280,
        column_config={"Avg. score": st.column_config.NumberColumn(format="%.2f")})
    if not df.empty:
        long = df.melt(id_vars="sport_name", value_vars=["gold_medals", "silver_medals", "bronze_medals"], var_name="Medal", value_name="Count")
        long["Medal"] = long["Medal"].str.replace("_medals", "", regex=False).str.title()
        fig = px.bar(long, x="sport_name", y="Count", color="Medal", barmode="group", title="Podium distribution by sport", labels={"sport_name":"Sport","Count":"Medals"}, color_discrete_map={"Gold":"#d99a2b", "Silver":"#8fa1b0", "Bronze":"#b36b39"})
        fig.update_layout(xaxis_title=None, yaxis_title="Medals", legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        compact_fig(fig, height=360, top=48)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

st.divider()
st.caption("AthleteX • Academic prototype • Synthetic telemetry data")
