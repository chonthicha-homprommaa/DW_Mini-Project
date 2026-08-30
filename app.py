import os
from pathlib import Path
import duckdb
import streamlit as st

st.set_page_config(page_title="Cinema Analytics Dashboard", layout="wide")
st.title("🎬 Cinema Data Analytics - 15 Business Insights")

# ----------------- Database Connection -----------------
PROJECT_ROOT = Path(__file__).resolve().parent

def find_duckdb_path():
    candidates = [
        os.getenv("DUCKDB_PATH"),
        str(PROJECT_ROOT / "dev.duckdb"),
        str(PROJECT_ROOT / "movie_dw" / "dev.duckdb"),
        str(PROJECT_ROOT.parent / "dev.duckdb"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None

db_path = find_duckdb_path()

if not db_path:
    st.error("❌ ไม่พบไฟล์ dev.duckdb ในระบบ กรุณาเช็ก Path อีกครั้ง")
    st.stop()

conn = duckdb.connect(db_path, read_only=True)

# ฟังก์ชันรัน Query แบบปลอดภัย
def run_query(sql):
    try:
        return conn.execute(sql).fetchdf()
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการรัน Query: {e}")
        return None

# ดึงชื่อตารางทั้งหมดในระบบ
try:
    all_tables = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
except:
    all_tables = []

def get_table(possible_names):
    for p in possible_names:
        for real in all_tables:
            if p.lower() == real.lower():
                return real
    return possible_names[0]

# กำหนดชื่อตารางจริงในระบบ
ticket_table = get_table(['fact_ticket_sales', 'fct_ticket_sales', 'stg_ticket_sales', 'ticket_sales'])
movie_table = get_table(['dim_movies', 'stg_movies', 'movies'])
customer_table = get_table(['dim_customers', 'stg_customers', 'customers'])
showtime_table = get_table(['dim_showtimes', 'stg_showtimes', 'showtimes'])
concession_table = get_table(['fact_concession_sales', 'fct_concession_sales', 'stg_concession_sales', 'concession_sales'])

# ----------------- รายการคำถามธุรกิจ -----------------
questions = [
    "1. รายได้รวมตั๋ว+สินค้าหน้าโรง ในแต่ละเดือน/ไตรมาส",
    "2. Top 5 หนังทำรายได้สูงสุด แยกตาม Genre",
    "3. รายได้ตั๋วหนังแยกตามช่วงเวลา (Time Slot)",
    "4. ยอดขาย Concession เฉลี่ยต่อผู้เข้าชม (Per Head)",
    "5. ยอด Spending รวมแยกตามระดับสมาชิก (Member Tier)",
    "6. ประเภทที่นั่งที่ลูกค้าระดับ Platinum นิยมซื้อ",
    "7. ยอดซื้อ Concession ของสมาชิกกลุ่ม Gold/Platinum",
    "8. ยอดขายตั๋วตามประเภทสมาชิกในแต่ละไตรมาส (Customer Loyalty)",
    "9. หนังประเภท (Genre) ที่ทำรายได้รวมสูงที่สุด",
    "10. รายได้แยกตามระดับความเหมาะสมของหนัง (Rating)",
    "11. โรงฉายหมายเลขใด (Screen Number) มีรายได้เฉลี่ยต่อรอบสูงสุด",
    "12. ผลกระทบของหนังยาว > 150 นาที ต่อรอบฉายและรายได้",
    "13. สัดส่วนรายได้ (%) แยกตามประเภทที่นั่ง (Seat Type)",
    "14. สินค้า Concession ที่ขายดีที่สุดเชิงปริมาณและรายได้",
    "15. ความสัมพันธ์วันหยุด/วันทำงาน กับการซื้อ Combo Set"
]

selected_q = st.selectbox("🎯 เลือกข้อคำถามธุรกิจที่ต้องการดูผลลัพธ์:", questions)
st.divider()

q_num = int(selected_q.split(".")[0])

# ----------------- SQL Logic แยกตามข้อ -----------------

if q_num == 1:
    st.subheader("1. รายได้รวมจากการขายตั๋วชมภาพยนตร์และสินค้าหน้าโรง ในแต่ละเดือน")
    sql = f"""
    SELECT 
        STRFTIME(CAST(s.start_time AS DATE), '%Y-%m') AS month,
        SUM(t.final_price) AS ticket_revenue
    FROM {ticket_table} t
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    GROUP BY 1 ORDER BY 1
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("month"))

elif q_num == 2:
    st.subheader("2. ภาพยนตร์ที่ทำรายได้รวม (Box Office) สูงสุด 5 อันดับแรกในแต่ละประเภทหนัง (Genre)")
    sql = f"""
    SELECT 
        m.genre,
        m.title,
        SUM(t.final_price) AS total_revenue
    FROM {ticket_table} t
    JOIN {movie_table} m ON t.movie_id = m.movie_id
    GROUP BY m.genre, m.title
    ORDER BY m.genre, total_revenue DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 3:
    st.subheader("3. ช่วงเวลาของวัน (Time Slot) ที่สร้างรายได้จากการขายตั๋วมากที่สุด")
    sql = f"""
    SELECT 
        CASE 
            WHEN EXTRACT(HOUR FROM CAST(s.start_time AS TIMESTAMP)) < 12 THEN 'Morning'
            WHEN EXTRACT(HOUR FROM CAST(s.start_time AS TIMESTAMP)) < 17 THEN 'Afternoon'
            ELSE 'Evening'
        END AS time_slot,
        SUM(t.final_price) AS total_revenue,
        COUNT(t.ticket_id) AS total_tickets
    FROM {ticket_table} t
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    GROUP BY 1 ORDER BY total_revenue DESC
    """
    df = run_query(sql)
    if df is not None:
        col1, col2 = st.columns([1.5, 1])
        col1.dataframe(df, use_container_width=True)
        if not df.empty:
            col2.bar_chart(df.set_index("time_slot")["total_revenue"])

elif q_num == 4:
    st.subheader("4. ยอดขายสินค้า Concession เฉลี่ยต่อผู้เข้าชม 1 คน (Spending Per Head)")
    sql = f"""
    SELECT 
        SUM(total_price) AS total_concession_rev, 
        5279 AS total_tickets, 
        ROUND(SUM(total_price) / 5279.0, 2) AS spend_per_head 
    FROM {concession_table}
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 5:
    st.subheader("5. สมาชิกแต่ละระดับ (Member Tier) มียอด Spending รวมต่างกันอย่างไร")
    sql = f"""
    SELECT 
        COALESCE(c.member_tier, 'Non-Member') AS member_tier, 
        SUM(t.final_price) AS ticket_spending,
        COUNT(t.ticket_id) AS tickets_bought
    FROM {ticket_table} t
    LEFT JOIN {customer_table} c ON t.customer_id = c.customer_id
    GROUP BY 1 ORDER BY ticket_spending DESC
    """
    df = run_query(sql)
    if df is not None:
        col1, col2 = st.columns([1.5, 1])
        col1.dataframe(df, use_container_width=True)
        if not df.empty:
            col2.bar_chart(df.set_index("member_tier")["ticket_spending"])

elif q_num == 6:
    st.subheader("6. ลูกค้าระดับ Platinum นิยมซื้อประเภทที่นั่งแบบใดมากที่สุด")
    sql = f"""
    SELECT 
        t.seat_type, 
        COUNT(t.ticket_id) AS total_seats_booked, 
        SUM(t.final_price) AS total_spending 
    FROM {ticket_table} t 
    JOIN {customer_table} c ON t.customer_id = c.customer_id 
    WHERE c.member_tier = 'Platinum' 
    GROUP BY 1 ORDER BY total_seats_booked DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 7:
    st.subheader("7. สมาชิกกลุ่ม Gold/Platinum กับการซื้อสินค้า Concession")
    sql = f"""
    SELECT 
        c.member_tier,
        f.item_name,
        SUM(f.quantity) AS total_qty,
        SUM(f.total_price) AS total_spending
    FROM {concession_table} f
    JOIN {customer_table} c ON f.customer_id = c.customer_id
    WHERE c.member_tier IN ('Gold', 'Platinum')
    GROUP BY 1, 2 ORDER BY total_spending DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 8:
    st.subheader("8. ยอดขายตั๋วจำแนกตามประเภทสมาชิกในแต่ละไตรมาส (Customer Loyalty)")
    sql = f"""
    SELECT 
        COALESCE(c.member_tier, 'Non-Member') AS member_tier,
        'Q' || EXTRACT(QUARTER FROM CAST(s.start_time AS DATE)) AS quarter,
        SUM(t.final_price) AS quarterly_revenue
    FROM {ticket_table} t
    LEFT JOIN {customer_table} c ON t.customer_id = c.customer_id
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    GROUP BY 1, 2
    ORDER BY quarter, quarterly_revenue DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 9:
    st.subheader("9. หนังประเภท (Genre) ใดที่ทำรายได้รวมสูงที่สุดในโรงภาพยนตร์")
    sql = f"""
    SELECT 
        m.genre, 
        SUM(t.final_price) AS total_revenue 
    FROM {ticket_table} t 
    JOIN {movie_table} m ON t.movie_id = m.movie_id 
    GROUP BY 1 ORDER BY total_revenue DESC
    """
    df = run_query(sql)
    if df is not None:
        col1, col2 = st.columns([1.5, 1])
        col1.dataframe(df, use_container_width=True)
        if not df.empty:
            col2.bar_chart(df.set_index("genre")["total_revenue"])

elif q_num == 10:
    st.subheader("10. รายได้จำแนกตามระดับความเหมาะสมของหนัง (Rating)")
    sql = f"""
    SELECT 
        m.rating, 
        SUM(t.final_price) AS total_revenue,
        COUNT(t.ticket_id) AS tickets_sold
    FROM {ticket_table} t 
    JOIN {movie_table} m ON t.movie_id = m.movie_id 
    GROUP BY 1 ORDER BY total_revenue DESC
    """
    df = run_query(sql)
    if df is not None:
        col1, col2 = st.columns([1.5, 1])
        col1.dataframe(df, use_container_width=True)
        if not df.empty:
            col2.bar_chart(df.set_index("rating")["total_revenue"])

elif q_num == 11:
    st.subheader("11. โรงฉายหมายเลขใด (Screen Number) มีอัตราการสร้างรายได้เฉลี่ยต่อรอบสูงสุด")
    sql = f"""
    SELECT 
        s.screen_number,
        COUNT(DISTINCT s.showtime_id) AS show_count,
        SUM(t.final_price) AS total_revenue,
        ROUND(SUM(t.final_price) / COUNT(DISTINCT s.showtime_id), 2) AS avg_rev_per_show
    FROM {ticket_table} t
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    GROUP BY 1 ORDER BY avg_rev_per_show DESC
    """
    df = run_query(sql)
    if df is not None:
        col1, col2 = st.columns([1.5, 1])
        col1.dataframe(df, use_container_width=True)
        if not df.empty:
            col2.bar_chart(df.set_index("screen_number")["avg_rev_per_show"])

elif q_num == 12:
    st.subheader("12. ภาพยนตร์ที่มีความยาวเกิน 150 นาที กระทบต่อรอบฉายและรายได้รวมหรือไม่")
    sql = f"""
    SELECT 
        CASE WHEN m.duration_minutes > 150 THEN 'Over 150 Mins' ELSE '150 Mins & Under' END AS duration_group,
        COUNT(DISTINCT m.movie_id) AS movie_count,
        SUM(t.final_price) AS total_revenue,
        ROUND(AVG(t.final_price), 2) AS avg_ticket_price
    FROM {ticket_table} t
    JOIN {movie_table} m ON t.movie_id = m.movie_id
    GROUP BY 1
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 13:
    st.subheader("13. สัดส่วนรายได้ (%) จำแนกตามประเภทที่นั่ง")
    sql = f"""
    SELECT 
        seat_type,
        SUM(final_price) AS total_revenue,
        ROUND(SUM(final_price) * 100.0 / (SELECT SUM(final_price) FROM {ticket_table}), 2) AS revenue_percentage
    FROM {ticket_table}
    GROUP BY 1 ORDER BY total_revenue DESC
    """
    df = run_query(sql)
    if df is not None:
        col1, col2 = st.columns([1.5, 1])
        col1.dataframe(df, use_container_width=True)
        if not df.empty:
            col2.bar_chart(df.set_index("seat_type")["revenue_percentage"])

elif q_num == 14:
    st.subheader("14. สินค้า Concession ประเภทใดขายดีที่สุดในเชิงปริมาณและเชิงรายได้")
    sql = f"""
    SELECT 
        item_name,
        SUM(quantity) AS total_quantity,
        SUM(total_price) AS total_revenue
    FROM {concession_table}
    GROUP BY 1 ORDER BY total_revenue DESC
    """
    df = run_query(sql)
    if df is not None:
        col1, col2 = st.columns([1.5, 1])
        col1.dataframe(df, use_container_width=True)
        if not df.empty:
            col2.bar_chart(df.set_index("item_name")["total_revenue"])

elif q_num == 15:
    st.subheader("15. ความสัมพันธ์วันหยุด/วันทำงาน กับการซื้อ Combo Set หน้าโรง")
    sql = f"""
    SELECT 
        CASE 
            WHEN EXTRACT(DAYOFWEEK FROM CAST(s.start_time AS DATE)) IN (0, 6) THEN 'Weekend' 
            ELSE 'Weekday' 
        END AS day_type,
        f.item_name,
        SUM(f.quantity) AS total_qty,
        SUM(f.total_price) AS total_spending
    FROM {concession_table} f
    JOIN {showtime_table} s ON f.showtime_id = s.showtime_id
    WHERE f.item_name LIKE '%Combo%' OR f.item_name LIKE '%Set%'
    GROUP BY 1, 2 ORDER BY total_spending DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)