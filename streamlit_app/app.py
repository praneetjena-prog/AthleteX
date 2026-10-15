import os
import pandas as pd
import plotly.express as px
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
</style>
""", unsafe_allow_html=True)
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = ["#087f8c","#4776a8","#d99a2b","#d96b62","#7b72b2"]
MEDAL_COLORS = {"Gold": "#d99a2b", "Silver": "#8fa1b0", "Bronze": "#b36b39"}

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
    # Preserve the SSL parameters and certificate path from CockroachDB Cloud.
    conn = psycopg2.connect(url, connect_timeout=10)
    conn.autocommit = True
    return conn

def get_connection(url):
    conn = connection(url)
    if conn.closed != 0:
        st.cache_resource.clear()
        conn = connection(url)
    return conn

def query(sql, params=None):
    url = database_url()
    if not url:
        st.error("Database connection is not configured. Add DATABASE_URL to .streamlit/secrets.toml.")
        st.stop()
    try:
        conn = get_connection(url)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, params or ())
            return pd.DataFrame(cur.fetchall() if cur.description else [])
    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        # Auto-reconnect if idle connection was dropped
        try:
            st.cache_resource.clear()
            conn = get_connection(url)
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params or ())
                return pd.DataFrame(cur.fetchall() if cur.description else [])
        except Exception as retry_exc:
            st.error("Could not query CockroachDB. Check the connection URL, SSL settings, and database permissions.")
            with st.expander("Technical details"):
                st.code(str(retry_exc))
            st.stop()
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
    st.cache_resource.clear()
    st.cache_data.clear()
    st.rerun()

st.title("AthleteX")
st.caption("Distributed Sports Performance Management System  ·  Performance intelligence")
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
        df = friendly_columns(df, {"full_name":"Athlete","competitions":"Competitions","gold_medals":"Gold","silver_medals":"Silver","bronze_medals":"Bronze","avg_competition_score":"Avg. score","best_evaluation_score":"Best evaluation"})
        st.dataframe(df, use_container_width=True, hide_index=True, height=360)
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
            if long["Count"].sum() > 0:
                fig = px.pie(long, names="Medal", values="Count", hole=0.58, color="Medal", color_discrete_map=MEDAL_COLORS)
                fig.update_layout(legend_title=None)
                compact_fig(fig, height=340, top=18)
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
            else:
                st.info("No medals recorded yet.")
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
    athlete_display = friendly_columns(athletes, {"full_name":"Athlete","competitions":"Competitions","gold_medals":"Gold","silver_medals":"Silver","bronze_medals":"Bronze","avg_competition_score":"Avg. score","best_evaluation_score":"Best evaluation"}).drop(columns=["athlete_id"], errors="ignore")
    st.dataframe(athlete_display, use_container_width=True, hide_index=True, height=340)
    if not athletes.empty:
        name = st.selectbox("Select athlete for telemetry", athletes["full_name"].tolist())
        athlete_id = athletes.loc[athletes["full_name"] == name, "athlete_id"].iloc[0]
        readings = query("""
            SELECT recorded_at, heart_rate, training_intensity, speed_kmh, distance_km
            FROM athletex.public.telemetry WHERE athlete_id = %s
            ORDER BY recorded_at DESC LIMIT 120
        """, (str(athlete_id),))
        if not readings.empty:
            readings = readings.sort_values("recorded_at")
            st.markdown(f"#### Recent telemetry — {name}")

            # Heart rate and training intensity use different units/scales.
            # Separate charts prevent one measure from distorting the other's axis.
            readings["heart_rate"] = pd.to_numeric(readings["heart_rate"], errors="coerce")
            readings["training_intensity"] = pd.to_numeric(
                readings["training_intensity"], errors="coerce"
            )

            hr_col, intensity_col = st.columns(2)
            with hr_col:
                st.markdown("**Heart rate (BPM)**")
                hr_data = readings.set_index("recorded_at")[["heart_rate"]].dropna()
                st.line_chart(
                    hr_data,
                    height=280,
                    use_container_width=True,
                )
            with intensity_col:
                st.markdown("**Training intensity**")
                intensity_data = readings.set_index("recorded_at")[["training_intensity"]].dropna()
                st.line_chart(
                    intensity_data,
                    height=280,
                    use_container_width=True,
                )
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
    training_display = friendly_columns(df, {"full_name":"Athlete","total_sessions":"Sessions","total_minutes":"Training minutes","total_hours":"Training hours","total_calories":"Calories burned","avg_session_minutes":"Avg. session (min)"})
    st.dataframe(training_display, use_container_width=True, hide_index=True, height=350)
    if not df.empty:
        # CockroachDB numeric values may arrive as Decimal/object dtype; coerce for plotting.
        df["total_minutes"] = pd.to_numeric(df["total_minutes"], errors="coerce").fillna(0)
        chart_df = df.nlargest(10, "total_minutes").sort_values("total_minutes", ascending=True)
        fig = px.bar(chart_df, x="total_minutes", y="full_name", orientation="h", labels={"total_minutes":"Training minutes","full_name":"Athlete"}, title="Top 10 athletes by training workload")
        fig.update_layout(yaxis_title=None, xaxis_title="Training minutes")
        compact_fig(fig, height=360, top=42)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

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
        daily["avg_heart_rate"] = pd.to_numeric(daily["avg_heart_rate"], errors="coerce")
        daily["avg_training_intensity"] = pd.to_numeric(daily["avg_training_intensity"], errors="coerce")
        daily["avg_speed_kmh"] = pd.to_numeric(daily["avg_speed_kmh"], errors="coerce")
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
    alerts_display = friendly_columns(alerts, {"full_name":"Athlete","flagged_readings":"Flagged readings","avg_heart_rate":"Avg. heart rate (bpm)","avg_intensity":"Avg. intensity","max_heart_rate":"Max heart rate (bpm)"})
    st.dataframe(alerts_display, use_container_width=True, hide_index=True, height=300)

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
    competition_display = friendly_columns(df, {"sport_name":"Sport","registered_athletes":"Registered athletes","total_competitions":"Competitions","gold_medals":"Gold","silver_medals":"Silver","bronze_medals":"Bronze","avg_competition_score":"Avg. score"})
    st.dataframe(competition_display, use_container_width=True, hide_index=True, height=300)
    if not df.empty:
        long = df.melt(id_vars="sport_name", value_vars=["gold_medals", "silver_medals", "bronze_medals"], var_name="Medal", value_name="Count")
        long["Medal"] = long["Medal"].str.replace("_medals", "", regex=False).str.title()
        long["Count"] = pd.to_numeric(long["Count"], errors="coerce").fillna(0)
        fig = px.bar(long, x="sport_name", y="Count", color="Medal", barmode="group", title="Medals by sport", labels={"sport_name":"Sport","Count":"Medals"}, color_discrete_map=MEDAL_COLORS)
        fig.update_layout(xaxis_title=None, yaxis_title="Medals")
        compact_fig(fig, height=340, top=48)
        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

st.divider()
st.caption("AthleteX • Academic prototype • Synthetic telemetry data")
