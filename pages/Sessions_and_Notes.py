"""
Page 2 — Sessions & Notes: full sessions table, field notes, trainer detail.
"""

import streamlit as st
import pandas as pd
from utils import (
    inject_css, sidebar_logo, sidebar_divider, sidebar_user,
    get_filtered_df, no_data_screen, attendance_note_box,
    NAVY, GOLD, CREAM, WHITE, MUTED, GREEN,
)

st.set_page_config(
    page_title="TcnAfrica · Sessions & Notes",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

with st.sidebar:
    sidebar_logo()
    sidebar_divider()
    st.markdown(
        f'<div style="font-size:11px;color:{MUTED};padding:4px 0;">'
        f'Filters are set on the 🏠 Home page.</div>',
        unsafe_allow_html=True,
    )
    sidebar_divider()
    sidebar_user()

df = get_filtered_df()
if df is None or df.empty:
    no_data_screen()
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="sec-title" style="font-size:24px;">Sessions & Notes</div>'
    f'<div class="sec-sub">{len(df):,} sessions in the selected range</div>',
    unsafe_allow_html=True,
)
attendance_note_box()

# ── Sessions Table ────────────────────────────────────────────────────────────
st.markdown('<div class="sec-title">Session Submissions</div>'
            '<div class="sec-sub">All records — scrollable and sortable</div>',
            unsafe_allow_html=True)

show = {
    "session_date": "Date",         "trainer_name": "Trainer",
    "county":       "County",       "class_name":   "Class",
    "ward":         "Ward",         "module":       "Module",
    "level":        "Level",        "total_learners":"Enrolled",
    "attended":     "Attendances*", "absent":       "Absent",
    "fee_received": "Fee (KES)",    "remarks":      "Notes",
}
disp = df[[c for c in show if c in df.columns]].rename(columns=show).copy()
if "Date" in disp.columns:
    disp["Date"] = pd.to_datetime(disp["Date"]).dt.strftime("%d %b %Y")

st.dataframe(disp, use_container_width=True,
             height=min(520, (len(disp) + 1) * 38),
             hide_index=True)
st.caption("* Session-attendances, not unique learners")

st.markdown("<hr>", unsafe_allow_html=True)

# ── Field Notes + Trainer breakdown ──────────────────────────────────────────
tb1, tb2 = st.columns([3, 2])

with tb1:
    notes_df = df[
        df["remarks"].str.strip().str.lower()
          .apply(lambda x: x not in ["", "nan", "none", "n/a", "no", "nil"])
    ].reset_index(drop=True)

    n_notes = len(notes_df)
    NOTES_PER_PAGE = 10

    st.markdown(
        f'<div class="sec-title">Field Notes</div>'
        f'<div class="sec-sub">{n_notes} trainer remarks in range</div>',
        unsafe_allow_html=True,
    )

    if notes_df.empty:
        st.markdown(
            f'<div style="font-size:13px;color:{MUTED};padding:14px 0;">'
            f'No remarks recorded in this period.</div>',
            unsafe_allow_html=True,
        )
    else:
        n_pages = max(1, -(-n_notes // NOTES_PER_PAGE))
        if n_pages > 1:
            pg1, pg2, pg3 = st.columns([1, 2, 1])
            with pg2:
                page = st.number_input(
                    f"Page (1-{n_pages})", min_value=1, max_value=n_pages,
                    value=1, step=1, key="notes_page",
                    label_visibility="collapsed")
            with pg1:
                st.markdown(
                    f'<div style="font-size:11px;color:{MUTED};padding-top:10px;">'
                    f'Page {int(page)} of {n_pages}</div>', unsafe_allow_html=True)
            with pg3:
                st.markdown(
                    f'<div style="font-size:11px;color:{MUTED};padding-top:10px;'
                    f'text-align:right;">{n_notes} total</div>', unsafe_allow_html=True)
        else:
            page = 1

        start_i = (int(page) - 1) * NOTES_PER_PAGE
        page_notes = notes_df.iloc[start_i: start_i + NOTES_PER_PAGE]

        notes_html = ""
        for _, row in page_notes.iterrows():
            dt = (row["session_date"].strftime("%d %b %Y")
                  if pd.notna(row["session_date"]) else "")
            notes_html += (
                f'<div class="trainer-note">'
                f'<div class="trainer-note-label">'
                f'{row["trainer_name"]}  ·  {row["county"]}  ·  {dt}'
                f'</div>"{row["remarks"]}"</div>'
            )

        st.markdown(
            f'<div style="height:480px;overflow-y:auto;padding-right:6px;'
            f'scrollbar-width:thin;scrollbar-color:{GOLD} {CREAM};">'
            f'{notes_html}</div>',
            unsafe_allow_html=True,
        )

with tb2:
    st.markdown('<div class="sec-title">Trainer Detail</div>'
                '<div class="sec-sub">Performance per trainer</div>',
                unsafe_allow_html=True)

    trainer_df = df[df["trainer_name"] != ""].groupby("trainer_name").agg(
        Sessions    =("row_id",        "count"),
        Enrolled    =("total_learners","sum"),
        Attendances =("attended",      "sum"),
        Absent      =("absent",        "sum"),
        Fee_KES     =("fee_received",  "sum"),
    ).reset_index().sort_values("Attendances", ascending=False)
    trainer_df.columns = ["Trainer","Sessions","Enrolled","Attendances*","Absent","Fee (KES)"]
    trainer_df["Fee (KES)"] = trainer_df["Fee (KES)"].apply(lambda x: f"{x:,.0f}")
    trainer_df["Att. Rate"] = (
        (trainer_df["Attendances*"] / trainer_df["Enrolled"] * 100)
        .apply(lambda x: f"{x:.0f}%" if trainer_df["Enrolled"].sum() > 0 else "—")
    )

    st.dataframe(trainer_df, use_container_width=True,
                 height=400, hide_index=True)
    st.caption("* Session-attendances, not unique learners")

    # Summary totals
    st.markdown(
        f'<div style="background:{WHITE};border-radius:8px;padding:14px 16px;'
        f'border:1px solid #d8cfc0;margin-top:12px;">'
        f'<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.1em;'
        f'color:{MUTED};font-weight:600;margin-bottom:8px;">Totals</div>'
        f'<div style="display:flex;gap:24px;flex-wrap:wrap;">'
        f'<div><div style="font-family:\'Playfair Display\',serif;font-size:22px;'
        f'font-weight:700;color:{NAVY};">{int(df["attended"].sum()):,}</div>'
        f'<div style="font-size:11px;color:{MUTED};">Session-attendances</div></div>'
        f'<div><div style="font-family:\'Playfair Display\',serif;font-size:22px;'
        f'font-weight:700;color:{GOLD};">{df["fee_received"].sum():,.0f}</div>'
        f'<div style="font-size:11px;color:{MUTED};">KES collected</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )
