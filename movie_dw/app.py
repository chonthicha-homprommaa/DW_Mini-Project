import os
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Cinema DW Dashboard",
    page_icon="🎬",
    layout="wide"
)

# =========================================================
# STYLE
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Prompt', sans-serif !important;
}

.stApp {
    background:#0B0F17 !important;
}

section[data-testid="stSidebar"] {
    background:#0F172A !important;
}

section[data-testid="stSidebar"] * {
    color:white !important;
}

div[data-testid="stMetric"] {
    background:#111827;
    border:1px solid #334155;
    padding:16px;
    border-radius:14px;
}

div[data-testid="stMetric"] label {
    color:#94A3B8 !important;
}

.stTabs [data-baseweb="tab"] {
    background:#111827 !important;
    color:#E2E8F0 !important;
    border-radius:8px 8px 0 0;
}

.stTabs [aria-selected="true"] {
    background:#1D4ED8 !important;
    color:white !important;
}

.answer {
    background:#111827;
    border:1px solid #334155;
    border-radius:12px;
    padding:14px 16px;
    margin:.3rem 0 1rem;
}

.answer b {
    color:#38BDF8;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def find_db():
    preferred = [
        os.path.join(BASE_DIR, "movie_dw", "dev.duckdb"),
        os.path.join(BASE_DIR, "dev.duckdb"),
    ]

    for path in preferred:
        if os.path.isfile(path):
            return path

    for root, _, files in os.walk(BASE_DIR):
        for f in files:
            if f.endswith(".duckdb"):
                return os.path.join(root, f)

    return None


DB_PATH = find_db()

if not DB_PATH:
    st.error("❌ ไม่พบไฟล์ dev.duckdb")
    st.stop()


@st.cache_resource
def get_conn(path):
    return duckdb.connect(path, read_only=True)


conn = get_conn(DB_PATH)


def q(sql, params=None):
    try:
        return conn.execute(sql, params or []).df()
    except Exception as e:
        st.error(f"SQL Error: {e}")
        return pd.DataFrame()


def scalar(sql, params=None, default=0):
    df = q(sql, params)
    if df.empty or pd.isna(df.iloc[0, 0]):
        return default
    return df.iloc[0, 0]


def style(fig, height=340):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=20, r=20, t=50, b=20),
        legend_title_text=""
    )
    return fig


# =========================================================
# CHECK TABLES
# =========================================================
required = [
    "fact_ticket_sales",
    "fact_concession_sales",
    "dim_movies",
    "dim_customers",
    "dim_showtimes",
]

existing_df = q("""
    SELECT lower(table_name) AS name
    FROM information_schema.tables
""")

existing = set(existing_df["name"].tolist()) if not existing_df.empty else set()
missing = [t for t in required if t not in existing]

if missing:
    st.error("❌ ไม่พบตาราง: " + ", ".join(missing))
    st.stop()


# =========================================================
# FILTERS
# =========================================================
genres_df = q("""
    SELECT DISTINCT genre
    FROM dim_movies
    WHERE genre IS NOT NULL
    ORDER BY genre
""")

genres = genres_df["genre"].astype(str).tolist() if not genres_df.empty else []

tiers_df = q("""
    SELECT DISTINCT
        CASE
            WHEN member_tier IS NULL OR trim(member_tier) = ''
            THEN 'Non-Member'
            ELSE member_tier
        END AS tier
    FROM dim_customers
    ORDER BY tier
""")

tiers = tiers_df["tier"].astype(str).tolist() if not tiers_df.empty else []

st.sidebar.title("🎬 Cinema DW")
page = st.sidebar.radio(
    "เลือกหน้า",
    ["🏠 Overview", "🔎 Business Questions"]
)

st.sidebar.divider()
st.sidebar.subheader("ตัวกรอง")

sel_genres = st.sidebar.multiselect(
    "Genre",
    genres,
    placeholder="ทั้งหมด"
)

sel_tiers = st.sidebar.multiselect(
    "Member Tier",
    tiers,
    placeholder="ทั้งหมด"
)

st.sidebar.caption("ไม่เลือก = แสดงข้อมูลทั้งหมด")

# ไม่ใช้ Date Filter
start_date = None
end_date = None


# =========================================================
# TICKET FILTER SQL
# =========================================================
conds = []
params = []

if sel_genres:
    ph = ",".join(["?"] * len(sel_genres))
    conds.append(f"m.genre IN ({ph})")
    params += sel_genres

