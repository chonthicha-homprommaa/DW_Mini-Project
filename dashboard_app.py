import os
from pathlib import Path

import altair as alt
import duckdb
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Movie DW OLAP Dashboard", layout="wide")

PROJECT_ROOT = Path(__file__).resolve().parent

def find_duckdb_path():
    candidates = [
        os.getenv("DUCKDB_PATH"),
        str(PROJECT_ROOT / "movie_dw" / "dev.duckdb"),
        str(PROJECT_ROOT / "movie_dw" / "target" / "dev.duckdb"),
        str(PROJECT_ROOT / "dev.duckdb"),
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None

def list_tables(con):
    return [
        row[0]
        for row in con.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        ).fetchall()
    ]

def resolve_table_name(tables, candidates):
    for candidate in candidates:
        for table in tables:
            if candidate.lower() in table.lower():
                return table
    return None

@st.cache_data
def load_data():
    db_path = find_duckdb_path()

    if db_path:
        try:
            con = duckdb.connect(db_path, read_only=True)
            tables = list_tables(con)

            fact_table = resolve_table_name(tables, ["fact_ticket", "fact_sales", "fact", "ticket_sales"])
            dim_movies = resolve_table_name(tables, ["dim_movie", "movie"])
            dim_showtime = resolve_table_name(tables, ["dim_showtime", "showtime"])

            if fact_table:
                df = con.execute(f"SELECT * FROM main.{fact_table}").fetchdf()

                # 1. JOIN กับ dim_movie เพื่อเอาชื่อเรื่องและประเภท
                if dim_movies and "movie_id" in df.columns:
                    try:
                        movies_df = con.execute(f"SELECT * FROM main.{dim_movies}").fetchdf()
                        movies_df.columns = [c.lower() for c in movies_df.columns]
                        rename_dict = {}
                        for c in movies_df.columns:
                            if "title" in c or "movie_name" in c or "name" in c:
                                rename_dict[c] = "product_name"
                            elif "genre" in c or "category" in c:
                                rename_dict[c] = "product_category"
                        movies_df = movies_df.rename(columns=rename_dict)
                        df = df.merge(movies_df, on="movie_id", how="left")
                    except Exception:
                        pass

                # 2. JOIN กับ dim_showtime เพื่อเอาวันที่และเวลาฉายจริง
                if dim_showtime and "showtime_id" in df.columns:
                    try:
                        st_df = con.execute(f"SELECT * FROM main.{dim_showtime}").fetchdf()
                        st_df.columns = [c.lower() for c in st_df.columns]
                        # หาคอลัมน์ที่เป็นวันที่/เวลาฉาย
                        st_date_col = [c for c in st_df.columns if "date" in c or "time" in c or "start" in c]
                        if st_date_col:
                            st_df = st_df.rename(columns={st_date_col[0]: "showtime_date"})
                            df = df.merge(st_df, on="showtime_id", how="left")
                    except Exception:
                        pass

                if not df.empty:
                    return enrich_dimensions(df)
        except Exception as e:
            st.warning(f"Error reading DuckDB: {e}")

    return pd.DataFrame()

def enrich_dimensions(df):
    # 1. ค้นหาราคา Revenue
    rev_col = None
    for c in df.columns:
        if any(k in c.lower() for k in ["revenue", "price", "amount", "total"]):
            rev_col = c
            break

    df["revenue"] = pd.to_numeric(df[rev_col], errors="coerce").fillna(0.0) if rev_col else 0.0

    # 2. จัดการ วันที่ (ใช้วันที่รอบฉาย หรือ วันที่สร้างข้อมูล)
    date_col = None
    for candidate in ["showtime_date", "show_date", "start_time", "sale_date", "insertion_timestamp", "order_date"]:
        if candidate in df.columns and df[candidate].notna().any():
            date_col = candidate
            break

    if date_col:
        df["order_date"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df["order_date"] = pd.Timestamp.now()

    # สร้าง Dimension มิติต่างๆ
    df["year"] = df["order_date"].dt.year.astype(str)
    df["quarter_label"] = "Q" + df["order_date"].dt.quarter.astype(str)
    df["month_name"] = df["order_date"].dt.strftime("%B")
    df["day_name"] = df["order_date"].dt.strftime("%A")
    df["day_type"] = (df["order_date"].dt.weekday < 5).map({True: "Weekday", False: "Weekend"})
    df["date_label"] = df["order_date"].dt.strftime("%Y-%m-%d")

    df["quantity"] = 1
    if "order_id" not in df.columns:
        df["order_id"] = df["ticket_id"] if "ticket_id" in df.columns else range(1, len(df) + 1)

    if "product_name" not in df.columns:
        df["product_name"] = df["movie_id"].apply(lambda x: f"Movie ID {x}" if pd.notna(x) else "Movie Ticket")
    if "product_category" not in df.columns:
        df["product_category"] = df["seat_type"] if "seat_type" in df.columns else "General"

    return df

def apply_filters(df):
    st.sidebar.header("Filters")
    for col in ["product_name", "product_category", "seat_type", "day_type"]:
        if col in df.columns:
            vals = sorted(df[col].dropna().astype(str).unique().tolist())
            if vals:
                selected = st.sidebar.multiselect(col.replace("_", " ").title(), vals, default=vals)
                df = df[df[col].astype(str).isin(selected)]
    return df

def main():
    st.title("Movie DW Sales OLAP Dashboard ")
    df = load_data()

    if df.empty:
        st.warning("No data found in DuckDB.")
        return

    df = apply_filters(df)

    rev = df["revenue"].sum()
    qty = df["quantity"].sum()
    orders = df["order_id"].nunique()

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Revenue", f"${rev:,.2f}")
    c2.metric("Tickets Sold", f"{qty:,.0f}")
    c3.metric("Transactions", f"{orders:,.0f}")

    st.sidebar.header("OLAP Views")
    
    # เพิ่มตัวเลือก มิติในการกระจายข้อมูล (Product Name / Seat Type / Category)
    dimension_option = st.sidebar.selectbox(
        "Group By Dimension", 
        ["product_name", "product_category", "seat_type", "day_type", "month_name", "date_label"],
        index=0
    )
    
    if dimension_option in df.columns:
        t_df = df.groupby(dimension_option, as_index=False)["revenue"].sum()
        st.subheader(f"Revenue by {dimension_option.replace('_', ' ').title()}")
        
        chart = alt.Chart(t_df).mark_bar().encode(
            x=alt.X(f"{dimension_option}:N", title=dimension_option.replace('_', ' ').title(), sort="-y"),
            y=alt.Y("revenue:Q", title="Revenue ($)"),
            color=alt.Color(f"{dimension_option}:N", legend=None),
            tooltip=[dimension_option, "revenue"]
        ).properties(height=400)
        
        st.altair_chart(chart, use_container_width=True)

    st.subheader("Detail Data")
    st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()