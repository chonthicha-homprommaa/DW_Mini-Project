import os
import sqlite3
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Cinema Data Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 Cinema Data Analytics Dashboard")
st.markdown("ระบบรายงานและวิเคราะห์ข้อมูลยอดขายภาพยนตร์และ Concession")

# --- ฟังก์ชันค้นหาไฟล์ CSV อัตโนมัติในโปรเจกต์ ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def find_csv_file(filename):
    # 1. เช็คในโฟลเดอร์ปัจจุบัน
    path_direct = os.path.join(BASE_DIR, filename)
    if os.path.exists(path_direct):
        return path_direct

    # 2. ค้นหาในโฟลเดอร์ย่อยทั้งหมด
    for root, dirs, files in os.walk(BASE_DIR):
        if filename in files:
            return os.path.join(root, filename)

    raise FileNotFoundError(f"ไม่พบไฟล์ {filename} ในระบบ")


# --- Function สำหรับโหลดข้อมูลเข้า SQLite (In-Memory) ---
@st.cache_data
def load_data_to_sqlite():
    conn = sqlite3.connect(":memory:", check_same_thread=False)

    df_tix = pd.read_csv(find_csv_file("ticket_sales_large.csv"))
    df_con = pd.read_csv(find_csv_file("concession_sales_large.csv"))
    df_show = pd.read_csv(find_csv_file("showtimes_large.csv"))
    df_cust = pd.read_csv(find_csv_file("customers.csv"))
    df_mov = pd.read_csv(find_csv_file("movies.csv"))

    df_tix.to_sql("ticket_sales", conn, index=False, if_exists="replace")
    df_con.to_sql("concession_sales", conn, index=False, if_exists="replace")
    df_show.to_sql("showtimes", conn, index=False, if_exists="replace")
    df_cust.to_sql("customers", conn, index=False, if_exists="replace")
    df_mov.to_sql("movies", conn, index=False, if_exists="replace")

    return conn


try:
    conn = load_data_to_sqlite()
except Exception as e:
    st.error(
        f"เกิดข้อผิดพลาดในการโหลดไฟล์ข้อมูล: {e}\n\nกรุณาตรวจสอบว่าไฟล์ CSV อยู่ในโฟลเดอร์โปรเจกต์หรือไม่"
    )
    st.stop()


def run_query(sql):
    try:
        return pd.read_sql_query(sql, conn)
    except Exception as e:
        st.error(f"SQL Error: {e}")
        return None


# --- Sidebar เลือกโจทย์วิเคราะห์ ---
st.sidebar.header("📌 เลือกหัวข้อวิเคราะห์")
question_option = st.sidebar.selectbox(
    "เลือกคำถามที่ต้องการดูข้อมูล:",
    [
        "1. รายได้รวมจากการขายตั๋วทั้งหมด",
        "2. รายได้ตามช่วงเวลา (Time Slot)",
        "3. ยอดซื้อเฉลี่ยต่อผู้เข้าชม (Spend Per Head)",
        "4. สัดส่วนรายได้ ตั๋ว vs Concession (%)",
        "5. ราคาตั๋วเฉลี่ยต่อใบ (Average Ticket Price)",
        "6. Top 5 ภาพยนตร์ทำรายได้สูงสุด",
        "7. หมวดหมู่ภาพยนตร์ (Genre) ที่ทำรายได้สูงสุด",
        "8. รายได้รวมตามระดับความเหมาะสม (Rating)",
        "9. โรงฉาย (Screen Number) ที่ทำรายได้สูงสุด",
        "10. ยอด Spending รวมตามสมาชิกระดับต่างๆ",
        "11. จำนวนตั๋วรวม จำแนกตามระดับสมาชิก",
        "12. ประเภทที่นั่งที่ลูกค้าระดับ Platinum นิยมซื้อ",
        "13. ประเภทที่นั่ง (Seat Type) ที่ทำรายได้สูงสุด",
        "14. สินค้า Concession ที่นิยมของ Platinum & Gold",
        "15. รายได้รวมตามหมวดหมู่ Concession",
    ],
)

st.divider()

# --- แสดงผลตามหัวข้อที่เลือก ---

if question_option.startswith("1."):
    st.header("1. รายได้รวมจากการขายตั๋วภาพยนตร์ทั้งหมด")
    sql = "SELECT SUM(final_price) AS 'รายได้รวมตั๋ว (บาท)' FROM ticket_sales;"
    df = run_query(sql)
    st.metric(
        "รายได้รวมจากการขายตั๋วทั้งหมด",
        f"฿{df['รายได้รวมตั๋ว (บาท)'][0]:,.2f}",
    )
    st.dataframe(df, use_container_width=True)

