import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# --- Configuration ---
st.set_page_config(
    page_title="Mirai RSS Analyzer",
    page_icon="📰",
    layout="wide"
)

# --- Data Loading ---
DATA_FILE = Path("articles_history.csv")

@st.cache_data
def load_data():
    if not DATA_FILE.exists():
        return pd.DataFrame()
    
    df = pd.read_csv(DATA_FILE)
    if not df.empty:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# --- Main App ---
st.title("📰 Mirai RSS Analyzer")
st.markdown("ミライ店主会向け：収集した記事データの分析ダッシュボード")

df = load_data()

if df.empty:
    st.info("データがありません。`python -m src.main` を実行して記事を収集してください。")
else:
    # --- Sidebar Filters ---
    st.sidebar.header("フィルター")
    
    # Category filter
    categories = ["すべて"] + list(df['category'].dropna().unique())
    selected_category = st.sidebar.selectbox("カテゴリを選択", categories)
    
    # Text search
    search_term = st.sidebar.text_input("キーワード検索（タイトルまたは要約）")
    
    # Apply filters
    filtered_df = df.copy()
    if selected_category != "すべて":
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    if search_term:
        filtered_df = filtered_df[
            filtered_df['title'].str.contains(search_term, case=False, na=False) |
            filtered_df['summary'].str.contains(search_term, case=False, na=False)
        ]

    # --- KPIs ---
    st.header("概要")
    col1, col2, col3 = st.columns(3)
    col1.metric("総記事数 (フィルタ後)", f"{len(filtered_df)}")
    col2.metric("カテゴリ数", f"{filtered_df['category'].nunique()}")
    col3.metric("最新取得日時", f"{filtered_df['timestamp'].max()}" if not filtered_df.empty else "-")

    st.markdown("---")

    # --- Charts ---
    if not filtered_df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("カテゴリ分布")
            cat_counts = filtered_df['category'].value_counts().reset_index()
            cat_counts.columns = ['category', 'count']
            if not cat_counts.empty:
                fig_pie = px.pie(cat_counts, values='count', names='category', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.write("データ不足")

        with col2:
            st.subheader("取得記事数の推移 (日別)")
            daily_counts = filtered_df.groupby(filtered_df['timestamp'].dt.date).size().reset_index()
            daily_counts.columns = ['date', 'count']
            if not daily_counts.empty:
                fig_line = px.line(daily_counts, x='date', y='count', markers=True)
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.write("データ不足")

    st.markdown("---")

    # --- Data Table ---
    st.header("記事一覧")
    st.dataframe(
        filtered_df[['timestamp', 'category', 'title', 'summary', 'link']].sort_values('timestamp', ascending=False),
        column_config={
            "link": st.column_config.LinkColumn("URL")
        },
        use_container_width=True,
        hide_index=True
    )
