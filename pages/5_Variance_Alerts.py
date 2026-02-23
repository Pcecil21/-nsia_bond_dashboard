"""
Page 5: Variance Alerts
Auto-flags line items where CSCG budget deviates from board-approved proposal.
Stoplight system: RED / YELLOW / GREEN with action items view.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Variance Alerts | NSIA", layout="wide", page_icon=":ice_hockey:")

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

st.title("Variance Alerts")
st.caption("Automated monitoring: CSCG operational budget vs. board-approved proposal")

from utils.data_loader import compute_variance_alerts

# ── Controls ──────────────────────────────────────────────────────────────
threshold = st.sidebar.slider("Variance threshold (%)", 1, 25, 5, 1,
                               help="Flag line items deviating more than this %") / 100

alerts = compute_variance_alerts(threshold_pct=threshold)

# ── Summary metrics ───────────────────────────────────────────────────────
red_count = len(alerts[alerts["Severity"] == "RED"])
yellow_count = len(alerts[alerts["Severity"] == "YELLOW"])
green_count = len(alerts[alerts["Severity"] == "GREEN"])
total_items = len(alerts)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Line Items", total_items)
with col2:
    st.metric("RED Alerts", red_count)
with col3:
    st.metric("YELLOW Alerts", yellow_count)
with col4:
    st.metric("GREEN (OK)", green_count)

# ── Stoplight summary chart ──────────────────────────────────────────────
fig_stop = go.Figure()
fig_stop.add_trace(go.Bar(
    x=["RED"], y=[red_count], name="RED",
    marker=dict(color="#eb144c", line=dict(width=1.5, color="rgba(255,255,255,0.3)")),
    text=[red_count], textposition="inside",
    textfont=dict(color="#fff", size=24, family="Arial Black"),
    hovertemplate="<b>RED Alerts</b><br>%{y} line items<br>>50% variance or >$10K<extra></extra>",
))
fig_stop.add_trace(go.Bar(
    x=["YELLOW"], y=[yellow_count], name="YELLOW",
    marker=dict(color="#fcb900", line=dict(width=1.5, color="rgba(255,255,255,0.3)")),
    text=[yellow_count], textposition="inside",
    textfont=dict(color="#1a1a2e", size=24, family="Arial Black"),
    hovertemplate=f"<b>YELLOW Alerts</b><br>%{{y}} line items<br>>{threshold:.0%} variance or >$2K<extra></extra>",
))
fig_stop.add_trace(go.Bar(
    x=["GREEN"], y=[green_count], name="GREEN",
    marker=dict(color="#00d084", line=dict(width=1.5, color="rgba(255,255,255,0.3)")),
    text=[green_count], textposition="inside",
    textfont=dict(color="#1a1a2e", size=24, family="Arial Black"),
    hovertemplate="<b>GREEN</b><br>%{y} line items<br>Within tolerance<extra></extra>",
))
fig_stop.update_layout(
    title="Budget Variance Stoplight Summary",
    showlegend=False,
    bargap=0.35,
    yaxis_title="Number of Line Items",
)
style_chart(fig_stop, 350)
st.plotly_chart(fig_stop, use_container_width=True)

# ── RED Alerts — Requires Immediate Board Attention ───────────────────────
st.markdown("---")
st.header("RED Alerts — Requires Board Attention")
st.markdown("Line items with **>50% variance** or **>$10,000 deviation** from approved proposal.")

red_alerts = alerts[alerts["Severity"] == "RED"].copy()
if red_alerts.empty:
    st.success("No RED alerts at current threshold.")
else:
    # Horizontal bar chart of RED items
    red_sorted = red_alerts.sort_values("Variance $", key=lambda x: x.abs(), ascending=True)
    colors = ["#ff6b6b" if v and v > 0 else "#ff4757" for v in red_sorted["Variance $"]]
    fig_red = go.Figure(go.Bar(
        y=red_sorted["Category"] + " — " + red_sorted["Line Item"],
        x=red_sorted["Variance $"],
        orientation="h",
        marker=dict(color=colors, line=dict(width=1, color="rgba(255,255,255,0.2)")),
        text=[f"${v:+,.0f}" if pd.notna(v) else "N/A" for v in red_sorted["Variance $"]],
        textposition="outside",
        textfont=dict(color="#ff6b6b", size=12, family="Arial Black"),
        hovertemplate="<b>%{y}</b><br>Variance: $%{x:,.0f}<extra></extra>",
    ))
    fig_red.add_vline(x=0, line_dash="dot", line_color="rgba(255,255,255,0.3)")
    fig_red.update_layout(title="RED Alert Items — YTD Variance ($)", xaxis_title="Variance ($)")
    style_chart(fig_red, max(350, len(red_sorted) * 40 + 100))
    st.plotly_chart(fig_red, use_container_width=True)

    # Detailed table
    def red_style(val):
        return "background-color: #eb144c22; color: #ff6b6b; font-weight: bold"

    display_red = red_alerts[["Category", "Line Item", "Proposal YTD", "CSCG YTD",
                               "Variance $", "Variance %", "Assessment"]].copy()
    st.dataframe(
        display_red.style.map(lambda _: red_style(_), subset=["Variance $"]),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Proposal YTD": st.column_config.NumberColumn(format="$%,.0f"),
            "CSCG YTD": st.column_config.NumberColumn(format="$%,.0f"),
            "Variance $": st.column_config.NumberColumn(format="$%,.0f"),
            "Variance %": st.column_config.NumberColumn(format="%.1%%"),
        },
    )

# ── YELLOW Alerts — Monitor Closely ──────────────────────────────────────
st.markdown("---")
st.header("YELLOW Alerts — Monitor Closely")
st.markdown(f"Line items with **>{threshold:.0%} variance** or **>$2,000 deviation**.")

yellow_alerts = alerts[alerts["Severity"] == "YELLOW"].copy()
if yellow_alerts.empty:
    st.success("No YELLOW alerts at current threshold.")
else:
    yellow_sorted = yellow_alerts.sort_values("Variance $", key=lambda x: x.abs(), ascending=True)
    fig_yellow = go.Figure(go.Bar(
        y=yellow_sorted["Category"] + " — " + yellow_sorted["Line Item"],
        x=yellow_sorted["Variance $"],
        orientation="h",
        marker=dict(color="#fcb900", line=dict(width=1, color="rgba(255,255,255,0.2)")),
        text=[f"${v:+,.0f}" if pd.notna(v) else "N/A" for v in yellow_sorted["Variance $"]],
        textposition="outside",
        textfont=dict(color="#fcb900", size=11),
        hovertemplate="<b>%{y}</b><br>Variance: $%{x:,.0f}<extra></extra>",
    ))
    fig_yellow.add_vline(x=0, line_dash="dot", line_color="rgba(255,255,255,0.3)")
    fig_yellow.update_layout(title="YELLOW Alert Items — YTD Variance ($)", xaxis_title="Variance ($)")
    style_chart(fig_yellow, max(350, len(yellow_sorted) * 35 + 100))
    st.plotly_chart(fig_yellow, use_container_width=True)

    display_yellow = yellow_alerts[["Category", "Line Item", "Proposal YTD", "CSCG YTD",
                                     "Variance $", "Variance %"]].copy()
    st.dataframe(
        display_yellow,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Proposal YTD": st.column_config.NumberColumn(format="$%,.0f"),
            "CSCG YTD": st.column_config.NumberColumn(format="$%,.0f"),
            "Variance $": st.column_config.NumberColumn(format="$%,.0f"),
            "Variance %": st.column_config.NumberColumn(format="%.1%%"),
        },
    )

# ── GREEN Items — Within Tolerance ────────────────────────────────────────
with st.expander("GREEN Items — Within Tolerance (click to expand)"):
    green_alerts = alerts[alerts["Severity"] == "GREEN"].copy()
    if green_alerts.empty:
        st.info("No GREEN items.")
    else:
        st.dataframe(
            green_alerts[["Category", "Line Item", "Proposal YTD", "CSCG YTD",
                           "Variance $", "Variance %"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Proposal YTD": st.column_config.NumberColumn(format="$%,.0f"),
                "CSCG YTD": st.column_config.NumberColumn(format="$%,.0f"),
                "Variance $": st.column_config.NumberColumn(format="$%,.0f"),
                "Variance %": st.column_config.NumberColumn(format="%.1%%"),
            },
        )

# ── Aggregate Impact ──────────────────────────────────────────────────────
st.markdown("---")
st.header("Aggregate Variance Impact")

non_green = alerts[alerts["Severity"] != "GREEN"].copy()
total_positive = non_green[non_green["Variance $"] > 0]["Variance $"].sum()
total_negative = non_green[non_green["Variance $"] < 0]["Variance $"].sum()
net_impact = non_green["Variance $"].sum()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Favorable Variances", f"${total_positive:+,.0f}",
              delta="Higher than proposal", delta_color="off")
with col2:
    st.metric("Total Unfavorable Variances", f"${total_negative:+,.0f}",
              delta="Lower than proposal", delta_color="off")
with col3:
    st.metric("Net Budget Impact (YTD)", f"${net_impact:+,.0f}",
              delta="Positive" if net_impact > 0 else "Negative",
              delta_color="normal" if net_impact > 0 else "inverse")

st.markdown(
    """
    ---
    **How to use this page:**
    - Adjust the **variance threshold** in the sidebar to change sensitivity
    - **RED** items require immediate board discussion and possible budget amendment
    - **YELLOW** items should be monitored monthly for trend changes
    - **GREEN** items are within normal tolerance
    - Ask CSCG to provide written justification for all RED and YELLOW items
    """
)
