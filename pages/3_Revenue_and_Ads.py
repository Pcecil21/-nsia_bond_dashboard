"""
Page 3: Revenue & Advertising
Current advertisers, sales pipeline, historical ad revenue, and scoreboard sponsorship model.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Revenue & Ads | NSIA", layout="wide", page_icon=":ice_hockey:")

# ── Shared chart theme ────────────────────────────────────────────────────
CHART_BG = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(168,178,209,0.15)"
FONT_COLOR = "#a8b2d1"
TITLE_COLOR = "#ccd6f6"

st.markdown("""
<style>
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    [data-testid="stMetric"] label { color: #a8b2d1 !important; }
    [data-testid="stMetric"] [data-testid="stMetricValue"] { color: #e6f1ff !important; }
</style>
""", unsafe_allow_html=True)

def style_chart(fig, height=450):
    fig.update_layout(
        height=height,
        paper_bgcolor=CHART_BG,
        plot_bgcolor=CHART_BG,
        font=dict(color=FONT_COLOR, size=12),
        title_font=dict(color=TITLE_COLOR, size=18),
        xaxis=dict(gridcolor=GRID_COLOR, tickfont=dict(color=FONT_COLOR)),
        yaxis=dict(gridcolor=GRID_COLOR, tickfont=dict(color=FONT_COLOR)),
        legend=dict(font=dict(color=FONT_COLOR)),
        margin=dict(t=60, b=40),
    )
    return fig

st.title("Revenue & Advertising")
st.caption("Advertiser tracking, sales pipeline, and historical ad revenue trends")

from utils.data_loader import (
    load_current_ads,
    load_done_deals_prospects,
    load_historical_ad_revenue,
    load_scoreboard_10yr,
)

# ── Current Advertisers ──────────────────────────────────────────────────
st.header("Current Advertisers")

ads = load_current_ads()

# Add status based on expiration date
now = pd.Timestamp.now()

def get_status(row):
    exp = row["Expiration Date"]
    if pd.isna(exp):
        return "TBD"
    if exp < now:
        return "Expired"
    elif exp < now + pd.Timedelta(days=90):
        return "Expiring Soon"
    return "Active"

ads["Status"] = ads.apply(get_status, axis=1)

def status_style(val):
    styles = {
        "Expired": "background-color: #eb144c33; color: #ff6b6b; font-weight: bold",
        "Expiring Soon": "background-color: #fcb90033; color: #fcb900; font-weight: bold",
        "Active": "background-color: #00d08433; color: #7bdcb5; font-weight: bold",
    }
    return styles.get(val, "")

display_ads = ads[["Customer", "Type", "Location/Notes", "Term", "Expiration Date", "Cost", "Status"]].copy()

st.dataframe(
    display_ads.style.map(status_style, subset=["Status"]),
    use_container_width=True,
    hide_index=True,
)

# Summary metrics
col1, col2, col3 = st.columns(3)
with col1:
    active_count = len(ads[ads["Status"].isin(["Active", "Expiring Soon"])])
    st.metric("Active/Expiring Advertisers", active_count)
with col2:
    expired_count = len(ads[ads["Status"] == "Expired"])
    st.metric("Expired Advertisers", expired_count)
with col3:
    total_annual = ads["Cost (Numeric)"].sum()
    st.metric("Total Contract Value", f"${total_annual:,.0f}" if pd.notna(total_annual) else "N/A")

# Status donut
status_counts = ads["Status"].value_counts().reset_index()
status_counts.columns = ["Status", "Count"]
status_color_map = {"Active": "#00d084", "Expiring Soon": "#fcb900", "Expired": "#eb144c", "TBD": "#b2bec3"}
fig_status = go.Figure(go.Pie(
    labels=status_counts["Status"],
    values=status_counts["Count"],
    hole=0.55,
    marker=dict(
        colors=[status_color_map.get(s, "#abb8c3") for s in status_counts["Status"]],
        line=dict(color="#0a192f", width=2),
    ),
    textinfo="label+value",
    textfont=dict(size=13, color="#e6f1ff"),
))
fig_status.update_layout(
    title=dict(text="Advertiser Status Breakdown", font=dict(size=16, color=TITLE_COLOR)),
    showlegend=False,
)
style_chart(fig_status, 350)
st.plotly_chart(fig_status, use_container_width=True)

# ── Sales Pipeline ────────────────────────────────────────────────────────
st.header("Sales Pipeline — Done Deals vs. Prospects")

pipeline = load_done_deals_prospects()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Done Deals")
    done = pipeline[pipeline["Pipeline Stage"] == "Done Deal"]
    st.dataframe(
        done[["Advertiser", "$$", "Term"]],
        use_container_width=True,
        hide_index=True,
    )
    done_total = done["Amount"].sum()
    st.metric("Total Done Deals", f"${done_total:,.0f}" if pd.notna(done_total) else "N/A")

with col2:
    st.subheader("Prospects")
    prospects = pipeline[pipeline["Pipeline Stage"] == "Prospect"]
    display_prospects = prospects[["Advertiser", "$$", "Term", "Status"]].copy()
    display_prospects.columns = ["Advertiser", "$$", "Term", "Notes"]
    st.dataframe(
        display_prospects,
        use_container_width=True,
        hide_index=True,
    )
    prospect_total = prospects["Amount"].sum()
    st.metric("Total Prospect Pipeline", f"${prospect_total:,.0f}" if pd.notna(prospect_total) else "N/A")

# Pipeline funnel-style chart
pipeline_summary = pipeline.groupby("Pipeline Stage")["Amount"].agg(["sum", "count"]).reset_index()
pipeline_summary.columns = ["Stage", "Total Value", "Count"]
if not pipeline_summary.empty:
    fig_pipeline = go.Figure()
    colors = {"Done Deal": "#00d084", "Prospect": "#0984e3"}
    for _, row in pipeline_summary.iterrows():
        fig_pipeline.add_trace(go.Bar(
            x=[row["Stage"]],
            y=[row["Total Value"]],
            name=row["Stage"],
            marker=dict(
                color=colors.get(row["Stage"], "#abb8c3"),
                line=dict(width=1.5, color="rgba(255,255,255,0.3)"),
            ),
            text=f"${row['Total Value']:,.0f}<br>({int(row['Count'])} deals)",
            textposition="inside",
            textfont=dict(color="#fff", size=14),
            hovertemplate=f"<b>{row['Stage']}</b><br>${row['Total Value']:,.0f}<br>{int(row['Count'])} deals<extra></extra>",
        ))
    fig_pipeline.update_layout(
        title="Pipeline Value by Stage",
        yaxis_title="Total Value ($)",
        showlegend=False,
        bargap=0.3,
    )
    style_chart(fig_pipeline, 380)
    st.plotly_chart(fig_pipeline, use_container_width=True)

# ── Historical Ad Revenue ─────────────────────────────────────────────────
st.header("Historical Ad Revenue (2014-2024)")

hist = load_historical_ad_revenue()
if not hist.empty:
    avg = hist["Ad Revenue"].mean()
    max_year = int(hist.loc[hist["Ad Revenue"].idxmax(), "Year"])

    # Gradient-colored bars
    colors = []
    for _, row in hist.iterrows():
        if row["Ad Revenue"] >= avg * 1.5:
            colors.append("#00d084")
        elif row["Ad Revenue"] >= avg:
            colors.append("#0984e3")
        else:
            colors.append("#636e72")

    fig_hist = go.Figure(go.Bar(
        x=hist["Year"],
        y=hist["Ad Revenue"],
        marker=dict(
            color=colors,
            line=dict(width=1, color="rgba(255,255,255,0.2)"),
        ),
        text=[f"${v:,.0f}" for v in hist["Ad Revenue"]],
        textposition="outside",
        textfont=dict(color=FONT_COLOR, size=11),
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
    ))
    fig_hist.add_hline(y=avg, line_dash="dash", line_color="#fcb900", line_width=2,
                       annotation=dict(text=f"Avg: ${avg:,.0f}", font=dict(color="#fcb900", size=13)))
    fig_hist.update_layout(
        title="Annual Advertising Revenue (2014-2024)",
        yaxis_title="Revenue ($)",
        xaxis=dict(dtick=1),
    )
    style_chart(fig_hist, 430)
    st.plotly_chart(fig_hist, use_container_width=True)

    st.info(
        f"**10-year average:** ${avg:,.0f}/year | "
        f"**Peak:** ${hist['Ad Revenue'].max():,.0f} ({max_year}) | "
        f"**Current proposal budget:** $12,300/year"
    )

# ── Scoreboard Sponsorship Model ─────────────────────────────────────────
st.header("Scoreboard Sponsorship Revenue Model")
st.caption("10-year projection from the ScoreVision deal")

sb = load_scoreboard_10yr()
revenue_rows = sb[sb["Category"].str.contains("Revenue", case=False)]

if not revenue_rows.empty:
    years_cols = [c for c in sb.columns if c.startswith("Year")]
    melted = revenue_rows.melt(id_vars=["Category"], value_vars=years_cols,
                                var_name="Year", value_name="Amount")
    melted["Year Num"] = melted["Year"].str.extract(r"(\d+)").astype(int)

    color_map = {
        "Existing Sponsor Revenue": "#ff6b6b",
        "Referral Sponsorship Revenue to NSIA": "#00d084",
        "Non-Referral Revenue to NSIA": "#0984e3",
        "Total NSIA Sponsorship Revenue": "#fcb900",
    }

    fig_sb = go.Figure()
    for cat in revenue_rows["Category"].unique():
        cat_data = melted[melted["Category"] == cat]
        fig_sb.add_trace(go.Scatter(
            x=cat_data["Year Num"],
            y=cat_data["Amount"],
            mode="lines+markers",
            name=cat,
            line=dict(color=color_map.get(cat, "#abb8c3"), width=3),
            marker=dict(size=8, line=dict(width=2, color="#fff")),
            hovertemplate=f"<b>{cat}</b><br>Year %{{x}}<br>${{y:,.0f}}<extra></extra>",
        ))

    fig_sb.update_layout(
        title="Scoreboard Sponsorship Revenue Projections (10-Year)",
        xaxis_title="Year",
        yaxis_title="Revenue ($)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
    )
    style_chart(fig_sb, 450)
    st.plotly_chart(fig_sb, use_container_width=True)
