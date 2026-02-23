"""
Page 1: Financial Overview
Budget vs Actual variance analysis and unauthorized modifications.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Financial Overview | NSIA", layout="wide", page_icon=":ice_hockey:")

# ── Shared chart theme ────────────────────────────────────────────────────
CHART_BG = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(168,178,209,0.15)"
FONT_COLOR = "#a8b2d1"
TITLE_COLOR = "#ccd6f6"
ACCENT_COLORS = ["#64ffda", "#f78da7", "#fcb900", "#7bdcb5", "#00d084",
                 "#8ed1fc", "#0693e3", "#abb8c3", "#eb144c", "#ff6900"]

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

st.title("Financial Overview")
st.caption("FY2026 Budget Reconciliation — Approved Proposal vs. CSCG Operational Budget")

from utils.data_loader import (
    load_revenue_reconciliation,
    load_expense_reconciliation,
    load_unauthorized_modifications,
    load_expense_flow_summary,
)

# ── Revenue Variance ─────────────────────────────────────────────────────
st.header("Revenue — Budget vs. CSCG Variance")

rev = load_revenue_reconciliation()
display_cols = ["Line Item", "Proposal Jan Budget", "CSCG Jan Budget",
                "Jan Variance $", "Proposal YTD Budget", "CSCG YTD Budget",
                "YTD Variance $"]
st.dataframe(
    rev[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Proposal Jan Budget": st.column_config.NumberColumn(format="$%,.0f"),
        "CSCG Jan Budget": st.column_config.NumberColumn(format="$%,.0f"),
        "Jan Variance $": st.column_config.NumberColumn(format="$%,.0f"),
        "Proposal YTD Budget": st.column_config.NumberColumn(format="$%,.0f"),
        "CSCG YTD Budget": st.column_config.NumberColumn(format="$%,.0f"),
        "YTD Variance $": st.column_config.NumberColumn(format="$%,.0f"),
    },
)

# Revenue YTD variance chart
rev_chart = rev.dropna(subset=["YTD Variance $"])
rev_chart = rev_chart[~rev_chart["Line Item"].str.startswith("Total")]
if not rev_chart.empty:
    colors = ["#00d084" if v >= 0 else "#eb144c" for v in rev_chart["YTD Variance $"]]
    fig_rev = go.Figure(go.Bar(
        x=rev_chart["Line Item"],
        y=rev_chart["YTD Variance $"],
        marker=dict(
            color=colors,
            line=dict(width=1, color="rgba(255,255,255,0.3)"),
        ),
        text=[f"${v:+,.0f}" for v in rev_chart["YTD Variance $"]],
        textposition="outside",
        textfont=dict(color=FONT_COLOR, size=11),
        hovertemplate="<b>%{x}</b><br>Variance: $%{y:,.0f}<extra></extra>",
    ))
    fig_rev.update_layout(title="Revenue YTD Variance by Line Item (Proposal vs CSCG)",
                          xaxis_tickangle=-40, yaxis_title="Variance ($)")
    fig_rev.add_hline(y=0, line_dash="dot", line_color="rgba(255,255,255,0.3)")
    style_chart(fig_rev, 480)
    st.plotly_chart(fig_rev, use_container_width=True)

# ── Expense Variance ─────────────────────────────────────────────────────
st.header("Expenses — Budget vs. CSCG Variance")

exp = load_expense_reconciliation()
st.dataframe(
    exp[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Proposal Jan Budget": st.column_config.NumberColumn(format="$%,.0f"),
        "CSCG Jan Budget": st.column_config.NumberColumn(format="$%,.0f"),
        "Jan Variance $": st.column_config.NumberColumn(format="$%,.0f"),
        "Proposal YTD Budget": st.column_config.NumberColumn(format="$%,.0f"),
        "CSCG YTD Budget": st.column_config.NumberColumn(format="$%,.0f"),
        "YTD Variance $": st.column_config.NumberColumn(format="$%,.0f"),
    },
)

# Expense YTD variance chart — top movers
exp_chart = exp.dropna(subset=["YTD Variance $"])
exp_chart = exp_chart[~exp_chart["Line Item"].str.startswith("Total")]
exp_chart = exp_chart[exp_chart["YTD Variance $"].abs() > 0]
if not exp_chart.empty:
    exp_chart = exp_chart.sort_values("YTD Variance $", key=abs, ascending=True).tail(15)
    colors = ["#eb144c" if v > 0 else "#00d084" for v in exp_chart["YTD Variance $"]]
    fig_exp = go.Figure(go.Bar(
        y=exp_chart["Line Item"],
        x=exp_chart["YTD Variance $"],
        orientation="h",
        marker=dict(
            color=colors,
            line=dict(width=1, color="rgba(255,255,255,0.3)"),
        ),
        text=[f"${v:+,.0f}" for v in exp_chart["YTD Variance $"]],
        textposition="outside",
        textfont=dict(color=FONT_COLOR, size=11),
        hovertemplate="<b>%{y}</b><br>Variance: $%{x:,.0f}<extra></extra>",
    ))
    fig_exp.update_layout(title="Top Expense YTD Variances (Proposal vs CSCG)",
                          xaxis_title="Variance ($)")
    fig_exp.add_vline(x=0, line_dash="dot", line_color="rgba(255,255,255,0.3)")
    style_chart(fig_exp, 550)
    st.plotly_chart(fig_exp, use_container_width=True)

# ── Unauthorized Modifications ────────────────────────────────────────────
st.header("Unauthorized Budget Modifications")
st.caption("Line items where CSCG operational budget differs from board-approved FY2026 Budget Proposal")

mods = load_unauthorized_modifications()

# Severity bar chart
mods_chart = mods.dropna(subset=["Annual Variance $", "Severity"])
mods_chart = mods_chart[~mods_chart["Line Item"].str.contains("AGGREGATE|Total|Net Budget", case=False, na=False)]
if not mods_chart.empty:
    severity_colors = {"HIGH": "#eb144c", "CRITICAL": "#ff006e", "MEDIUM": "#fcb900", "LOW": "#00d084"}
    mods_chart = mods_chart.sort_values("Annual Variance $", key=abs, ascending=True)
    fig_mods = go.Figure(go.Bar(
        y=mods_chart["Line Item"],
        x=mods_chart["Annual Variance $"],
        orientation="h",
        marker=dict(
            color=[severity_colors.get(s, "#abb8c3") for s in mods_chart["Severity"]],
            line=dict(width=1, color="rgba(255,255,255,0.2)"),
        ),
        text=[f"${v:+,.0f}" for v in mods_chart["Annual Variance $"]],
        textposition="outside",
        textfont=dict(color=FONT_COLOR, size=11),
        hovertemplate="<b>%{y}</b><br>Severity: " +
                      mods_chart["Severity"].values.astype(str) +
                      "<br>Variance: $%{x:,.0f}<extra></extra>",
    ))
    fig_mods.update_layout(title="Unauthorized Modifications by Annual Variance",
                           xaxis_title="Annual Variance ($)")
    fig_mods.add_vline(x=0, line_dash="dot", line_color="rgba(255,255,255,0.3)")
    style_chart(fig_mods, 550)

    # Add severity legend manually
    for sev, color in severity_colors.items():
        fig_mods.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=color),
            name=sev, showlegend=True,
        ))
    fig_mods.update_layout(legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        font=dict(color=FONT_COLOR),
    ))
    st.plotly_chart(fig_mods, use_container_width=True)

# Severity table
def severity_color(val):
    colors = {"HIGH": "background-color: #eb144c33; color: #ff6b6b",
              "CRITICAL": "background-color: #ff006e33; color: #ff69b4",
              "MEDIUM": "background-color: #fcb90033; color: #fcb900",
              "LOW": "background-color: #00d08433; color: #7bdcb5"}
    return colors.get(val, "")

styled = mods.style.map(severity_color, subset=["Severity"])
st.dataframe(
    styled,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Proposal Annual": st.column_config.NumberColumn(format="$%,.0f"),
        "CSCG Annual (Implied)": st.column_config.NumberColumn(format="$%,.0f"),
        "Annual Variance $": st.column_config.NumberColumn(format="$%,.0f"),
    },
)

# ── Expense Approval Breakdown ────────────────────────────────────────────
st.header("Expense Approval Breakdown")
st.caption("How NSIA expenses are approved (July-December 2025)")

summary = load_expense_flow_summary()

col1, col2 = st.columns([1, 1])

with col1:
    if not summary.empty and "% of Total" in summary.columns:
        fig_donut = go.Figure(go.Pie(
            labels=summary["Approval Method"],
            values=summary["% of Total"],
            hole=0.5,
            marker=dict(
                colors=["#00b894", "#fdcb6e", "#6c5ce7", "#b2bec3"],
                line=dict(color="#0a192f", width=2.5),
            ),
            textinfo="percent+label",
            textfont=dict(size=12, color="#e6f1ff"),
            hovertemplate="<b>%{label}</b><br>%{percent:.1%}<extra></extra>",
        ))
        fig_donut.update_layout(
            title=dict(text="Expense Approval by Method", font=dict(size=16, color=TITLE_COLOR)),
            showlegend=False,
            annotations=[dict(text="<b>25.5%</b><br>Board-Approved",
                              x=0.5, y=0.5, font_size=14, font_color="#e6f1ff", showarrow=False)],
        )
        style_chart(fig_donut, 420)
        st.plotly_chart(fig_donut, use_container_width=True)

with col2:
    st.dataframe(
        summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "YTD Amount": st.column_config.NumberColumn(format="$%,.0f"),
            "% of Total": st.column_config.NumberColumn(format="%.1%%"),
        },
    )
    st.markdown(
        """
        **Key takeaway:** Only **25.5%** of NSIA expenses require individual
        invoice approval by the Board President. The remaining 74.5% flows
        through CSCG auto-pay, fixed contracts, or other channels with
        limited board oversight.
        """
    )
