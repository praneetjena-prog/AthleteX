import os
import pandas as pd
import plotly.express as px
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

st.set_page_config(page_title="AthleteX | Sports Performance", page_icon="🏅", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: var(--secondary-background-color); border: 1px solid rgba(128,128,128,.18); padding: 14px 16px; border-radius: 12px;}
</style>
""", unsafe_allow_html=True)

def database_url():
    try:
        secret = st.secrets.get("DATABASE_URL", "")
    except Exception:
        secret = ""
    return secret or os.getenv("DATABASE_URL", "")

@st.cache_resource
def connection(url):
    # Preserve the SSL parameters and certificate path from CockroachDB Cloud.
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

st.sidebar.title("🏅 AthleteX")
st.sidebar.caption("Sports Performance Management")
page = st.sidebar.radio("Navigate", ["Overview", "Athletes", "Training", "Telemetry", "Competitions"])
st.sidebar.divider()
st.sidebar.caption("CockroachDB Cloud · athletex")
if st.sidebar.button("Refresh data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

st.title("AthleteX")
st.caption("Distributed Sports Performance Management System")
status = query("SELECT current_database() AS database_name, now() AS server_time")
st.sidebar.success(f"Database: {status.iloc[0]['database_name']}")

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
        st.dataframe(df, use_container_width=True, hide_index=True)
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
            fig = px.pie(long, names="Medal", values="Count", hole=0.58)
            fig.update_layout(margin=dict(l=8, r=8, t=8, b=8), legend_title=None)
            st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Database server time: {status.iloc[0]['server_time']}")

elif page == "Athletes":
    st.subheader("Athlete directory")
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
    st.dataframe(athletes, use_container_width=True, hide_index=True)
    if not athletes.empty:
        name = st.selectbox("Select athlete for telemetry", athletes["full_name"].tolist())
        athlete_id = athletes.loc[athletes["full_name"] == name, "athlete_id"].iloc[0]
        readings = query("""
            SELECT recorded_at, heart_rate, training_intensity, speed_kmh, distance_km
            FROM athletex.public.telemetry WHERE athlete_id = %s
            ORDER BY recorded_at DESC LIMIT 500
        """, (str(athlete_id),))
        if not readings.empty:
            readings = readings.sort_values("recorded_at")
            st.markdown(f"#### Recent telemetry — {name}")
            st.line_chart(readings.set_index("recorded_at")[["heart_rate", "training_intensity"]])
        else:
            st.info("No telemetry readings are linked to this athlete.")

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
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        fig = px.bar(df.sort_values("total_minutes", ascending=True), x="total_minutes", y="full_name", orientation="h", labels={"total_minutes": "Training minutes", "full_name": "Athlete"})
        fig.update_layout(yaxis_title=None, margin=dict(l=8, r=8, t=8, b=8))
        st.plotly_chart(fig, use_container_width=True)

elif page == "Telemetry":
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
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.line(daily, x="reading_day", y="avg_heart_rate", markers=True, title="Average heart rate by day"), use_container_width=True)
        with c2:
            st.plotly_chart(px.line(daily, x="reading_day", y="avg_training_intensity", markers=True, title="Average training intensity by day"), use_container_width=True)
        st.markdown("#### Daily data")
        st.dataframe(daily, use_container_width=True, hide_index=True)
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
    st.caption("Synthetic-data demonstration only; flags are not medical diagnoses.")
    st.dataframe(alerts, use_container_width=True, hide_index=True)

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
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        long = df.melt(id_vars="sport_name", value_vars=["gold_medals", "silver_medals", "bronze_medals"], var_name="Medal", value_name="Count")
        long["Medal"] = long["Medal"].str.replace("_medals", "", regex=False).str.title()
        fig = px.bar(long, x="sport_name", y="Count", color="Medal", barmode="group", title="Medals by sport")
        fig.update_layout(xaxis_title=None, margin=dict(l=8, r=8, t=45, b=8))
        st.plotly_chart(fig, use_container_width=True)

st.divider()
st.caption("AthleteX • Academic prototype • Synthetic telemetry data")
