import os
from pathlib import Path
import duckdb
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cinema Analytics Dashboard", layout="wide")
st.title("🎬 Cinema Data Analytics - 15 Business Insights")

# ----------------- Database Connection -----------------
PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / "movie_dw" / "dev.duckdb"

if not DB_PATH.exists():
    DB_PATH = PROJECT_ROOT / "dev.duckdb"

if not DB_PATH.exists():
    st.error(f"❌ ไม่พบไฟล์ฐานข้อมูลที่: {DB_PATH}")
    st.info("💡 กรุณารันคำสั่ง `cd movie_dw && dbt build` ใน Terminal ก่อนครับ")
    st.stop()

try:
    conn = duckdb.connect(str(DB_PATH), read_only=True)
except Exception as e:
    st.error(f"❌ ไม่สามารถเชื่อมต่อ DuckDB ได้: {e}")
    st.stop()

def run_query(sql):
    try:
        return conn.execute(sql).fetchdf()
    except Exception as e:
        st.error(f"❌ เกิดข้อผิดพลาดในการรัน Query: {e}")
        return None

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

# Mapping Table Names
ticket_table = get_table(['fact_ticket_sales', 'fct_ticket_sales', 'stg_ticket_sales', 'ticket_sales'])
movie_table = get_table(['dim_movies', 'stg_movies', 'movies'])
customer_table = get_table(['dim_customers', 'stg_customers', 'customers'])
showtime_table = get_table(['dim_showtimes', 'stg_showtimes', 'showtimes'])
concession_table = get_table(['fact_concession_sales', 'fct_concession_sales', 'stg_concession_sales', 'concession_sales'])
date_table = get_table(['dim_dates', 'dim_date', 'date_dim'])

# ----------------- รายการคำถามธุรกิจ -----------------
questions = [
    "1. รายได้รวมตั๋ว+สินค้าหน้าโรง ในแต่ละเดือน/ไตรมาส",
    "2. ภาพยนตร์ที่สร้างรายได้และยอดขายตั๋วสูงสุด",
    "3. ช่วงเวลาการฉาย (Time Slot) ที่ทำรายได้สูงสุด",
    "4. รายได้แบ่งตามระดับสมาชิก (Member Tier)",
    "5. สินค้า Concession ที่ขายดีที่สุด (รายได้)",
    "6. ประเภทที่นั่ง (Seat Type) ที่ทำรายได้สูงสุด",
    "7. หมวดหมู่ภาพยนตร์ (Genre) ที่ได้รับความนิยมสูงสุด",
    "8. สัดส่วนรายได้ตามระดับสมาชิกในแต่ละไตรมาส",
    "9. โรงภาพยนตร์ (Screen Number) ที่มียอดขายตั๋วสูงสุด",
    "10. ราคาตั๋วเฉลี่ยและรายได้ต่อลูกค้า (ARPU) ตามระดับสมาชิก",
    "11. ความสัมพันธ์ระหว่างความยาวหนัง (Duration) กับยอดขายตั๋ว",
    "12. การเปรียบเทียบยอดขายสินค้าหน้าโรง กับ ยอดขายตั๋ว",
    "13. การกระจายตัวของเรตติ้งภาพยนตร์ (Rating) และรายได้",
    "14. ลูกค้า Top 10 ที่มียอดใช้จ่ายสูงสุดรวมทุกบริการ",
    "15. ความสัมพันธ์วันหยุด/วันทำงาน กับการซื้อสินค้า Concession"
]

selected_q = st.selectbox("🎯 เลือกข้อคำถามธุรกิจที่ต้องการดูผลลัพธ์:", questions)
st.divider()

q_num = int(selected_q.split(".")[0])

# ----------------- SQL Logic (Pure DW / Star Schema) -----------------

