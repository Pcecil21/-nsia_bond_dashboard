"""
Page 4: Operations
Hockey schedule, ice revenue breakdown, and CSCG relationship summary.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Operations | NSIA", layout="wide", page_icon=":ice_hockey:")

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

st.title("Operations")
st.caption("Hockey schedule, ice revenue, and CSCG management relationship")

from utils.data_loader import (
    load_hockey_schedule,
    load_revenue_reconciliation,
    load_cscg_relationship,
    load_expense_flow_summary,
)

# ── Hockey Schedule ───────────────────────────────────────────────────────
st.header("Hockey Schedule — New Trier Varsity")

schedule = load_hockey_schedule()

# Parse results
def parse_result(val):
    if pd.isna(val):
        return "TBD"
    s = str(val).strip()
    if "(W)" in s:
        return "Win"
    elif "(L)" in s:
        return "Loss"
    elif "(T)" in s or "(OTL)" in s:
        return "Tie/OTL"
    return "Upcoming"

schedule["Outcome"] = schedule["Result / Time"].apply(parse_result)

def outcome_style(val):
    styles = {
        "Win": "background-color: #00d08433; color: #7bdcb5; font-weight: bold",
        "Loss": "background-color: #eb144c33; color: #ff6b6b; font-weight: bold",
        "Tie/OTL": "background-color: #fcb90033; color: #fcb900; font-weight: bold",
    }
    return styles.get(val, "")

st.dataframe(
    schedule.style.map(outcome_style, subset=["Outcome"]),
    use_container_width=True,
    hide_index=True,
    height=400,
)

# Record summary
wins = len(schedule[schedule["Outcome"] == "Win"])
losses = len(schedule[schedule["Outcome"] == "Loss"])
ties = len(schedule[schedule["Outcome"].isin(["Tie/OTL"])])
upcoming = len(schedule[schedule["Outcome"] == "Upcoming"])

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Wins", wins)
with col2:
    st.metric("Losses", losses)
with col3:
    st.metric("Ties/OTL", ties)
with col4:
    st.metric("Upcoming", upcoming)

# Win/Loss pie
fig_record = go.Figure(go.Pie(
    labels=["Wins", "Losses", "Ties/OTL", "Upcoming"],
    values=[wins, losses, ties, upcoming],
    hole=0.55,
    marker=dict(
        colors=["#00d084", "#eb144c", "#fcb900", "#636e72"],
        line=dict(color="#0a192f", width=2),
    ),
    textinfo="label+value",
    textfont=dict(size=13, color="#e6f1ff"),
    hovertemplate="<b>%{label}</b>: %{value}<br>%{percent:.1%}<extra></extra>",
))
fig_record.update_layout(
    title=dict(text="Season Record", font=dict(size=16, color=TITLE_COLOR)),
    showlegend=False,
    annotations=[dict(text=f"<b>{wins}-{losses}</b>",
                      x=0.5, y=0.5, font_size=22, font_color="#e6f1ff", showarrow=False)],
)
style_chart(fig_record, 380)
st.plotly_chart(fig_record, use_container_width=True)

# ── Ice Revenue by Program ────────────────────────────────────────────────
st.header("Ice Revenue by Program")
st.caption("Contract ice sales from Budget Reconciliation (YTD through January)")

rev = load_revenue_reconciliation()

# Extract contract ice programs
ice_programs = rev[
    rev["Line Item"].isin(["New Trier Boys", "New Trier Girls", "Wilmette Hockey", "Winnetka Hockey"])
].copy()

if not ice_programs.empty:
    proposal_colors = ["#0984e3", "#00b894", "#6c5ce7", "#e17055"]
    cscg_colors = ["#74b9ff", "#55efc4", "#a29bfe", "#fab1a0"]

    fig_ice = go.Figure()
    for i, (_, row) in enumerate(ice_programs.iterrows()):
        fig_ice.add_trace(go.Bar(
            x=[row["Line Item"]],
            y=[row["Proposal YTD Budget"]],
            name="Proposal" if i == 0 else None,
            legendgroup="Proposal",
            showlegend=(i == 0),
            marker=dict(color=proposal_colors[i],
                        line=dict(width=1, color="rgba(255,255,255,0.3)")),
            text=f"${row['Proposal YTD Budget']:,.0f}",
            textposition="outside",
            textfont=dict(color=FONT_COLOR, size=11),
            hovertemplate=f"<b>{row['Line Item']}</b><br>Proposal: ${row['Proposal YTD Budget']:,.0f}<extra></extra>",
            offsetgroup="proposal",
        ))
        fig_ice.add_trace(go.Bar(
            x=[row["Line Item"]],
            y=[row["CSCG YTD Budget"]],
            name="CSCG" if i == 0 else None,
            legendgroup="CSCG",
            showlegend=(i == 0),
            marker=dict(color=cscg_colors[i],
                        line=dict(width=1, color="rgba(255,255,255,0.3)")),
            text=f"${row['CSCG YTD Budget']:,.0f}",
            textposition="outside",
            textfont=dict(color=FONT_COLOR, size=11),
            hovertemplate=f"<b>{row['Line Item']}</b><br>CSCG: ${row['CSCG YTD Budget']:,.0f}<extra></extra>",
            offsetgroup="cscg",
        ))

    fig_ice.update_layout(
        title="Contract Ice Revenue by Program (YTD Budget)",
        barmode="group",
        yaxis_title="YTD Budget ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    style_chart(fig_ice, 450)
    st.plotly_chart(fig_ice, use_container_width=True)

    total_proposal = ice_programs["Proposal YTD Budget"].sum()
    total_cscg = ice_programs["CSCG YTD Budget"].sum()
    variance = total_cscg - total_proposal
    st.markdown(
        f"**Total Contract Ice YTD:** Proposal **${total_proposal:,.0f}** vs. "
        f"CSCG **${total_cscg:,.0f}** (Variance: **${variance:+,.0f}**)"
    )

# ── CSCG Relationship ─────────────────────────────────────────────────────
st.header("CSCG Management Relationship")
st.caption("Financial summary of disclosed vs. undisclosed payment flows (Jul-Dec 2025)")

cscg = load_cscg_relationship()

col1, col2 = st.columns([2, 1])

with col1:
    st.dataframe(
        cscg,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Amount": st.column_config.NumberColumn(format="$%,.0f"),
        },
    )

with col2:
    total_cscg_rel = cscg["Amount"].sum()
    st.metric("Total CSCG Relationship (6 mo)", f"${total_cscg_rel:,.0f}")
    st.metric("Annualized", f"${total_cscg_rel * 2:,.0f}")

# CSCG breakdown donut
cscg_detail = cscg[cscg["Amount"] > 0].copy()
if not cscg_detail.empty:
    fig_cscg = go.Figure(go.Pie(
        labels=cscg_detail["Component"],
        values=cscg_detail["Amount"],
        hole=0.5,
        marker=dict(
            colors=["#6c5ce7", "#0984e3", "#00b894", "#fdcb6e", "#e17055"],
            line=dict(color="#0a192f", width=2.5),
        ),
        textinfo="label+percent",
        textfont=dict(size=12, color="#e6f1ff"),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent:.1%}<extra></extra>",
    ))
    fig_cscg.update_layout(
        title=dict(text="CSCG Payment Components (6-Month Period)", font=dict(size=16, color=TITLE_COLOR)),
        showlegend=False,
        annotations=[dict(text=f"<b>${total_cscg_rel:,.0f}</b>",
                          x=0.5, y=0.5, font_size=16, font_color="#e6f1ff", showarrow=False)],
    )
    style_chart(fig_cscg, 420)
    st.plotly_chart(fig_cscg, use_container_width=True)

# ── Expense Approval Summary ──────────────────────────────────────────────
st.header("Expense Approval Overview")

summary = load_expense_flow_summary()
if not summary.empty:
    bar_colors = ["#00b894", "#fdcb6e", "#6c5ce7", "#b2bec3"]
    fig_bar = go.Figure(go.Bar(
        x=summary["Approval Method"],
        y=summary["YTD Amount"],
        marker=dict(
            color=bar_colors[:len(summary)],
            line=dict(width=1.5, color="rgba(255,255,255,0.3)"),
        ),
        text=[f"${v:,.0f}" for v in summary["YTD Amount"]],
        textposition="inside",
        textfont=dict(color="#fff", size=14, family="Arial Black"),
        hovertemplate="<b>%{x}</b><br>$%{y:,.0f}<extra></extra>",
    ))
    fig_bar.update_layout(
        title="Expenses by Approval Method (Jul-Dec 2025)",
        yaxis_title="6-Month Amount ($)",
        showlegend=False,
        bargap=0.3,
    )
    style_chart(fig_bar, 420)
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown(
    """
    ---
    ### CSCG Disclosure Summary

    | Category | Amount (6 mo) | Board Visibility |
    |----------|--------------|-----------------|
    | **Management Fee** | $21,000 | Visible in Budget vs. Actuals |
    | **Payroll Reimbursement** | $205,550 | Visible but auto-approved |
    | **Total CSCG Payments** | $226,550 | Only 9.3% requires invoice approval |

    The CSCG management relationship represents a significant portion of NSIA expenses
    that flows without individual invoice approval. Per the management agreement,
    payroll costs are reimbursed automatically as CSCG employees serve the rink.
    """
)
