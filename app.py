"""
InsightFlow — Enterprise Sales Analytics Dashboard
====================================================
Self-contained Streamlit app. Chart logic lives in charts.py, visual
styling lives in style.css. This file only wires data -> filters -> pages.
"""

import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

try:
    import charts
except ModuleNotFoundError:
    # Falls back to the original project layout (src/charts.py)
    from src import charts

# ============================================================
# CONFIG
# ============================================================

PAGE_TITLE = "InsightFlow | Enterprise Sales Analytics"
PAGE_ICON = "📊"
LAYOUT = "wide"


DATA_CANDIDATES = [
    "data/Superstore.csv",
    "data/Sample - Superstore.csv",
    "data raw/Superstore.csv",
    "data raw/Sample - Superstore.csv",
    "data_raw/Superstore.csv",
    "data_raw/Sample - Superstore.csv",
    "Superstore.csv",
    "Sample - Superstore.csv",
]


def _find_data_file():
    """Check the known candidate paths first, then fall back to a
    recursive search (any .csv with 'superstore' in its name) under
    the folder app.py lives in — so odd folder names still work."""
    for p in DATA_CANDIDATES:
        if Path(p).exists():
            return Path(p)

    skip_dirs = {".venv", "venv", ".git", "__pycache__", "node_modules"}
    app_dir = Path(__file__).parent
    for f in app_dir.rglob("*.csv"):
        if skip_dirs & set(f.parts):
            continue
        if "superstore" in f.name.lower():
            return f
    return None

NAV_PAGES = [
    ("🏠", "Executive Dashboard"),
    ("📈", "Sales Analytics"),
    ("📦", "Product Analytics"),
    ("🌍", "Regional Analytics"),
    ("💰", "Profit Analytics"),
    ("💡", "Business Insights"),
]


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data(show_spinner="Loading Superstore data...")
def load_data(uploaded_file=None):
    """Locate and load the Superstore dataset, parsing date columns."""
    source = uploaded_file if uploaded_file is not None else _find_data_file()
    if source is None:
        return None

    try:
        df = pd.read_csv(source, encoding="latin-1")
    except UnicodeDecodeError:
        if uploaded_file is not None:
            uploaded_file.seek(0)
        df = pd.read_csv(source, encoding="utf-8")

    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    if "Ship Date" in df.columns:
        df["Ship Date"] = pd.to_datetime(df["Ship Date"], errors="coerce")

    df = df.dropna(subset=["Order Date"])
    return df


# ============================================================
# UI HELPERS
# ============================================================

def load_css():
    css_path = Path(__file__).parent / "style2.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="logo-badge">📊</div>
                <div>
                    <div class="brand-title">InsightFlow</div>
                    <div class="brand-sub">Enterprise Analytics</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        labels = [f"{icon}  {name}" for icon, name in NAV_PAGES]
        choice = st.radio("Navigation", labels, label_visibility="collapsed")
        page = choice.split("  ", 1)[1]

        st.markdown("---")
        st.caption("Data source: Superstore dataset")
        st.caption("Theme: Dark · Power BI style")
        return page


def render_filters(df):
    """Global filter bar shown above every page. Returns the filtered df."""
    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">🔍 Filters</div>', unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        regions = st.multiselect(
            " Region", sorted(df["Region"].unique()),
            default=sorted(df["Region"].unique()),
        )
    with f2:
        categories = st.multiselect(
            " Category", sorted(df["Category"].unique()),
            default=sorted(df["Category"].unique()),
        )
    with f3:
        segments = st.multiselect(
            " Segment", sorted(df["Segment"].unique()),
            default=sorted(df["Segment"].unique()),
        )
    with f4:
        start_date, end_date = st.date_input(
            " Date Range",
            value=(df["Order Date"].min(), df["Order Date"].max()),
        )
    st.markdown("</div>", unsafe_allow_html=True)

    filtered = df[
        df["Region"].isin(regions)
        & df["Category"].isin(categories)
        & df["Segment"].isin(segments)
        & (df["Order Date"] >= pd.to_datetime(start_date))
        & (df["Order Date"] <= pd.to_datetime(end_date))
    ]
    return filtered


