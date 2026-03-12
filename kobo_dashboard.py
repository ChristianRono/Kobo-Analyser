"""
Home — File upload, date range & filter controls.
All selections are stored in st.session_state and shared across pages.
"""

import streamlit as st
import pandas as pd
from utils import (
    inject_css, sidebar_logo, sidebar_divider, sidebar_user,
    load_data, apply_filters, no_data_screen,
    NAVY, GOLD, CREAM, WHITE, MUTED, GREEN, RED,
    ATTENDANCE_NOTE, ATTENDANCE_NOTE_SHORT
)

st.set_page_config(
    page_title="TcnAfrica · Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    sidebar_logo()
    sidebar_divider()

    st.markdown(
        f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.12em;'
        f'color:{MUTED};font-weight:600;margin-bottom:6px;">📂 Data Source</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Upload Kobo Excel Export (.xlsx)",
        type=["xlsx", "xls"],
        label_visibility="collapsed",
        key="file_uploader",
    )

    if uploaded:
        file_bytes = uploaded.read()
        # Only reload if file changed
        if st.session_state.get("file_name") != uploaded.name:
            raw_df, warns = load_data(file_bytes)
            st.session_state["raw_df"]    = raw_df
            st.session_state["file_name"] = uploaded.name
            st.session_state["load_warns"] = warns
            # Reset filters on new file
            valid = raw_df["session_date"].dropna()
            st.session_state["date_from"] = valid.min().date()
            st.session_state["date_to"]   = valid.max().date()
            st.session_state["f_county"]  = []
            st.session_state["f_trainer"] = []
            st.session_state["f_module"]  = []
            st.session_state["f_level"]   = []

    raw_df = st.session_state.get("raw_df", None)

    if raw_df is not None and not raw_df.empty:
        for w in st.session_state.get("load_warns", []):
            st.warning(w, icon="⚠️")

        sidebar_divider()
        st.markdown(
            f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.12em;'
            f'color:{MUTED};font-weight:600;margin-bottom:6px;">📅 Date Range</div>',
            unsafe_allow_html=True,
        )
        valid = raw_df["session_date"].dropna()
        min_d, max_d = valid.min().date(), valid.max().date()

        d_from = st.date_input("From", value=st.session_state.get("date_from", min_d),
                               min_value=min_d, max_value=max_d, key="date_from")
        d_to   = st.date_input("To",   value=st.session_state.get("date_to",   max_d),
                               min_value=min_d, max_value=max_d, key="date_to")

        sidebar_divider()
        st.markdown(
            f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.12em;'
            f'color:{MUTED};font-weight:600;margin-bottom:6px;">🔍 Filters</div>',
            unsafe_allow_html=True,
        )
        st.multiselect("County",
            sorted(raw_df["county"].replace("", pd.NA).dropna().unique()),
            default=st.session_state.get("f_county", []), key="f_county")
        st.multiselect("Trainer",
            sorted(raw_df["trainer_name"].replace("", pd.NA).dropna().unique()),
            default=st.session_state.get("f_trainer", []), key="f_trainer")
        st.multiselect("Module",
            sorted(raw_df["module"].replace("", pd.NA).dropna().unique()),
            default=st.session_state.get("f_module", []), key="f_module")
        if "level" in raw_df.columns:
            st.multiselect("Level",
                sorted(raw_df["level"].replace("", pd.NA).dropna().unique()),
                default=st.session_state.get("f_level", []), key="f_level")

        # Store filtered df in session state so all pages can use it
        filtered = apply_filters(raw_df)
        st.session_state["filtered_df"] = filtered

    else:
        st.markdown(
            f'<div style="font-size:12px;color:{MUTED};">Upload a file to begin.</div>',
            unsafe_allow_html=True,
        )

    sidebar_divider()
    sidebar_user()


# ── Main content ──────────────────────────────────────────────────────────────
if raw_df is None or raw_df.empty:
    no_data_screen()
    st.stop()

df = st.session_state.get("filtered_df", raw_df)

# ── Welcome banner ────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:{NAVY};border-radius:12px;padding:32px 36px;
            margin-bottom:24px;border-bottom:4px solid {GOLD};">
    <div style="font-family:'Playfair Display',serif;font-size:28px;
                font-weight:700;color:{WHITE};margin-bottom:6px;">
        TcnAfrica Field Report Dashboard
    </div>
    <div style="font-size:14px;color:#a0b4cc;margin-bottom:16px;">
        Kobo Collect  ·  {st.session_state.get('file_name','—')}
    </div>
    <div style="display:flex;gap:24px;flex-wrap:wrap;">
        <div style="color:{GOLD};font-size:13px;font-weight:600;">
            📅 {df['session_date'].min().strftime('%d %b %Y') if not df.empty else '—'}
            &nbsp;→&nbsp;
            {df['session_date'].max().strftime('%d %b %Y') if not df.empty else '—'}
        </div>
        <div style="color:#a0b4cc;font-size:13px;">
            {len(df):,} sessions &nbsp;·&nbsp;
            {df['county'].nunique()} counties &nbsp;·&nbsp;
            {df['trainer_name'].nunique()} trainers
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Attendance note ───────────────────────────────────────────────────────────
st.info(ATTENDANCE_NOTE)

# ── Quick-stats overview ──────────────────────────────────────────────────────
st.markdown(
    f'<div class="sec-title">At a Glance</div>'
    f'<div class="sec-sub">Key figures for the selected date range and filters</div>',
    unsafe_allow_html=True,
)

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

from utils import kpi
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi("Sessions", f"{n_sessions:,}", "Kobo submissions",
                    "tag-blue", "in selected range", "kpi-navy"),
                unsafe_allow_html=True)