elif question_option.startswith("2."):
    st.header("2. รายได้จากการขายตั๋วแบ่งตามช่วงเวลา (Time Slot)")
    sql = """
    SELECT 
        CASE 
            WHEN strftime('%H', show_date) BETWEEN '06' AND '11' THEN 'Morning (06:00-11:59)'
            WHEN strftime('%H', show_date) BETWEEN '12' AND '16' THEN 'Afternoon (12:00-16:59)'
            ELSE 'Evening (17:00-23:59)'
        END AS Time_Slot,
        SUM(t.final_price) AS 'รายได้รวม (บาท)'
    FROM ticket_sales t
    JOIN showtimes s ON t.showtime_id = s.showtime_id
    GROUP BY 1 ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("Time_Slot")["รายได้รวม (บาท)"])

elif question_option.startswith("3."):
    st.header("3. ยอดซื้อ Concession เฉลี่ยต่อผู้เข้าชม 1 คน (Spend Per Head)")
    sql = """
    SELECT 
        (SELECT SUM(total_price) FROM concession_sales) * 1.0 / COUNT(ticket_id) AS 'Spend Per Head (บาท/คน)'
    FROM ticket_sales;
    """
    df = run_query(sql)
    st.metric(
        "Concession Spend Per Head",
        f"฿{df['Spend Per Head (บาท/คน)'][0]:,.2f}",
    )
    st.dataframe(df, use_container_width=True)

elif question_option.startswith("4."):
    st.header(
        "4. สัดส่วนรายได้รวมระหว่างยอดขายตั๋ว (Ticket) กับ Concession (%)"
    )
    sql = """
    WITH totals AS (
        SELECT 
            (SELECT SUM(final_price) FROM ticket_sales) AS ticket_rev,
            (SELECT SUM(total_price) FROM concession_sales) AS concession_rev
    )
    SELECT 
        'Ticket Revenue' AS Category, ticket_rev AS 'Revenue (THB)', ROUND(ticket_rev * 100.0 / (ticket_rev + concession_rev), 2) AS 'Percentage (%)' FROM totals
    UNION ALL
    SELECT 
        'Concession Revenue' AS Category, concession_rev AS 'Revenue (THB)', ROUND(concession_rev * 100.0 / (ticket_rev + concession_rev), 2) AS 'Percentage (%)' FROM totals;
    """
    df = run_query(sql)
    st.dataframe(df, use_container_width=True)
    st.bar_chart(df.set_index("Category")["Percentage (%)"])

elif question_option.startswith("5."):
    st.header("5. ราคาตั๋วเฉลี่ยต่อใบ (Average Ticket Price)")
    sql = "SELECT AVG(final_price) AS 'ราคาตั๋วเฉลี่ย (บาท/ใบ)' FROM ticket_sales;"
    df = run_query(sql)
    st.metric(
        "ราคาตั๋วเฉลี่ย (Average Ticket Price)",
        f"฿{df['ราคาตั๋วเฉลี่ย (บาท/ใบ)'][0]:,.2f}",
    )
    st.dataframe(df, use_container_width=True)

elif question_option.startswith("6."):
    st.header("6. ภาพยนตร์ทำรายได้รวมสูงสุด 5 อันดับแรก (Top 5 Movies)")
    sql = """
    SELECT m.title AS 'ชื่อภาพยนตร์', SUM(t.final_price) AS 'รายได้รวม (บาท)'
    FROM ticket_sales t
    JOIN showtimes s ON t.showtime_id = s.showtime_id
    JOIN movies m ON s.movie_id = m.movie_id
    GROUP BY m.title ORDER BY 2 DESC LIMIT 5;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("ชื่อภาพยนตร์")["รายได้รวม (บาท)"])

elif question_option.startswith("7."):
    st.header("7. หมวดหมู่ภาพยนตร์ (Genre) ที่ทำรายได้รวมสูงที่สุด")
    sql = """
    SELECT m.genre AS 'หมวดหมู่ภาพยนตร์', SUM(t.final_price) AS 'รายได้รวม (บาท)'
    FROM ticket_sales t
    JOIN showtimes s ON t.showtime_id = s.showtime_id
    JOIN movies m ON s.movie_id = m.movie_id
    GROUP BY m.genre ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("หมวดหมู่ภาพยนตร์")["รายได้รวม (บาท)"])

elif question_option.startswith("8."):
    st.header("8. รายได้รวมจำแนกตามระดับความเหมาะสม (Rating)")
    sql = """
    SELECT m.rating AS 'Rating', SUM(t.final_price) AS 'รายได้รวม (บาท)'
    FROM ticket_sales t
    JOIN showtimes s ON t.showtime_id = s.showtime_id
    JOIN movies m ON s.movie_id = m.movie_id
    GROUP BY m.rating ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("Rating")["รายได้รวม (บาท)"])

