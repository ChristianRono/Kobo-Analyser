"""
Page 1 — Overview: KPI cards, all charts, county & module summaries.
"""

import streamlit as st
import pandas as pd
from utils import (
    inject_css, sidebar_logo, sidebar_divider, sidebar_user,
    get_raw_df, get_filtered_df, no_data_screen,
    attendance_note_box, kpi,
    fig_trend, fig_monthly, fig_county, fig_module_donut,
    fig_fees, fig_trainers,
    NAVY, GOLD, CREAM, WHITE, MUTED, GREEN, RED,
    ATTENDANCE_NOTE_SHORT,
)

st.set_page_config(
    page_title="TcnAfrica · Overview",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

with st.sidebar:
    sidebar_logo()
    sidebar_divider()
    st.markdown(
        f'<div style="font-size:11px;color:{MUTED};padding:4px 0 8px;">'
        f'Filters are set on the 🏠 Home page.</div>',
        unsafe_allow_html=True,
    )
    raw_df = get_raw_df()
    if raw_df is not None and not raw_df.empty:
        f = st.session_state
        parts = []
        if f.get("f_county"):  parts.append(f"County: {', '.join(f['f_county'])}")
        if f.get("f_trainer"): parts.append(f"Trainer: {', '.join(f['f_trainer'][:2])}{'…' if len(f['f_trainer'])>2 else ''}")
        if f.get("f_module"):  parts.append(f"Module: {', '.join(f['f_module'])}")
        if parts:
            st.markdown(
                f'<div style="background:rgba(201,168,76,0.12);border-radius:6px;'
                f'padding:8px 10px;font-size:11px;color:#a0b4cc;">'
                + "<br>".join(parts) + "</div>",
                unsafe_allow_html=True,
            )
    sidebar_divider()
    sidebar_user()

# ── Guard ─────────────────────────────────────────────────────────────────────
df = get_filtered_df()
if df is None or df.empty:
    no_data_screen()
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
d_from = st.session_state.get("date_from")
d_to   = st.session_state.get("date_to")
h1, h2 = st.columns([3, 1])
with h1:
    st.markdown(
        f'<div class="sec-title" style="font-size:24px;">Overview</div>'
        f'<div class="sec-sub">'
        f'{d_from.strftime("%d %b %Y") if d_from else ""}  —  '
        f'{d_to.strftime("%d %b %Y") if d_to else ""}  ·  '
        f'{len(df):,} sessions</div>',
        unsafe_allow_html=True,
    )
with h2:
    st.markdown(
        f'<div style="text-align:right;padding-top:10px;">'
        f'<span class="status-pill">● &nbsp;{len(df):,} records</span>'
        f'</div>', unsafe_allow_html=True,
    )

attendance_note_box()

# ── KPI Row ───────────────────────────────────────────────────────────────────
n_sessions  = len(df)
n_enrolled  = int(df["total_learners"].sum())
n_attended  = int(df["attended"].sum())
n_absent    = int(df["absent"].sum())
att_rate    = f"{n_attended/n_enrolled*100:.1f}%" if n_enrolled else "—"
n_counties  = df["county"].nunique()
n_trainers  = df["trainer_name"].nunique()
fee_total   = df["fee_received"].sum()
grad_total  = df["graduation_fee"].sum()
county_str  = " · ".join(sorted(df["county"].replace("", pd.NA).dropna().unique()))

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi("Sessions", f"{n_sessions:,}", "Kobo submissions",
                    "tag-blue", "in selected range", "kpi-navy"), unsafe_allow_html=True)
with k2:
    st.markdown(kpi("Session-Attendances", f"{n_attended:,}",
                    f"Rate: {att_rate}", "tag-green",
                    f"of {n_enrolled:,} enrolled", "kpi-green",
                    note=ATTENDANCE_NOTE_SHORT), unsafe_allow_html=True)
with k3:
    ab_pct = f"{n_absent/n_enrolled*100:.1f}%" if n_enrolled else "—"
    st.markdown(kpi("Absences", f"{n_absent:,}", f"{ab_pct} of enrolled",
                    "tag-red", "across all sessions", "kpi-red"), unsafe_allow_html=True)
with k4:
    st.markdown(kpi("Counties", str(n_counties), county_str[:40],
                    "tag-gold", f"{n_trainers} trainers active"), unsafe_allow_html=True)
with k5:
    st.markdown(kpi("Collected", f"{fee_total+grad_total:,.0f}",
                    "KES total", "tag-blue",
                    f"Fee {fee_total:,.0f} + Grad {grad_total:,.0f}", "kpi-navy"),
                unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Charts Row 1 ──────────────────────────────────────────────────────────────
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(fig_trend(df),   use_container_width=True, config={"displayModeBar": False})
with c2:
    st.plotly_chart(fig_monthly(df), use_container_width=True, config={"displayModeBar": False})

# ── Charts Row 2 ──────────────────────────────────────────────────────────────
c3, c4, c5 = st.columns([2, 1, 2])
with c3:
    st.plotly_chart(fig_county(df),       use_container_width=True, config={"displayModeBar": False})
with c4:
    st.markdown('<div class="sec-title">Module Split</div>'
                '<div class="sec-sub">Session-attendances by module</div>',
                unsafe_allow_html=True)
    st.plotly_chart(fig_module_donut(df), use_container_width=True, config={"displayModeBar": False})
with c5:
    st.plotly_chart(fig_fees(df),         use_container_width=True, config={"displayModeBar": False})

# ── Trainer Leaderboard + Summary Tables ─────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
lt1, lt2 = st.columns([2, 1])

with lt1:
    st.markdown('<div class="sec-title">Trainer Leaderboard</div>'
                '<div class="sec-sub">By total session-attendances in selected range</div>',
                unsafe_allow_html=True)
    st.plotly_chart(fig_trainers(df, top_n=min(15, n_trainers)),
                    use_container_width=True, config={"displayModeBar": False})

with lt2:
    st.markdown('<div class="sec-title">County Summary</div>'
                '<div class="sec-sub">Sessions, attendances & fees</div>',
                unsafe_allow_html=True)
    ct = df.groupby("county").agg(
        Sessions   =("row_id",        "count"),
        Enrolled   =("total_learners","sum"),
        Attendances=("attended",      "sum"),
        Absent     =("absent",        "sum"),
        Fee_KES    =("fee_received",  "sum"),
    ).reset_index().sort_values("Attendances", ascending=False)
    ct.columns = ["County", "Sessions", "Enrolled", "Attendances*", "Absent", "Fee (KES)"]
    ct["Fee (KES)"] = ct["Fee (KES)"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(ct, use_container_width=True, hide_index=True, height=220)
    st.caption("* Session-attendances, not unique learners")

    st.markdown('<div class="sec-title" style="margin-top:16px;">Module Summary</div>',
                unsafe_allow_html=True)
    mt = df.groupby("module").agg(
        Sessions   =("row_id",   "count"),
        Attendances=("attended", "sum"),
    ).reset_index().sort_values("Attendances", ascending=False)
    mt = mt[mt["module"] != ""]
    mt.columns = ["Module", "Sessions", "Attendances*"]
    st.dataframe(mt, use_container_width=True, hide_index=True)
    st.caption("* Session-attendances, not unique learners")