with k2:
    st.markdown(kpi("Session-Attendances", f"{n_attended:,}",
                    f"Rate: {att_rate}", "tag-green",
                    f"of {n_enrolled:,} enrolled",
                    "kpi-green",
                    note=ATTENDANCE_NOTE_SHORT if True else ""),
                unsafe_allow_html=True)

with k3:
    ab_pct = f"{n_absent/n_enrolled*100:.1f}%" if n_enrolled else "—"
    st.markdown(kpi("Absences", f"{n_absent:,}", f"{ab_pct} of enrolled",
                    "tag-red", "across all sessions", "kpi-red"),
                unsafe_allow_html=True)
with k4:
    st.markdown(kpi("Counties", str(n_counties), county_str[:40],
                    "tag-gold", f"{n_trainers} trainers active"),
                unsafe_allow_html=True)
with k5:
    st.markdown(kpi("Collected", f"{fee_total+grad_total:,.0f}",
                    "KES total", "tag-blue",
                    f"Fee {fee_total:,.0f} + Grad {grad_total:,.0f}", "kpi-navy"),
                unsafe_allow_html=True)


st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ── Navigation cards ──────────────────────────────────────────────────────────
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(
    f'<div class="sec-title">Navigate the Dashboard</div>'
    f'<div class="sec-sub">Use the sidebar or click a page below</div>',
    unsafe_allow_html=True,
)

nav1, nav2, nav3, nav4 = st.columns(4)

def nav_card(icon, title, desc, colour=NAVY):
    return (
        f'<div style="background:{WHITE};border-radius:10px;padding:22px 20px;'
        f'border:1px solid #d8cfc0;box-shadow:0 4px 16px rgba(15,30,53,0.07);'
        f'border-top:3px solid {colour};">'
        f'<div style="font-size:28px;margin-bottom:10px;">{icon}</div>'
        f'<div style="font-family:\'Playfair Display\',serif;font-size:15px;'
        f'font-weight:600;color:{NAVY};margin-bottom:6px;">{title}</div>'
        f'<div style="font-size:12px;color:{MUTED};">{desc}</div>'
        f'</div>'
    )

with nav1:
    st.markdown(nav_card("📊", "Overview",
        "KPI cards, attendance trend, monthly breakdown, county and module charts.",
        NAVY), unsafe_allow_html=True)
with nav2:
    st.markdown(nav_card("📋", "Sessions & Notes",
        "Full sessions table, field notes from trainers, trainer leaderboard.",
        GOLD), unsafe_allow_html=True)
with nav3:
    st.markdown(nav_card("🔍", "Record Inspector",
        "Search any record, view full details and attached payment photos.",
        GREEN), unsafe_allow_html=True)
with nav4:
    st.markdown(nav_card("📄", "PDF Export",
        "Generate and download a styled PDF report with optional sections.",
        RED), unsafe_allow_html=True)
