import os
from pathlib import Path
import duckdb
import streamlit as st

st.set_page_config(page_title="Cinema Analytics Dashboard", layout="wide")
st.title("🎬 Cinema Data Analytics - 15 Business Insights")

# ----------------- Database Connection -----------------
PROJECT_ROOT = Path(__file__).resolve().parent

# กำหนด Path ตรงไปยัง dev.duckdb ในโฟลเดอร์ movie_dw
DB_PATH = PROJECT_ROOT / "movie_dw" / "dev.duckdb"

# หากหาใน movie_dw ไม่เจอ ให้ลองถอยออกไปดูชั้นนอก
if not DB_PATH.exists():
    DB_PATH = PROJECT_ROOT / "dev.duckdb"

if not DB_PATH.exists():
    st.error(f"❌ ไม่พบไฟล์ฐานข้อมูลที่: {DB_PATH}")
    st.info("💡 กรุณารันคำสั่ง `cd movie_dw && dbt build` ใน Terminal ก่อนครับ")
    st.stop()

# เชื่อมต่อ DuckDB
try:
    conn = duckdb.connect(str(DB_PATH), read_only=True)
except Exception as e:
    st.error(f"❌ ไม่สามารถเชื่อมต่อ DuckDB ได้: {e}")
    st.stop()

# ฟังก์ชันรัน Query
def run_query(sql):
    try:
        return conn.execute(sql).fetchdf()
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการรัน Query: {e}")
        return None

# ดึงชื่อตารางจริงใน DuckDB (รองรับทั้ง fact_... และ fct_...)
try:
    all_tables = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
except Exception:
    all_tables = []

def get_table(possible_names):
    for p in possible_names:
        for real in all_tables:
            if p.lower() == real.lower():
                return real
    return possible_names[0]

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

# ----------------- Logic 15 Business Queries -----------------
if q_num == 1:
    st.subheader("1. รายได้รวมจากการขายตั๋วชมภาพยนตร์และสินค้าหน้าโรง ในแต่ละเดือนและไตรมาส")
    
    sql = f"""
    WITH ticket_monthly AS (
        SELECT 
            STRFTIME(STRPTIME(CAST(s.show_date AS VARCHAR), '%d/%m/%Y %H:%M'), '%Y-%m') AS month_key,
            'Q' || EXTRACT(QUARTER FROM STRPTIME(CAST(s.show_date AS VARCHAR), '%d/%m/%Y %H:%M')) AS quarter_key,
            SUM(t.final_price) AS ticket_rev
        FROM {ticket_table} t
        JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
        GROUP BY 1, 2
    ),
    concession_monthly AS (
        SELECT 
            STRFTIME(CAST(sale_date AS DATE), '%Y-%m') AS month_key,
            SUM(total_price) AS concession_rev
        FROM {concession_table}
        GROUP BY 1
    )
    SELECT 
        tm.month_key AS "เดือน (Year-Month)",
        tm.quarter_key AS "ไตรมาส (Quarter)",
        tm.ticket_rev AS "รายได้ขายตั๋ว (บาท)",
        COALESCE(cm.concession_rev, 0) AS "รายได้สินค้าหน้าโรง (บาท)",
        (tm.ticket_rev + COALESCE(cm.concession_rev, 0)) AS "รายได้รวมทั้งหมด (บาท)"
    FROM ticket_monthly tm
    LEFT JOIN concession_monthly cm ON tm.month_key = cm.month_key
    ORDER BY tm.month_key
    """
    
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        st.info("📌 **หมายเหตุการวิเคราะห์:** เนื่องจากชุดข้อมูลทดสอบ (Seed Data) มีบันทึกธุรกรรมครอบคลุมเฉพาะช่วงเดือนสิงหาคม 2026 (Q3) ระบบจึงแสดงผลสรุปรายได้รวมของไตรมาส 3 (Q3-2026) จำนวน 1 เดือนตามข้อมูลจริงใน Database")