if q_num == 1:
    st.subheader("1. รายได้รวมจากการขายตั๋วชมภาพยนตร์และสินค้าหน้าโรง ในแต่ละเดือนและไตรมาส")
    sql = f"""
    WITH combined_sales AS (
        SELECT 
            STRFTIME(TRY_CAST(s.show_date AS TIMESTAMP), '%Y-%m') AS month_key,
            'Q' || EXTRACT(QUARTER FROM TRY_CAST(s.show_date AS TIMESTAMP)) AS quarter_key,
            t.final_price AS ticket_amount,
            0 AS concession_amount
        FROM {ticket_table} t
        JOIN {showtime_table} s ON t.showtime_id = s.showtime_id
        
        UNION ALL
        
        SELECT 
            STRFTIME(TRY_CAST(sale_date AS TIMESTAMP), '%Y-%m') AS month_key,
            'Q' || EXTRACT(QUARTER FROM TRY_CAST(sale_date AS TIMESTAMP)) AS quarter_key,
            0 AS ticket_amount,
            total_price AS concession_amount
        FROM {concession_table}
    )
    SELECT 
        month_key AS "เดือน (Year-Month)",
        quarter_key AS "ไตรมาส (Quarter)",
        SUM(ticket_amount) AS "รายได้ขายตั๋ว (บาท)",
        SUM(concession_amount) AS "รายได้สินค้าหน้าโรง (บาท)",
        SUM(ticket_amount + concession_amount) AS "รายได้รวมทั้งหมด (บาท)"
    FROM combined_sales
    GROUP BY 1, 2
    ORDER BY month_key
    """
    df = run_query(sql)
    if df is not None:
        st.dataframe(df, use_container_width=True)

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
            WHEN EXTRACT(HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP)) BETWEEN 6 AND 11 THEN 'Morning (06:00-11:59)'
            WHEN EXTRACT(HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP)) BETWEEN 12 AND 16 THEN 'Afternoon (12:00-16:59)'
            WHEN EXTRACT(HOUR FROM TRY_CAST(s.show_date AS TIMESTAMP)) BETWEEN 17 AND 21 THEN 'Evening (17:00-21:59)'
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
        'Q' || EXTRACT(QUARTER FROM TRY_CAST(s.show_date AS TIMESTAMP)) AS "ไตรมาส",
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
    st.subheader("15. ความสัมพันธ์วันหยุด/วันทำงาน กับการซื้อสินค้าหน้าโรง (Concession)")
    
    sql = f"""
    WITH split_date AS (
        SELECT 
            item_name,
            total_price,
            -- ดึงวัน เดือน ปี ออกมาจาก Text โดยตรง (รองรับทั้ง 1/8/2026 และ 2026-08-01)
            CAST(SPLIT_PART(CAST(sale_date AS VARCHAR), '/', 1) AS INT) AS d,
            CAST(SPLIT_PART(CAST(sale_date AS VARCHAR), '/', 2) AS INT) AS m,
            CAST(SPLIT_PART(SPLIT_PART(CAST(sale_date AS VARCHAR), '/', 3), ' ', 1) AS INT) AS y
        FROM {concession_table}
    ),
    calculated_dow AS (
        SELECT 
            item_name,
            total_price,
            -- สูตร Zeller's congruence คำนวณวันในสัปดาห์ (0=Saturday, 1=Sunday)
            (
                d + 
                ((13 * (CASE WHEN m <= 2 THEN m + 12 ELSE m END + 1)) / 5) + 
                ((CASE WHEN m <= 2 THEN y - 1 ELSE y END) % 100) + 
                (((CASE WHEN m <= 2 THEN y - 1 ELSE y END) % 100) / 4) + 
                (((CASE WHEN m <= 2 THEN y - 1 ELSE y END) / 100) / 4) + 
                (5 * ((CASE WHEN m <= 2 THEN y - 1 ELSE y END) / 100))
            ) % 7 AS dow
        FROM split_date
    )
    SELECT 
        item_name AS "สินค้า",
        SUM(CASE 
            WHEN dow IN (0, 1) THEN total_price 
            ELSE 0 
        END) AS "ยอดขาย Weekend (บาท)",
        SUM(CASE 
            WHEN dow NOT IN (0, 1) THEN total_price 
            ELSE 0 
        END) AS "ยอดขาย Weekday (บาท)",
        SUM(total_price) AS "ยอดขายรวมทั้งหมด (บาท)"
    FROM calculated_dow
    GROUP BY 1
    ORDER BY "ยอดขายรวมทั้งหมด (บาท)" DESC
    """
    df = run_query(sql)
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True)
        st.bar_chart(df.set_index("สินค้า")[["ยอดขาย Weekday (บาท)", "ยอดขาย Weekend (บาท)"]])