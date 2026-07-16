"""
charts.py
---------
All Plotly chart builders for the InsightFlow dashboard.

Design system:
  - Every chart calls apply_enterprise_theme() before it's returned — one
    shared premium, dark, transparent theme (Datadog / Fabric / Power BI
    Premium style) lives there, so no chart re-implements its own layout.
  - Every chart shares one colour language (see COLORS / SEQUENCE).
  - Business-insight generation lives here too, next to the data it reads.

NOTE: this file preserves every function name, parameter, and dataframe
operation from the previous version. Only Plotly presentation (traces +
layout) changed.
"""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd


# ============================================================
# DESIGN TOKENS  (kept in sync with style2.css)
# ============================================================

COLORS = {
    "bg": "#090B12",
    "panel": "#161B2C",
    "grid": "rgba(255, 255, 255, 0.08)",
    "axis": "#AEB8C5",
    "text": "#F5F7FA",
    "muted": "#8A93A8",
    "blue": "#4DA3FF",
    "teal": "#00D9B8",
    "purple": "#7C5CFF",
    "orange": "#FFB020",
    "pink": "#FF5C72",
    "green": "#00C48C",
}

# One consistent categorical sequence, reused everywhere so a Region/Category
# is always the same colour no matter which chart it appears on.
SEQUENCE = [
    COLORS["blue"], COLORS["teal"], COLORS["purple"],
    COLORS["orange"], COLORS["pink"], COLORS["green"],
    "#5EEAD4", "#C4B5FD",
]

FONT_FAMILY = "Inter, -apple-system, Segoe UI, sans-serif"
MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]


