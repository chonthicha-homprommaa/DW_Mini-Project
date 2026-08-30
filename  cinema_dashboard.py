import streamlit as st
import duckdb
import pandas as pd

st.set_page_config(
    page_title="Cinema Data Analytics Dashboard",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Cinema Data Analytics Dashboard")
st.caption("สรุปรายงานเชิงวิเคราะห์ข้อมูลโรงภาพยนตร์ 15 รายการ (dbt + DuckDB)")

# เชื่อมต่อกับ DuckDB
@st.cache_resource
def get_connection():
    return duckdb.connect("dev.duckdb")

conn = get_connection()

# โหลดคำสั่ง SQL จากไฟล์
@st.cache_data
def load_queries():
    with open("sql/analytical_queries.sql", "r", encoding="utf-8") as f:
        content = f.read()
    # แยกแต่ละ Query ด้วยเครื่องหมาย ;
    raw_queries = [q.strip() for q in content.split(";") if q.strip()]
    return raw_queries

queries = load_queries()

# หัวข้อรายงานทั้ง 15 ข้อ
titles = [
    "1. รายได้ตั๋วหนังตามวัน",
    "2. Top 5 หนังทำรายได้สูงสุด แยกตาม Genre",
    "3. รายได้ตั๋วหนังแยกตาม Time Slot",
    "4. Concession Spending Per Head",
    "5. ยอด Spending แยกตาม Member Tier",
    "6. ประเภทที่นั่งที่ลูกค้า Platinum นิยมซื้อ",
    "7. ยอดซื้อ Concession ของ Gold / Platinum",
    "8. ยอดขายตั๋วตามประเภทสมาชิกและวัน",
    "9. รายได้รวมแยกตาม Genre",
    "10. รายได้รวมแยกตาม Rating หนัง",
    "11. รายได้เฉลี่ยและรวมแยกตาม Screen Number",
    "12. ผลกระทบของหนังความยาว > 150 นาที",
    "13. สัดส่วนรายได้ (%) แยกตามประเภทที่นั่ง",
    "14. สินค้า Concession ขายดีที่สุด",
    "15. ความสัมพันธ์วันหยุด/วันทำงาน กับการซื้อ Combo Set"
]

# สร้าง Sidebar ให้เลือกดูรายข้อได้ หรือดูทั้งหมด
st.sidebar.header("📌 เมนูเลือกรายงาน")
view_option = st.sidebar.radio("รูปแบบการแสดงผล:", ["แสดงผลทั้งหมด (All 15)", "เลือกดูทีละหัวข้อ"])

if view_option == "แสดงผลทั้งหมด (All 15)":
    for idx, query in enumerate(queries):
        if idx < len(titles):
            st.header(titles[idx])
            try:
                df = conn.execute(query).fetchdf()
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.dataframe(df, use_container_width=True)
                with col2:
                    # แสดงกราฟแท่งอัตโนมัติหากมีคอลัมน์ตัวเลข
                    num_cols = df.select_dtypes(include=['number']).columns
                    if len(df) > 0 and len(num_cols) > 0:
                        st.bar_chart(df.set_index(df.columns[0])[num_cols[0]])
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการรัน Query ข้อที่ {idx+1}: {e}")
            st.divider()

else:
    selected_title = st.sidebar.selectbox("เลือกหัวข้อที่ต้องการ:", titles)
    idx = titles.index(selected_title)
    st.header(selected_title)
    
    try:
        df = conn.execute(queries[idx]).fetchdf()
        
        tab1, tab2 = st.tabs(["📊 ตารางข้อมูล", "📈 กราฟแสดงผล"])
        with tab1:
            st.dataframe(df, use_container_width=True)
        with tab2:
            num_cols = df.select_dtypes(include=['number']).columns
            if len(df) > 0 and len(num_cols) > 0:
                st.bar_chart(df.set_index(df.columns[0])[num_cols[0]])
            else:
                st.info("ไม่มีข้อมูลตัวเลขสำหรับสร้างกราฟ")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการรัน Query: {e}")