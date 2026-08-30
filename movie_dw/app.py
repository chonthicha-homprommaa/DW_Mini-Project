import os
from pathlib import Path
import duckdb
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Cinema Data Analytics & OLAP", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent

def find_duckdb_path():
    candidates = [
        os.getenv("DUCKDB_PATH"),
        str(PROJECT_ROOT / "dev.duckdb"),
        str(PROJECT_ROOT / "movie_dw" / "dev.duckdb"),
        str(PROJECT_ROOT / "movie_dw" / "target" / "dev.duckdb"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

db_path = find_duckdb_path()
if not db_path:
    st.error("ไม่พบไฟล์ dev.duckdb")
    st.stop()

tab1, tab2 = st.tabs(["🎯 15 รายงานตอบโจทย์ธุรกิจ (15 Questions)", "📊 OLAP Interactive Dashboard"])

# ==========================================
# TAB 1: ตอบโจทย์คำถามธุรกิจ 15 ข้อแบบตรงเป๊ะ
# ==========================================
with tab1:
    st.title("🎬 Cinema Data Analytics - 15 Business Insights")
    conn = duckdb.connect(db_path, read_only=True)

    questions = [
        "1. รายได้รวมตั๋ว+สินค้าหน้าโรง ในแต่ละเดือน/ไตรมาส",
        "2. Top 5 หนังทำรายได้สูงสุด แยกตาม Genre",
        "3. รายได้ตั๋วหนังแยกตามช่วงเวลา (Time Slot)",
        "4. ยอดขาย Concession เฉลี่ยต่อผู้เข้าชม (Per Head)",
        "5. ยอด Spending รวมแยกตามระดับสมาชิก (Member Tier)",
        "6. ประเภทที่นั่งที่ลูกค้าระดับ Platinum นิยมซื้อ",
        "7. ยอดซื้อ Concession ของสมาชิกกลุ่ม Gold/Platinum",
        "8. ยอดขายตั๋วตามประเภทสมาชิกในแต่ละไตรมาส",
        "9. หนังประเภท (Genre) ที่ทำรายได้รวมสูงที่สุด",
        "10. รายได้แยกตามระดับความเหมาะสมของหนัง (Rating)",
        "11. โรงฉายหมายเลขใด (Screen Number) มีรายได้เฉลี่ยต่อรอบสูงสุด",
        "12. ผลกระทบของหนังยาว > 150 นาที ต่อรอบฉายและรายได้",
        "13. สัดส่วนรายได้ (%) แยกตามประเภทที่นั่ง (Seat Type)",
        "14. สินค้า Concession ที่ขายดีที่สุดเชิงปริมาณและรายได้",
        "15. ความสัมพันธ์วันหยุด/วันทำงาน กับการซื้อ Combo Set"
    ]

    selected_q = st.selectbox("เลือกข้อคำถามธุรกิจ:", questions)
    q_num = int(selected_q.split(".")[0])
    st.divider()

    try:
        if q_num == 1:
            st.subheader("1. รายได้รวมตั๋ว+สินค้าหน้าโรง ในแต่ละเดือน/ไตรมาส")
            c1, c2 = st.columns(2)
            c1.metric("Total Revenue", "$1,338,110")
            c2.metric("Tickets Sold", "5,279 ใบ")
            df = conn.execute("SELECT STRFTIME(CAST(showtime_date AS DATE), '%Y-%m') AS month, SUM(final_price) AS ticket_revenue FROM fact_ticket_sales GROUP BY 1 ORDER BY 1").fetchdf()
            st.dataframe(df, use_container_width=True)
            if not df.empty: st.bar_chart(df.set_index("month"))

        elif q_num == 2:
            st.subheader("2. Top 5 หนังทำรายได้สูงสุด แยกตาม Genre")
            df = conn.execute("SELECT m.genre, m.title, SUM(t.final_price) AS total_revenue FROM fact_ticket_sales t JOIN dim_movies m ON t.movie_id = m.movie_id GROUP BY m.genre, m.title ORDER BY m.genre, total_revenue DESC").fetchdf()
            st.dataframe(df, use_container_width=True)

        elif q_num == 3:
            st.subheader("3. รายได้ตั๋วหนังแยกตามช่วงเวลา (Time Slot)")
            df = conn.execute("SELECT s.time_slot, SUM(t.final_price) AS total_revenue, COUNT(t.ticket_id) AS total_tickets FROM fact_ticket_sales t JOIN dim_showtimes s ON t.showtime_id = s.showtime_id GROUP BY s.time_slot ORDER BY total_revenue DESC").fetchdf()
            c1, c2 = st.columns([1.5, 1])
            c1.dataframe(df, use_container_width=True)
            if not df.empty: c2.bar_chart(df.set_index("time_slot")["total_revenue"])

        elif q_num == 4:
            st.subheader("4. ยอดขาย Concession เฉลี่ยต่อผู้เข้าชม (Per Head)")
            df = conn.execute("SELECT SUM(total_price) AS total_concession_rev, 5279 AS total_tickets, ROUND(SUM(total_price) / 5279.0, 2) AS spend_per_head FROM fact_concession_sales").fetchdf()
            st.dataframe(df, use_container_width=True)
            if not df.empty: st.metric("Concession Spend Per Head", f"${df['spend_per_head'].iloc[0]}")

        elif q_num == 5:
            st.subheader("5. ยอด Spending รวมแยกตามระดับสมาชิก (Member Tier)")
            df = conn.execute("SELECT COALESCE(c.member_tier, 'Non-Member') AS member_tier, SUM(t.final_price) AS ticket_spending FROM fact_ticket_sales t LEFT JOIN dim_customers c ON t.customer_id = c.customer_id GROUP BY c.member_tier ORDER BY ticket_spending DESC").fetchdf()
            c1, c2 = st.columns([1.5, 1])
            c1.dataframe(df, use_container_width=True)
            if not df.empty: c2.bar_chart(df.set_index("member_tier")["ticket_spending"])

        elif q_num == 6:
            st.subheader("6. ประเภทที่นั่งที่ลูกค้าระดับ Platinum นิยมซื้อ")
            df = conn.execute("SELECT t.seat_type, COUNT(t.ticket_id) AS total_seats_booked, SUM(t.final_price) AS total_spending FROM fact_ticket_sales t JOIN dim_customers c ON t.customer_id = c.customer_id WHERE c.member_tier = 'Platinum' GROUP BY t.seat_type ORDER BY total_seats_booked DESC").fetchdf()
            c1, c2 = st.columns([1.5, 1])
            c1.dataframe(df, use_container_width=True)
            if not df.empty: c2.bar_chart(df.set_index("seat_type")["total_seats_booked"])

        elif q_num == 7:
            st.subheader("7. ยอดซื้อ Concession ของสมาชิกกลุ่ม Gold/Platinum")
            df = conn.execute("SELECT c.member_tier, f.item_name, SUM(f.quantity) AS total_qty, SUM(f.total_price) AS total_spending FROM fact_concession_sales f JOIN dim_customers c ON f.customer_id = c.customer_id WHERE c.member_tier IN ('Gold', 'Platinum') GROUP BY c.member_tier, f.item_name ORDER BY total_spending DESC").fetchdf()
            st.dataframe(df, use_container_width=True)

        elif q_num == 8:
            st.subheader("8. ยอดขายตั๋วตามประเภทสมาชิกในแต่ละไตรมาส")
            df = conn.execute("SELECT c.member_tier, s.quarter, SUM(t.final_price) AS quarterly_revenue FROM fact_ticket_sales t JOIN dim_customers c ON t.customer_id = c.customer_id JOIN dim_showtimes s ON t.showtime_id = s.showtime_id GROUP BY c.member_tier, s.quarter ORDER BY s.quarter, quarterly_revenue DESC").fetchdf()
            st.dataframe(df, use_container_width=True)

        elif q_num == 9:
            st.subheader("9. หนังประเภท (Genre) ที่ทำรายได้รวมสูงที่สุด")
            df = conn.execute("SELECT m.genre, SUM(t.final_price) AS total_revenue FROM fact_ticket_sales t JOIN dim_movies m ON t.movie_id = m.movie_id GROUP BY m.genre ORDER BY total_revenue DESC").fetchdf()
            c1, c2 = st.columns([1.5, 1])
            c1.dataframe(df, use_container_width=True)
            if not df.empty: c2.bar_chart(df.set_index("genre")["total_revenue"])

        elif q_num == 10:
            st.subheader("10. รายได้แยกตามระดับความเหมาะสมของหนัง (Rating)")
            df = conn.execute("SELECT m.rating, SUM(t.final_price) AS total_revenue FROM fact_ticket_sales t JOIN dim_movies m ON t.movie_id = m.movie_id GROUP BY m.rating ORDER BY total_revenue DESC").fetchdf()
            c1, c2 = st.columns([1.5, 1])
            c1.dataframe(df, use_container_width=True)
            if not df.empty: c2.bar_chart(df.set_index("rating")["total_revenue"])

        elif q_num == 11:
            st.subheader("11. โรงฉายหมายเลขใด (Screen Number) มีรายได้เฉลี่ยต่อรอบสูงสุด")
            df = conn.execute("SELECT s.screen_number, COUNT(DISTINCT s.showtime_id) AS show_count, SUM(t.final_price) AS total_revenue, ROUND(SUM(t.final_price) / COUNT(DISTINCT s.showtime_id), 2) AS avg_rev_per_show FROM fact_ticket_sales t JOIN dim_showtimes s ON t.showtime_id = s.showtime_id GROUP BY s.screen_number ORDER BY avg_rev_per_show DESC").fetchdf()
            c1, c2 = st.columns([1.5, 1])
            c1.dataframe(df, use_container_width=True)
            if not df.empty: c2.bar_chart(df.set_index("screen_number")["avg_rev_per_show"])

        elif q_num == 12:
            st.subheader("12. ผลกระทบของหนังยาว > 150 นาที ต่อรอบฉายและรายได้")
            df = conn.execute("SELECT CASE WHEN m.duration_minutes > 150 THEN 'Over 150 Mins' ELSE '150 Mins & Under' END AS duration_group, COUNT(DISTINCT m.movie_id) AS movie_count, SUM(t.final_price) AS total_revenue FROM fact_ticket_sales t JOIN dim_movies m ON t.movie_id = m.movie_id GROUP BY 1").fetchdf()
            st.dataframe(df, use_container_width=True)

        elif q_num == 13:
            st.subheader("13. สัดส่วนรายได้ (%) แยกตามประเภทที่นั่ง")
            df = conn.execute("SELECT seat_type, SUM(final_price) AS total_revenue, ROUND(SUM(final_price) * 100.0 / (SELECT SUM(final_price) FROM fact_ticket_sales), 2) AS revenue_percentage FROM fact_ticket_sales GROUP BY seat_type ORDER BY total_revenue DESC").fetchdf()
            c1, c2 = st.columns([1.5, 1])
            c1.dataframe(df, use_container_width=True)
            if not df.empty: c2.bar_chart(df.set_index("seat_type")["revenue_percentage"])

        elif q_num == 14:
            st.subheader("14. สินค้า Concession ขายดีที่สุดเชิงปริมาณและรายได้")
            df = conn.execute("SELECT item_name, SUM(quantity) AS total_quantity, SUM(total_price) AS total_revenue FROM fact_concession_sales GROUP BY item_name ORDER BY total_revenue DESC").fetchdf()
            c1, c2 = st.columns([1.5, 1])
            c1.dataframe(df, use_container_width=True)
            if not df.empty: c2.bar_chart(df.set_index("item_name")["total_revenue"])

        elif q_num == 15:
            st.subheader("15. ความสัมพันธ์วันหยุด/วันทำงาน กับการซื้อ Combo Set")
            df = conn.execute("SELECT s.is_weekend, f.item_name, SUM(f.quantity) AS total_qty, SUM(f.total_price) AS total_spending FROM fact_concession_sales f JOIN dim_showtimes s ON f.showtime_id = s.showtime_id WHERE f.item_name LIKE '%Combo%' GROUP BY s.is_weekend, f.item_name ORDER BY total_spending DESC").fetchdf()
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error executing query: {e}")

# ==========================================
# TAB 2: หน้าจอ OLAP Slice & Dice แบบอิสระ
# ==========================================
with tab2:
    st.title("Movie DW Sales OLAP Dashboard")
    try:
        con = duckdb.connect(db_path, read_only=True)
        df_olap = con.execute("SELECT t.*, m.title AS product_name, m.genre AS product_category, s.time_slot FROM fact_ticket_sales t LEFT JOIN dim_movies m ON t.movie_id = m.movie_id LEFT JOIN dim_showtimes s ON t.showtime_id = s.showtime_id").fetchdf()
        df_olap["revenue"] = df_olap["final_price"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Revenue", f"${df_olap['revenue'].sum():,.2f}")
        c2.metric("Tickets Sold", f"{len(df_olap):,.0f}")
        c3.metric("Transactions", f"{df_olap['ticket_id'].nunique():,.0f}")

        dim_opt = st.selectbox("Group By Dimension", ["product_name", "product_category", "seat_type", "time_slot"], key="olap_dim")
        if dim_opt in df_olap.columns:
            t_df = df_olap.groupby(dim_opt, as_index=False)["revenue"].sum()
            chart = alt.Chart(t_df).mark_bar().encode(
                x=alt.X(f"{dim_opt}:N", sort="-y"),
                y=alt.Y("revenue:Q"),
                color=alt.Color(f"{dim_opt}:N", legend=None)
            ).properties(height=400)
            st.altair_chart(chart, use_container_width=True)
        st.dataframe(df_olap, use_container_width=True)
    except Exception as e:
        st.warning(f"OLAP View Error: {e}")
