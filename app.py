import os
from pathlib import Path
import duckdb
import pandas as pd
import streamlit as st

# Page config
st.set_page_config(
    page_title="Kanokwan DW Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

PROJECT_ROOT = Path(__file__).resolve().parent

# Helper to find DuckDB automatically
def find_duckdb_path():
    candidates = [
        os.getenv("DUCKDB_PATH"),
        str(PROJECT_ROOT / "kanokwan_dw_duckdb" / "dev.duckdb"),
        str(PROJECT_ROOT / "movie_dw" / "dev.duckdb"),
        str(PROJECT_ROOT / "dev.duckdb"),
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None

DB_PATH = find_duckdb_path()

@st.cache_resource
def get_connection(path):
    if path:
        return duckdb.connect(path, read_only=True)
    return None

def run_query(query):
    if not DB_PATH:
        return pd.DataFrame()
    conn = get_connection(DB_PATH)
    try:
        return conn.execute(query).fetch_df()
    except Exception as e:
        st.error(f"Error running query: {e}")
        return pd.DataFrame()

# App Title & Style
st.markdown("""
    <style>
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1F2937;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📊MOVIE DW Explorer</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Inspect and preview raw datasets, staging tables, and dimension views in dev.duckdb</div>', unsafe_allow_html=True)

if not DB_PATH:
    st.error("❌ Database file (dev.duckdb) not found! Please make sure the database file exists.")
else:
    tables_df = run_query("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY table_name")
    tables = tables_df['table_name'].tolist() if not tables_df.empty else []

    if not tables:
        st.warning("No tables found in the database. Please make sure the dbt run was successful.")
    else:
        table_stats = []
        for t in tables:
            count_df = run_query(f"SELECT COUNT(*) as count FROM main.{t}")
            count = count_df['count'].iloc[0] if not count_df.empty else 0
            table_stats.append({"table_name": t, "row_count": count})
        
        stats_df = pd.DataFrame(table_stats)
        
        st.sidebar.title("🗂️ Table Browser")
        selected_table = st.sidebar.selectbox("Select a table to inspect", tables)
        
        st.sidebar.markdown("---")
        st.sidebar.subheader("Quick Stats")
        st.sidebar.markdown(f"**Total Tables:** {len(tables)}")
        st.sidebar.markdown(f"**Total Rows Staged:** {stats_df['row_count'].sum():,}")
        
        tab1, tab2 = st.tabs(["📋 Database Schema & Overview", "🔍 Data Viewer & Metadata"])
        
        with tab1:
            st.subheader("Database Tables Overview")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Tables in 'main' Schema", len(tables))
            with col2:
                st.metric("Total Records Across All Tables", f"{stats_df['row_count'].sum():,}")
                
            st.markdown("### Table List & Record Counts")
            st.dataframe(
                stats_df.rename(columns={"table_name": "Table Name", "row_count": "Row Count"}),
                use_container_width=True,
                hide_index=True
            )
            
        with tab2:
            st.subheader(f"Table Details: `{selected_table}`")
            cols_df = run_query(f"PRAGMA table_info('main.{selected_table}')")
            
            col1, col2 = st.columns([1, 3])
            with col1:
                st.write("**Table Summary**")
                row_cnt = stats_df[stats_df['table_name'] == selected_table]['row_count'].values[0]
                st.write(f"- **Rows**: `{row_cnt}`")
                st.write(f"- **Columns**: `{len(cols_df)}`")
                
                st.markdown("---")
                st.write("**Columns & Types**")
                st.dataframe(
                    cols_df[['name', 'type']].rename(columns={"name": "Column", "type": "Type"}),
                    use_container_width=True,
                    hide_index=True
                )
                
            with col2:
                st.write("**Data Preview (First 100 rows)**")
                data_df = run_query(f"SELECT * FROM main.{selected_table} LIMIT 100")
                st.dataframe(data_df, use_container_width=True, hide_index=True)
                
                csv_data = data_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label=f"📥 Download `{selected_table}` as CSV",
                    data=csv_data,
                    file_name=f"{selected_table}_preview.csv",
                    mime="text/csv"
                )