def kpi_card(col, icon, value, label, accent="var(--purple)"):
    with col:
        st.markdown(
            f"""
            <div class="kpi-card" style="--accent:{accent}">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def chart_card(title, fig, caption=None):
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="chart-card-title">{title}</div>', unsafe_allow_html=True)
    if caption:
        st.markdown(f'<div class="chart-card-caption">{caption}</div>', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)


def insight_card(icon, title, text, tone="info"):
    st.markdown(
        f"""
        <div class="insight-card insight-{tone}">
            <div class="insight-title">{icon} {title}</div>
            <div class="insight-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def compute_kpis(df):
    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    total_orders = df["Order ID"].nunique()
    margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    return total_sales, total_profit, total_orders, margin


# ============================================================
# PAGES
# ============================================================

def page_header(title, subtitle):
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def executive_dashboard(df):
    page_header("🏠 Executive Dashboard", "High-level snapshot of business performance.")

    total_sales, total_profit, total_orders, margin = compute_kpis(df)
    c1, c2, c3, c4 = st.columns(4)
    kpi_card(c1, "💰", f"${total_sales/1_000_000:.2f}M", "Total Sales", "var(--purple)")
    kpi_card(c2, "📈", f"${total_profit/1_000:.1f}K", "Total Profit", "var(--green)")
    kpi_card(c3, "📦", f"{total_orders:,}", "Orders", "var(--blue)")
    kpi_card(c4, "🎯", f"{margin:.2f}%", "Profit Margin", "var(--amber)")

    st.markdown('<div class="section-label">Trends</div>', unsafe_allow_html=True)
    left, right = st.columns([2, 1])
    with left:
        chart_card("📈 Monthly Sales Trend", charts.monthly_sales_chart(df))
    with right:
        chart_card("🔻 Sales Funnel", charts.sales_funnel_chart(df))

    st.markdown('<div class="section-label">Executive Summary</div>', unsafe_allow_html=True)
    st.info(
        "Welcome to **InsightFlow Enterprise Sales Dashboard**. "
        "Use the filters above to explore sales trends, product performance, "
        "regional analysis and business insights."
    )

    st.markdown('<div class="section-label">💡 Top Insights</div>', unsafe_allow_html=True)
    for ins in charts.generate_insights(df)[:3]:
        insight_card(ins["icon"], ins["title"], ins["text"], ins["type"])


def sales_analytics(df):
    page_header("📈 Sales Analytics", "Sales trends, seasonality and distribution.")

    tab1, tab2, tab3 = st.tabs(["📅 Trends", "🔥 Seasonality", "📊 Distribution"])

    with tab1:
        chart_card("📈 Monthly Sales Trend", charts.monthly_sales_chart(df))
        c1, c2 = st.columns(2)
        with c1:
            chart_card("📊 Quarterly Sales", charts.quarterly_sales_chart(df))
        with c2:
            chart_card("👥 Sales by Customer Segment", charts.segment_sales_chart(df))

    with tab2:
        chart_card(
            "🔥 Seasonal Sales Heatmap", charts.seasonal_heatmap(df),
            "Darker cells indicate higher sales for that year/month.",
        )

    with tab3:
        chart_card(
            "📦 Monthly Sales Distribution", charts.monthly_sales_distribution_chart(df),
            "Spread of order-level sales for each calendar month, across all years.",
        )


def product_analytics(df):
    page_header("📦 Product Analytics", "Category, sub-category and product performance.")

    tab1, tab2 = st.tabs(["🌳 Category Breakdown", "🏆 Top Performers"])

    with tab1:
        c1, c2 = st.columns([1, 1])
        with c1:
            chart_card("📊 Sales by Category", charts.category_sales_chart(df))
        with c2:
            chart_card("🌳 Category → Sub-Category Treemap", charts.product_treemap(df))

    with tab2:
        c1, c2 = st.columns(2)
        with c1:
            chart_card("🏆 Top 10 Products", charts.top_products_chart(df))
        with c2:
            chart_card("🏆 Top 10 Sub-Categories", charts.top_subcategories_chart(df))


def regional_analytics(df):
    page_header("🌍 Regional Analytics", "Regional and city-level performance.")

    tab1, tab2 = st.tabs(["🌍 Region Overview", "🏙️ Top Cities"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            chart_card("🌍 Regional Sales", charts.region_sales_chart(df))
        with c2:
            chart_card("💰 Regional Profit", charts.region_profit_chart(df))
        chart_card("⚖️ Sales vs. Profit by Region", charts.region_comparison_chart(df))

    with tab2:
        chart_card("🏙️ Top 10 Cities by Sales", charts.top_cities_chart(df))


def profit_analytics(df):
    page_header("💰 Profit Analytics", "Profitability across categories and time.")

    total_sales, total_profit, total_orders, margin = compute_kpis(df)
    c1, c2, c3 = st.columns(3)
    kpi_card(c1, "💰", f"${total_profit/1_000:.1f}K", "Total Profit", "var(--green)")
    kpi_card(c2, "🎯", f"{margin:.2f}%", "Profit Margin", "var(--amber)")
    best_cat = df.groupby("Category")["Profit"].sum().idxmax() if not df.empty else "—"
    kpi_card(c3, "🏆", best_cat, "Top Category", "var(--purple)")

    tab1, tab2 = st.tabs(["📊 By Category", "📈 Over Time"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            chart_card("💰 Profit by Category", charts.profit_category_chart(df))
        with c2:
            chart_card("📦 Profit by Sub-Category", charts.profit_subcategory_chart(df))
        chart_card("🎯 Profit Margin by Category", charts.profit_margin_chart(df))

    with tab2:
        chart_card("📈 Monthly Profit Trend", charts.profit_trend_chart(df))


def business_insights(df):
    page_header("💡 Business Insights", "Automated takeaways from the current selection.")

    for ins in charts.generate_insights(df):
        insight_card(ins["icon"], ins["title"], ins["text"], ins["type"])


# ============================================================
# MAIN
# ============================================================

def main():
    st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout=LAYOUT)
    load_css()

    df = load_data()
    
    page = render_sidebar()

    # Everything below must stay INSIDE main()

    col1, col2 = st.columns([9,1])

    with col1:
        st.markdown("""
        <div>
            <h1 style="margin-bottom:0;">📊 InsightFlow</h1>
            <p style="margin-top:0;color:#8A93A8;">
                Enterprise Sales Analytics Dashboard
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        if st.button("Refresh "):
            st.cache_data.clear()   # Clear cached data
            st.rerun()              # Reload app

    filtered_df = render_filters(df)

    csv = filtered_df.to_csv(index=False).encode("utf-8")

    st.sidebar.download_button(
        label="📥 Export CSV",
        data=csv,
        file_name="InsightFlow_Report.csv",
        mime="text/csv"
    )

    if filtered_df.empty:
        st.warning("No records match the current filters.")
        st.stop()

    router = {
        "Executive Dashboard": executive_dashboard,
        "Sales Analytics": sales_analytics,
        "Product Analytics": product_analytics,
        "Regional Analytics": regional_analytics,
        "Profit Analytics": profit_analytics,
        "Business Insights": business_insights,
    }

    router[page](filtered_df)

    st.markdown("---")

    st.caption(
        f"🕒 Last Updated: {datetime.now().strftime('%d %b %Y • %I:%M %p')}"
    )

    st.caption("📊 Dataset: Sample Superstore")


if __name__ == "__main__":
    main()