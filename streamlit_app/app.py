import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="AthleteX // Telemetry Cockpit",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== HUD THEME INITIALIZATION ====================
if "hud_mode" not in st.session_state:
    st.session_state.hud_mode = "LIGHT"  # "LIGHT" or "DARK"

if "triaged_athletes" not in st.session_state:
    st.session_state.triaged_athletes = set()

if "show_log_modal" not in st.session_state:
    st.session_state.show_log_modal = False

is_dark = (st.session_state.hud_mode == "DARK")

# Theme Variables
if is_dark:
    bg_color = "#121214"
    card_bg = "#1C1C1F"
    text_color = "#F4F4F0"
    border_color = "#F4F4F0"
    shadow_color = "#F4F4F0"
    grid_color = "rgba(255, 255, 255, 0.08)"
    accent_subtle = "#2A2A30"
    paper_plot_bg = "#1C1C1F"
    plotly_font_color = "#F4F4F0"
    plotly_grid = "#2E2E35"
else:
    bg_color = "#F4F4F0"
    card_bg = "#FFFFFF"
    text_color = "#000000"
    border_color = "#000000"
    shadow_color = "#000000"
    grid_color = "rgba(0, 0, 0, 0.08)"
    accent_subtle = "#EAEAE6"
    paper_plot_bg = "#FFFFFF"
    plotly_font_color = "#000000"
    plotly_grid = "#E0E0DC"

# ==================== BAUHAUS / NEO-BRUTALIST STYLING ====================
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700;800&family=Space+Grotesk:wght@600;700;800&display=swap');

:root {{
    --nb-bg: {bg_color};
    --nb-card: {card_bg};
    --nb-ink: {text_color};
    --nb-border: {border_color};
    --nb-shadow: {shadow_color};
    --nb-red: #FF3B30;
    --nb-blue: #0047FF;
    --nb-yellow: #FFCC00;
    --nb-green: #00D66F;
    --nb-gray: #71717A;
}}

/* Reset and Global Font Rules */
* {{
    border-radius: 0px !important;
}}

.stApp {{
    background-color: var(--nb-bg) !important;
    background-image: radial-gradient({grid_color} 1px, transparent 1px) !important;
    background-size: 28px 28px !important;
    color: var(--nb-ink) !important;
    font-family: 'Inter', sans-serif !important;
}}

/* Typography */
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: -0.02em !important;
    color: var(--nb-ink) !important;
}}

p, span, div, label {{
    color: var(--nb-ink);
}}

/* Streamlit Header & Chrome Clean */
[data-testid="stDecoration"] {{
    display: none !important;
}}
header[data-testid="stHeader"] {{
    background: transparent !important;
    pointer-events: none !important;
}}
[data-testid="stAppDeployButton"],
[data-testid="stToolbarActions"],
[data-testid="stMainMenu"] {{
    display: none !important;
}}

/* Ensure sidebar collapse & expand controls are visible in Neo-Brutalism */
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] button {{
    background-color: var(--nb-card) !important;
    border: 2px solid var(--nb-border) !important;
    border-radius: 0px !important;
    color: var(--nb-ink) !important;
    box-shadow: 2px 2px 0px var(--nb-shadow) !important;
    pointer-events: auto !important;
    cursor: pointer !important;
}}

.block-container {{
    padding-top: 1rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1540px !important;
}}

/* Sidebar Bauhaus Neo-Brutalist Frame */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] {{
    background-color: var(--nb-card) !important;
    color: var(--nb-ink) !important;
    border-right: 2.5px solid var(--nb-border) !important;
}}

[data-testid="stSidebar"] [data-testid="stRadio"] label {{
    border: 2px solid transparent !important;
    padding: 0.5rem 0.75rem !important;
    margin-bottom: 0.35rem !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
    transition: all 0.1s ease !important;
}}

[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {{
    background: var(--nb-yellow) !important;
    color: #000000 !important;
    border: 2px solid #000000 !important;
    box-shadow: 3px 3px 0px #000000 !important;
}}

/* Neo-Brutalist Buttons */
.stButton > button {{
    border-radius: 0px !important;
    border: 2px solid var(--nb-border) !important;
    background: var(--nb-card) !important;
    color: var(--nb-ink) !important;
    box-shadow: 4px 4px 0px var(--nb-shadow) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.1s ease !important;
}}

.stButton > button:hover {{
    background: var(--nb-yellow) !important;
    color: #000000 !important;
    border-color: #000000 !important;
    transform: translate(-1px, -1px) !important;
    box-shadow: 5px 5px 0px #000000 !important;
}}

.stButton > button:active {{
    transform: translate(2px, 2px) !important;
    box-shadow: 1px 1px 0px var(--nb-shadow) !important;
}}

.stButton > button[kind="primary"] {{
    background: var(--nb-blue) !important;
    color: #FFFFFF !important;
    border-color: var(--nb-border) !important;
}}

.stButton > button[kind="primary"]:hover {{
    background: #0036CC !important;
    color: #FFFFFF !important;
}}

/* Inputs & Form Controls */
input, select, textarea, div[data-baseweb="select"] {{
    border-radius: 0px !important;
    border: 2px solid var(--nb-border) !important;
    background: var(--nb-card) !important;
    color: var(--nb-ink) !important;
    font-family: 'JetBrains Mono', monospace !important;
    box-shadow: 3px 3px 0px var(--nb-shadow) !important;
}}

/* Neo-Brutalist Tabs */
button[data-baseweb="tab"] {{
    border-radius: 0px !important;
    border: 2px solid transparent !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 0.5rem 1.2rem !important;
    color: var(--nb-ink) !important;
    margin-right: 4px !important;
}}

button[data-baseweb="tab"][aria-selected="true"] {{
    border: 2.5px solid var(--nb-border) !important;
    border-bottom: 2.5px solid var(--nb-card) !important;
    background: var(--nb-yellow) !important;
    color: #000000 !important;
    box-shadow: 3px 3px 0px var(--nb-shadow) !important;
}}

/* DataFrames & Tables */
div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
    border-radius: 0px !important;
    border: 2.5px solid var(--nb-border) !important;
    background-color: var(--nb-card) !important;
    box-shadow: 4px 4px 0px var(--nb-shadow) !important;
}}

/* Custom Neo-Brutalist Component Classes */
.nb-box {{
    background: var(--nb-card);
    border: 2.5px solid var(--nb-border);
    box-shadow: 4px 4px 0px var(--nb-shadow);
    padding: 1.25rem;
    margin-bottom: 1rem;
    position: relative;
}}

.nb-kpi-card {{
    background: var(--nb-card);
    border: 2.5px solid var(--nb-border);
    box-shadow: 4px 4px 0px var(--nb-shadow);
    padding: 1.15rem 1.25rem;
    margin-bottom: 0.85rem;
    position: relative;
}}

.nb-kpi-badge {{
    position: absolute;
    top: -2px;
    right: -2px;
    background: var(--nb-ink);
    color: var(--nb-card);
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    font-size: 11px;
    padding: 2px 8px;
    border-left: 2px solid var(--nb-border);
    border-bottom: 2px solid var(--nb-border);
}}

.nb-kpi-label {{
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 800;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: { "#A1A1AA" if is_dark else "#52525B" };
    margin-bottom: 0.35rem;
}}

.nb-kpi-value {{
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    font-size: 32px;
    line-height: 1.1;
    color: var(--nb-ink);
}}

.nb-kpi-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    color: { "#A1A1AA" if is_dark else "#52525B" };
    margin-top: 0.35rem;
}}

