import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="Cinema DW Executive Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. Custom CSS styling ---
st.markdown("""
    <style>
    /* Global background & text */
    .main {
        background-color: #0F172A;
    }
    
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        transition: transform 0.2s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #38BDF8;
    }
    div[data-testid="stMetric"] label {
        color: #94A3B8 !important;
        font-size: 0.9rem !important;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #F8FAFC !important;
        font-size: 2rem !important;
        font-weight: 800;
    }

    /* Container Spacing */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        background-color: #1E293B;
        color: #94A3B8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0284C7 !important;
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_file_path(target_keywords):
    """ค้นหาไฟล์ CSV อัตโนมัติจากคำสำคัญ"""
    for root, dirs, files in os.walk(BASE_DIR):
        for f in files:
            if f.endswith('.csv'):
                for kw in target_keywords:
                    if kw in f.lower():
                        return os.path.join(root, f)
    return None

@st.cache_resource
def load_data_to_sqlite():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    
    schema_mapping = {
        "fact_ticket_sales": ["ticket_sales_5000", "ticket_sales_large", "ticket_sales"],
        "fact_concession_sales": ["concession_sales_large", "concession_sales"],
        "dim_showtimes": ["showtimes_large", "showtimes"],
        "dim_customers": ["customers"],
        "dim_movies": ["movies"]
    }
    
    missing_tables = []
    for table_name, keywords in schema_mapping.items():
        file_path = get_file_path(keywords)
        if file_path:
            df = pd.read_csv(file_path)
            df.to_sql(table_name, conn, index=False, if_exists="replace")
        else:
            missing_tables.append(table_name)
            
    if missing_tables:
        raise FileNotFoundError(f"ไม่พบไฟล์ข้อมูลสำหรับตาราง: {', '.join(missing_tables)}")
        
    return conn

try:
    conn = load_data_to_sqlite()
except Exception as e:
    st.error(f"❌ โหลดข้อมูลไม่สำเร็จ: {e}")
    st.stop()

def run_query(sql):
    try:
        return pd.read_sql_query(sql, conn)
    except Exception as err:
        st.error(f"SQL Error: {err}")
        return None

# --- Header Banner ---
st.title("🎬 Cinema Data Analytics Platform")
st.caption("⚡ Interactive Executive Dashboard • Powered by Data Warehouse")

# --- Executive Top KPI Cards ---
kpi_df1 = run_query("SELECT SUM(final_price) FROM fact_ticket_sales;")
kpi_df2 = run_query("SELECT SUM(total_price) FROM fact_concession_sales;")
kpi_df3 = run_query("SELECT COUNT(ticket_id) FROM fact_ticket_sales;")

ticket_rev = kpi_df1.iloc[0,0] if kpi_df1 is not None else 0
concess_rev = kpi_df2.iloc[0,0] if kpi_df2 is not None else 0
total_tickets = kpi_df3.iloc[0,0] if kpi_df3 is not None else 0

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("🍿 รายได้รวมทั้งหมด", f"฿{(ticket_rev + concess_rev):,.0f}")
with c2:
    st.metric("🎟️ รายได้ตั๋วหนัง", f"฿{ticket_rev:,.0f}")
with c3:
    st.metric("🥤 รายได้ Concession", f"฿{concess_rev:,.0f}")
with c4:
    st.metric("🎟️ จำนวนตั๋วที่ขายได้", f"{total_tickets:,.0f} ใบ")

st.divider()

# --- Sidebar Controls ---
st.sidebar.header("🎯 Navigation & Analysis")
analysis_mode = st.sidebar.radio("มุมมองข้อมูล:", ["📊 Overview Dashboard", "🔎 Deep-Dive Query Analysis"])

# --- Helper Function for Clean Charts ---
def create_chart_layout(fig):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94A3B8"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig

# --- MODE 1: Overview Dashboard ---
if analysis_mode == "📊 Overview Dashboard":
    col_left, col_right = st.columns(2)
    
    with col_left:
        # Chart 1: Top Movies Revenue
        sql = """
        SELECT m.title AS Movie, SUM(t.final_price) AS Revenue
        FROM fact_ticket_sales t
        JOIN dim_showtimes s ON t.showtime_id = s.showtime_id
        JOIN dim_movies m ON s.movie_id = m.movie_id
        GROUP BY m.title ORDER BY Revenue DESC LIMIT 5;
        """
        df = run_query(sql)
        if df is not None:
            fig = px.bar(df, x="Revenue", y="Movie", orientation='h', title="🏆 Top 5 Movies by Revenue",
                         color_discrete_sequence=["#38BDF8"], text_auto=",.0f")
            fig.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(create_chart_layout(fig), use_container_width=True)

        # Chart 2: Revenue by Time Slot
        sql = """
        SELECT 
            CASE 
                WHEN CAST(substr(s.show_date, instr(s.show_date, ' ') + 1, instr(substr(s.show_date, instr(s.show_date, ' ') + 1), ':') - 1) AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning'
                WHEN CAST(substr(s.show_date, instr(s.show_date, ' ') + 1, instr(substr(s.show_date, instr(s.show_date, ' ') + 1), ':') - 1) AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon'
                ELSE 'Evening'
            END AS Time_Slot,
            SUM(t.final_price) AS Revenue
        FROM fact_ticket_sales t
        JOIN dim_showtimes s ON t.showtime_id = s.showtime_id
        GROUP BY 1 ORDER BY Revenue DESC;
        """
        df = run_query(sql)
        if df is not None:
            fig = px.pie(df, names="Time_Slot", values="Revenue", title="⏰ Revenue Share by Time Slot",
                         hole=0.4, color_discrete_sequence=px.colors.sequential.Darkmint)
            st.plotly_chart(create_chart_layout(fig), use_container_width=True)

    with col_right:
        # Chart 3: Member Tier Revenue
        sql = """
        SELECT 
            CASE WHEN c.member_tier IS NULL OR c.member_tier = '' THEN 'Non-Member' ELSE c.member_tier END AS Tier,
            SUM(t.final_price) AS Revenue
        FROM fact_ticket_sales t
        JOIN dim_customers c ON t.customer_id = c.customer_id
        GROUP BY 1 ORDER BY Revenue DESC;
        """
        df = run_query(sql)
        if df is not None:
            fig = px.bar(df, x="Tier", y="Revenue", title="💎 Revenue Breakdown by Member Tier",
                         color="Tier", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(create_chart_layout(fig), use_container_width=True)

        # Chart 4: Concession Categories
        sql = """
        SELECT 
            CASE 
                WHEN item_name LIKE '%Popcorn%' THEN 'Popcorn'
                WHEN item_name LIKE '%Soda%' OR item_name LIKE '%Water%' THEN 'Beverage'
                WHEN item_name LIKE '%Combo%' THEN 'Combo Set'
                ELSE 'Other'
            END AS Category,
            SUM(total_price) AS Revenue
        FROM fact_concession_sales
        GROUP BY 1 ORDER BY Revenue DESC;
        """
        df = run_query(sql)
        if df is not None:
            fig = px.pie(df, names="Category", values="Revenue", title="🍿 Concession Revenue Distribution",
                         hole=0.4, color_discrete_sequence=px.colors.sequential.Plasma)
            st.plotly_chart(create_chart_layout(fig), use_container_width=True)

# --- MODE 2: Deep-Dive Query Analysis ---
else:
    question_option = st.sidebar.selectbox(
        "เลือกคำถามเชิงลึก (1-15):",
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
            "15. รายได้รวมตามหมวดหมู่ Concession"
        ]
    )

    def render_detail_analytics(title, sql, x_col=None, y_col=None, chart_type="bar", is_metric=False, metric_label=""):
        st.subheader(title)
        df = run_query(sql)
        
        if df is not None and not df.empty:
            if is_metric:
                val = df.iloc[0, 0]
                st.metric(metric_label, f"฿{val:,.2f}")
                st.divider()
                st.dataframe(df, use_container_width=True)
            else:
                t1, t2 = st.tabs(["📊 Interactive Chart", "📋 Raw Data Table"])
                with t1:
                    if chart_type == "bar":
                        fig = px.bar(df, x=x_col, y=y_col, text_auto=",.0f", color_discrete_sequence=["#38BDF8"])
                    elif chart_type == "pie":
                        fig = px.pie(df, names=x_col, values=y_col, hole=0.4, color_discrete_sequence=px.colors.qualitative.Bold)
                    st.plotly_chart(create_chart_layout(fig), use_container_width=True)
                with t2:
                    st.dataframe(df, use_container_width=True)

    # Dispatcher Logic
    if question_option.startswith("1."):
        render_detail_analytics("1. รายได้รวมจากการขายตั๋วภาพยนตร์ทั้งหมด", "SELECT SUM(final_price) AS 'รายได้รวมตั๋ว (บาท)' FROM fact_ticket_sales;", is_metric=True, metric_label="Total Ticket Revenue")
    elif question_option.startswith("2."):
        sql = """SELECT CASE WHEN CAST(substr(s.show_date, instr(s.show_date, ' ') + 1, instr(substr(s.show_date, instr(s.show_date, ' ') + 1), ':') - 1) AS INTEGER) BETWEEN 6 AND 11 THEN 'Morning (06:00-11:59)' WHEN CAST(substr(s.show_date, instr(s.show_date, ' ') + 1, instr(substr(s.show_date, instr(s.show_date, ' ') + 1), ':') - 1) AS INTEGER) BETWEEN 12 AND 16 THEN 'Afternoon (12:00-16:59)' ELSE 'Evening (17:00-23:59)' END AS Time_Slot, SUM(t.final_price) AS 'รายได้รวม (บาท)' FROM fact_ticket_sales t JOIN dim_showtimes s ON t.showtime_id = s.showtime_id GROUP BY 1 ORDER BY 2 DESC;"""
        render_detail_analytics("2. รายได้ตามช่วงเวลา (Time Slot)", sql, "Time_Slot", "รายได้รวม (บาท)")
    elif question_option.startswith("3."):
        sql = "SELECT (SELECT SUM(total_price) FROM fact_concession_sales) * 1.0 / COUNT(ticket_id) AS 'Spend Per Head (บาท/คน)' FROM fact_ticket_sales;"
        render_detail_analytics("3. ยอดซื้อ Concession เฉลี่ยต่อผู้เข้าชม (Spend Per Head)", sql, is_metric=True, metric_label="Concession Spend Per Head")
    elif question_option.startswith("4."):
        sql = "WITH totals AS (SELECT (SELECT SUM(final_price) FROM fact_ticket_sales) AS ticket_rev, (SELECT SUM(total_price) FROM fact_concession_sales) AS concession_rev) SELECT 'Ticket Revenue' AS Category, ticket_rev AS 'Revenue (THB)', ROUND(ticket_rev * 100.0 / (ticket_rev + concession_rev), 2) AS 'Percentage (%)' FROM totals UNION ALL SELECT 'Concession Revenue' AS Category, concession_rev AS 'Revenue (THB)', ROUND(concession_rev * 100.0 / (ticket_rev + concession_rev), 2) AS 'Percentage (%)' FROM totals;"
        render_detail_analytics("4. สัดส่วนรายได้ ตั๋ว vs Concession (%)", sql, "Category", "Percentage (%)", chart_type="pie")
    elif question_option.startswith("5."):
        render_detail_analytics("5. ราคาตั๋วเฉลี่ยต่อใบ", "SELECT AVG(final_price) AS 'ราคาตั๋วเฉลี่ย (บาท/ใบ)' FROM fact_ticket_sales;", is_metric=True, metric_label="Average Ticket Price")
    elif question_option.startswith("6."):
        sql = "SELECT m.title AS 'ชื่อภาพยนตร์', SUM(t.final_price) AS 'รายได้รวม (บาท)' FROM fact_ticket_sales t JOIN dim_showtimes s ON t.showtime_id = s.showtime_id JOIN dim_movies m ON s.movie_id = m.movie_id GROUP BY m.title ORDER BY 2 DESC LIMIT 5;"
        render_detail_analytics("6. Top 5 ภาพยนตร์ทำรายได้สูงสุด", sql, "ชื่อภาพยนตร์", "รายได้รวม (บาท)")
    elif question_option.startswith("7."):
        sql = "SELECT m.genre AS 'หมวดหมู่ภาพยนตร์', SUM(t.final_price) AS 'รายได้รวม (บาท)' FROM fact_ticket_sales t JOIN dim_showtimes s ON t.showtime_id = s.showtime_id JOIN dim_movies m ON s.movie_id = m.movie_id GROUP BY m.genre ORDER BY 2 DESC;"
        render_detail_analytics("7. หมวดหมู่ภาพยนตร์ (Genre) ที่ทำรายได้สูงสุด", sql, "หมวดหมู่ภาพยนตร์", "รายได้รวม (บาท)")
    elif question_option.startswith("8."):
        sql = "SELECT m.rating AS 'Rating', SUM(t.final_price) AS 'รายได้รวม (บาท)' FROM fact_ticket_sales t JOIN dim_showtimes s ON t.showtime_id = s.showtime_id JOIN dim_movies m ON s.movie_id = m.movie_id GROUP BY m.rating ORDER BY 2 DESC;"
        render_detail_analytics("8. รายได้รวมตามระดับความเหมาะสม (Rating)", sql, "Rating", "รายได้รวม (บาท)", chart_type="pie")
    elif question_option.startswith("9."):
        sql = "SELECT 'Screen ' || s.screen_number AS 'โรงฉาย', SUM(t.final_price) AS 'รายได้รวม (บาท)' FROM fact_ticket_sales t JOIN dim_showtimes s ON t.showtime_id = s.showtime_id GROUP BY s.screen_number ORDER BY 2 DESC;"
        render_detail_analytics("9. โรงฉาย (Screen Number) ที่ทำรายได้สูงสุด", sql, "โรงฉาย", "รายได้รวม (บาท)")
    elif question_option.startswith("10."):
        sql = "SELECT CASE WHEN c.member_tier IS NULL OR c.member_tier = '' THEN 'General (Non-Member)' ELSE c.member_tier END AS 'ระดับสมาชิก', SUM(t.final_price) AS 'ยอดซื้อตั๋วรวม (บาท)' FROM fact_ticket_sales t JOIN dim_customers c ON t.customer_id = c.customer_id GROUP BY 1 ORDER BY 2 DESC;"
        render_detail_analytics("10. ยอด Spending รวมตามสมาชิกระดับต่างๆ", sql, "ระดับสมาชิก", "ยอดซื้อตั๋วรวม (บาท)")
    elif question_option.startswith("11."):
        sql = "SELECT CASE WHEN c.member_tier IS NULL OR c.member_tier = '' THEN 'General (Non-Member)' ELSE c.member_tier END AS 'ระดับสมาชิก', COUNT(t.ticket_id) AS 'จำนวนตั๋ว (ใบ)' FROM fact_ticket_sales t JOIN dim_customers c ON t.customer_id = c.customer_id GROUP BY 1 ORDER BY 2 DESC;"
        render_detail_analytics("11. จำนวนตั๋วรวม จำแนกตามระดับสมาชิก", sql, "ระดับสมาชิก", "จำนวนตั๋ว (ใบ)")
    elif question_option.startswith("12."):
        sql = "SELECT t.seat_type AS 'ประเภทที่นั่ง', COUNT(t.ticket_id) AS 'จำนวนตั๋วที่ซื้อ (ใบ)' FROM fact_ticket_sales t JOIN dim_customers c ON t.customer_id = c.customer_id WHERE c.member_tier = 'Platinum' GROUP BY t.seat_type ORDER BY 2 DESC;"
        render_detail_analytics("12. ประเภทที่นั่งที่ลูกค้าระดับ Platinum นิยมซื้อ", sql, "ประเภทที่นั่ง", "จำนวนตั๋วที่ซื้อ (ใบ)")
    elif question_option.startswith("13."):
        sql = "SELECT seat_type AS 'ประเภทที่นั่ง', SUM(final_price) AS 'รายได้รวม (บาท)' FROM fact_ticket_sales GROUP BY seat_type ORDER BY 2 DESC;"
        render_detail_analytics("13. ประเภทที่นั่ง (Seat Type) ที่ทำรายได้สูงสุด", sql, "ประเภทที่นั่ง", "รายได้รวม (บาท)")
    elif question_option.startswith("14."):
        sql = "SELECT cs.item_name AS 'ชื่อสินค้า Concession', SUM(cs.quantity) AS 'จำนวนชิ้นรวม' FROM fact_concession_sales cs JOIN dim_customers c ON cs.customer_id = c.customer_id WHERE c.member_tier IN ('Gold', 'Platinum') GROUP BY cs.item_name ORDER BY 2 DESC;"
        render_detail_analytics("14. สินค้า Concession ที่นิยมของ Platinum & Gold", sql, "ชื่อสินค้า Concession", "จำนวนชิ้นรวม")
    elif question_option.startswith("15."):
        sql = "SELECT CASE WHEN item_name LIKE '%Popcorn%' THEN 'Popcorn' WHEN item_name LIKE '%Soda%' OR item_name LIKE '%Water%' THEN 'Beverage' WHEN item_name LIKE '%Combo%' THEN 'Combo Set' ELSE 'Other' END AS 'หมวดหมู่ Concession', SUM(total_price) AS 'รายได้รวม (บาท)' FROM fact_concession_sales GROUP BY 1 ORDER BY 2 DESC;"
        render_detail_analytics("15. รายได้รวมตามหมวดหมู่ Concession", sql, "หมวดหมู่ Concession", "รายได้รวม (บาท)", chart_type="pie")