elif question_option.startswith("9."):
    st.header("9. โรงฉายหมายเลขใด (Screen Number) ที่ทำรายได้สูงที่สุด")
    sql = """
    SELECT 'Screen ' || s.screen_number AS 'โรงฉาย', SUM(t.final_price) AS 'รายได้รวม (บาท)'
    FROM ticket_sales t
    JOIN showtimes s ON t.showtime_id = s.showtime_id
    GROUP BY s.screen_number ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("โรงฉาย")["รายได้รวม (บาท)"])

elif question_option.startswith("10."):
    st.header("10. ยอด Spending รวมจำแนกตามระดับสมาชิก (Member Tier)")
    sql = """
    SELECT 
        CASE WHEN c.member_tier IS NULL OR c.member_tier = '' THEN 'General (Non-Member)' ELSE c.member_tier END AS 'ระดับสมาชิก',
        SUM(t.final_price) AS 'ยอดซื้อตั๋วรวม (บาท)'
    FROM ticket_sales t
    JOIN customers c ON t.customer_id = c.customer_id
    GROUP BY 1 ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("ระดับสมาชิก")["ยอดซื้อตั๋วรวม (บาท)"])

elif question_option.startswith("11."):
    st.header("11. ยอดขายตั๋วรวม (Total Tickets) จำแนกตามประเภทสมาชิก")
    sql = """
    SELECT 
        CASE WHEN c.member_tier IS NULL OR c.member_tier = '' THEN 'General (Non-Member)' ELSE c.member_tier END AS 'ระดับสมาชิก',
        COUNT(t.ticket_id) AS 'จำนวนตั๋ว (ใบ)'
    FROM ticket_sales t
    JOIN customers c ON t.customer_id = c.customer_id
    GROUP BY 1 ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("ระดับสมาชิก")["จำนวนตั๋ว (ใบ)"])

elif question_option.startswith("12."):
    st.header("12. ประเภทที่นั่งที่ลูกค้าระดับ Platinum นิยมซื้อมากที่สุด")
    sql = """
    SELECT t.seat_type AS 'ประเภทที่นั่ง', COUNT(t.ticket_id) AS 'จำนวนตั๋วที่ซื้อ (ใบ)'
    FROM ticket_sales t
    JOIN customers c ON t.customer_id = c.customer_id
    WHERE c.member_tier = 'Platinum'
    GROUP BY t.seat_type ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("ประเภทที่นั่ง")["จำนวนตั๋วที่ซื้อ (ใบ)"])

elif question_option.startswith("13."):
    st.header("13. ประเภทที่นั่ง (Seat Type) ที่สร้างรายได้รวมมากที่สุด")
    sql = """
    SELECT seat_type AS 'ประเภทที่นั่ง', SUM(final_price) AS 'รายได้รวม (บาท)'
    FROM ticket_sales
    GROUP BY seat_type ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("ประเภทที่นั่ง")["รายได้รวม (บาท)"])

elif question_option.startswith("14."):
    st.header("14. สินค้า Concession ที่นิยมซื้อมากที่สุดของกลุ่ม Gold & Platinum")
    sql = """
    SELECT cs.item_name AS 'ชื่อสินค้า Concession', SUM(cs.quantity) AS 'จำนวนชิ้นรวม'
    FROM concession_sales cs
    JOIN customers c ON cs.customer_id = c.customer_id
    WHERE c.member_tier IN ('Gold', 'Platinum')
    GROUP BY cs.item_name ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("ชื่อสินค้า Concession")["จำนวนชิ้นรวม"])

elif question_option.startswith("15."):
    st.header("15. รายได้รวมจำแนกตามหมวดหมู่สินค้า Concession")
    sql = """
    SELECT 
        CASE 
            WHEN item_name LIKE '%Popcorn%' THEN 'Popcorn'
            WHEN item_name LIKE '%Soda%' OR item_name LIKE '%Water%' THEN 'Beverage'
            WHEN item_name LIKE '%Combo%' THEN 'Combo Set'
            ELSE 'Other'
        END AS 'หมวดหมู่ Concession',
        SUM(total_price) AS 'รายได้รวม (บาท)'
    FROM concession_sales
    GROUP BY 1 ORDER BY 2 DESC;
    """
    df = run_query(sql)
    col1, col2 = st.columns([1, 1])
    with col1:
        st.dataframe(df, use_container_width=True)
    with col2:
        st.bar_chart(df.set_index("หมวดหมู่ Concession")["รายได้รวม (บาท)"])