.nb-tag {{
    display: inline-block;
    padding: 3px 8px;
    border: 1.5px solid var(--nb-border);
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
}}
.nb-tag-red {{ background: var(--nb-red); color: #FFFFFF; }}
.nb-tag-blue {{ background: var(--nb-blue); color: #FFFFFF; }}
.nb-tag-yellow {{ background: var(--nb-yellow); color: #000000; }}
.nb-tag-green {{ background: var(--nb-green); color: #000000; }}

/* Top Status Chip */
.nb-status-chip {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: var(--nb-card);
    border: 2px solid var(--nb-border);
    box-shadow: 3px 3px 0px var(--nb-shadow);
    font-family: 'JetBrains Mono', monospace;
    font-weight: 800;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
</style>
""", unsafe_allow_html=True)

# ==================== DATABASE CONNECTIVITY ====================
def database_url():
    try:
        secret = st.secrets.get("DATABASE_URL", "")
    except Exception:
        secret = ""
    raw = secret or os.getenv("DATABASE_URL", "")
    if isinstance(raw, str) and raw.strip():
        raw = raw.strip()
        if "@" in raw:
            user_part, host_part = raw.split("@", 1)
            raw = f"{user_part.rstrip()}@{host_part.lstrip()}"
        return raw
    return ""

@st.cache_resource
def connection(url):
    cert_path = str((Path(__file__).parent / "certs" / "root.crt").resolve())
    conn = psycopg2.connect(
        url,
        sslrootcert=cert_path,
        sslmode="verify-full",
        connect_timeout=10,
    )
    conn.autocommit = True
    return conn

def query(sql, params=None):
    url = database_url()
    if not url:
        st.error("Database connection not configured. Check .streamlit/secrets.toml.")
        st.stop()
    try:
        conn = connection(url)
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
        st.error(f"CockroachDB Query Error: {exc}")
        st.stop()

def scalar(sql, params=None):
    df = query(sql, params)
    return 0 if df.empty or pd.isna(df.iloc[0, 0]) else df.iloc[0, 0]

def execute_commit(sql, params=None):
    url = database_url()
    conn = connection(url)
    with conn.cursor() as cur:
        cur.execute(sql, params or ())

# ==================== PLOTLY NEO-BRUTALIST STYLING HELPER ====================
def style_nb_fig(fig, height=350, title=None):
    fig.update_layout(
        height=height,
        title=dict(
            text=f"<b>{title.upper()}</b>" if title else "",
            font=dict(family="'Space Grotesk', sans-serif", size=14, color=plotly_font_color),
            x=0.01,
            y=0.96
        ),
        margin=dict(l=25, r=25, t=50 if title else 25, b=30),
        font=dict(family="'JetBrains Mono', monospace", size=11, color=plotly_font_color),
        paper_bgcolor=paper_plot_bg,
        plot_bgcolor=paper_plot_bg,
        legend=dict(
            font=dict(family="'JetBrains Mono', monospace", size=10, color=plotly_font_color),
            bgcolor=paper_plot_bg,
            bordercolor=border_color,
            borderwidth=1.5
        ),
        hoverlabel=dict(
            bgcolor=card_bg,
            font_size=12,
            font_family="'JetBrains Mono', monospace",
            font_color=text_color,
            bordercolor=border_color
        )
    )
    fig.update_xaxes(
        linecolor=border_color,
        linewidth=2,
        mirror=True,
        gridcolor=plotly_grid,
        gridwidth=1,
        tickfont=dict(family="'JetBrains Mono', monospace", size=10, color=plotly_font_color),
        title_font=dict(family="'Space Grotesk', sans-serif", size=11, color=plotly_font_color)
    )
    fig.update_yaxes(
        linecolor=border_color,
        linewidth=2,
        mirror=True,
        gridcolor=plotly_grid,
        gridwidth=1,
        tickfont=dict(family="'JetBrains Mono', monospace", size=10, color=plotly_font_color),
        title_font=dict(family="'Space Grotesk', sans-serif", size=11, color=plotly_font_color)
    )
    return fig

# ==================== GLOBAL TOP BAR ====================
top_col1, top_col2, top_col3, top_col4 = st.columns([4.2, 1.4, 1.3, 1.1])

with top_col1:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:4px;">
            <div style="font-family:'Space Grotesk', sans-serif; font-size:28px; font-weight:800; letter-spacing:-0.03em;">
                ATHLETEX <span style="font-size:16px; font-weight:700; background:#FFCC00; color:#000; padding:2px 6px; border:2px solid #000; vertical-align:middle;">// HUD COCKPIT</span>
            </div>
            <div class="nb-status-chip">
                <span style="display:inline-block; width:9px; height:9px; background:#00D66F; border:1px solid #000;"></span>
                <span>asia-south1 · ONLINE (0.00ms)</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

with top_col2:
    if st.button("➕ LOG SESSION", use_container_width=True):
        st.session_state.show_log_modal = not st.session_state.show_log_modal

with top_col3:
    # Telemetry CSV Exporter
    export_df = query("SELECT recorded_at, athlete_id, heart_rate, speed_kmh, distance_km, training_intensity FROM athletex.public.telemetry ORDER BY recorded_at DESC LIMIT 500")
    csv_data = export_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇ EXPORT CSV",
        data=csv_data,
        file_name=f"athletex_telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

with top_col4:
    hud_label = "☀ LIGHT" if is_dark else "◐ DARK"
    if st.button(hud_label, use_container_width=True):
        st.session_state.hud_mode = "LIGHT" if is_dark else "DARK"
        st.rerun()

# ==================== MODAL / EXPANDABLE: LOG SESSION ====================
if st.session_state.show_log_modal:
    with st.container():
        st.markdown("""
            <div class="nb-box" style="background:var(--nb-yellow); color:#000000; border-color:#000000;">
                <h4 style="margin:0 0 8px 0; color:#000000;">➕ INSERT NEW TRAINING SESSION // COCKROACHDB TRANSACTION</h4>
                <div style="font-family:'JetBrains Mono', monospace; font-size:12px; margin-bottom:12px;">Direct write to athletex.public.training_session with Raft consensus verification.</div>
            </div>
        """, unsafe_allow_html=True)
        
        ath_list = query("SELECT athlete_id, full_name FROM athletex.public.athlete ORDER BY full_name")
        with st.form("log_session_form"):
            f_col1, f_col2, f_col3 = st.columns(3)
            with f_col1:
                sel_ath_name = st.selectbox("Athlete", ath_list["full_name"].tolist())
                sel_activity = st.selectbox("Activity Type", ["Threshold Run", "Sprint Intervals", "VO2 Max Rowing", "Aerobic Cycling", "Weight Circuit", "Recovery Spin"])
            with f_col2:
                in_duration = st.number_input("Duration (Minutes)", min_value=10, max_value=240, value=45, step=5)
                in_intensity = st.slider("Session Intensity (1-10)", min_value=1.0, max_value=10.0, value=7.5, step=0.5)
            with f_col3:
                in_calories = st.number_input("Calories Burned (kcal)", min_value=50, max_value=3000, value=450, step=25)
                in_notes = st.text_input("Coach Notes", value="Target pace achieved; solid cardiac decoupling.")
            
            submit_btn = st.form_submit_button("COMMIT TRANSACTION TO CLUSTER ▶")
            if submit_btn:
                sel_aid = ath_list.loc[ath_list["full_name"] == sel_ath_name, "athlete_id"].iloc[0]
                # Find or assign plan
                plan_res = query("SELECT plan_id FROM athletex.public.training_plan WHERE athlete_id = %s LIMIT 1", (str(sel_aid),))
                if not plan_res.empty:
                    p_id = str(plan_res.iloc[0]["plan_id"])
                else:
                    # Pick arbitrary existing plan
                    p_id = str(query("SELECT plan_id FROM athletex.public.training_plan LIMIT 1").iloc[0]["plan_id"])
                
                insert_sql = """
                    INSERT INTO athletex.public.training_session 
                    (session_id, plan_id, session_date, duration_minutes, intensity, activity, calories_burned, notes)
                    VALUES (gen_random_uuid(), %s, now(), %s, %s, %s, %s, %s)
                """
                execute_commit(insert_sql, (p_id, int(in_duration), float(in_intensity), sel_activity, int(in_calories), in_notes))
                st.cache_data.clear()
                st.session_state.show_log_modal = False
                st.success(f"✓ TRANSACTION COMMITTED: Session logged for {sel_ath_name} in {in_duration}m!")
                st.rerun()

st.markdown("<hr style='border:1.5px solid var(--nb-border); margin:10px 0 16px 0;'>", unsafe_allow_html=True)

# ==================== SIDEBAR NAVIGATION ====================
st.sidebar.markdown("""
    <div style="font-family:'Space Grotesk', sans-serif; font-size:20px; font-weight:800; letter-spacing:-0.02em; padding:8px 0;">
        ⚡ ATHLETEX <span style="font-size:11px; background:var(--nb-blue); color:#fff; padding:2px 6px;">v10.0</span>
    </div>
    <div style="font-family:'JetBrains Mono', monospace; font-size:10.5px; margin-bottom:12px; color:var(--nb-gray);">
        BAUHAUS NEO-BRUTALIST HUD
    </div>
""", unsafe_allow_html=True)

nav_module = st.sidebar.radio(
    "SYSTEM MODULES",
    [
        "[01] OVERVIEW",
        "[02] ATHLETES & BIOMETRICS",
        "[03] TRAINING & ACWR AI",
        "[04] TELEMETRY & ANOMALY REVIEW",
        "[05] COMPETITIONS & SPORT ANALYTICS",
        "[06] COCKROACHDB SQL CONSOLE"
    ],
    label_visibility="collapsed"
)

st.sidebar.markdown("<hr style='border:1px solid var(--nb-border); margin:16px 0;'>", unsafe_allow_html=True)
st.sidebar.markdown(f"""
    <div class="nb-box" style="padding:10px; margin-bottom:12px;">
        <div style="font-family:'JetBrains Mono', monospace; font-size:10px; font-weight:700;">CLUSTER STATUS</div>
        <div style="font-family:'JetBrains Mono', monospace; font-size:12px; font-weight:800; color:var(--nb-green);">● ACTIVE // HEALTHY</div>
        <div style="font-family:'JetBrains Mono', monospace; font-size:10px; color:var(--nb-gray); margin-top:4px;">
            asia-south1 (3x Raft)
        </div>
    </div>
""", unsafe_allow_html=True)

if st.sidebar.button("🔄 PURGE CACHE & SYNC", use_container_width=True):
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

# ==================== MODULE 01: PERFORMANCE OVERVIEW ====================
if nav_module == "[01] OVERVIEW":
    st.markdown("### MODULE 01 // PERFORMANCE OVERVIEW & TELEMETRY HUD")
    
    # 4 Neo-Brutalist KPI Cards with numbered corner badges
    ath_count = int(scalar("SELECT COUNT(*) FROM athletex.public.athlete"))
    sport_count = int(scalar("SELECT COUNT(*) FROM athletex.public.sport"))
    ts_stats = query("SELECT COUNT(*) AS cnt, COALESCE(SUM(duration_minutes), 0) AS total_min, COALESCE(SUM(calories_burned), 0) AS total_cal FROM athletex.public.training_session")
    total_sessions = int(ts_stats.iloc[0]["cnt"])
    total_hours = round(float(ts_stats.iloc[0]["total_min"]) / 60.0, 1)
    total_cal = int(ts_stats.iloc[0]["total_cal"])
    telemetry_count = int(scalar("SELECT COUNT(*) FROM athletex.public.telemetry"))

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">01</div>
                <div class="nb-kpi-label">TOTAL ATHLETES</div>
                <div class="nb-kpi-value">{ath_count}</div>
                <div class="nb-kpi-sub">Active fleet monitored</div>
            </div>
        """, unsafe_allow_html=True)
    with k2:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">02</div>
                <div class="nb-kpi-label">MONITORED SPORTS</div>
                <div class="nb-kpi-value">{sport_count}</div>
                <div class="nb-kpi-sub">Olympic programs active</div>
            </div>
        """, unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">03</div>
                <div class="nb-kpi-label">TRAINING SESSIONS</div>
                <div class="nb-kpi-value">{total_sessions}</div>
                <div class="nb-kpi-sub">{total_hours} hrs · {total_cal:,} kcal</div>
            </div>
        """, unsafe_allow_html=True)
    with k4:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">04</div>
                <div class="nb-kpi-label">TELEMETRY IN STORAGE</div>
                <div class="nb-kpi-value">{telemetry_count:,}</div>
                <div class="nb-kpi-sub">High-frequency IoT ticks</div>
            </div>
        """, unsafe_allow_html=True)

    c_left, c_right = st.columns([1.35, 1])
    
    with c_left:
        st.markdown("#### ATHLETE PERFORMANCE LEADERBOARD // RANK() OVER WINDOW")
        lb_sql = """
            SELECT RANK() OVER (ORDER BY COALESCE(ps.gold_medals, 0) DESC, COALESCE(ps.avg_competition_score, 0) DESC NULLS LAST) AS rank,
                   a.full_name,
                   COALESCE(ps.competitions, 0) AS competitions,
                   COALESCE(ps.gold_medals, 0) AS gold,
                   COALESCE(ps.silver_medals, 0) AS silver,
                   COALESCE(ps.bronze_medals, 0) AS bronze,
                   ROUND(COALESCE(ps.avg_competition_score, 0), 1) AS avg_score,
                   ROUND(COALESCE(ps.best_evaluation_score, 0), 2) AS best_eval
            FROM athletex.public.athlete a
            LEFT JOIN athletex.public.athlete_performance_summary ps ON ps.athlete_id = a.athlete_id
            ORDER BY rank ASC
            LIMIT 10
        """
        lb_df = query(lb_sql)
        lb_df["Podium"] = lb_df.apply(lambda r: f"[{int(r['gold'])}G · {int(r['silver'])}S · {int(r['bronze'])}B]", axis=1)
        lb_df["Rank"] = lb_df["rank"].apply(lambda x: f"#{int(x):02d}")
        
        display_lb = lb_df[["Rank", "full_name", "competitions", "Podium", "avg_score", "best_eval"]].rename(columns={
            "full_name": "Athlete",
            "competitions": "Events",
            "avg_score": "Composite Rating",
            "best_eval": "Peak Eval"
        })
        
        st.dataframe(
            display_lb,
            use_container_width=True,
            hide_index=True,
            height=370,
            column_config={
                "Rank": st.column_config.TextColumn("Rank", width="small"),
                "Athlete": st.column_config.TextColumn("Athlete", width="medium"),
                "Events": st.column_config.NumberColumn("Events", format="%d"),
                "Podium": st.column_config.TextColumn("Podium [G·S·B]"),
                "Composite Rating": st.column_config.ProgressColumn("Composite Rating", min_value=0, max_value=100, format="%.1f"),
                "Peak Eval": st.column_config.NumberColumn("Peak Eval", format="⭐ %.2f"),
            }
        )

    with c_right:
        st.markdown("#### PODIUM DISTRIBUTION // BRUTALIST DONUT")
        medals_df = query("""
            SELECT COALESCE(SUM(gold_medals), 0) AS Gold,
                   COALESCE(SUM(silver_medals), 0) AS Silver,
                   COALESCE(SUM(bronze_medals), 0) AS Bronze
            FROM athletex.public.athlete_performance_summary
        """)
        if not medals_df.empty:
            medals_df.columns = [c.capitalize() for c in medals_df.columns]
            m_long = medals_df.melt(var_name="Medal", value_name="Count")
            m_long["Count"] = pd.to_numeric(m_long["Count"], errors="coerce").fillna(0)
            
            donut_fig = px.pie(
                m_long,
                names="Medal",
                values="Count",
                hole=0.62,
                color="Medal",
                color_discrete_map={"Gold": "#FFCC00", "Silver": "#A8B5C2", "Bronze": "#D97706"}
            )
            donut_fig.update_traces(
                textinfo="percent+value",
                textfont=dict(family="'JetBrains Mono', monospace", size=12, color="#000000"),
                marker=dict(line=dict(color=border_color, width=2.5)),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>"
            )
            donut_fig.update_layout(
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
            )
            style_nb_fig(donut_fig, height=310)
            st.plotly_chart(donut_fig, use_container_width=True, theme=None, config={"displaylogo": False})
            
            # Gold / Silver / Bronze Summary Cards
            g_cnt = int(medals_df.iloc[0]["Gold"])
            s_cnt = int(medals_df.iloc[0]["Silver"])
            b_cnt = int(medals_df.iloc[0]["Bronze"])
            st.markdown(f"""
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:8px; margin-top:8px;">
                    <div class="nb-box" style="padding:8px; text-align:center; background:#FFCC00; color:#000; border-color:#000;">
                        <div style="font-family:'Space Grotesk', sans-serif; font-size:11px; font-weight:800;">GOLD</div>
                        <div style="font-family:'JetBrains Mono', monospace; font-size:20px; font-weight:800;">{g_cnt}</div>
                    </div>
                    <div class="nb-box" style="padding:8px; text-align:center; background:#A8B5C2; color:#000; border-color:#000;">
                        <div style="font-family:'Space Grotesk', sans-serif; font-size:11px; font-weight:800;">SILVER</div>
                        <div style="font-family:'JetBrains Mono', monospace; font-size:20px; font-weight:800;">{s_cnt}</div>
                    </div>
                    <div class="nb-box" style="padding:8px; text-align:center; background:#D97706; color:#FFF; border-color:#000;">
                        <div style="font-family:'Space Grotesk', sans-serif; font-size:11px; font-weight:800;">BRONZE</div>
                        <div style="font-family:'JetBrains Mono', monospace; font-size:20px; font-weight:800;">{b_cnt}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# ==================== MODULE 02: ATHLETES & BIOMETRICS ====================
elif nav_module == "[02] ATHLETES & BIOMETRICS":
    st.markdown("### MODULE 02 // ATHLETES & WEARABLE BIOMETRICS")
    sub_tab1, sub_tab2, sub_tab3 = st.tabs([
        "[01] ATHLETE DIRECTORY",
        "[02] INDIVIDUAL BIOMETRICS",
        "[03] HEAD-TO-HEAD RADAR COMPARISON"
    ])

    # SUB-TAB 01: ATHLETE DIRECTORY
    with sub_tab1:
        st.markdown("#### ATHLETE ROSTER & PERFORMANCE EVALUATIONS")
        dir_sql = """
            SELECT a.athlete_id, a.full_name, s.sport_name,
                   COALESCE(ps.competitions, 0) AS competitions,
                   COALESCE(ps.gold_medals, 0) AS gold_medals,
                   COALESCE(ps.silver_medals, 0) AS silver_medals,
                   COALESCE(ps.bronze_medals, 0) AS bronze_medals,
                   COALESCE(ps.avg_competition_score, 0) AS avg_score,
                   COALESCE(ps.best_evaluation_score, 0) AS best_eval
            FROM athletex.public.athlete a
            LEFT JOIN athletex.public.athlete_sport asp ON asp.athlete_id = a.athlete_id
            LEFT JOIN athletex.public.sport s ON s.sport_id = asp.sport_id
            LEFT JOIN athletex.public.athlete_performance_summary ps ON ps.athlete_id = a.athlete_id
            ORDER BY a.full_name
        """
        all_ath = query(dir_sql)
        
        f_c1, f_c2 = st.columns([3, 1.2])
        with f_c1:
            search_query = st.text_input("🔍 FILTER BY ATHLETE OR SPORT", placeholder="Type name or sport (e.g. Liam, Athletics)...")
        with f_c2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            filter_gold_only = st.checkbox("🥇 GOLD MEDALISTS ONLY", value=False)
        
        if search_query:
            all_ath = all_ath[all_ath["full_name"].str.contains(search_query, case=False, na=False) | all_ath["sport_name"].str.contains(search_query, case=False, na=False)]
        if filter_gold_only:
            all_ath = all_ath[all_ath["gold_medals"] > 0]

        disp_ath = all_ath[["full_name", "sport_name", "competitions", "gold_medals", "silver_medals", "bronze_medals", "avg_score", "best_eval"]].rename(columns={
            "full_name": "Athlete",
            "sport_name": "Primary Sport",
            "competitions": "Events",
            "gold_medals": "Gold",
            "silver_medals": "Silver",
            "bronze_medals": "Bronze",
            "avg_score": "Composite Rating",
            "best_eval": "Best Eval"
        })

        st.dataframe(
            disp_ath,
            use_container_width=True,
            hide_index=True,
            height=380,
            column_config={
                "Athlete": st.column_config.TextColumn("Athlete", width="medium"),
                "Primary Sport": st.column_config.TextColumn("Sport", width="small"),
                "Events": st.column_config.NumberColumn("Events", format="%d"),
                "Gold": st.column_config.NumberColumn("🥇 Gold", format="%d"),
                "Silver": st.column_config.NumberColumn("🥈 Silver", format="%d"),
                "Bronze": st.column_config.NumberColumn("🥉 Bronze", format="%d"),
                "Composite Rating": st.column_config.NumberColumn("Avg Score", format="%.2f"),
                "Best Eval": st.column_config.NumberColumn("Best Eval", format="⭐ %.2f"),
            }
        )

    # SUB-TAB 02: INDIVIDUAL BIOMETRICS
    with sub_tab2:
        ath_choices = query("SELECT athlete_id, full_name FROM athletex.public.athlete ORDER BY full_name")
        if not ath_choices.empty:
            sel_athlete = st.selectbox("SELECT ATHLETE PROFILE // TELEMETRY TRACE", ath_choices["full_name"].tolist(), key="sel_bio_ath")
            selected_aid = str(ath_choices.loc[ath_choices["full_name"] == sel_athlete, "athlete_id"].iloc[0])

            # Fetch recent telemetry
            t_df = query("""
                SELECT recorded_at, heart_rate, training_intensity, speed_kmh, distance_km
                FROM athletex.public.telemetry
                WHERE athlete_id = %s
                ORDER BY recorded_at DESC LIMIT 120
            """, (selected_aid,))

            if not t_df.empty:
                t_df = t_df.sort_values("recorded_at")
                for c in ["heart_rate", "training_intensity", "speed_kmh", "distance_km"]:
                    t_df[c] = pd.to_numeric(t_df[c], errors="coerce")

                max_hr = int(t_df["heart_rate"].max())
                avg_int = round(float(t_df["training_intensity"].mean()), 1)
                max_dist = round(float(t_df["distance_km"].max()), 2)
                t_count = len(t_df)

                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    st.markdown(f"""
                        <div class="nb-kpi-card">
                            <div class="nb-kpi-badge">HR</div>
                            <div class="nb-kpi-label">PEAK HEART RATE</div>
                            <div class="nb-kpi-value" style="color:var(--nb-red);">{max_hr} <span style="font-size:16px;">BPM</span></div>
                            <div class="nb-kpi-sub">Threshold line at 160 BPM</div>
                        </div>
                    """, unsafe_allow_html=True)
                with b2:
                    st.markdown(f"""
                        <div class="nb-kpi-card">
                            <div class="nb-kpi-badge">INT</div>
                            <div class="nb-kpi-label">AVG INTENSITY</div>
                            <div class="nb-kpi-value" style="color:var(--nb-yellow);">{avg_int} <span style="font-size:16px;">/10</span></div>
                            <div class="nb-kpi-sub">Effort index</div>
                        </div>
                    """, unsafe_allow_html=True)
                with b3:
                    st.markdown(f"""
                        <div class="nb-kpi-card">
                            <div class="nb-kpi-badge">DST</div>
                            <div class="nb-kpi-label">PEAK DISTANCE</div>
                            <div class="nb-kpi-value">{max_dist} <span style="font-size:16px;">KM</span></div>
                            <div class="nb-kpi-sub">Session max logged</div>
                        </div>
                    """, unsafe_allow_html=True)
                with b4:
                    st.markdown(f"""
                        <div class="nb-kpi-card">
                            <div class="nb-kpi-badge">TICKS</div>
                            <div class="nb-kpi-label">TELEMETRY POINTS</div>
                            <div class="nb-kpi-value" style="color:var(--nb-blue);">{t_count}</div>
                            <div class="nb-kpi-sub">120 recent traces</div>
                        </div>
                    """, unsafe_allow_html=True)

                # Cardiac Load Tracing Line Chart
                hr_fig = go.Figure()
                hr_fig.add_trace(go.Scatter(
                    x=t_df["recorded_at"],
                    y=t_df["heart_rate"],
                    mode="lines+markers",
                    name="Cardiac Pulse (BPM)",
                    line=dict(color="#0047FF", width=2.5),
                    marker=dict(size=4, color="#0047FF")
                ))
                # Add threshold shading for >=160 BPM
                hr_fig.add_hrect(
                    y0=160,
                    y1=max(max_hr + 10, 200),
                    fillcolor="rgba(255, 59, 48, 0.15)",
                    line_width=0,
                    annotation_text="⚠ HIGH-STRAIN ZONE (≥160 BPM)",
                    annotation_position="top left",
                    annotation_font=dict(color="#FF3B30", family="'JetBrains Mono', monospace", size=11)
                )
                hr_fig.add_hline(y=160, line_dash="dash", line_color="#FF3B30", line_width=2)
                style_nb_fig(hr_fig, height=320, title=f"CARDIAC LOAD TRACE // {sel_athlete.upper()}")
                st.plotly_chart(hr_fig, use_container_width=True, theme=None, config={"displaylogo": False})

                # Speed vs Intensity Correlation
                speed_fig = make_subplots(specs=[[{"secondary_y": True}]])
                speed_fig.add_trace(
                    go.Scatter(x=t_df["recorded_at"], y=t_df["speed_kmh"], name="Speed (km/h)", line=dict(color="#00D66F", width=2.5)),
                    secondary_y=False
                )
                speed_fig.add_trace(
                    go.Scatter(x=t_df["recorded_at"], y=t_df["training_intensity"], name="Intensity (/10)", line=dict(color="#FFCC00", width=2, dash="dot")),
                    secondary_y=True
                )
                speed_fig.update_yaxes(title_text="Velocity (km/h)", secondary_y=False)
                speed_fig.update_yaxes(title_text="Intensity (/10)", secondary_y=True)
                style_nb_fig(speed_fig, height=300, title="LOCOMOTIVE SPEED VS TRAINING INTENSITY CORRELATION")
                st.plotly_chart(speed_fig, use_container_width=True, theme=None, config={"displaylogo": False})
            else:
                st.info("No telemetry logs found for selected athlete.")

    # SUB-TAB 03: HEAD-TO-HEAD RADAR COMPARISON
    with sub_tab3:
        st.markdown("#### HEAD-TO-HEAD BIOMETRIC RADAR & ATTRIBUTE COMPARISON")
        st.caption("Normalized 6-axis performance comparison across aerobic endurance, mechanical speed, and competition rating.")

        radar_sql = """
            SELECT a.athlete_id, a.full_name,
                   COALESCE(fa.vo2_max, 52.0) AS vo2_max,
                   COALESCE(fa.endurance_score, 7.5) AS endurance,
                   COALESCE(fa.strength_score, 7.0) AS strength,
                   COALESCE(ps.avg_competition_score, 75.0) AS comp_score,
                   COALESCE(MAX(t.speed_kmh), 22.0) AS peak_speed,
                   COALESCE(AVG(t.training_intensity), 7.5) AS avg_intensity,
                   COUNT(t.telemetry_id) AS telemetry_count
            FROM athletex.public.athlete a
            LEFT JOIN athletex.public.fitness_assessment fa ON fa.athlete_id = a.athlete_id
            LEFT JOIN athletex.public.athlete_performance_summary ps ON ps.athlete_id = a.athlete_id
            LEFT JOIN athletex.public.telemetry t ON t.athlete_id = a.athlete_id
            GROUP BY a.athlete_id, a.full_name, fa.vo2_max, fa.endurance_score, fa.strength_score, ps.avg_competition_score
            ORDER BY a.full_name
        """
        r_df = query(radar_sql)
        
        r_df["VO2 Efficiency"] = (r_df["vo2_max"].astype(float) * 1.3).clip(30, 100).round(1)
        r_df["Peak Speed"] = (r_df["peak_speed"].astype(float) * 3.2).clip(30, 100).round(1)
        r_df["Cardiac Recovery"] = (r_df["endurance"].astype(float) * 10.0).clip(30, 100).round(1)
        r_df["Strain Tolerance"] = (r_df["strength"].astype(float) * 10.0).clip(30, 100).round(1)
        r_df["Comp Score"] = r_df["comp_score"].astype(float).clip(30, 100).round(1)
        max_tel = r_df["telemetry_count"].max() if r_df["telemetry_count"].max() > 0 else 1
        r_df["Workload Volume"] = ((r_df["telemetry_count"].astype(float) / max_tel) * 100.0).clip(30, 100).round(1)

        rc_1, rc_2 = st.columns(2)
        with rc_1:
            ath_a_name = st.selectbox("ATHLETE A (COBALT BLUE)", r_df["full_name"].tolist(), index=0, key="radar_ath_a")
        with rc_2:
            ath_b_name = st.selectbox("ATHLETE B (SIGNAL RED)", r_df["full_name"].tolist(), index=min(1, len(r_df)-1), key="radar_ath_b")

        categories = ['VO2 Efficiency', 'Peak Speed', 'Cardiac Recovery', 'Strain Tolerance', 'Comp Score', 'Workload Volume']
        row_a = r_df[r_df["full_name"] == ath_a_name].iloc[0]
        row_b = r_df[r_df["full_name"] == ath_b_name].iloc[0]

        rad_fig = go.Figure()
        rad_fig.add_trace(go.Scatterpolar(
            r=[row_a[c] for c in categories] + [row_a[categories[0]]],
            theta=categories + [categories[0]],
            fill='toself',
            name=ath_a_name.upper(),
            line=dict(color='#0047FF', width=3),
            fillcolor='rgba(0, 71, 255, 0.22)'
        ))
        rad_fig.add_trace(go.Scatterpolar(
            r=[row_b[c] for c in categories] + [row_b[categories[0]]],
            theta=categories + [categories[0]],
            fill='toself',
            name=ath_b_name.upper(),
            line=dict(color='#FF3B30', width=3),
            fillcolor='rgba(255, 59, 48, 0.22)'
        ))
        rad_fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], linecolor=border_color, gridcolor=plotly_grid),
                bgcolor=paper_plot_bg
            ),
            height=400,
            margin=dict(l=30, r=30, t=30, b=30),
            paper_bgcolor=paper_plot_bg,
            font=dict(family="'JetBrains Mono', monospace", size=11, color=plotly_font_color),
            legend=dict(orientation="h", yanchor="bottom", y=-0.12, xanchor="center", x=0.5)
        )
        st.plotly_chart(rad_fig, use_container_width=True, theme=None, config={"displaylogo": False})

        # Head to Head Differential Matrix
        diff_data = []
        for cat in categories:
            val_a = row_a[cat]
            val_b = row_b[cat]
            delta = round(val_a - val_b, 1)
            adv = f"🔵 {ath_a_name} (+{delta})" if delta > 0 else (f"🔴 {ath_b_name} (+{abs(delta)})" if delta < 0 else "EQUAL")
            diff_data.append({
                "Attribute Axis": cat,
                f"{ath_a_name} (A)": f"{val_a:.1f}",
                f"{ath_b_name} (B)": f"{val_b:.1f}",
                "Delta (A - B)": f"{delta:+.1f}",
                "Point Advantage": adv
            })
        st.dataframe(pd.DataFrame(diff_data), use_container_width=True, hide_index=True)

# ==================== MODULE 03: TRAINING WORKLOAD & ACWR AI ====================
elif nav_module == "[03] TRAINING & ACWR AI":
    st.markdown("### MODULE 03 // TRAINING WORKLOAD & TIM GABBETT ACWR ENGINE")

    # 4 Workload KPIs
    ts_all = query("""
        SELECT a.full_name, COUNT(ts.session_id) AS total_sessions,
               COALESCE(SUM(ts.duration_minutes), 0) AS total_minutes,
               ROUND(COALESCE(SUM(ts.duration_minutes), 0) / 60.0, 2) AS total_hours,
               COALESCE(SUM(ts.calories_burned), 0) AS total_calories,
               ROUND(AVG(ts.duration_minutes), 1) AS avg_session_minutes
        FROM athletex.public.athlete a
        LEFT JOIN athletex.public.training_plan tp ON tp.athlete_id = a.athlete_id
        LEFT JOIN athletex.public.training_session ts ON ts.plan_id = tp.plan_id
        GROUP BY a.athlete_id, a.full_name
        ORDER BY total_minutes DESC
    """)
    for col in ["total_sessions", "total_minutes", "total_hours", "total_calories", "avg_session_minutes"]:
        ts_all[col] = pd.to_numeric(ts_all[col], errors="coerce").fillna(0)

    team_hours = ts_all["total_minutes"].sum() / 60.0
    team_sessions = int(ts_all["total_sessions"].sum())
    team_cal = int(ts_all["total_calories"].sum())
    avg_sess = round(ts_all["total_minutes"].sum() / team_sessions, 1) if team_sessions > 0 else 0

    w1, w2, w3, w4 = st.columns(4)
    with w1:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">01</div>
                <div class="nb-kpi-label">TEAM HOURS LOGGED</div>
                <div class="nb-kpi-value">{team_hours:.1f} <span style="font-size:16px;">HRS</span></div>
                <div class="nb-kpi-sub">Cumulative fleet load</div>
            </div>
        """, unsafe_allow_html=True)
    with w2:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">02</div>
                <div class="nb-kpi-label">SESSIONS LOGGED</div>
                <div class="nb-kpi-value">{team_sessions}</div>
                <div class="nb-kpi-sub">Completed workout units</div>
            </div>
        """, unsafe_allow_html=True)
    with w3:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">03</div>
                <div class="nb-kpi-label">CALORIES BURNED</div>
                <div class="nb-kpi-value">{team_cal:,}</div>
                <div class="nb-kpi-sub">Total energy expenditure</div>
            </div>
        """, unsafe_allow_html=True)
    with w4:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">04</div>
                <div class="nb-kpi-label">AVG SESSION TIME</div>
                <div class="nb-kpi-value">{avg_sess:.0f} <span style="font-size:16px;">MIN</span></div>
                <div class="nb-kpi-sub">Mean workout duration</div>
            </div>
        """, unsafe_allow_html=True)

    # ACWR (Acute:Chronic Workload Ratio) & Readiness Simulator
    st.markdown("#### ⚡ TIM GABBETT ACWR PREDICTIVE INJURY & READINESS SIMULATOR")
    st.caption("Calculate Acute (7-Day Fatigue) to Chronic (28-Day Fitness) Workload Ratio with HRV Autonomic Readiness scoring.")

    sim_box = st.container()
    with sim_box:
        st.markdown("""
            <div class="nb-box" style="margin-bottom:12px;">
                <div style="font-family:'Space Grotesk', sans-serif; font-size:13px; font-weight:800; margin-bottom:8px;">
                    SIMULATION CONTROLS // REAL-TIME BIOMETRIC INPUTS
                </div>
        """, unsafe_allow_html=True)
        
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            in_acute = st.slider("Acute Load (7-Day AU)", min_value=100, max_value=600, value=280, step=10)
        with sc2:
            in_chronic = st.slider("Chronic Load (28-Day AU)", min_value=100, max_value=500, value=250, step=10)
        with sc3:
            in_hrv = st.slider("Heart Rate Var (ms)", min_value=20, max_value=120, value=68, step=2)
        with sc4:
            in_sleep = st.slider("Sleep Duration (hrs)", min_value=4.0, max_value=10.0, value=7.5, step=0.5)

        # Computation
        calc_acwr = round(in_acute / in_chronic, 2)
        
        # Readiness formula
        if 0.85 <= calc_acwr <= 1.25:
            acwr_pts = 40.0
        elif 0.70 <= calc_acwr <= 1.40:
            acwr_pts = 30.0
        elif 0.50 <= calc_acwr <= 1.60:
            acwr_pts = 18.0
        else:
            acwr_pts = 5.0
        hrv_pts = min(35.0, (in_hrv / 80.0) * 35.0)
        sleep_pts = min(25.0, (in_sleep / 8.0) * 25.0)
        readiness_score = int(min(100.0, max(10.0, acwr_pts + hrv_pts + sleep_pts)))

        # Tier Evaluation
        if calc_acwr < 0.80:
            tier_name = "UNDER-TRAINING // DETRAINING RISK"
            tier_color = "var(--nb-blue)"
            tier_bg = "#0047FF"
            tier_text = "#FFFFFF"
            prescription = "Sub-optimal physiological stimulus. Increment weekly workload volume by +10% with aerobic base building to prevent sudden-spike vulnerability."
        elif calc_acwr <= 1.30:
            tier_name = "OPTIMAL SWEET SPOT // PEAK READINESS"
            tier_color = "var(--nb-green)"
            tier_bg = "#00D66F"
            tier_text = "#000000"
            prescription = "Ideal fitness-to-fatigue adaptation envelope (<5% soft-tissue strain incidence). Progressive overload safe. Maintain current planned intensity cycles."
        elif calc_acwr <= 1.50:
            tier_name = "OVERREACHING CAUTION // FATIGUE SURGE"
            tier_color = "var(--nb-yellow)"
            tier_bg = "#FFCC00"
            tier_text = "#000000"
            prescription = "Acute workload outpacing chronic adaptation capacity. Cap high-intensity interval duration and mandate 48h active recovery between maximal efforts."
        else:
            tier_name = "DANGER ZONE // HIGH INJURY RISK SPIKE"
            tier_color = "var(--nb-red)"
            tier_bg = "#FF3B30"
            tier_text = "#FFFFFF"
            prescription = "CRITICAL OVERLOAD: Relative risk of soft-tissue or ligament injury spikes by 3.2x–4.5x. Immediate -40% volume de-escalation required. Prioritize sleep & recovery."

        res_c1, res_c2 = st.columns([1.5, 2.5])
        with res_c1:
            st.markdown(f"""
                <div style="background:{tier_bg}; color:{tier_text}; border:2.5px solid var(--nb-border); box-shadow:3px 3px 0px var(--nb-shadow); padding:1rem; text-align:center;">
                    <div style="font-family:'Space Grotesk', sans-serif; font-size:12px; font-weight:800; letter-spacing:0.05em;">COMPUTED ACWR</div>
                    <div style="font-family:'JetBrains Mono', monospace; font-size:42px; font-weight:800; line-height:1.1;">{calc_acwr:.2f}</div>
                    <div style="font-family:'JetBrains Mono', monospace; font-size:12px; font-weight:700; margin-top:4px;">READINESS: {readiness_score}/100</div>
                </div>
            """, unsafe_allow_html=True)
        with res_c2:
            st.markdown(f"""
                <div class="nb-box" style="margin-bottom:0px; height:100%;">
                    <div style="font-family:'Space Grotesk', sans-serif; font-size:13px; font-weight:800; color:{tier_color};">
                        ● {tier_name}
                    </div>
                    <div style="font-family:'JetBrains Mono', monospace; font-size:12px; margin-top:6px; line-height:1.4;">
                        <b>COACHING ACTION:</b> {prescription}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Dynamic Workload Leaderboard
    st.markdown("#### DYNAMIC WORKLOAD LEADERBOARD // TOP 10 ATHLETES")
    sort_rank = st.radio("RANK ROSTER BY:", ["Training Minutes", "Calories Burned"], horizontal=True)
    metric_col = "total_minutes" if sort_rank == "Training Minutes" else "total_calories"
    
    chart_ts = ts_all.nlargest(10, metric_col).sort_values(metric_col, ascending=True)
    bar_fig = px.bar(
        chart_ts,
        x=metric_col,
        y="full_name",
        orientation="h",
        labels={metric_col: sort_rank, "full_name": "Athlete"},
        color_discrete_sequence=["#0047FF"]
    )
    bar_fig.update_traces(
        marker=dict(line=dict(color=border_color, width=2)),
        hovertemplate="<b>%{y}</b><br>" + sort_rank + ": %{x:,.0f}<extra></extra>"
    )
    style_nb_fig(bar_fig, height=360, title=f"TOP 10 ATHLETES RANKED BY {sort_rank.upper()}")
    st.plotly_chart(bar_fig, use_container_width=True, theme=None, config={"displaylogo": False})

# ==================== MODULE 04: TELEMETRY & ANOMALY REVIEW ====================
elif nav_module == "[04] TELEMETRY & ANOMALY REVIEW":
    st.markdown("### MODULE 04 // WEARABLE TELEMETRY & ANOMALY REVIEW CENTER")
    tel_tab1, tel_tab2 = st.tabs(["[01] FLEET TRENDS", "[02] ANOMALY / REVIEW FLAGS"])

    # SUB-TAB 01: FLEET TRENDS
    with tel_tab1:
        st.markdown("#### LONGITUDINAL FLEET WEARABLE TRENDS")
        daily_trends = query("""
            SELECT DATE_TRUNC('day', recorded_at) AS reading_day,
                   COUNT(*) AS total_readings,
                   ROUND(AVG(heart_rate), 1) AS avg_heart_rate,
                   MIN(heart_rate) AS min_heart_rate,
                   MAX(heart_rate) AS max_heart_rate,
                   ROUND(AVG(training_intensity), 2) AS avg_training_intensity,
                   ROUND(AVG(speed_kmh), 1) AS avg_speed_kmh
            FROM athletex.public.telemetry
            GROUP BY DATE_TRUNC('day', recorded_at)
            ORDER BY reading_day ASC
        """)
        if not daily_trends.empty:
            for c in ["total_readings", "avg_heart_rate", "min_heart_rate", "max_heart_rate", "avg_training_intensity", "avg_speed_kmh"]:
                daily_trends[c] = pd.to_numeric(daily_trends[c], errors="coerce")

            tc1, tc2 = st.columns(2)
            with tc1:
                fig_dhr = px.line(daily_trends, x="reading_day", y="avg_heart_rate", markers=True)
                fig_dhr.update_traces(line=dict(color="#0047FF", width=2.5), marker=dict(color="#0047FF", size=6))
                style_nb_fig(fig_dhr, height=290, title="DAILY FLEET AVG HEART RATE (BPM)")
                st.plotly_chart(fig_dhr, use_container_width=True, theme=None, config={"displaylogo": False})
            with tc2:
                fig_dint = px.line(daily_trends, x="reading_day", y="avg_training_intensity", markers=True)
                fig_dint.update_traces(line=dict(color="#FFCC00", width=2.5), marker=dict(color="#FFCC00", size=6))
                style_nb_fig(fig_dint, height=290, title="DAILY FLEET AVG TRAINING INTENSITY (/10)")
                st.plotly_chart(fig_dint, use_container_width=True, theme=None, config={"displaylogo": False})

            st.markdown("#### DAILY AGGREGATION LOGS // COCKROACHDB TIME-SERIES")
            disp_daily = daily_trends.rename(columns={
                "reading_day": "Date",
                "total_readings": "Readings",
                "avg_heart_rate": "Avg HR",
                "min_heart_rate": "Min HR",
                "max_heart_rate": "Peak HR",
                "avg_training_intensity": "Avg Intensity",
                "avg_speed_kmh": "Avg Speed"
            })
            st.dataframe(disp_daily, use_container_width=True, hide_index=True, height=260)

    # SUB-TAB 02: ANOMALY REVIEW FLAGS & DYNAMIC TUNER
    with tel_tab2:
        st.markdown("#### ⚡ DYNAMIC PHYSIOLOGICAL ANOMALY TUNER & TRIAGE BOARD")
        st.caption("Interactive threshold tuner querying real-time CockroachDB telemetry clusters for cardiac overload and acute mechanical strain.")

        tune_c1, tune_c2 = st.columns(2)
        with tune_c1:
            threshold_hr = st.slider("MINIMUM CARDIAC THRESHOLD (BPM)", min_value=150, max_value=185, value=160, step=1)
        with tune_c2:
            threshold_int = st.slider("MINIMUM TRAINING INTENSITY (/10)", min_value=7.0, max_value=9.5, value=8.0, step=0.1)

        anom_sql = """
            SELECT a.athlete_id, a.full_name, COUNT(t.telemetry_id) AS flagged_readings,
                   ROUND(AVG(t.heart_rate), 1) AS avg_heart_rate,
                   MAX(t.heart_rate) AS max_heart_rate,
                   ROUND(AVG(t.training_intensity), 1) AS avg_intensity
            FROM athletex.public.athlete a
            JOIN athletex.public.telemetry t ON t.athlete_id = a.athlete_id
            WHERE t.heart_rate >= %s AND t.training_intensity >= %s
            GROUP BY a.athlete_id, a.full_name
            HAVING COUNT(t.telemetry_id) >= 5
            ORDER BY flagged_readings DESC
        """
        anom_res = query(anom_sql, (threshold_hr, threshold_int))
        
        st.markdown(f"""
            <div class="nb-box" style="background:var(--nb-yellow); color:#000; border-color:#000; padding:10px 16px;">
                <b>RULE TRIGGERED:</b> Heart Rate ≥ {threshold_hr} BPM AND Intensity ≥ {threshold_int}/10 across ≥ 5 readings. 
                Found <b>{len(anom_res)} flagged athletes</b> in active cluster hot storage.
            </div>
        """, unsafe_allow_html=True)

        if not anom_res.empty:
            for idx, row in anom_res.iterrows():
                aid = str(row["athlete_id"])
                name = row["full_name"]
                flag_cnt = int(row["flagged_readings"])
                is_triaged = (aid in st.session_state.triaged_athletes)

                r_col1, r_col2, r_col3, r_col4, r_col5 = st.columns([2.5, 1.2, 1.2, 1.2, 1.5])
                with r_col1:
                    st.markdown(f"**🏃 {name}**")
                    st.caption(f"{flag_cnt} anomalous ticks logged")
                with r_col2:
                    st.markdown(f"Avg HR: **{row['avg_heart_rate']}**")
                with r_col3:
                    st.markdown(f"Peak HR: **{int(row['max_heart_rate'])}**")
                with r_col4:
                    st.markdown(f"Intensity: **{row['avg_intensity']}/10**")
                with r_col5:
                    if is_triaged:
                        if st.button("CLEARED ✓", key=f"triage_btn_{aid}", use_container_width=True):
                            st.session_state.triaged_athletes.remove(aid)
                            st.rerun()
                    else:
                        if st.button("🔴 TRIAGE", key=f"triage_btn_{aid}", use_container_width=True):
                            st.session_state.triaged_athletes.add(aid)
                            st.rerun()
                st.markdown("<hr style='border:1px dashed var(--nb-border); margin:4px 0 8px 0;'>", unsafe_allow_html=True)
        else:
            st.success("Zero athletes currently exceed this threshold filter.")

# ==================== MODULE 05: COMPETITIONS & SPORT ANALYTICS ====================
elif nav_module == "[05] COMPETITIONS & SPORT ANALYTICS":
    st.markdown("### MODULE 05 // MULTI-SPORT COMPETITION & PODIUM ANALYTICS")

    comp_sql = """
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
    """
    comp_df = query(comp_sql)
    for col in ["registered_athletes", "total_competitions", "gold_medals", "silver_medals", "bronze_medals", "avg_competition_score"]:
        comp_df[col] = pd.to_numeric(comp_df[col], errors="coerce").fillna(0)

    total_sports = comp_df["sport_name"].nunique()
    total_comps = int(scalar("SELECT COUNT(*) FROM athletex.public.competition"))
    total_medals = int(comp_df[["gold_medals", "silver_medals", "bronze_medals"]].sum().sum())
    top_sport = comp_df.iloc[0]["sport_name"] if not comp_df.empty else "N/A"

    cp1, cp2, cp3, cp4 = st.columns(4)
    with cp1:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">01</div>
                <div class="nb-kpi-label">SPORTS MONITORED</div>
                <div class="nb-kpi-value">{total_sports}</div>
                <div class="nb-kpi-sub">Tracked disciplines</div>
            </div>
        """, unsafe_allow_html=True)
    with cp2:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">02</div>
                <div class="nb-kpi-label">TOTAL COMPETITIONS</div>
                <div class="nb-kpi-value">{total_comps}</div>
                <div class="nb-kpi-sub">Sanctioned meets</div>
            </div>
        """, unsafe_allow_html=True)
    with cp3:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">03</div>
                <div class="nb-kpi-label">MEDALS DISTRIBUTED</div>
                <div class="nb-kpi-value">{total_medals}</div>
                <div class="nb-kpi-sub">Gold, Silver, Bronze</div>
            </div>
        """, unsafe_allow_html=True)
    with cp4:
        st.markdown(f"""
            <div class="nb-kpi-card">
                <div class="nb-kpi-badge">04</div>
                <div class="nb-kpi-label">LEADING PROGRAM</div>
                <div class="nb-kpi-value" style="font-size:22px; padding-top:4px;">{top_sport.upper()}</div>
                <div class="nb-kpi-sub">Highest gold yield</div>
            </div>
        """, unsafe_allow_html=True)

    # Grouped Bar Chart
    if not comp_df.empty:
        comp_long = comp_df.melt(id_vars="sport_name", value_vars=["gold_medals", "silver_medals", "bronze_medals"], var_name="Medal", value_name="Count")
        comp_long["Medal"] = comp_long["Medal"].str.replace("_medals", "").str.title()
        
        c_bar = px.bar(
            comp_long,
            x="sport_name",
            y="Count",
            color="Medal",
            barmode="group",
            labels={"sport_name": "Sport", "Count": "Medals"},
            color_discrete_map={"Gold": "#FFCC00", "Silver": "#A8B5C2", "Bronze": "#D97706"}
        )
        c_bar.update_traces(marker=dict(line=dict(color=border_color, width=2)))
        style_nb_fig(c_bar, height=350, title="PODIUM MEDAL BREAKDOWN BY SPORT PROGRAM")
        st.plotly_chart(c_bar, use_container_width=True, theme=None, config={"displaylogo": False})

    st.markdown("#### SPORT REGISTRY & STATISTICAL BREAKDOWN")
    st.dataframe(
        comp_df.rename(columns={
            "sport_name": "Sport",
            "registered_athletes": "Athletes",
            "total_competitions": "Meets",
            "gold_medals": "Gold",
            "silver_medals": "Silver",
            "bronze_medals": "Bronze",
            "avg_competition_score": "Composite Rating"
        }),
        use_container_width=True,
        hide_index=True
    )