if sel_tiers:
    ph = ",".join(["?"] * len(sel_tiers))
    conds.append(
        f"""
        CASE
            WHEN c.member_tier IS NULL OR trim(c.member_tier) = ''
            THEN 'Non-Member'
            ELSE c.member_tier
        END IN ({ph})
        """
    )
    params += sel_tiers

where = " AND ".join(conds) if conds else "1=1"

TICKET = f"""
WITH ft AS (
    SELECT
        t.ticket_id,
        t.showtime_id,
        t.customer_id,
        t.movie_id,
        t.seat_type,
        t.final_price,
        t.show_date,
        m.title,
        m.genre,
        m.rating,
        s.screen_number,
        CASE
            WHEN c.member_tier IS NULL OR trim(c.member_tier) = ''
            THEN 'Non-Member'
            ELSE c.member_tier
        END AS member_tier,
        CASE
            WHEN EXTRACT(HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP)) BETWEEN 6 AND 11
            THEN 'Morning'
            WHEN EXTRACT(HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP)) BETWEEN 12 AND 16
            THEN 'Afternoon'
            ELSE 'Evening'
        END AS time_slot
    FROM fact_ticket_sales t
    LEFT JOIN dim_movies m
        ON t.movie_id = m.movie_id
    LEFT JOIN dim_showtimes s
        ON t.showtime_id = s.showtime_id
    LEFT JOIN dim_customers c
        ON t.customer_id = c.customer_id
    WHERE {where}
)
"""


# =========================================================
# CONCESSION FILTER SQL
# =========================================================
cconds = []
cparams = []

if sel_tiers:
    ph = ",".join(["?"] * len(sel_tiers))
    cconds.append(
        f"""
        CASE
            WHEN c.member_tier IS NULL OR trim(c.member_tier) = ''
            THEN 'Non-Member'
            ELSE c.member_tier
        END IN ({ph})
        """
    )
    cparams += sel_tiers

cwhere = " AND ".join(cconds) if cconds else "1=1"

CONC = f"""
WITH fc AS (
    SELECT
        cs.*,
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
    FROM fact_concession_sales cs
    LEFT JOIN dim_customers c
        ON cs.customer_id = c.customer_id
    WHERE {cwhere}
)
"""


# =========================================================
# KPI
# =========================================================
ticket_rev = scalar(
    TICKET + "SELECT COALESCE(SUM(final_price),0) FROM ft",
    params
)

ticket_count = scalar(
    TICKET + "SELECT COUNT(*) FROM ft",
    params
)

avg_ticket = scalar(
    TICKET + "SELECT COALESCE(AVG(final_price),0) FROM ft",
    params
)

conc_rev = scalar(
    CONC + "SELECT COALESCE(SUM(total_price),0) FROM fc",
    cparams
)

total_rev = ticket_rev + conc_rev


# =========================================================
# HEADER
# =========================================================
st.title("🎬 Cinema Data Warehouse Dashboard")
st.caption("ดูภาพรวมง่าย ๆ และตอบ Business Questions จาก Data Warehouse โดยตรง")

k1, k2, k3, k4 = st.columns(4)

k1.metric("💰 รายได้รวม", f"฿{total_rev:,.0f}")
k2.metric("🎟️ รายได้ตั๋ว", f"฿{ticket_rev:,.0f}")
k3.metric("🍿 รายได้ Concession", f"฿{conc_rev:,.0f}")
k4.metric("🎫 จำนวนตั๋ว", f"{ticket_count:,.0f} ใบ")

if ticket_count == 0 and conc_rev == 0:
    st.warning("⚠️ ไม่พบข้อมูลตามตัวกรอง ลองลบ Genre หรือ Member Tier ที่เลือก")
    st.stop()