def apply_enterprise_theme(fig, height=380, showlegend=False, y_title=None, x_title=None):
    """
    Shared premium theme applied to every figure in the app — Datadog /
    Grafana Enterprise / Power BI Premium visual language: transparent
    surfaces, thin grid lines, muted axes, large readable type, unified
    hover, and subtle spike lines for a "pro BI tool" feel.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, " + FONT_FAMILY, size=14, color=COLORS["text"]),
        title=dict(text="", font=dict(size=22, color=COLORS["text"], family="Inter")),
        legend_font_size=12,
        height=height,
        showlegend=showlegend,
        margin=dict(l=20, r=20, t=40, b=20),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["muted"], size=12),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=COLORS["panel"],
            bordercolor=COLORS["blue"],
            font_size=14,
            font_family="Inter",
            font_color=COLORS["text"],
        ),
        transition=dict(duration=400, easing="cubic-in-out"),
    )
    fig.update_xaxes(
        title_text=x_title,
        gridcolor=COLORS["grid"],
        zeroline=False,
        showline=False,
        color=COLORS["axis"],
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        spikecolor=COLORS["blue"],
        spikethickness=1,
        spikedash="dot",
    )
    fig.update_yaxes(
        title_text=y_title,
        gridcolor=COLORS["grid"],
        zeroline=False,
        showline=False,
        color=COLORS["axis"],
    )
    return fig


def _period_to_str(df, col, freq):
    out = df.copy()
    out[col] = out[col].dt.to_period(freq).astype(str)
    return out


# ============================================================
# 1. SALES
# ============================================================

def monthly_sales_chart(df):
    """Monthly sales trend (line)."""
    monthly = (
        df.groupby(df["Order Date"].dt.to_period("M"))["Sales"]
        .sum().reset_index()
    )
    monthly["Order Date"] = monthly["Order Date"].astype(str)

    fig = px.area(
        monthly, x="Order Date", y="Sales", markers=True,
        color_discrete_sequence=[COLORS["blue"]],
    )
    fig.update_traces(
        line=dict(width=3, shape="spline", smoothing=1.1),
        marker=dict(size=7, symbol="circle", color=COLORS["blue"],
                    line=dict(width=2, color=COLORS["bg"])),
        fill="tozeroy",
        fillgradient=dict(
            type="vertical",
            colorscale=[[0, "rgba(77,163,255,0.35)"], [1, "rgba(77,163,255,0)"]],
        ),
        hovertemplate="<b>%{x}</b><br>Sales: $%{y:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, y_title="Sales ($)", x_title="Month")


def quarterly_sales_chart(df):
    """Sales aggregated by quarter (bar)."""
    q = _period_to_str(
        df.assign(**{"Order Date": df["Order Date"]}), "Order Date", "Q"
    )
    q = q.groupby("Order Date")["Sales"].sum().reset_index()

    fig = px.bar(
        q, x="Order Date", y="Sales", text_auto=".2s",
        color_discrete_sequence=[COLORS["teal"]],
    )
    fig.update_traces(
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=13),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Sales: $%{y:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, y_title="Sales ($)", x_title="Quarter")


def monthly_sales_distribution_chart(df):
    """Spread of order-level sales for each calendar month (box plot)."""
    d = df.copy()
    d["Month"] = pd.Categorical(
        d["Order Date"].dt.month_name(), categories=MONTH_ORDER, ordered=True
    )
    fig = px.box(
        d.sort_values("Month"), x="Month", y="Sales",
        color_discrete_sequence=[COLORS["green"]],
    )
    fig.update_traces(
        marker=dict(size=3, opacity=0.55, color=COLORS["green"]),
        line=dict(width=1.5),
        fillcolor="rgba(0, 196, 140, 0.18)",
    )
    return apply_enterprise_theme(fig, height=600, y_title="Sales ($)", x_title="Month")


def seasonal_heatmap(df):
    """Year x Month sales heatmap."""
    d = df.copy()
    d["Year"] = d["Order Date"].dt.year
    d["Month"] = pd.Categorical(
        d["Order Date"].dt.month_name(), categories=MONTH_ORDER, ordered=True
    )
    matrix = d.groupby(["Year", "Month"], observed=True)["Sales"].sum().reset_index()
    pivot = matrix.pivot(index="Year", columns="Month", values="Sales")

    fig = px.imshow(
        pivot, aspect="auto",
        color_continuous_scale=[
            [0.0, "#101A33"],
            [0.35, COLORS["blue"]],
            [0.7, COLORS["teal"]],
            [1.0, COLORS["green"]],
        ],
        labels={"x": "Month", "y": "Year", "color": "Sales"},
        text_auto=".2s",
    )
    fig.update_traces(
        xgap=3, ygap=3,
        hovertemplate="<b>%{y} · %{x}</b><br>Sales: $%{z:,.0f}<extra></extra>",
        textfont=dict(size=11, color=COLORS["text"]),
    )
    fig.update_layout(
        coloraxis_colorbar=dict(
            title="Sales", tickfont=dict(color=COLORS["muted"]),
            outlinewidth=0, thickness=12,
        )
    )
    return apply_enterprise_theme(fig, height=600)


def segment_sales_chart(df):
    """Sales distribution by customer segment (donut)."""
    seg = df.groupby("Segment")["Sales"].sum().reset_index()
    total = seg["Sales"].sum()

    fig = px.pie(
        seg, names="Segment", values="Sales", hole=0.68,
        color_discrete_sequence=SEQUENCE,
    )
    fig.update_traces(
        textinfo="percent+label",
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=13),
        marker=dict(line=dict(color=COLORS["bg"], width=2)),
        hovertemplate="<b>%{label}</b><br>Sales: $%{value:,.0f} (%{percent})<extra></extra>",
    )
    fig.add_annotation(
        text=f"<b>${total:,.0f}</b><br><span style='font-size:11px;color={COLORS['muted']}'>Total Sales</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=18, color=COLORS["text"], family="Inter"),
    )
    return apply_enterprise_theme(fig, height=600, showlegend=True)


def sales_funnel_chart(df):
    """
    Pipeline-style funnel: how the full transaction base narrows down to
    high-value, profitable orders. A practical proxy for a sales funnel
    on a retail order dataset (no literal lead-stage data available).
    """
    total_orders = df["Order ID"].nunique()
    profitable_orders = df.loc[df["Profit"] > 0, "Order ID"].nunique()
    high_value_orders = df.loc[df["Sales"] > 500, "Order ID"].nunique()
    top_tier_orders = df.loc[df["Sales"] > 1000, "Order ID"].nunique()

    fig = go.Figure(go.Funnel(
        y=["Total Orders", "Profitable Orders", "High Value (>$500)", "Premium (>$1,000)"],
        x=[total_orders, profitable_orders, high_value_orders, top_tier_orders],
        textinfo="value+percent initial",
        textfont=dict(color=COLORS["text"], size=13),
        marker=dict(
            color=[COLORS["blue"], COLORS["teal"], COLORS["purple"], COLORS["orange"]],
            line=dict(width=0),
        ),
        connector=dict(line=dict(color=COLORS["grid"], width=1)),
        hovertemplate="<b>%{y}</b><br>%{x} orders<extra></extra>",
    ))
    return apply_enterprise_theme(fig, height=600)


# ============================================================
# 2. PRODUCTS
# ============================================================

def category_sales_chart(df):
    cat = df.groupby("Category")["Sales"].sum().reset_index()
    fig = px.bar(
        cat, x="Category", y="Sales", color="Category", text_auto=".2s",
        color_discrete_sequence=SEQUENCE,
    )
    fig.update_traces(
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=13),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Sales: $%{y:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, y_title="Sales ($)")


def product_treemap(df):
    tree = (
        df.groupby(["Category", "Sub-Category"])["Sales"]
        .sum().reset_index()
    )
    fig = px.treemap(
        tree, path=["Category", "Sub-Category"], values="Sales",
        color="Sales",
        color_continuous_scale=[COLORS["panel"], COLORS["blue"], COLORS["teal"]],
    )
    fig.update_traces(
        textfont=dict(color="white", size=13),
        marker=dict(line=dict(color=COLORS["bg"], width=2)),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Sales: $%{value:,.0f}<br>"
            "Share of parent: %{percentParent:.1%}<extra></extra>"
        ),
    )
    fig.update_layout(margin=dict(t=10, l=0, r=0, b=0), height=440)
    return apply_enterprise_theme(fig, height=600)


def top_products_chart(df, n=10):
    top = (
        df.groupby("Product Name")["Sales"].sum()
        .reset_index().sort_values("Sales", ascending=False).head(n)
    )
    fig = px.bar(
        top.sort_values("Sales"), x="Sales", y="Product Name", orientation="h",
        text_auto=".2s", color_discrete_sequence=[COLORS["blue"]],
    )
    fig.update_traces(
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=12),
        hovertemplate="<b>%{y}</b><br>Sales: $%{x:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, x_title="Sales ($)")


def top_subcategories_chart(df, n=10):
    top = (
        df.groupby("Sub-Category")["Sales"].sum()
        .reset_index().sort_values("Sales", ascending=False).head(n)
    )
    fig = px.bar(
        top.sort_values("Sales"), x="Sales", y="Sub-Category", orientation="h",
        text_auto=".2s", color_discrete_sequence=[COLORS["purple"]],
    )
    fig.update_traces(
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=12),
        hovertemplate="<b>%{y}</b><br>Sales: $%{x:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, x_title="Sales ($)")


# ============================================================
# 3. REGIONAL
# ============================================================

def region_sales_chart(df):
    reg = df.groupby("Region")["Sales"].sum().reset_index()
    fig = px.bar(
        reg, x="Region", y="Sales", color="Region", text_auto=".2s",
        color_discrete_sequence=SEQUENCE,
    )
    fig.update_traces(
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=13),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Sales: $%{y:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, y_title="Sales ($)")


def region_profit_chart(df):
    reg = df.groupby("Region")["Profit"].sum().reset_index()
    fig = px.bar(
        reg, x="Region", y="Profit", color="Region", text_auto=".2s",
        color_discrete_sequence=SEQUENCE,
    )
    fig.update_traces(
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=13),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Profit: $%{y:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, y_title="Profit ($)")


def top_cities_chart(df, n=10):
    top = (
        df.groupby("City")["Sales"].sum()
        .reset_index().sort_values("Sales", ascending=False).head(n)
    )
    fig = px.bar(
        top.sort_values("Sales"), x="Sales", y="City", orientation="h",
        text_auto=".2s", color_discrete_sequence=[COLORS["green"]],
    )
    fig.update_traces(
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=12),
        hovertemplate="<b>%{y}</b><br>Sales: $%{x:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, x_title="Sales ($)")


def region_comparison_chart(df):
    """Sales vs. Profit side-by-side for every region."""
    reg = df.groupby("Region")[["Sales", "Profit"]].sum().reset_index()
    melted = reg.melt(id_vars="Region", value_vars=["Sales", "Profit"],
                       var_name="Metric", value_name="Amount")
    fig = px.bar(
        melted, x="Region", y="Amount", color="Metric", barmode="group",
        text_auto=".2s", color_discrete_sequence=[COLORS["blue"], COLORS["teal"]],
    )
    fig.update_traces(
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=12),
        hovertemplate="<b>%{x}</b><br>%{fullData.name}: $%{y:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, showlegend=True, y_title="Amount ($)")


# ============================================================
# 4. PROFIT
# ============================================================

def profit_category_chart(df):
    prof = df.groupby("Category")["Profit"].sum().reset_index()
    fig = px.bar(
        prof, x="Category", y="Profit", text_auto=".2s",
        color="Category", color_discrete_sequence=SEQUENCE,
    )
    fig.update_traces(
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=13),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Profit: $%{y:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, y_title="Profit ($)")


def profit_subcategory_chart(df):
    prof = (
        df.groupby("Sub-Category")["Profit"].sum()
        .reset_index().sort_values("Profit", ascending=False)
    )
    colors = [COLORS["green"] if v >= 0 else COLORS["pink"] for v in prof["Profit"]]
    fig = px.bar(prof, x="Sub-Category", y="Profit", text_auto=".2s")
    fig.update_traces(
        marker=dict(color=colors, opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=12),
        hovertemplate="<b>%{x}</b><br>Profit: $%{y:,.0f}<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, y_title="Profit ($)")


def profit_trend_chart(df):
    prof = (
        df.groupby(df["Order Date"].dt.to_period("M"))["Profit"]
        .sum().reset_index()
    )
    prof["Order Date"] = prof["Order Date"].astype(str)
    fig = px.line(
        prof, x="Order Date", y="Profit", markers=True,
        color_discrete_sequence=[COLORS["orange"]],
    )
    fig.update_traces(
        line=dict(width=3, shape="spline", smoothing=1.1),
        marker=dict(size=7, color=COLORS["orange"], line=dict(width=2, color=COLORS["bg"])),
        hovertemplate="<b>%{x}</b><br>Profit: $%{y:,.0f}<extra></extra>",
    )
    fig.add_hline(y=0, line_dash="dot", line_color=COLORS["muted"], line_width=1)
    return apply_enterprise_theme(fig, height=600, y_title="Profit ($)", x_title="Month")


def profit_margin_chart(df):
    """Profit margin (%) by category."""
    cat = df.groupby("Category")[["Sales", "Profit"]].sum().reset_index()
    cat["Margin %"] = (cat["Profit"] / cat["Sales"] * 100).round(2)
    fig = px.bar(
        cat, x="Category", y="Margin %", text="Margin %",
        color="Category", color_discrete_sequence=SEQUENCE,
    )
    fig.update_traces(
        texttemplate="%{text}%",
        textposition="outside",
        marker=dict(opacity=0.88, line=dict(width=0)),
        textfont=dict(color=COLORS["text"], size=13),
        hovertemplate="<b>%{x}</b><br>Margin: %{y:.2f}%<extra></extra>",
    )
    return apply_enterprise_theme(fig, height=600, y_title="Margin (%)")


# ============================================================
# 5. BUSINESS INSIGHTS
# ============================================================

def generate_insights(df):
    """
    Return a list of dicts: {"icon", "title", "text", "type"}
    type is one of: success | warning | info | danger  -> maps to CSS card colour.
    """
    insights = []
    if df.empty:
        return [{
            "icon": "⚠️", "title": "No data in range",
            "text": "Adjust your filters to see business insights.",
            "type": "warning",
        }]

    # Highest sales region
    reg_sales = df.groupby("Region")["Sales"].sum()
    top_region = reg_sales.idxmax()
    insights.append({
        "icon": "🌍", "title": "Top Performing Region",
        "text": f"**{top_region}** leads all regions with **${reg_sales.max():,.0f}** in sales.",
        "type": "success",
    })

    # Highest profit category
    cat_profit = df.groupby("Category")["Profit"].sum()
    top_cat = cat_profit.idxmax()
    insights.append({
        "icon": "💰", "title": "Most Profitable Category",
        "text": f"**{top_cat}** generates the highest profit at **${cat_profit.max():,.0f}**.",
        "type": "success",
    })

    # Highest sales month
    monthly = df.groupby(df["Order Date"].dt.to_period("M"))["Sales"].sum()
    if len(monthly) > 0:
        best_month = monthly.idxmax()
        insights.append({
            "icon": "📈", "title": "Peak Sales Month",
            "text": f"**{best_month.strftime('%B %Y')}** was the strongest month, with **${monthly.max():,.0f}** in sales.",
            "type": "info",
        })

    # Lowest performing category (by profit)
    worst_cat = cat_profit.idxmin()
    worst_val = cat_profit.min()
    tone = "danger" if worst_val < 0 else "warning"
    insights.append({
        "icon": "📉", "title": "Underperforming Category",
        "text": f"**{worst_cat}** trails behind with only **${worst_val:,.0f}** in profit — review pricing or discounting strategy.",
        "type": tone,
    })

    # Lowest margin sub-category
    sub = df.groupby("Sub-Category")[["Sales", "Profit"]].sum()
    sub["Margin"] = sub["Profit"] / sub["Sales"] * 100
    worst_sub = sub["Margin"].idxmin()
    insights.append({
        "icon": "🧭", "title": "Recommendation",
        "text": f"**{worst_sub}** has the thinnest margin ({sub.loc[worst_sub, 'Margin']:.1f}%). "
                f"Consider bundling or reducing discounts on this sub-category to protect profitability.",
        "type": "warning",
    })

    return insights
