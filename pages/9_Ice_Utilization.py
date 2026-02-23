"""
Page 9: Ice Utilization
Weekday/weekend ice allocation and Winnetka usage gap analysis.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Ice Utilization | NSIA", layout="wide", page_icon=":ice_hockey:")

CHART_BG = "rgba(0,0,0,0)"
GRID_COLOR = "rgba(168,178,209,0.15)"
FONT_COLOR = "#a8b2d1"
TITLE_COLOR = "#ccd6f6"
CLUB_COLORS = {"NT": "#fcb900", "Winnetka": "#64ffda", "Wilmette": "#f78da7"}

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

st.title("Ice Utilization")
st.caption("Weekday & weekend ice allocation analysis and Winnetka usage gaps")

from utils.data_loader import (
    load_weekday_ice_summary,
    load_weekend_ice_summary,
    load_winnetka_weekend_summary,
    load_winnetka_day_level_gaps,
)

# ══════════════════════════════════════════════════════════════════════════
# Section 1: Weekday Allocation
# ══════════════════════════════════════════════════════════════════════════
st.header("Weekday Ice Allocation")

weekday = load_weekday_ice_summary()
totals_wd = weekday[weekday["Day"] == "Total"]
daily = weekday[weekday["Day"] != "Total"]

col1, col2, col3 = st.columns(3)
for i, club in enumerate(["NT", "Winnetka", "Wilmette"]):
    club_total = totals_wd[totals_wd["Club"] == club]
    curr = club_total["Current Hours"].values[0] if len(club_total) > 0 else 0
    prop = club_total["Proposed Hours"].values[0] if len(club_total) > 0 else 0
    with [col1, col2, col3][i]:
        delta_hrs = prop - curr
        st.metric(f"{club} — Hours/Week",
                  f"{curr:.1f}h current",
                  delta=f"{delta_hrs:+.1f}h proposed" if delta_hrs != 0 else "No change")

# Grouped bar: hours per day per club (Current vs Proposed)
view = st.radio("View", ["Current", "Proposed", "Both"], horizontal=True, key="wd_view")

days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
fig_wd = go.Figure()

for club in ["NT", "Winnetka", "Wilmette"]:
    club_data = daily[daily["Club"] == club].copy()
    club_data["Day"] = pd.Categorical(club_data["Day"], categories=days_order, ordered=True)
    club_data = club_data.sort_values("Day")

    if view in ("Current", "Both"):
        fig_wd.add_trace(go.Bar(
            x=club_data["Day"],
            y=club_data["Current Hours"],
            name=f"{club} (Current)" if view == "Both" else club,
            marker=dict(color=CLUB_COLORS[club],
                        opacity=0.6 if view == "Both" else 1.0,
                        line=dict(width=1, color="rgba(255,255,255,0.2)")),
            text=[f"{v:.1f}" for v in club_data["Current Hours"]],
            textposition="outside",
            textfont=dict(size=9, color=FONT_COLOR),
            hovertemplate=f"<b>{club}</b> (Current)<br>" + "%{x}: %{y:.1f}h<extra></extra>",
        ))
    if view in ("Proposed", "Both"):
        fig_wd.add_trace(go.Bar(
            x=club_data["Day"],
            y=club_data["Proposed Hours"],
            name=f"{club} (Proposed)" if view == "Both" else club,
            marker=dict(color=CLUB_COLORS[club],
                        pattern=dict(shape="/") if view == "Both" else None,
                        line=dict(width=1, color="rgba(255,255,255,0.2)")),
            text=[f"{v:.1f}" for v in club_data["Proposed Hours"]],
            textposition="outside",
            textfont=dict(size=9, color=FONT_COLOR),
            hovertemplate=f"<b>{club}</b> (Proposed)<br>" + "%{x}: %{y:.1f}h<extra></extra>",
        ))

fig_wd.update_layout(
    title="Weekday Ice Hours by Club & Day",
    barmode="group",
    yaxis_title="Hours",
    xaxis_title="Day of Week",
)
style_chart(fig_wd, 450)
st.plotly_chart(fig_wd, use_container_width=True)

# Summary table
with st.expander("Weekday Summary Table"):
    pivot = weekday.pivot_table(index="Club", columns="Day",
                                values=["Current Hours", "Proposed Hours"],
                                aggfunc="first")
    st.dataframe(pivot, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════
# Section 2: Weekend Allocation
# ══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("Weekend Ice Allocation")

weekend = load_weekend_ice_summary()

wknd_view = st.radio("View", ["Current", "Proposed", "Both"], horizontal=True, key="we_view")

for wknd in ["Weekend 1", "Weekend 2"]:
    wknd_data = weekend[weekend["Weekend"] == wknd]
    fig_we = go.Figure()

    for club in ["NT", "Winnetka", "Wilmette"]:
        club_row = wknd_data[wknd_data["Club"] == club]
        if club_row.empty:
            continue
        r = club_row.iloc[0]
        days = ["Saturday", "Sunday"]

        if wknd_view in ("Current", "Both"):
            fig_we.add_trace(go.Bar(
                x=days,
                y=[r["Current Saturday"], r["Current Sunday"]],
                name=f"{club} (Current)" if wknd_view == "Both" else club,
                marker=dict(color=CLUB_COLORS[club],
                            opacity=0.6 if wknd_view == "Both" else 1.0,
                            line=dict(width=1, color="rgba(255,255,255,0.2)")),
                text=[f"{v:.1f}" for v in [r["Current Saturday"], r["Current Sunday"]]],
                textposition="outside",
                textfont=dict(size=10, color=FONT_COLOR),
                hovertemplate=f"<b>{club}</b> (Current)<br>" + "%{x}: %{y:.1f}h<extra></extra>",
            ))
        if wknd_view in ("Proposed", "Both"):
            fig_we.add_trace(go.Bar(
                x=days,
                y=[r["Proposed Saturday"], r["Proposed Sunday"]],
                name=f"{club} (Proposed)" if wknd_view == "Both" else club,
                marker=dict(color=CLUB_COLORS[club],
                            pattern=dict(shape="/") if wknd_view == "Both" else None,
                            line=dict(width=1, color="rgba(255,255,255,0.2)")),
                text=[f"{v:.1f}" for v in [r["Proposed Saturday"], r["Proposed Sunday"]]],
                textposition="outside",
                textfont=dict(size=10, color=FONT_COLOR),
                hovertemplate=f"<b>{club}</b> (Proposed)<br>" + "%{x}: %{y:.1f}h<extra></extra>",
            ))

    fig_we.update_layout(
        title=f"{wknd} — Ice Hours by Club",
        barmode="group",
        yaxis_title="Hours",
    )
    style_chart(fig_we, 380)
    st.plotly_chart(fig_we, use_container_width=True)

# Weekend summary table
with st.expander("Weekend Summary Table"):
    st.dataframe(
        weekend,
        use_container_width=True,
        hide_index=True,
        column_config={c: st.column_config.NumberColumn(format="%.1f")
                       for c in weekend.columns if c not in ("Club", "Weekend")},
    )

# ══════════════════════════════════════════════════════════════════════════
# Section 3: Winnetka Usage Gaps
# ══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.header("Winnetka Usage Gap Analysis")

wk_summary = load_winnetka_weekend_summary()
day_gaps = load_winnetka_day_level_gaps()

num_weekends = len(wk_summary)
total_gap = wk_summary["Gap_Total"].sum()
pct_underused = (wk_summary["Underused_Weekend"] == "YES").sum() / num_weekends * 100

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Weekends Analyzed", str(num_weekends))
with col2:
    st.metric("Total Gap Hours", f"{total_gap:.1f}h")
with col3:
    st.metric("% Underused Weekends", f"{pct_underused:.0f}%",
              delta="All weekends flagged" if pct_underused == 100 else None,
              delta_color="inverse" if pct_underused > 50 else "normal")

# Bar chart: owned vs used per weekend
fig_gaps = go.Figure()
fig_gaps.add_trace(go.Bar(
    x=[f"Wknd {w}" for w in wk_summary["WeekendNumber"]],
    y=wk_summary["TotalHours_club"],
    name="Owned Hours",
    marker=dict(color="#8ed1fc", line=dict(width=1, color="rgba(255,255,255,0.2)")),
    hovertemplate="Weekend %{x}<br>Owned: %{y:.1f}h<extra></extra>",
))
fig_gaps.add_trace(go.Bar(
    x=[f"Wknd {w}" for w in wk_summary["WeekendNumber"]],
    y=wk_summary["TotalHours_FriToSun_WithCut"],
    name="Used Hours",
    marker=dict(color="#64ffda", line=dict(width=1, color="rgba(255,255,255,0.2)")),
    hovertemplate="Weekend %{x}<br>Used: %{y:.1f}h<extra></extra>",
))
fig_gaps.update_layout(
    title="Winnetka: Owned vs Used Hours per Weekend",
    barmode="group",
    yaxis_title="Hours",
)
style_chart(fig_gaps, 420)
st.plotly_chart(fig_gaps, use_container_width=True)

# Day-level breakdown
st.subheader("Day-Level Gap Breakdown")

day_agg = day_gaps.groupby("Day")[["Club_Owned_Hours", "Used_Hours_WithCut", "Unused_Hours"]].sum().reset_index()
day_order = ["Friday", "Saturday", "Sunday"]
day_agg["Day"] = pd.Categorical(day_agg["Day"], categories=day_order, ordered=True)
day_agg = day_agg.sort_values("Day")

fig_day = go.Figure()
fig_day.add_trace(go.Bar(
    x=day_agg["Day"], y=day_agg["Club_Owned_Hours"],
    name="Owned", marker=dict(color="#8ed1fc"),
    hovertemplate="%{x}<br>Owned: %{y:.1f}h<extra></extra>",
))
fig_day.add_trace(go.Bar(
    x=day_agg["Day"], y=day_agg["Used_Hours_WithCut"],
    name="Used", marker=dict(color="#64ffda"),
    hovertemplate="%{x}<br>Used: %{y:.1f}h<extra></extra>",
))
fig_day.add_trace(go.Bar(
    x=day_agg["Day"], y=day_agg["Unused_Hours"],
    name="Gap (Unused)", marker=dict(color="#eb144c"),
    hovertemplate="%{x}<br>Gap: %{y:.1f}h<extra></extra>",
))
fig_day.update_layout(
    title="Usage Gaps by Day of Week (All Weekends Combined)",
    barmode="group",
    yaxis_title="Hours",
)
style_chart(fig_day, 380)
st.plotly_chart(fig_day, use_container_width=True)

# Detail tables in expander
with st.expander("Weekend Summary Detail"):
    st.dataframe(
        wk_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "WeekendStart": st.column_config.DateColumn(format="MM/DD/YYYY"),
            "WeekendEnd": st.column_config.DateColumn(format="MM/DD/YYYY"),
            "Gap_Total": st.column_config.NumberColumn("Gap (hrs)", format="%.1f"),
            "TotalHours_club": st.column_config.NumberColumn("Owned (hrs)", format="%.1f"),
            "TotalHours_FriToSun_WithCut": st.column_config.NumberColumn("Used (hrs)", format="%.1f"),
        },
    )

with st.expander("Day-Level Gap Detail"):
    st.dataframe(
        day_gaps,
        use_container_width=True,
        hide_index=True,
        column_config={
            "WeekendStart": st.column_config.DateColumn(format="MM/DD/YYYY"),
            "WeekendEnd": st.column_config.DateColumn(format="MM/DD/YYYY"),
            "Club_Owned_Hours": st.column_config.NumberColumn(format="%.1f"),
            "Used_Hours_WithCut": st.column_config.NumberColumn(format="%.1f"),
            "Unused_Hours": st.column_config.NumberColumn(format="%.1f"),
        },
    )

# Warning callout
st.warning(
    "**Underutilization Alert:** 100% of analyzed weekends show Winnetka ice time going unused. "
    "Total gap across all weekends: **{:.1f} hours**. Weekend 6 is missing from the sequence. "
    "This represents contracted ice time that Winnetka is paying for but not using — "
    "an opportunity for either schedule optimization or reallocation to other clubs.".format(total_gap)
)