# =========================================================
# OVERVIEW
# =========================================================
if page == "🏠 Overview":

    st.subheader("ภาพรวมที่ควรรู้")

    tm = q(
        TICKET + """
        SELECT title, SUM(final_price) AS revenue
        FROM ft
        WHERE title IS NOT NULL
        GROUP BY title
        ORDER BY revenue DESC
        LIMIT 1
        """,
        params
    )

    tg = q(
        TICKET + """
        SELECT genre, SUM(final_price) AS revenue
        FROM ft
        WHERE genre IS NOT NULL
        GROUP BY genre
        ORDER BY revenue DESC
        LIMIT 1
        """,
        params
    )

    ts = q(
        TICKET + """
        SELECT time_slot, SUM(final_price) AS revenue
        FROM ft
        GROUP BY time_slot
        ORDER BY revenue DESC
        LIMIT 1
        """,
        params
    )

    a, b, c = st.columns(3)

    a.metric(
        "🏆 หนังทำเงินสูงสุด",
        tm.iloc[0]["title"] if not tm.empty else "-"
    )

    b.metric(
        "🎭 Genre ทำเงินสูงสุด",
        tg.iloc[0]["genre"] if not tg.empty else "-"
    )

    c.metric(
        "⏰ ช่วงเวลาทำเงินสูงสุด",
        ts.iloc[0]["time_slot"] if not ts.empty else "-"
    )

    # Revenue Trend
    df = q(
        TICKET + """
        SELECT show_date AS date, SUM(final_price) AS revenue
        FROM ft
        WHERE show_date IS NOT NULL
        GROUP BY show_date
        ORDER BY show_date
        """,
        params
    )

    if not df.empty and df["date"].nunique() > 1:
        fig = px.line(
            df,
            x="date",
            y="revenue",
            markers=True,
            title="📈 Revenue Trend"
        )
        st.plotly_chart(style(fig), use_container_width=True)

    c1, c2 = st.columns(2)

    with c1:
        df = q(
            TICKET + """
            SELECT title AS movie, SUM(final_price) AS revenue
            FROM ft
            WHERE title IS NOT NULL
            GROUP BY title
            ORDER BY revenue DESC
            LIMIT 5
            """,
            params
        )

        if not df.empty:
            fig = px.bar(
                df,
                x="revenue",
                y="movie",
                orientation="h",
                title="🏆 Top 5 Movies",
                text_auto=",.0f"
            )
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(style(fig), use_container_width=True)

    with c2:
        df = q(
            TICKET + """
            SELECT genre, SUM(final_price) AS revenue
            FROM ft
            WHERE genre IS NOT NULL
            GROUP BY genre
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="genre",
                        y="revenue",
                        title="🎭 Revenue by Genre",
                        text_auto=",.0f"
                    )
                ),
                use_container_width=True
            )

    c3, c4 = st.columns(2)

    with c3:
        df = q(
            TICKET + """
            SELECT member_tier, SUM(final_price) AS revenue
            FROM ft
            GROUP BY member_tier
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="member_tier",
                        y="revenue",
                        title="💎 Revenue by Member Tier",
                        text_auto=",.0f"
                    )
                ),
                use_container_width=True
            )

    with c4:
        df = q(
            TICKET + """
            SELECT time_slot, SUM(final_price) AS revenue
            FROM ft
            GROUP BY time_slot
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.plotly_chart(
                style(
                    px.pie(
                        df,
                        names="time_slot",
                        values="revenue",
                        hole=.42,
                        title="⏰ Revenue by Time Slot"
                    )
                ),
                use_container_width=True
            )

    c5, c6 = st.columns(2)

    with c5:
        df = q(
            TICKET + """
            SELECT seat_type, SUM(final_price) AS revenue
            FROM ft
            WHERE seat_type IS NOT NULL
            GROUP BY seat_type
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="seat_type",
                        y="revenue",
                        title="💺 Revenue by Seat Type",
                        text_auto=",.0f"
                    )
                ),
                use_container_width=True
            )

    with c6:
        df = q(
            CONC + """
            SELECT category, SUM(total_price) AS revenue
            FROM fc
            GROUP BY category
            ORDER BY revenue DESC
            """,
            cparams
        )

        if not df.empty:
            st.plotly_chart(
                style(
                    px.pie(
                        df,
                        names="category",
                        values="revenue",
                        hole=.42,
                        title="🍿 Concession Revenue by Category"
                    )
                ),
                use_container_width=True
            )