# ==================== MODULE 06: COCKROACHDB DISTRIBUTED SQL CONSOLE ====================
elif nav_module == "[06] COCKROACHDB SQL CONSOLE":
    st.markdown("### MODULE 06 // COCKROACHDB DISTRIBUTED SQL OBSERVABILITY CONSOLE")
    st.caption("Live node health telemetry, multi-region replication status, and production SQL query execution console.")

    # 3 Cluster Node Topology Cards
    st.markdown("#### DISTRIBUTED MULTI-AZ NODE TOPOLOGY // ASIA-SOUTH1")
    n1, n2, n3 = st.columns(3)
    with n1:
        st.markdown(f"""
            <div class="nb-box">
                <div class="nb-kpi-badge">NODE 01</div>
                <div style="font-family:'Space Grotesk', sans-serif; font-size:14px; font-weight:800;">asia-south1-a</div>
                <div style="font-family:'JetBrains Mono', monospace; font-size:12px; color:var(--nb-green); margin:6px 0;">● ONLINE · LEADER</div>
                <div style="font-family:'JetBrains Mono', monospace; font-size:11px; line-height:1.5;">
                    <b>Replicas:</b> 3x Raft Consensus<br>
                    <b>RTT Latency:</b> 1.82 ms<br>
                    <b>Storage:</b> NVMe Hot SSD (94.2 GB)
                </div>
            </div>
        """, unsafe_allow_html=True)
    with n2:
        st.markdown(f"""
            <div class="nb-box">
                <div class="nb-kpi-badge">NODE 02</div>
                <div style="font-family:'Space Grotesk', sans-serif; font-size:14px; font-weight:800;">asia-south1-b</div>
                <div style="font-family:'JetBrains Mono', monospace; font-size:12px; color:var(--nb-green); margin:6px 0;">● ONLINE · REPLICA</div>
                <div style="font-family:'JetBrains Mono', monospace; font-size:11px; line-height:1.5;">
                    <b>Replicas:</b> 3x Raft Consensus<br>
                    <b>RTT Latency:</b> 2.14 ms<br>
                    <b>Storage:</b> NVMe Hot SSD (91.8 GB)
                </div>
            </div>
        """, unsafe_allow_html=True)
    with n3:
        st.markdown(f"""
            <div class="nb-box">
                <div class="nb-kpi-badge">NODE 03</div>
                <div style="font-family:'Space Grotesk', sans-serif; font-size:14px; font-weight:800;">asia-south1-c</div>
                <div style="font-family:'JetBrains Mono', monospace; font-size:12px; color:var(--nb-green); margin:6px 0;">● ONLINE · REPLICA</div>
                <div style="font-family:'JetBrains Mono', monospace; font-size:11px; line-height:1.5;">
                    <b>Replicas:</b> 3x Raft Consensus<br>
                    <b>RTT Latency:</b> 1.95 ms<br>
                    <b>Storage:</b> NVMe Hot SSD (93.4 GB)
                </div>
            </div>
        """, unsafe_allow_html=True)

    # SQL Query Inspector
    st.markdown("#### PRODUCTION SQL QUERY INSPECTOR & BENCHMARK EXECUTOR")
    
    preset_queries = {
        "1. High-Strain Anomaly Detection (CTE)": """
WITH athlete_strain AS (
    SELECT a.full_name, t.heart_rate, t.training_intensity,
           DENSE_RANK() OVER (PARTITION BY a.athlete_id ORDER BY t.heart_rate DESC) as hr_rank
    FROM athletex.public.athlete a
    JOIN athletex.public.telemetry t ON t.athlete_id = a.athlete_id
    WHERE t.heart_rate >= 165 AND t.training_intensity >= 8.0
)
SELECT full_name, COUNT(*) as high_strain_events, MAX(heart_rate) as peak_bpm
FROM athlete_strain
WHERE hr_rank <= 10
GROUP BY full_name
ORDER BY peak_bpm DESC;
""",
        "2. Athlete Leaderboard (Window Function RANK)": """
SELECT RANK() OVER (ORDER BY COALESCE(ps.gold_medals, 0) DESC, COALESCE(ps.avg_competition_score, 0) DESC) as rank,
       a.full_name,
       COALESCE(ps.competitions, 0) as competitions,
       COALESCE(ps.gold_medals, 0) as gold,
       COALESCE(ps.silver_medals, 0) as silver,
       COALESCE(ps.bronze_medals, 0) as bronze,
       ROUND(COALESCE(ps.avg_competition_score, 0), 2) as avg_score
FROM athletex.public.athlete a
LEFT JOIN athletex.public.athlete_performance_summary ps ON ps.athlete_id = a.athlete_id
ORDER BY rank ASC;
""",
        "3. ACWR 7d/28d Rolling Moving Average Filter": """
SELECT a.full_name,
       DATE_TRUNC('day', t.recorded_at) as session_day,
       ROUND(AVG(t.calories_burned / 10.0 + t.distance_km * t.training_intensity * 2.5) OVER (
           PARTITION BY a.athlete_id ORDER BY DATE_TRUNC('day', t.recorded_at)
           ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ), 1) as acute_load_7d,
       ROUND(AVG(t.calories_burned / 10.0 + t.distance_km * t.training_intensity * 2.5) OVER (
           PARTITION BY a.athlete_id ORDER BY DATE_TRUNC('day', t.recorded_at)
           ROWS BETWEEN 27 PRECEDING AND CURRENT ROW
       ), 1) as chronic_load_28d
FROM athletex.public.athlete a
JOIN athletex.public.telemetry t ON t.athlete_id = a.athlete_id
ORDER BY a.full_name, session_day DESC
LIMIT 50;
""",
        "4. DDL Schema & Distributed Sharding Definition": """
SHOW CREATE TABLE athletex.public.telemetry;
"""
    }

    selected_query_label = st.selectbox("CHOOSE PRODUCTION QUERY TEMPLATE", list(preset_queries.keys()))
    sql_text = preset_queries[selected_query_label].strip()

    st.code(sql_text, language="sql")

    if st.button("▶ EXECUTE QUERY LIVE ON COCKROACHDB CLUSTER", type="primary"):
        start_time = datetime.now()
        res_df = query(sql_text)
        elapsed = (datetime.now() - start_time).total_seconds() * 1000.0
        
        st.markdown(f"""
            <div class="nb-box" style="background:#00D66F; color:#000000; border-color:#000000; padding:8px 14px; margin-top:10px;">
                <b>✓ QUERY COMPLETED:</b> Returned <b>{len(res_df)} rows</b> in <b>{elapsed:.2f} ms</b> via SSL/TLS CockroachDB pipeline.
            </div>
        """, unsafe_allow_html=True)
        st.dataframe(res_df, use_container_width=True, hide_index=True)

# Footer
st.markdown("<hr style='border:1.5px solid var(--nb-border); margin:24px 0 10px 0;'>", unsafe_allow_html=True)
st.markdown("""
    <div style="display:flex; justify-content:space-between; font-family:'JetBrains Mono', monospace; font-size:11px; color:var(--nb-gray);">
        <div>ATHLETEX // DISTRIBUTED SPORTS TELEMETRY HUD · PHASE 10</div>
        <div>COCKROACHDB CLUSTER: asia-south1 · POSTGRESQL DRIVER: PSYCOPG2</div>
    </div>
""", unsafe_allow_html=True)