elif q_num == 2:
    st.subheader("2. ภาพยนตร์เรื่องใดสร้างรายได้รวมและจำนวนตั๋วสูงที่สุด")
    sql = f"""
    SELECT 
        m.title AS "ชื่อภาพยนตร์",
        m.genre AS "ประเภท",
        COUNT(t.ticket_id) AS "จำนวนตั๋วที่ขายได้",
        SUM(t.final_price) AS "รายได้รวม (บาท)"
    FROM {ticket_table} t
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    JOIN {movie_table} m ON s.movie_id = m.movie_id
    GROUP BY 1, 2
    ORDER BY "รายได้รวม (บาท)" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("ชื่อภาพยนตร์")["รายได้รวม (บาท)"])

elif q_num == 3:
    st.subheader("3. ช่วงเวลาการฉาย (Time Slot) ใดมีผู้เข้าชมและสร้างรายได้มากที่สุด")
    sql = f"""
    SELECT 
        CASE 
            WHEN EXTRACT(HOUR FROM STRPTIME(CAST(s.show_date AS VARCHAR), '%d/%m/%Y %H:%M')) BETWEEN 6 AND 11 THEN 'Morning (06:00-11:59)'
            WHEN EXTRACT(HOUR FROM STRPTIME(CAST(s.show_date AS VARCHAR), '%d/%m/%Y %H:%M')) BETWEEN 12 AND 16 THEN 'Afternoon (12:00-16:59)'
            WHEN EXTRACT(HOUR FROM STRPTIME(CAST(s.show_date AS VARCHAR), '%d/%m/%Y %H:%M')) BETWEEN 17 AND 21 THEN 'Evening (17:00-21:59)'
            ELSE 'Night/Late (22:00-05:59)'
        END AS "ช่วงเวลา",
        COUNT(t.ticket_id) AS "จำนวนตั๋ว",
        SUM(t.final_price) AS "รายได้รวม (บาท)"
    FROM {ticket_table} t
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    GROUP BY 1
    ORDER BY "รายได้รวม (บาท)" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("ช่วงเวลา")["รายได้รวม (บาท)"])

elif q_num == 4:
    st.subheader("4. สมาชิกแต่ละระดับ (Member Tier) สร้างรายได้รวมเท่าใด")
    sql = f"""
    SELECT 
        COALESCE(c.member_tier, 'Non-Member') AS "ระดับสมาชิก",
        COUNT(DISTINCT t.customer_id) AS "จำนวนลูกค้า",
        COUNT(t.ticket_id) AS "จำนวนตั๋ว",
        SUM(t.final_price) AS "รายได้จากตั๋ว (บาท)"
    FROM {ticket_table} t
    LEFT JOIN {customer_table} c ON t.customer_id = c.customer_id
    GROUP BY 1
    ORDER BY "รายได้จากตั๋ว (บาท)" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("ระดับสมาชิก")["รายได้จากตั๋ว (บาท)"])

elif q_num == 5:
    st.subheader("5. สินค้าหน้าโรง (Concession) รายการใดขายดีที่สุด")
    sql = f"""
    SELECT 
        item_name AS "ชื่อสินค้า",
        SUM(quantity) AS "จำนวนที่ขายได้ (ชิ้น)",
        SUM(total_price) AS "ยอดขายรวม (บาท)"
    FROM {concession_table}
    GROUP BY 1
    ORDER BY "ยอดขายรวม (บาท)" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("ชื่อสินค้า")["ยอดขายรวม (บาท)"])