# =========================================================
# BUSINESS QUESTIONS
# =========================================================
else:

    st.subheader("🔎 Business Questions")
    st.caption("แบ่งเป็น 4 หมวด อ่านง่ายกว่าเดิม และทุกข้อมีคำตอบสรุป")

    t1, t2, t3, t4 = st.tabs([
        "💰 Revenue",
        "🎬 Movies",
        "👥 Customers",
        "🍿 Concession"
    ])

    # -----------------------------------------------------
    # Q1-Q5
    # -----------------------------------------------------
    with t1:

        st.markdown("### Q1. รายได้จากการขายตั๋วทั้งหมดเท่าไร?")
        st.metric("คำตอบ", f"฿{ticket_rev:,.2f}")

        st.markdown("### Q2. ช่วงเวลาใดสร้างรายได้สูงสุด?")

        df = q(
            TICKET + """
            SELECT time_slot, SUM(final_price) AS revenue
            FROM ft
            GROUP BY time_slot
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.success(
                f"คำตอบ: {df.iloc[0]['time_slot']} — ฿{df.iloc[0]['revenue']:,.2f}"
            )
            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="time_slot",
                        y="revenue",
                        text_auto=",.0f"
                    ),
                    300
                ),
                use_container_width=True
            )

        st.markdown("### Q3. Concession Spend Per Head เท่าไร?")

        spend_per_head = conc_rev / ticket_count if ticket_count else 0

        st.metric(
            "คำตอบ",
            f"฿{spend_per_head:,.2f} / คน"
        )

        st.markdown("### Q4. สัดส่วนรายได้ Ticket กับ Concession เป็นเท่าไร?")

        sdf = pd.DataFrame({
            "category": ["Ticket", "Concession"],
            "revenue": [ticket_rev, conc_rev]
        })

        total = sdf["revenue"].sum()

        if total > 0:
            st.success(
                f"คำตอบ: Ticket {ticket_rev/total*100:.1f}% • "
                f"Concession {conc_rev/total*100:.1f}%"
            )

            st.plotly_chart(
                style(
                    px.pie(
                        sdf,
                        names="category",
                        values="revenue",
                        hole=.42
                    ),
                    300
                ),
                use_container_width=True
            )

        st.markdown("### Q5. ราคาตั๋วเฉลี่ยต่อใบเท่าไร?")
        st.metric("คำตอบ", f"฿{avg_ticket:,.2f} / ใบ")

    # -----------------------------------------------------
    # Q6-Q9
    # -----------------------------------------------------
    with t2:

        st.markdown("### Q6. Top 5 ภาพยนตร์ที่ทำรายได้สูงสุดคือเรื่องใด?")

        df = q(
            TICKET + """
            SELECT title AS movie, SUM(final_price) AS revenue
            FROM ft
            WHERE title IS NOT NULL
            GROUP BY title
            ORDER BY revenue DESC
            LIMIT 5
            """,
            params
        )

        if not df.empty:
            st.success(
                f"อันดับ 1: {df.iloc[0]['movie']} — ฿{df.iloc[0]['revenue']:,.2f}"
            )

            fig = px.bar(
                df,
                x="revenue",
                y="movie",
                orientation="h",
                text_auto=",.0f"
            )

            fig.update_layout(yaxis=dict(autorange="reversed"))

            st.plotly_chart(
                style(fig, 320),
                use_container_width=True
            )

        st.markdown("### Q7. Genre ใดทำรายได้สูงสุด?")

        df = q(
            TICKET + """
            SELECT genre, SUM(final_price) AS revenue
            FROM ft
            WHERE genre IS NOT NULL
            GROUP BY genre
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.success(
                f"คำตอบ: {df.iloc[0]['genre']} — ฿{df.iloc[0]['revenue']:,.2f}"
            )

            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="genre",
                        y="revenue",
                        text_auto=",.0f"
                    ),
                    300
                ),
                use_container_width=True
            )

        st.markdown("### Q8. Rating ใดทำรายได้สูงสุด?")

        df = q(
            TICKET + """
            SELECT rating, SUM(final_price) AS revenue
            FROM ft
            WHERE rating IS NOT NULL
            GROUP BY rating
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.success(
                f"คำตอบ: {df.iloc[0]['rating']} — ฿{df.iloc[0]['revenue']:,.2f}"
            )

            st.plotly_chart(
                style(
                    px.pie(
                        df,
                        names="rating",
                        values="revenue",
                        hole=.42
                    ),
                    300
                ),
                use_container_width=True
            )

        st.markdown("### Q9. Screen ใดทำรายได้สูงสุด?")

        df = q(
            TICKET + """
            SELECT
                CAST(screen_number AS VARCHAR) AS screen,
                SUM(final_price) AS revenue
            FROM ft
            WHERE screen_number IS NOT NULL
            GROUP BY screen_number
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.success(
                f"คำตอบ: Screen {df.iloc[0]['screen']} — ฿{df.iloc[0]['revenue']:,.2f}"
            )

            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="screen",
                        y="revenue",
                        text_auto=",.0f"
                    ),
                    300
                ),
                use_container_width=True
            )

    # -----------------------------------------------------
    # Q10-Q13
    # -----------------------------------------------------
    with t3:

        st.markdown("### Q10. Member Tier ใดสร้างรายได้สูงสุด?")

        df = q(
            TICKET + """
            SELECT member_tier, SUM(final_price) AS revenue
            FROM ft
            GROUP BY member_tier
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.success(
                f"คำตอบ: {df.iloc[0]['member_tier']} — ฿{df.iloc[0]['revenue']:,.2f}"
            )

            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="member_tier",
                        y="revenue",
                        text_auto=",.0f"
                    ),
                    300
                ),
                use_container_width=True
            )

        st.markdown("### Q11. Member Tier ใดซื้อตั๋วมากที่สุด?")

        df = q(
            TICKET + """
            SELECT member_tier, COUNT(*) AS tickets
            FROM ft
            GROUP BY member_tier
            ORDER BY tickets DESC
            """,
            params
        )

        if not df.empty:
            st.success(
                f"คำตอบ: {df.iloc[0]['member_tier']} — {df.iloc[0]['tickets']:,.0f} ใบ"
            )

            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="member_tier",
                        y="tickets",
                        text_auto=True
                    ),
                    300
                ),
                use_container_width=True
            )

        st.markdown("### Q12. Platinum นิยม Seat Type ใด?")

        df = q("""
            SELECT
                t.seat_type,
                COUNT(*) AS tickets
            FROM fact_ticket_sales t
            JOIN dim_customers c
                ON t.customer_id = c.customer_id
            WHERE c.member_tier = 'Platinum'
            GROUP BY t.seat_type
            ORDER BY tickets DESC
        """)

        if not df.empty:
            st.success(
                f"คำตอบ: {df.iloc[0]['seat_type']} — {df.iloc[0]['tickets']:,.0f} ใบ"
            )

            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="seat_type",
                        y="tickets",
                        text_auto=True
                    ),
                    300
                ),
                use_container_width=True
            )

        st.markdown("### Q13. Seat Type ใดทำรายได้สูงสุด?")

        df = q(
            TICKET + """
            SELECT seat_type, SUM(final_price) AS revenue
            FROM ft
            WHERE seat_type IS NOT NULL
            GROUP BY seat_type
            ORDER BY revenue DESC
            """,
            params
        )

        if not df.empty:
            st.success(
                f"คำตอบ: {df.iloc[0]['seat_type']} — ฿{df.iloc[0]['revenue']:,.2f}"
            )

            st.plotly_chart(
                style(
                    px.bar(
                        df,
                        x="seat_type",
                        y="revenue",
                        text_auto=",.0f"
                    ),
                    300
                ),
                use_container_width=True
            )

    # -----------------------------------------------------
    # Q14-Q15
    # -----------------------------------------------------
    with t4:

        st.markdown("### Q14. Gold & Platinum นิยมซื้อ Concession อะไรมากที่สุด?")

        df = q("""
            SELECT
                cs.item_name,
                SUM(cs.quantity) AS qty
            FROM fact_concession_sales cs
            JOIN dim_customers c
                ON cs.customer_id = c.customer_id
            WHERE c.member_tier IN ('Gold','Platinum')
            GROUP BY cs.item_name
            ORDER BY qty DESC
        """)

        if not df.empty:
            st.success(
                f"คำตอบ: {df.iloc[0]['item_name']} — {df.iloc[0]['qty']:,.0f} ชิ้น"
            )

            fig = px.bar(
                df.head(10),
                x="qty",
                y="item_name",
                orientation="h",
                text_auto=True
            )

            fig.update_layout(yaxis=dict(autorange="reversed"))

            st.plotly_chart(
                style(fig, 340),
                use_container_width=True
            )

        st.markdown("### Q15. หมวดหมู่ Concession ใดสร้างรายได้สูงสุด?")

        df = q(
            CONC + """
            SELECT category, SUM(total_price) AS revenue
            FROM fc
            GROUP BY category
            ORDER BY revenue DESC
            """,
            cparams
        )

        if not df.empty:
            st.success(
                f"คำตอบ: {df.iloc[0]['category']} — ฿{df.iloc[0]['revenue']:,.2f}"
            )

            st.plotly_chart(
                style(
                    px.pie(
                        df,
                        names="category",
                        values="revenue",
                        hole=.42
                    ),
                    300
                ),
                use_container_width=True
            )

st.divider()
st.caption(
    f"Data source: {os.path.relpath(DB_PATH, BASE_DIR)} • DuckDB Data Warehouse"
)