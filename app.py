"""
NSIA Bond Dashboard — Home Page
North Shore Ice Arena financial transparency dashboard.
"""
import streamlit as st
import plotly.graph_objects as go
import os

st.set_page_config(
    page_title="NSIA Bond Dashboard",
    page_icon=":ice_hockey:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    [data-testid="stMetric"] label {
        color: #a8b2d1 !important;
        font-size: 0.85rem !important;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #e6f1ff !important;
        font-size: 1.8rem !important;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #ccd6f6;
    }
    div[data-testid="stSidebarContent"] {
        background: linear-gradient(180deg, #0a192f 0%, #112240 100%);
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ──────────────────────────────────────────────────────────────
logo_path = os.path.join(os.path.dirname(__file__), "data", "nsia_logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=200)
st.sidebar.title("NSIA Bond Dashboard")
st.sidebar.markdown(
    """
    **Navigation**
    - **Home** — KPI Summary
    - **Financial Overview** — Budget variances
    - **Bond & Debt** — Obligations & hidden flows
    - **Revenue & Ads** — Advertising pipeline
    - **Operations** — Ice Revenue & CSCG
    - **Variance Alerts** — Stoplight flags
    - **CSCG Scorecard** — Contract compliance
    - **Monthly Financials** — P&L, Cash, Receivables
    - **Multi-Year Trends** — 3yr Revenue & Payroll
    - **Ice Utilization** — Allocation & Gaps
    """
)
st.sidebar.markdown("---")
st.sidebar.caption("FY2026 | Data through January 2026 (Month 7)")

# ── Main content ─────────────────────────────────────────────────────────
from utils.data_loader import compute_kpis, load_hidden_cash_flows, load_expense_flow_summary

st.title("North Shore Ice Arena")
st.subheader("Board Financial Transparency Dashboard")
st.markdown("**Fiscal Year 2026** | July 2025 - June 2026 | Data through January 2026")

st.markdown("---")

kpis = compute_kpis()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="Total Annual Revenue (est.)",
        value=f"${kpis['total_annual_revenue']:,.0f}",
    )

with col2:
    st.metric(
        label="Total Annual Expenses (est.)",
        value=f"${kpis['total_annual_expenses']:,.0f}",
    )

with col3:
    ncf = kpis["net_cash_flow"]
    st.metric(
        label="Net Cash Flow (est.)",
        value=f"${ncf:,.0f}",
        delta=f"{'Positive' if ncf > 0 else 'Negative'}",
        delta_color="normal" if ncf > 0 else "inverse",
    )

col4, col5, col6 = st.columns(3)

with col4:
    st.metric(
        label="Hidden Cash Outflows",
        value=f"${kpis['hidden_cash_outflows']:,.0f}",
        delta="Not in Budget vs Actuals",
        delta_color="off",
    )

with col5:
    st.metric(
        label="% Board-Approved Expenses",
        value=f"{kpis['pct_board_approved']:.1%}",
        delta="of total spending",
        delta_color="off",
    )

with col6:
    dscr = kpis["dscr"]
    st.metric(
        label="Debt Service Coverage Ratio",
        value=f"{dscr:.2f}x",
        delta="Above 1.0x = can cover debt" if dscr >= 1.0 else "BELOW 1.0x — RISK",
        delta_color="normal" if dscr >= 1.0 else "inverse",
    )

# ── DSCR Gauge ────────────────────────────────────────────────────────
st.markdown("")
dscr_col, info_col = st.columns([1, 2])

with dscr_col:
    dscr_color = "#00d084" if dscr >= 1.25 else ("#fcb900" if dscr >= 1.0 else "#eb144c")
    fig_dscr = go.Figure(go.Indicator(
        mode="gauge+number",
        value=dscr,
        number=dict(suffix="x", font=dict(size=48, color="#e6f1ff")),
        title=dict(text="Debt Service Coverage Ratio", font=dict(size=16, color="#ccd6f6")),
        gauge=dict(
            axis=dict(range=[0, 3], tickfont=dict(color="#a8b2d1"), tickcolor="#a8b2d1",
                      dtick=0.5),
            bar=dict(color=dscr_color, thickness=0.75),
            bgcolor="rgba(168,178,209,0.1)",
            bordercolor="rgba(168,178,209,0.3)",
            steps=[
                dict(range=[0, 1.0], color="rgba(235,20,76,0.2)"),
                dict(range=[1.0, 1.25], color="rgba(252,185,0,0.2)"),
                dict(range=[1.25, 3], color="rgba(0,208,132,0.2)"),
            ],
            threshold=dict(
                line=dict(color="#e6f1ff", width=3),
                thickness=0.8,
                value=1.0,
            ),
        ),
    ))
    fig_dscr.update_layout(
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a8b2d1"),
        margin=dict(t=60, b=20, l=30, r=30),
    )
    st.plotly_chart(fig_dscr, use_container_width=True)

with info_col:
    st.markdown(f"""
    ### DSCR Breakdown
    | Component | Amount |
    |-----------|--------|
    | **Net Operating Income** (Revenue - Expenses) | **${kpis['net_operating_income']:,.0f}** |
    | **Annual Debt Service** (Bonds + Techny Loan) | **${kpis['debt_service']:,.0f}** |
    | **DSCR** (NOI / Debt Service) | **{dscr:.2f}x** |

    **What this means:**
    - **Above 1.25x** — Healthy. Comfortable margin to cover debt obligations.
    - **1.0x - 1.25x** — Caution. Minimal buffer; any revenue shortfall threatens debt payments.
    - **Below 1.0x** — Operating income alone cannot cover debt service.
      The arena depends on cash reserves or other sources to make bond payments.

    *Note: DSCR is calculated from annualized 7-month budget data. Actual DSCR may vary
    based on seasonal revenue patterns and timing of debt payments.*
    """)

st.markdown("---")

# ── Visual summary charts ─────────────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    # Hidden cash flows donut
    hidden = load_hidden_cash_flows()
    fig_hidden = go.Figure(go.Pie(
        labels=hidden["Item"],
        values=hidden["Annual Impact"],
        hole=0.5,
        marker=dict(
            colors=["#ff6b6b", "#ee5a24", "#f0932b", "#ffbe76", "#6ab04c", "#22a6b3"],
            line=dict(color="#0a192f", width=2),
        ),
        textinfo="label+value",
        texttemplate="%{label}<br>$%{value:,.0f}",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}<br>%{percent:.1%}<extra></extra>",
    ))
    fig_hidden.update_layout(
        title=dict(text="Hidden Cash Outflows Breakdown", font=dict(size=16, color="#ccd6f6")),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a8b2d1"),
        showlegend=False,
        annotations=[dict(text=f"<b>${hidden['Annual Impact'].sum():,.0f}</b><br>Total/yr",
                          x=0.5, y=0.5, font_size=16, font_color="#e6f1ff", showarrow=False)],
    )
    st.plotly_chart(fig_hidden, use_container_width=True)

with col_right:
    # Expense approval breakdown
    summary = load_expense_flow_summary()
    fig_approval = go.Figure(go.Pie(
        labels=summary["Approval Method"],
        values=summary["% of Total"],
        hole=0.5,
        marker=dict(
            colors=["#00b894", "#fdcb6e", "#6c5ce7", "#b2bec3"],
            line=dict(color="#0a192f", width=2),
        ),
        textinfo="percent+label",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>%{percent:.1%}<br>$%{value:,.0f}<extra></extra>",
    ))
    fig_approval.update_layout(
        title=dict(text="Expense Approval Breakdown", font=dict(size=16, color="#ccd6f6")),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#a8b2d1"),
        showlegend=False,
        annotations=[dict(text="<b>25.5%</b><br>Board-Approved",
                          x=0.5, y=0.5, font_size=14, font_color="#e6f1ff", showarrow=False)],
    )
    st.plotly_chart(fig_approval, use_container_width=True)

st.markdown("---")

# Quick context
st.markdown(
    """
    ### Key Findings

    | Finding | Detail |
    |---------|--------|
    | **Hidden cash outflows** | ~$916K/year in debt service and cash obligations excluded from the board's primary Budget vs. Actuals report |
    | **Limited board approval** | Only 25.5% of expenses require individual invoice approval by the Board President |
    | **CSCG auto-pay** | 21% of expenses ($227K/6mo) flow through CSCG without invoice-level approval |
    | **Unauthorized modifications** | Multiple budget line items changed by CSCG without formal board amendment |
    | **Scoreboard economics** | Current deal projects negative NPV of -$14.6K over 10 years vs. +$17.5K for a cheaper alternative |

    ---
    *Use the sidebar to navigate to detailed pages.*
    """
)