elif q_num == 6:
    st.subheader("6. ประเภทที่นั่ง (Seat Type) แบบใดทำรายได้สูงที่สุด")
    sql = f"""
    SELECT 
        seat_type AS "ประเภทที่นั่ง",
        COUNT(ticket_id) AS "จำนวนตั๋ว",
        SUM(final_price) AS "รายได้รวม (บาท)"
    FROM {ticket_table}
    GROUP BY 1
    ORDER BY "รายได้รวม (บาท)" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("ประเภทที่นั่ง")["รายได้รวม (บาท)"])

elif q_num == 7:
    st.subheader("7. ภาพยนตร์หมวดหมู่ (Genre) ใดได้รับความนิยมสูงสุด")
    sql = f"""
    SELECT 
        m.genre AS "หมวดหมู่ภาพยนตร์",
        COUNT(t.ticket_id) AS "ตั๋วที่ขายได้",
        SUM(t.final_price) AS "รายได้รวม (บาท)"
    FROM {ticket_table} t
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    JOIN {movie_table} m ON s.movie_id = m.movie_id
    GROUP BY 1
    ORDER BY "ตั๋วที่ขายได้" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("หมวดหมู่ภาพยนตร์")["ตั๋วที่ขายได้"])

elif q_num == 8:
    st.subheader("8. สัดส่วนรายได้ตามระดับสมาชิกในแต่ละไตรมาส")
    sql = f"""
    SELECT 
        COALESCE(c.member_tier, 'Non-Member') AS "ระดับสมาชิก",
        'Q' || EXTRACT(QUARTER FROM STRPTIME(CAST(s.show_date AS VARCHAR), '%d/%m/%Y %H:%M')) AS "ไตรมาส",
        SUM(t.final_price) AS "รายได้ (บาท)"
    FROM {ticket_table} t
    LEFT JOIN {customer_table} c ON t.customer_id = c.customer_id
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    GROUP BY 1, 2
    ORDER BY "ไตรมาส", "รายได้ (บาท)" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 9:
    st.subheader("9. โรงภาพยนตร์ (Screen Number) ใดมีอัตราการขายตั๋วสูงสุด")
    sql = f"""
    SELECT 
        s.screen_number AS "หมายเลขโรงภาพยนตร์",
        COUNT(t.ticket_id) AS "จำนวนตั๋วที่ขายได้",
        SUM(t.final_price) AS "รายได้รวม (บาท)"
    FROM {ticket_table} t
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    GROUP BY 1
    ORDER BY "จำนวนตั๋วที่ขายได้" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("หมายเลขโรงภาพยนตร์")["จำนวนตั๋วที่ขายได้"])

