import os
from datetime import date

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

# =========================================================
# 1) PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Cinema DW Executive Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# 2) THEME / CSS
# =========================================================
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Prompt', sans-serif !important;
    }

    .stApp {
        background-color: #0B0F17 !important;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    .stMainBlockContainer h1,
    .stMainBlockContainer h2,
    .stMainBlockContainer h3,
    .stMainBlockContainer h4,
    .stMainBlockContainer p {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #1E293B !important;
    }

    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #FFFFFF !important;
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #38BDF8 !important;
    }

    div[data-baseweb="select"] * {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
    }

    div[data-baseweb="popover"] * {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        background-color: #1E293B !important;
        color: #F1F5F9 !important;
        font-weight: 600 !important;
        border: 1px solid #334155 !important;
    }

    .stTabs [aria-selected="true"] {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
        border-color: #38BDF8 !important;
    }

    div[data-testid="stMetric"] {
        background: #1E293B !important;
        border: 1px solid #38BDF8 !important;
        padding: 18px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35) !important;
    }

    div[data-testid="stMetric"] label {
        color: #38BDF8 !important;
        font-size: 0.95rem !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }

    div[data-testid="stDataFrame"] {
        background-color: #1E293B !important;
        border-radius: 10px;
        border: 1px solid #334155;
    }

    .dw-note {
        padding: 0.8rem 1rem;
        border: 1px solid #334155;
        background: #111827;
        border-radius: 10px;
        color: #CBD5E1;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# 3) DIRECT DATA WAREHOUSE CONNECTION (DuckDB)
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def find_duckdb_file() -> str | None:
    """
    Search for the project's DuckDB warehouse.
    Streamlit Cloud will clone the repository, so the database can be
    located either at repo root or inside movie_dw/.
    """
    preferred = [
    os.path.join(BASE_DIR, "movie_dw", "dev.duckdb"),
    os.path.join(BASE_DIR, "dev.duckdb"),
    ]

    for path in preferred:
        if os.path.isfile(path):
            return path

    for root, _, files in os.walk(BASE_DIR):
        for filename in files:
            if filename.lower().endswith(".duckdb"):
                return os.path.join(root, filename)

    return None


DB_PATH = find_duckdb_file()

if not DB_PATH:
    st.error(
        "❌ ไม่พบไฟล์ Data Warehouse (.duckdb) ใน repository\n\n"
        "กรุณาเก็บ dev.duckdb ไว้ที่ root ของ repository "
        "หรือ movie_dw/dev.duckdb แล้ว deploy ใหม่"
    )
    st.stop()


@st.cache_resource
def get_connection(db_path: str):
    # Read-only prevents the dashboard from modifying the warehouse.
    return duckdb.connect(database=db_path, read_only=True)


try:
    conn = get_connection(DB_PATH)
except Exception as exc:
    st.error(f"❌ เชื่อมต่อ Data Warehouse ไม่สำเร็จ: {exc}")
    st.stop()


def resolve_table(table_name: str) -> str:
    """
    Resolve a dbt model table even if it lives in a non-default schema.
    Returns a safely quoted schema.table name.
    """
    result = conn.execute(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE lower(table_name) = lower(?)
        ORDER BY
            CASE WHEN table_schema = 'main' THEN 0 ELSE 1 END,
            table_schema
        LIMIT 1
        """,
        [table_name],
    ).fetchone()

    if not result:
        raise RuntimeError(
            f"ไม่พบตาราง {table_name} ใน Data Warehouse "
            "กรุณารัน dbt run ก่อน deploy"
        )

    schema, table = result
    return f'"{schema}"."{table}"'


try:
    FACT_TICKET = resolve_table("fact_ticket_sales")
    FACT_CONCESSION = resolve_table("fact_concession_sales")
    DIM_SHOWTIMES = resolve_table("dim_showtimes")
    DIM_CUSTOMERS = resolve_table("dim_customers")
    DIM_MOVIES = resolve_table("dim_movies")
except Exception as exc:
    st.error(f"❌ ตรวจสอบ Data Warehouse ไม่ผ่าน: {exc}")
    st.stop()


def run_query(sql: str, params=None) -> pd.DataFrame:
    """Execute analytical SQL against DuckDB and return a DataFrame."""
    try:
        if params:
            return conn.execute(sql, params).df()
        return conn.execute(sql).df()
    except Exception as exc:
        st.error(f"SQL Error: {exc}")
        return pd.DataFrame()


def scalar(sql: str, params=None, default=0):
    df = run_query(sql, params)
    if df.empty:
        return default
    value = df.iloc[0, 0]
    return default if pd.isna(value) else value


# =========================================================
# 4) CHART HELPERS
# =========================================================
def style_chart(fig, height=410):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FFFFFF", family="Prompt, sans-serif", size=13),
        title=dict(font=dict(color="#FFFFFF", size=18)),
        legend=dict(font=dict(color="#FFFFFF", size=12)),
        margin=dict(l=20, r=20, t=55, b=30),
        height=height,
    )
    fig.update_xaxes(
        title_font=dict(color="#FFFFFF"),
        tickfont=dict(color="#E2E8F0"),
        gridcolor="rgba(148,163,184,0.15)",
    )
    fig.update_yaxes(
        title_font=dict(color="#FFFFFF"),
        tickfont=dict(color="#E2E8F0"),
        gridcolor="rgba(148,163,184,0.15)",
    )
    return fig


def show_chart_and_table(fig, df: pd.DataFrame, key_prefix: str):
    tab_chart, tab_table = st.tabs(["📊 Interactive Chart", "📋 Raw Data"])
    with tab_chart:
        st.plotly_chart(style_chart(fig), use_container_width=True, key=f"{key_prefix}_chart")
    with tab_table:
        st.dataframe(df, use_container_width=True, hide_index=True)


def in_clause(values: list[str]):
    """
    Build safe positional placeholders for selected string values.
    Returns SQL fragment and params.
    """
    if not values:
        return None, []
    placeholders = ", ".join(["?"] * len(values))
    return f"({placeholders})", list(values)


# =========================================================
# 5) FILTER METADATA
# =========================================================
filter_meta = run_query(
    f"""
    SELECT
        MIN(t.show_date) AS min_date,
        MAX(t.show_date) AS max_date
    FROM {FACT_TICKET} t
    """
)

if filter_meta.empty or pd.isna(filter_meta.loc[0, "min_date"]):
    st.error("❌ ไม่พบข้อมูลวันที่ใน fact_ticket_sales")
    st.stop()

min_date = pd.to_datetime(filter_meta.loc[0, "min_date"]).date()
max_date = pd.to_datetime(filter_meta.loc[0, "max_date"]).date()

genres = (
    run_query(f"SELECT DISTINCT genre FROM {DIM_MOVIES} WHERE genre IS NOT NULL ORDER BY genre")
    .iloc[:, 0]
    .dropna()
    .astype(str)
    .tolist()
)

movies = (
    run_query(f"SELECT DISTINCT title FROM {DIM_MOVIES} WHERE title IS NOT NULL ORDER BY title")
    .iloc[:, 0]
    .dropna()
    .astype(str)
    .tolist()
)

tiers = (
    run_query(
        f"""
        SELECT DISTINCT
            CASE
                WHEN member_tier IS NULL OR trim(member_tier) = ''
                THEN 'Non-Member'
                ELSE member_tier
            END AS tier
        FROM {DIM_CUSTOMERS}
        ORDER BY tier
        """
    )
    .iloc[:, 0]
    .dropna()
    .astype(str)
    .tolist()
)

# =========================================================
# 6) SIDEBAR / GLOBAL INTERACTIVITY
# =========================================================
st.sidebar.header("🎯 Navigation & Analysis")

analysis_mode = st.sidebar.radio(
    "มุมมองข้อมูล",
    ["📊 Overview Dashboard", "🔎 Deep-Dive 15 Business Questions"],
)

st.sidebar.subheader("🔍 Global Filters")

selected_genres = st.sidebar.multiselect(
    "Genre",
    genres,
    default=[],
    placeholder="ทั้งหมด"
)

selected_tiers = st.sidebar.multiselect(
    "Member Tier",
    tiers,
    default=[],
    placeholder="ทั้งหมด"
)

# ไม่มี Date filter
# ไม่มี Movie filter
start_date = None
end_date = None


if st.sidebar.button("↻ Reset filters", use_container_width=True):
    st.rerun()

# =========================================================
# 7) BUILD FILTERED FACT DATASETS
# =========================================================
ticket_conditions = []
ticket_params = []

# Genre filter
if selected_genres and len(selected_genres) < len(genres):
    placeholders = ",".join(["?"] * len(selected_genres))
    ticket_conditions.append(
        f"m.genre IN ({placeholders})"
    )
    ticket_params.extend(selected_genres)

# Member Tier filter
if selected_tiers and len(selected_tiers) < len(tiers):
    placeholders = ",".join(["?"] * len(selected_tiers))

    ticket_conditions.append(f"""
        CASE
            WHEN c.member_tier IS NULL OR trim(c.member_tier) = ''
            THEN 'Non-Member'
            ELSE c.member_tier
        END IN ({placeholders})
    """)

    ticket_params.extend(selected_tiers)
ticket_where = " AND ".join(ticket_conditions) if ticket_conditions else "1=1"

TICKET_CTE = f"""
WITH filtered_ticket AS (
    SELECT
        t.ticket_id,
        t.showtime_id,
        t.customer_id,
        t.movie_id,
        t.seat_number,
        t.seat_type,
        t.final_price,
        t.show_date,
        s.screen_number,
        s.ticket_price AS listed_ticket_price,
        m.title,
        m.genre,
        m.rating,
        m.duration_min,
        CASE
            WHEN c.member_tier IS NULL OR trim(c.member_tier) = ''
            THEN 'Non-Member'
            ELSE c.member_tier
        END AS member_tier,
        CASE
            WHEN EXTRACT(
                HOUR FROM COALESCE(
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%m/%d/%Y %H:%M:%S'),
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%m/%d/%Y %H:%M'),
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%Y-%m-%d %H:%M:%S'),
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%Y-%m-%d %H:%M'),
                    TRY_CAST(s.show_date AS TIMESTAMP)
                )
            ) BETWEEN 6 AND 11 THEN 'Morning'

            WHEN EXTRACT(
                HOUR FROM COALESCE(
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%m/%d/%Y %H:%M:%S'),
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%m/%d/%Y %H:%M'),
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%Y-%m-%d %H:%M:%S'),
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%Y-%m-%d %H:%M'),
                    TRY_CAST(s.show_date AS TIMESTAMP)
                )
            ) BETWEEN 12 AND 16 THEN 'Afternoon'

            WHEN EXTRACT(
                HOUR FROM COALESCE(
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%m/%d/%Y %H:%M:%S'),
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%m/%d/%Y %H:%M'),
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%Y-%m-%d %H:%M:%S'),
                    TRY_STRPTIME(CAST(s.show_date AS VARCHAR), '%Y-%m-%d %H:%M'),
                    TRY_CAST(s.show_date AS TIMESTAMP)
                )
            ) BETWEEN 17 AND 23 THEN 'Evening'

            ELSE 'Unknown'
        END AS time_slot
    FROM {FACT_TICKET} t
    LEFT JOIN {DIM_SHOWTIMES} s
        ON t.showtime_id = s.showtime_id
    LEFT JOIN {DIM_MOVIES} m
        ON t.movie_id = m.movie_id
    LEFT JOIN {DIM_CUSTOMERS} c
        ON t.customer_id = c.customer_id
    WHERE {ticket_where}
)
"""

# Concession supports date + member-tier filters directly.
# Movie / Genre do not naturally apply to concession sales because the current
# warehouse fact_concession_sales has no showtime/movie key.
concession_conditions = []
concession_params = []

# Member Tier filter สำหรับ Concession
if selected_tiers and len(selected_tiers) < len(tiers):
    placeholders = ",".join(["?"] * len(selected_tiers))

    concession_conditions.append(f"""
        CASE
            WHEN c.member_tier IS NULL OR trim(c.member_tier) = ''
            THEN 'Non-Member'
            ELSE c.member_tier
        END IN ({placeholders})
    """)

    concession_params.extend(selected_tiers)

concession_where = (
    " AND ".join(concession_conditions)
    if concession_conditions
    else "1=1"
)

CONCESSION_CTE = f"""
WITH filtered_concession AS (
    SELECT
        cs.concession_sale_id,
        cs.customer_id,
        cs.item_name,
        cs.quantity,
        cs.unit_price,
        cs.total_price,
        cs.sale_date,
        CASE
            WHEN c.member_tier IS NULL OR trim(c.member_tier) = ''
            THEN 'Non-Member'
            ELSE c.member_tier
        END AS member_tier,
        CASE
            WHEN lower(cs.item_name) LIKE '%combo%' THEN 'Combo Set'
            WHEN lower(cs.item_name) LIKE '%popcorn%' THEN 'Popcorn'
            WHEN lower(cs.item_name) LIKE '%soda%'
              OR lower(cs.item_name) LIKE '%water%' THEN 'Beverage'
            ELSE 'Other'
        END AS category
    FROM {FACT_CONCESSION} cs
    LEFT JOIN {DIM_CUSTOMERS} c
        ON cs.customer_id = c.customer_id
    WHERE {concession_where}
)
"""

# =========================================================
# 8) HEADER + FILTER SUMMARY
# =========================================================
st.title("🎬 Cinema Data Analytics Platform")
st.caption("Interactive Executive Dashboard • Directly querying the DuckDB Data Warehouse")

active_filters = [
    f"Genre: {', '.join(selected_genres) if selected_genres else 'All'}",
    f"Member Tier: {', '.join(selected_tiers) if selected_tiers else 'All'}",
]

st.markdown(
    '<div class="dw-note"><b>Active filters:</b> '
    + " • ".join(active_filters)
    + "</div>",
    unsafe_allow_html=True,
)

# =========================================================
# 9) KPI CARDS (RESPOND TO GLOBAL FILTERS)
# =========================================================
ticket_rev = scalar(
    TICKET_CTE + "SELECT COALESCE(SUM(final_price), 0) FROM filtered_ticket",
    ticket_params,
)

total_tickets = scalar(
    TICKET_CTE + "SELECT COUNT(ticket_id) FROM filtered_ticket",
    ticket_params,
)

avg_ticket_price = scalar(
    TICKET_CTE + "SELECT COALESCE(AVG(final_price), 0) FROM filtered_ticket",
    ticket_params,
)

concession_rev = scalar(
    CONCESSION_CTE + "SELECT COALESCE(SUM(total_price), 0) FROM filtered_concession",
    concession_params,
)

total_revenue = ticket_rev + concession_rev

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 รายได้รวม", f"฿{total_revenue:,.0f}")
k2.metric("🎟️ Ticket Revenue", f"฿{ticket_rev:,.0f}")
k3.metric("🍿 Concession Revenue", f"฿{concession_rev:,.0f}")
k4.metric("🎫 Tickets Sold", f"{total_tickets:,.0f} ใบ")
k5.metric("💳 Avg Ticket Price", f"฿{avg_ticket_price:,.2f}")

st.divider()

# =========================================================
# 10) OVERVIEW DASHBOARD
# =========================================================
if analysis_mode == "📊 Overview Dashboard":

    st.subheader("📈 Executive Overview")

    # ---------- Chart 1: Revenue trend ----------
    trend_df = run_query(
        TICKET_CTE
        + """
        SELECT
            show_date AS Date,
            SUM(final_price) AS Revenue
        FROM filtered_ticket
        GROUP BY show_date
        ORDER BY show_date
        """,
        ticket_params,
    )

    if not trend_df.empty:
        fig = px.line(
            trend_df,
            x="Date",
            y="Revenue",
            markers=True,
            title="📅 Ticket Revenue Trend by Date",
        )
        st.plotly_chart(style_chart(fig, 380), use_container_width=True)

    row1_left, row1_right = st.columns(2)

    # ---------- Chart 2: Top Movies ----------
    with row1_left:
        top_movies_df = run_query(
            TICKET_CTE
            + """
            SELECT
                title AS Movie,
                SUM(final_price) AS Revenue
            FROM filtered_ticket
            WHERE title IS NOT NULL
            GROUP BY title
            ORDER BY Revenue DESC
            LIMIT 5
            """,
            ticket_params,
        )
        if not top_movies_df.empty:
            fig = px.bar(
                top_movies_df,
                x="Revenue",
                y="Movie",
                orientation="h",
                title="🏆 Top 5 Movies by Revenue",
                text_auto=",.0f",
            )
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(style_chart(fig), use_container_width=True)

    # ---------- Chart 3: Genre ----------
    with row1_right:
        genre_df = run_query(
            TICKET_CTE
            + """
            SELECT
                genre AS Genre,
                SUM(final_price) AS Revenue
            FROM filtered_ticket
            WHERE genre IS NOT NULL
            GROUP BY genre
            ORDER BY Revenue DESC
            """,
            ticket_params,
        )
        if not genre_df.empty:
            fig = px.bar(
                genre_df,
                x="Genre",
                y="Revenue",
                title="🎭 Revenue by Genre",
                text_auto=",.0f",
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)

    row2_left, row2_right = st.columns(2)

    # ---------- Chart 4: Time Slot ----------
    with row2_left:
        time_df = run_query(
            TICKET_CTE
            + """
            SELECT
                time_slot AS Time_Slot,
                SUM(final_price) AS Revenue
            FROM filtered_ticket
            GROUP BY time_slot
            ORDER BY Revenue DESC
            """,
            ticket_params,
        )
        if not time_df.empty:
            fig = px.pie(
                time_df,
                names="Time_Slot",
                values="Revenue",
                title="⏰ Revenue Share by Time Slot",
                hole=0.42,
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)

    # ---------- Chart 5: Member Tier ----------
    with row2_right:
        member_df = run_query(
            TICKET_CTE
            + """
            SELECT
                member_tier AS Member_Tier,
                SUM(final_price) AS Revenue
            FROM filtered_ticket
            GROUP BY member_tier
            ORDER BY Revenue DESC
            """,
            ticket_params,
        )
        if not member_df.empty:
            fig = px.bar(
                member_df,
                x="Member_Tier",
                y="Revenue",
                title="💎 Ticket Revenue by Member Tier",
                text_auto=",.0f",
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)

    row3_left, row3_right = st.columns(2)

    # ---------- Chart 6: Seat Type ----------
    with row3_left:
        seat_df = run_query(
            TICKET_CTE
            + """
            SELECT
                seat_type AS Seat_Type,
                SUM(final_price) AS Revenue
            FROM filtered_ticket
            WHERE seat_type IS NOT NULL
            GROUP BY seat_type
            ORDER BY Revenue DESC
            """,
            ticket_params,
        )
        if not seat_df.empty:
            fig = px.bar(
                seat_df,
                x="Seat_Type",
                y="Revenue",
                title="💺 Revenue by Seat Type",
                text_auto=",.0f",
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)

    # ---------- Chart 7: Concession Category ----------
    with row3_right:
        concession_category_df = run_query(
            CONCESSION_CTE
            + """
            SELECT
                category AS Category,
                SUM(total_price) AS Revenue
            FROM filtered_concession
            GROUP BY category
            ORDER BY Revenue DESC
            """,
            concession_params,
        )
        if not concession_category_df.empty:
            fig = px.pie(
                concession_category_df,
                names="Category",
                values="Revenue",
                title="🍿 Concession Revenue by Category",
                hole=0.42,
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)

    st.subheader("🔍 Additional Interactive Analysis")

    row4_left, row4_right = st.columns(2)

    # ---------- Chart 8: Rating ----------
    with row4_left:
        rating_df = run_query(
            TICKET_CTE
            + """
            SELECT
                rating AS Rating,
                SUM(final_price) AS Revenue
            FROM filtered_ticket
            WHERE rating IS NOT NULL
            GROUP BY rating
            ORDER BY Revenue DESC
            """,
            ticket_params,
        )
        if not rating_df.empty:
            fig = px.donut if False else px.pie  # keep standard Plotly compatibility
            chart = px.pie(
                rating_df,
                names="Rating",
                values="Revenue",
                title="🔞 Revenue by Movie Rating",
                hole=0.42,
            )
            st.plotly_chart(style_chart(chart), use_container_width=True)

    # ---------- Chart 9: Screens ----------
    with row4_right:
        screen_df = run_query(
            TICKET_CTE
            + """
            SELECT
                CAST(screen_number AS VARCHAR) AS Screen,
                SUM(final_price) AS Revenue
            FROM filtered_ticket
            WHERE screen_number IS NOT NULL
            GROUP BY screen_number
            ORDER BY Revenue DESC
            """,
            ticket_params,
        )
        if not screen_df.empty:
            fig = px.bar(
                screen_df,
                x="Screen",
                y="Revenue",
                title="🎥 Revenue by Screen Number",
                text_auto=",.0f",
            )
            st.plotly_chart(style_chart(fig), use_container_width=True)

    # ---------- Insight summary ----------
    st.subheader("🧠 Auto-generated KPI Summary")
    summary_cols = st.columns(3)

    top_movie_name = (
        top_movies_df.iloc[0]["Movie"] if "top_movies_df" in locals() and not top_movies_df.empty else "-"
    )
    top_genre_name = (
        genre_df.iloc[0]["Genre"] if "genre_df" in locals() and not genre_df.empty else "-"
    )
    top_time_slot = (
        time_df.iloc[0]["Time_Slot"] if "time_df" in locals() and not time_df.empty else "-"
    )

    summary_cols[0].metric("🏆 Top Movie", str(top_movie_name))
    summary_cols[1].metric("🎭 Top Genre", str(top_genre_name))
    summary_cols[2].metric("⏰ Peak Time Slot", str(top_time_slot))

# =========================================================
# 11) DEEP-DIVE: 15 BUSINESS QUESTIONS
# =========================================================
else:
    st.subheader("🔎 Deep-Dive: 15 Business Questions")

    question_option = st.selectbox(
        "เลือกคำถามทางธุรกิจ",
        [
            "1. รายได้รวมจากการขายตั๋วทั้งหมด",
            "2. รายได้ตามช่วงเวลา (Time Slot)",
            "3. Concession Spend Per Head",
            "4. สัดส่วนรายได้ Ticket vs Concession",
            "5. ราคาตั๋วเฉลี่ยต่อใบ",
            "6. Top 5 ภาพยนตร์ทำรายได้สูงสุด",
            "7. Genre ที่ทำรายได้สูงสุด",
            "8. รายได้ตาม Rating",
            "9. Screen Number ที่ทำรายได้สูงสุด",
            "10. Spending ตาม Member Tier",
            "11. จำนวนตั๋วตาม Member Tier",
            "12. Seat Type ที่ Platinum นิยม",
            "13. Seat Type ที่ทำรายได้สูงสุด",
            "14. Concession ที่ Gold & Platinum นิยม",
            "15. รายได้ตามหมวดหมู่ Concession",
        ],
    )

    def metric_result(title, value, suffix="", currency=True):
        st.markdown(f"### {title}")
        if currency:
            st.metric(title, f"฿{value:,.2f}{suffix}")
        else:
            st.metric(title, f"{value:,.2f}{suffix}")

    def bar_result(title, df, x, y, key, horizontal=False):
        st.markdown(f"### {title}")
        if df.empty:
            st.info("ไม่พบข้อมูลตาม filter ที่เลือก")
            return
        if horizontal:
            fig = px.bar(df, x=y, y=x, orientation="h", text_auto=",.0f", title=title)
            fig.update_layout(yaxis=dict(autorange="reversed"))
        else:
            fig = px.bar(df, x=x, y=y, text_auto=",.0f", title=title)
        show_chart_and_table(fig, df, key)

    def pie_result(title, df, names, values, key):
        st.markdown(f"### {title}")
        if df.empty:
            st.info("ไม่พบข้อมูลตาม filter ที่เลือก")
            return
        fig = px.pie(df, names=names, values=values, hole=0.42, title=title)
        show_chart_and_table(fig, df, key)

    # ---------------- Q1 ----------------
    if question_option.startswith("1."):
        value = scalar(
            TICKET_CTE + "SELECT COALESCE(SUM(final_price),0) FROM filtered_ticket",
            ticket_params,
        )
        metric_result("1. Total Ticket Revenue", value)

    # ---------------- Q2 ----------------
    elif question_option.startswith("2."):
        df = run_query(
            TICKET_CTE
            + """
            SELECT
                time_slot AS Time_Slot,
                SUM(final_price) AS Revenue_THB
            FROM filtered_ticket
            GROUP BY time_slot
            ORDER BY Revenue_THB DESC
            """,
            ticket_params,
        )
        bar_result("2. Revenue by Time Slot", df, "Time_Slot", "Revenue_THB", "q2")

    # ---------------- Q3 ----------------
    elif question_option.startswith("3."):
        concession_total = scalar(
            CONCESSION_CTE + "SELECT COALESCE(SUM(total_price),0) FROM filtered_concession",
            concession_params,
        )
        ticket_count = scalar(
            TICKET_CTE + "SELECT COUNT(ticket_id) FROM filtered_ticket",
            ticket_params,
        )
        spend_per_head = concession_total / ticket_count if ticket_count else 0
        metric_result("3. Concession Spend Per Head", spend_per_head, " บาท/คน")
         # ---------------- Q4 ----------------
    elif question_option.startswith("4."):
        ticket_total = scalar(
            TICKET_CTE + "SELECT COALESCE(SUM(final_price),0) FROM filtered_ticket",
            ticket_params,
        )
        concession_total = scalar(
            CONCESSION_CTE + "SELECT COALESCE(SUM(total_price),0) FROM filtered_concession",
            concession_params,
        )
        df = pd.DataFrame(
            {
                "Category": ["Ticket Revenue", "Concession Revenue"],
                "Revenue_THB": [ticket_total, concession_total],
            }
        )
        pie_result("4. Ticket vs Concession Revenue Share", df, "Category", "Revenue_THB", "q4")

    # ---------------- Q5 ----------------
    elif question_option.startswith("5."):
        value = scalar(
            TICKET_CTE + "SELECT COALESCE(AVG(final_price),0) FROM filtered_ticket",
            ticket_params,
        )
        metric_result("5. Average Ticket Price", value, " บาท/ใบ")

    # ---------------- Q6 ----------------
    elif question_option.startswith("6."):
        df = run_query(
            TICKET_CTE
            + """
            SELECT title AS Movie, SUM(final_price) AS Revenue_THB
            FROM filtered_ticket
            WHERE title IS NOT NULL
            GROUP BY title
            ORDER BY Revenue_THB DESC
            LIMIT 5
            """,
            ticket_params,
        )
        bar_result("6. Top 5 Movies by Revenue", df, "Movie", "Revenue_THB", "q6", horizontal=True)

    # ---------------- Q7 ----------------
    elif question_option.startswith("7."):
        df = run_query(
            TICKET_CTE
            + """
            SELECT genre AS Genre, SUM(final_price) AS Revenue_THB
            FROM filtered_ticket
            WHERE genre IS NOT NULL
            GROUP BY genre
            ORDER BY Revenue_THB DESC
            """,
            ticket_params,
        )
        bar_result("7. Revenue by Genre", df, "Genre", "Revenue_THB", "q7")

    # ---------------- Q8 ----------------
    elif question_option.startswith("8."):
        df = run_query(
            TICKET_CTE
            + """
            SELECT rating AS Rating, SUM(final_price) AS Revenue_THB
            FROM filtered_ticket
            WHERE rating IS NOT NULL
            GROUP BY rating
            ORDER BY Revenue_THB DESC
            """,
            ticket_params,
        )
        pie_result("8. Revenue by Rating", df, "Rating", "Revenue_THB", "q8")

    # ---------------- Q9 ----------------
    elif question_option.startswith("9."):
        df = run_query(
            TICKET_CTE
            + """
            SELECT
                CAST(screen_number AS VARCHAR) AS Screen,
                SUM(final_price) AS Revenue_THB
            FROM filtered_ticket
            WHERE screen_number IS NOT NULL
            GROUP BY screen_number
            ORDER BY Revenue_THB DESC
            """,
            ticket_params,
        )
        bar_result("9. Revenue by Screen Number", df, "Screen", "Revenue_THB", "q9")
        # ---------------- Q10 ----------------
    elif question_option.startswith("10."):
        df = run_query(
            TICKET_CTE
            + """
            SELECT member_tier AS Member_Tier, SUM(final_price) AS Revenue_THB
            FROM filtered_ticket
            GROUP BY member_tier
            ORDER BY Revenue_THB DESC
            """,
            ticket_params,
        )
        bar_result("10. Spending by Member Tier", df, "Member_Tier", "Revenue_THB", "q10")

    # ---------------- Q11 ----------------
    elif question_option.startswith("11."):
        df = run_query(
            TICKET_CTE
            + """
            SELECT member_tier AS Member_Tier, COUNT(ticket_id) AS Tickets
            FROM filtered_ticket
            GROUP BY member_tier
            ORDER BY Tickets DESC
            """,
            ticket_params,
        )
        bar_result("11. Tickets Sold by Member Tier", df, "Member_Tier", "Tickets", "q11")

    # ---------------- Q12 ----------------
    elif question_option.startswith("12."):
        platinum_conditions = ["c.member_tier = 'Platinum'"]
        platinum_params = []

        # ถ้าเลือก Genre ให้ Q12 filter ตาม Genre ได้
        if selected_genres and len(selected_genres) < len(genres):
            placeholders = ",".join(["?"] * len(selected_genres))
            platinum_conditions.append(
                f"m.genre IN ({placeholders})"
            )
            platinum_params.extend(selected_genres)

        platinum_where = " AND ".join(platinum_conditions)

        sql = f"""
        SELECT
            t.seat_type AS Seat_Type,
            COUNT(t.ticket_id) AS Tickets
        FROM {FACT_TICKET} t
        LEFT JOIN {DIM_MOVIES} m
            ON t.movie_id = m.movie_id
        INNER JOIN {DIM_CUSTOMERS} c
            ON t.customer_id = c.customer_id
        WHERE {platinum_where}
        GROUP BY t.seat_type
        ORDER BY Tickets DESC
        """

        df = run_query(sql, platinum_params)

        bar_result(
            "12. Seat Type Preferred by Platinum Members",
            df,
            "Seat_Type",
            "Tickets",
            "q12",
        )
    # ---------------- Q13 ----------------
    elif question_option.startswith("13."):
        df = run_query(
            TICKET_CTE
            + """
            SELECT seat_type AS Seat_Type, SUM(final_price) AS Revenue_THB
            FROM filtered_ticket
            WHERE seat_type IS NOT NULL
            GROUP BY seat_type
            ORDER BY Revenue_THB DESC
            """,
            ticket_params,
        )
        bar_result("13. Revenue by Seat Type", df, "Seat_Type", "Revenue_THB", "q13")

    # ---------------- Q14 ----------------
    # ---------------- Q14 ----------------
    elif question_option.startswith("14."):
        sql = f"""
        SELECT
            cs.item_name AS Concession_Item,
            SUM(cs.quantity) AS Quantity
        FROM {FACT_CONCESSION} cs
        INNER JOIN {DIM_CUSTOMERS} c
            ON cs.customer_id = c.customer_id
        WHERE c.member_tier IN ('Gold', 'Platinum')
        GROUP BY cs.item_name
        ORDER BY Quantity DESC
        """

        df = run_query(sql)

        bar_result(
            "14. Most Popular Concession Items among Gold & Platinum",
            df,
            "Concession_Item",
            "Quantity",
            "q14",
            horizontal=True,
        )

    # ---------------- Q15 ----------------
    elif question_option.startswith("15."):
        df = run_query(
            CONCESSION_CTE
            + """
            SELECT category AS Category, SUM(total_price) AS Revenue_THB
            FROM filtered_concession
            GROUP BY category
            ORDER BY Revenue_THB DESC
            """,
            concession_params,
        )
        pie_result("15. Concession Revenue by Category", df, "Category", "Revenue_THB", "q15")
        # =========================================================
# 12) FOOTER / DATA-WAREHOUSE TRANSPARENCY
# =========================================================
st.divider()
with st.expander("ℹ️ Data Warehouse Connection & Model Information"):
    st.write(f"**DuckDB file:** `{os.path.relpath(DB_PATH, BASE_DIR)}`")
    st.write("**Dashboard source:** Direct query from dbt-generated DuckDB Data Warehouse")
    st.write(
        "**Models used:** fact_ticket_sales, fact_concession_sales, "
        "dim_showtimes, dim_customers, dim_movies"
    )
    st.caption(
        "หมายเหตุ: Movie/Genre filters ไม่ถูกนำไปใช้กับ Concession โดยตรง "
        "เพราะ fact_concession_sales ในโมเดลปัจจุบันไม่มี movie_id/showtime_id "
        "จึงหลีกเลี่ยงการสร้างความสัมพันธ์ที่ไม่มีอยู่จริงใน Data Warehouse"
    )