elif q_num == 10:
    st.subheader("10. ราคาตั๋วเฉลี่ยและรายได้ต่อลูกค้า (ARPU) แยกตามระดับสมาชิก")
    sql = f"""
    SELECT 
        COALESCE(c.member_tier, 'Non-Member') AS "ระดับสมาชิก",
        COUNT(DISTINCT t.customer_id) AS "จำนวนลูกค้า",
        ROUND(AVG(t.final_price), 2) AS "ราคาตั๋วเฉลี่ย (บาท)",
        ROUND(SUM(t.final_price) / COUNT(DISTINCT t.customer_id), 2) AS "รายได้เฉลี่ยต่อคน (ARPU)"
    FROM {ticket_table} t
    LEFT JOIN {customer_table} c ON t.customer_id = c.customer_id
    GROUP BY 1
    ORDER BY "รายได้เฉลี่ยต่อคน (ARPU)" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 11:
    st.subheader("11. ความสัมพันธ์ระหว่างความยาวหนัง (Duration) กับยอดขายตั๋ว")
    sql = f"""
    SELECT 
        m.title AS "ชื่อภาพยนตร์",
        m.duration_min AS "ความยาว (นาที)",
        COUNT(t.ticket_id) AS "จำนวนตั๋วที่ขายได้",
        SUM(t.final_price) AS "รายได้รวม (บาท)"
    FROM {ticket_table} t
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    JOIN {movie_table} m ON s.movie_id = m.movie_id
    GROUP BY 1, 2
    ORDER BY m.duration_min DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 12:
    st.subheader("12. การเปรียบเทียบยอดขายสินค้าหน้าโรง กับ ยอดขายตั๋วภาพยนตร์")
    sql = f"""
    SELECT 
        'Ticket Sales' AS "ประเภทรายได้",
        SUM(final_price) AS "รายได้รวม (บาท)"
    FROM {ticket_table}
    UNION ALL
    SELECT 
        'Concession Sales' AS "ประเภทรายได้",
        SUM(total_price) AS "รายได้รวม (บาท)"
    FROM {concession_table}
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("ประเภทรายได้")["รายได้รวม (บาท)"])

elif q_num == 13:
    st.subheader("13. การกระจายตัวของเรตติ้งภาพยนตร์ (Rating) และรายได้")
    sql = f"""
    SELECT 
        m.rating AS "เรตติ้งภาพยนตร์",
        COUNT(DISTINCT m.movie_id) AS "จำนวนเรื่อง",
        COUNT(t.ticket_id) AS "จำนวนตั๋วที่ขายได้",
        SUM(t.final_price) AS "รายได้รวม (บาท)"
    FROM {ticket_table} t
    JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
    JOIN {movie_table} m ON s.movie_id = m.movie_id
    GROUP BY 1
    ORDER BY "รายได้รวม (บาท)" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 14:
    st.subheader("14. ลูกค้า Top 10 ที่มียอดใช้จ่ายสูงสุดรวมทุกบริการ")
    sql = f"""
    WITH customer_tickets AS (
        SELECT customer_id, SUM(final_price) AS ticket_spend
        FROM {ticket_table}
        GROUP BY 1
    ),
    customer_concession AS (
        SELECT customer_id, SUM(total_price) AS concession_spend
        FROM {concession_table}
        GROUP BY 1
    )
    SELECT 
        c.customer_id AS "ID ลูกค้า",
        c.first_name || ' ' || c.last_name AS "ชื่อลูกค้า",
        c.member_tier AS "ระดับสมาชิก",
        COALESCE(ct.ticket_spend, 0) AS "ยอดซื้อตั๋ว (บาท)",
        COALESCE(cc.concession_spend, 0) AS "ยอดซื้อสินค้า (บาท)",
        (COALESCE(ct.ticket_spend, 0) + COALESCE(cc.concession_spend, 0)) AS "ยอดใช้จ่ายรวม (บาท)"
    FROM {customer_table} c
    LEFT JOIN customer_tickets ct ON c.customer_id = ct.customer_id
    LEFT JOIN customer_concession cc ON c.customer_id = cc.customer_id
    ORDER BY "ยอดใช้จ่ายรวม (บาท)" DESC
    LIMIT 10
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

elif q_num == 15:
    st.subheader("15. ความสัมพันธ์วันหยุด/วันทำงาน กับการซื้อสินค้าหน้าโรง")
    sql = f"""
    WITH parsed_sales AS (
        SELECT 
            item_name,
            total_price,
            quantity,
            COALESCE(
                TRY_STRPTIME(CAST(sale_date AS VARCHAR), '%d/%m/%Y %H:%M'),
                TRY_STRPTIME(CAST(sale_date AS VARCHAR), '%d/%m/%Y'),
                TRY_CAST(sale_date AS TIMESTAMP)
            ) AS clean_date
        FROM {concession_table}
    )
    SELECT 
        CASE 
            WHEN DAYNAME(clean_date) IN ('Saturday', 'Sunday') THEN 'Weekend' 
            ELSE 'Weekday' 
        END AS "ประเภทวัน",
        item_name AS "ชื่อสินค้า",
        SUM(quantity) AS "จำนวน (ชิ้น)",
        SUM(total_price) AS "ยอดขายรวม (บาท)"
    FROM parsed_sales
    GROUP BY 1, 2
    ORDER BY "ประเภทวัน", "ยอดขายรวม (บาท)" DESC
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)
        if not df.empty:
            st.bar_chart(df.set_index("ชื่อสินค้า")["ยอดขายรวม (บาท)"])