"""
utils.py — Shared constants, styles, data loader, chart builders.
Imported by every page. Never run directly.
"""

import io
import re
import warnings
from datetime import date, datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
import os

load_dotenv()  # loads .env when running locally; no-op on Streamlit Cloud

def get_api_token() -> str:
    """Load token from Streamlit secrets (cloud) or .env (local)."""
    try:
        return st.secrets["KOBO_API_TOKEN"]
    except (KeyError, FileNotFoundError):
        return os.getenv("KOBO_API_TOKEN", "")

# ─────────────────────────────────────────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────────────────────────────────────────
NAVY  = "#0f1e35"
GOLD  = "#c9a84c"
CREAM = "#f5f0e8"
WHITE = "#ffffff"
GREEN = "#2a7a5a"
RED   = "#8b2a2a"
MUTED = "#7a8fa8"

# ─────────────────────────────────────────────────────────────────────────────
# ATTENDANCE NOTE — shown wherever attendance figures appear
# ─────────────────────────────────────────────────────────────────────────────
ATTENDANCE_NOTE = (
    "⚠️ **Note on attendance figures:** Numbers shown are "
    "**session-attendances** (total bodies in seats per session), "
    "not unique individuals. The same learner attending multiple sessions "
    "is counted each time. There is no unique learner ID in the Kobo export."
)

ATTENDANCE_NOTE_SHORT = (
    "Session-attendances, not unique people. "
    "Repeat learners are counted per session."
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS  (injected by every page via inject_css())
# ─────────────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;600;700&family=Source+Sans+3:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Source Sans 3', sans-serif;
        background-color: {CREAM};
    }}
    [data-testid="stSidebar"] {{
        background-color: {NAVY} !important;
        border-right: 3px solid {GOLD};
    }}
    [data-testid="stSidebar"] * {{ color: #a0b4cc !important; }}
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: {WHITE} !important;
        font-family: 'Playfair Display', serif !important;
    }}
    [data-testid="stSidebar"] label {{
        color: #8aa0b8 !important;
        font-size: 11px !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-weight: 600;
    }}
    [data-testid="stSidebar"] .stButton > button {{
        background: {GOLD}; color: {NAVY}; border: none;
        border-radius: 6px; font-weight: 700; width: 100%; margin-top: 8px;
    }}
    [data-testid="stSidebar"] .stButton > button:hover {{
        background: #e8c97a; color: {NAVY};
    }}
    .main .block-container {{
        background-color: {CREAM};
        padding-top: 1.5rem;
        max-width: 1400px;
    }}
    .kpi-card {{
        background: {WHITE}; border-radius: 10px; padding: 22px 22px 16px;
        border: 1px solid #d8cfc0; box-shadow: 0 4px 24px rgba(15,30,53,0.09);
        position: relative; overflow: hidden; height: 100%;
    }}
    .kpi-card::before {{
        content:''; position:absolute; top:0; left:0; right:0;
        height:3px; background:{GOLD};
    }}
    .kpi-card.kpi-green::before {{ background:{GREEN}; }}
    .kpi-card.kpi-red::before   {{ background:{RED};   }}
    .kpi-card.kpi-navy::before  {{ background:{NAVY};  }}
    .kpi-label {{
        font-size:10px; text-transform:uppercase; letter-spacing:0.13em;
        color:{MUTED}; font-weight:600; margin-bottom:8px;
    }}
    .kpi-value {{
        font-family:'Playfair Display',serif; font-size:32px;
        color:{NAVY}; font-weight:700; line-height:1; margin-bottom:6px;
    }}
    .kpi-tag {{
        display:inline-block; font-size:11px; font-weight:600;
        padding:3px 9px; border-radius:4px; margin-bottom:4px;
    }}
    .tag-blue  {{ color:{NAVY};  background:#e8f0f8; }}
    .tag-gold  {{ color:#7a5a10; background:#fdf3d8; }}
    .tag-green {{ color:{GREEN}; background:#e8f5ef; }}
    .tag-red   {{ color:{RED};   background:#f5e8e8; }}
    .kpi-sub {{ font-size:11px; color:{MUTED}; margin-top:4px; }}
    .kpi-note {{
        font-size:10px; color:{MUTED}; font-style:italic;
        margin-top:6px; padding-top:6px;
        border-top:1px solid #ede5d5;
    }}
    .sec-title {{
        font-family:'Playfair Display',serif; font-size:17px;
        font-weight:600; color:{NAVY}; margin-bottom:2px;
    }}
    .sec-sub {{ font-size:12px; color:{MUTED}; margin-bottom:10px; }}
    .att-note {{
        background:#fdf3d8; border-left:3px solid {GOLD};
        border-radius:0 6px 6px 0; padding:10px 14px;
        font-size:12px; color:#7a5a10; margin:10px 0 16px;
    }}
    .trainer-note {{
        background:#f5f0e8; border-left:3px solid {GOLD};
        border-radius:0 6px 6px 0; padding:12px 16px;
        margin-bottom:8px; font-style:italic; font-size:13px; color:#3a4f6a;
    }}
    .trainer-note-label {{
        font-size:10px; text-transform:uppercase; letter-spacing:0.1em;
        color:{MUTED}; font-weight:600; margin-bottom:4px; font-style:normal;
    }}
    .status-pill {{
        display:inline-flex; align-items:center; gap:6px;
        padding:5px 14px; background:#e8f5ef;
        border:1px solid #b2d9c8; border-radius:20px;
        font-size:12px; font-weight:600; color:{GREEN};
    }}
    hr {{ border-color:#d8cfc0; margin:18px 0; }}
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR LOGO  (called by every page)
# ─────────────────────────────────────────────────────────────────────────────
def sidebar_logo():
    st.sidebar.markdown(f"""
    <div style="padding:8px 0 20px;">
        <div style="font-family:'Playfair Display',serif;font-size:20px;
                    color:{WHITE};letter-spacing:0.02em;">
            Tcn<span style="color:{GOLD};">Africa</span>
        </div>
        <div style="font-size:10px;color:{MUTED};letter-spacing:0.12em;
                    text-transform:uppercase;margin-top:4px;">
            Field Report · Kobo
        </div>
    </div>
    """, unsafe_allow_html=True)


def sidebar_user():
    st.sidebar.markdown(f"""
    <div style="margin-top:20px;display:flex;align-items:center;gap:12px;">
        <div style="width:36px;height:36px;background:{GOLD};border-radius:50%;
                    display:flex;align-items:center;justify-content:center;
                    font-weight:700;color:{NAVY};font-size:15px;">TC</div>
        <div>
            <div style="font-size:13px;font-weight:600;color:{WHITE};">TcnAfrica Admin</div>
            <div style="font-size:11px;color:{MUTED};">Field Coordinator</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def sidebar_divider():
    st.sidebar.markdown(
        f"<hr style='border-color:#1a2f4a;margin:14px 0;'>",
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

HEADER_ALIASES = {
    "start":                                   "start_dt",
    "end":                                     "end_dt",
    "enter a date and time":                   "session_date",
    "enter facilitators name":                 "trainer_name",
    "enter county":                            "county",
    "enter class name (bomet county)":         "class_bomet",
    "enter class name (kericho county)":       "class_kericho",
    "enter class name (narok county)":         "class_narok",
    "type in ward name":                       "ward",
    "expected class hours":                    "class_hours",
    "select class level":                      "level",
    "select module":                           "module",
    "type in lesson taught":                   "lesson",
    "type in field assignment":                "assignment",
    "total number of learners":                "total_learners",
    "learners that attended class":            "attended",
    "absent learners":                         "absent",
    "class attendance":                        "attendance_photo_file",
    "class attendance_url":                    "attendance_photo_url",
    "total fee received":                      "fee_received",
    "take photo of payment information":       "payment_photo_file",
    "take photo of payment information _url":  "payment_photo_url",
    "transaction code (if fee sent)":          "transaction_code",
    "reason why no transaction code":          "no_code_reason",
    "graduation fee (if received)":            "graduation_fee",
    "enter tla (actual amount)":               "tla_amount",
    "class requirement":                       "class_requirement",
    "other comment":                           "remarks",
    "_submission_time":                        "submission_time",
    "_submitted_by":                           "submitted_by",
    "_id":                                     "row_id",
    "_uuid":                                   "uuid",
    "_record your current location_latitude":  "latitude",
    "_record your current location_longitude": "longitude",
    "_index":                                  "row_index",

    # ── Kobo API group-prefixed aliases ────────────────────────────────────
    "group_vi7dq15/enter_facilitators_name":        "trainer_name",
    "group_vi7dq15/enter_a_date_and_time":          "session_date",
    "group_es1rh04/enter_county":                   "county",
    "group_es1rh04/enter_class_name_bomet_county":  "class_bomet",
    "group_es1rh04/enter_class_name_kericho_county":"class_kericho",
    "group_es1rh04/enter_class_name_narok_county":  "class_narok",
    "group_es1rh04/type_in_ward_name":              "ward",
    "group_es1rh04/select_module":                  "module",
    "group_es1rh04/type_in_lesson_taught":          "lesson",
    "group_es1rh04/type_in_field_assign_n_a_if_not_not_done": "assignment",
    "group_es1rh04/total_number_of_learners":       "total_learners",
    "group_es1rh04/learners_that_attended_class":   "attended",
    "group_es1rh04/absent_learners":                "absent",
    "group_es1rh04/select_class_level":             "level",
    "group_es1rh04/class_attendance":               "attendance_photo_url",
    "group_qm5qq25/total_fee_received":             "fee_received",
    "group_qm5qq25/take_photo_of_payment_information": "payment_photo_url",
    "group_qm5qq25/transaction_code_if_fee_sent":   "transaction_code",
    "group_qm5qq25/graduation_fee_if_received":     "graduation_fee",
    "group_jm2xr29/enter_tla_actual_amount":        "tla_amount",
    "group_jm2xr29/class_requirement":              "remarks",
    "group_jm2xr29/other_comment":                  "remarks",  # fallback if remarks not yet mapped
    "record_your_current_location":                 "geolocation",
    "_geolocation":                                 "geolocation",
    "_submission_time":                             "submission_time",
    "_uuid":                                        "uuid",
    "start":                                        "start_dt",
    "end":                                          "end_dt",
    "_attachments":                                 "attachments",
}


def _norm(h) -> str:
    if h is None:
        return ""
    return re.sub(r"\s+", " ", str(h).strip().lower())


def _coerce_date(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return pd.NaT
    if isinstance(val, (datetime, date)):
        ts = pd.Timestamp(val)
        return ts.tz_localize(None) if ts.tzinfo is not None else ts
    try:
        ts = pd.to_datetime(str(val).strip(), utc=True)
        return ts.tz_convert(None)   # strips tz, keeps local time value
    except Exception:
        return pd.NaT


def _coerce_num(series: pd.Series) -> pd.Series:
    def clean(v):
        s = re.sub(r"[^\d.\-]", "", str(v).strip())
        return s if s else "0"
    return pd.to_numeric(series.apply(clean), errors="coerce").fillna(0)

@st.cache_data(show_spinner="Loading data…")
def load_data(source: bytes | pd.DataFrame) -> tuple:
    load_warns: list[str] = []

    # ── Normalise input to a raw DataFrame ───────────────────────────────────
    if isinstance(source, pd.DataFrame):
        # Coming from KoboToolbox API: already a flat DataFrame.
        # Treat every column header as a potential alias to remap.
        raw_headers = list(source.columns)
        data = source.copy().reset_index(drop=True)

        col_map: dict = {}
        used: set = set()
        for i, h in enumerate(raw_headers):
            n = _norm(h)
            matched = None
            if n in HEADER_ALIASES:
                matched = HEADER_ALIASES[n]
            else:
                for alias, internal in HEADER_ALIASES.items():
                    if alias and n and (alias in n or n.startswith(alias[:12])):
                        matched = internal
                        break
            if matched and matched not in used:
                col_map[i] = matched
                used.add(matched)

        data.columns = [col_map.get(i, f"_x{i}") for i in range(len(data.columns))]

    else:
        # Coming from a file upload: bytes → Excel → header detection.
        buf = io.BytesIO(source)
        raw = pd.read_excel(buf, header=None, dtype=object)

        header_idx = None
        for i in range(min(6, len(raw))):
            vals = [_norm(v) for v in raw.iloc[i]]
            if any(v in ("start", "end") or "county" in v
                   or "facilitator" in v or "date and time" in v for v in vals):
                header_idx = i
                break
        if header_idx is None:
            header_idx = 0
            load_warns.append("Header row not auto-detected; assuming row 1.")

        raw_headers = list(raw.iloc[header_idx])
        data = raw.iloc[header_idx + 1:].reset_index(drop=True)

        col_map: dict = {}
        used: set = set()
        for i, h in enumerate(raw_headers):
            n = _norm(h)
            matched = None
            if n in HEADER_ALIASES:
                matched = HEADER_ALIASES[n]
            else:
                for alias, internal in HEADER_ALIASES.items():
                    if alias and n and (alias in n or n.startswith(alias[:12])):
                        matched = internal
                        break
            if matched and matched not in used:
                col_map[i] = matched
                used.add(matched)

        data.columns = [col_map.get(i, f"_x{i}") for i in range(len(data.columns))]

    # ── Everything below is shared between both paths ─────────────────────────
    keep = [c for c in data.columns if not c.startswith("_x")]
    df = data[keep].copy()

    for dc in ["session_date", "start_dt", "end_dt", "submission_time"]:
        if dc in df.columns:
            df[dc] = df[dc].apply(_coerce_date)

    if "session_date" not in df.columns or df["session_date"].isna().all():
        if "start_dt" in df.columns and df["start_dt"].notna().any():
            df["session_date"] = df["start_dt"]
            load_warns.append("Used 'start' timestamp as session date.")
        else:
            load_warns.append("WARNING: No date column found.")
            df["session_date"] = pd.NaT

    for nc in ["total_learners", "attended", "absent",
               "fee_received", "graduation_fee", "tla_amount",
               "latitude", "longitude"]:
        if nc in df.columns:
            df[nc] = _coerce_num(df[nc])
        else:
            df[nc] = 0.0

    BAD = {"nan", "none", "nat", ""}
    for tc in ["trainer_name", "county", "ward", "module", "level",
               "lesson", "assignment", "remarks",
               "class_bomet", "class_kericho", "class_narok",
               "transaction_code", "payment_photo_url",
               "attendance_photo_url", "uuid"]:
        if tc in df.columns:
            df[tc] = (df[tc].astype(str).str.strip()
                            .apply(lambda x: "" if x.lower() in BAD else x))

    if "trainer_name" in df.columns:
        df["trainer_name"] = df["trainer_name"].str.title().str.strip()

    def pick_class(row):
        for col in ["class_bomet", "class_kericho", "class_narok"]:
            v = row.get(col, "")
            if v and v.lower() not in BAD:
                return v
        return ""
    df["class_name"] = df.apply(pick_class, axis=1)

    df = df.dropna(how="all").reset_index(drop=True)
    n_before = len(df)
    df = df[df["session_date"].notna() & (df["session_date"] != pd.NaT)].copy()
    dropped = n_before - len(df)
    if dropped:
        load_warns.append(f"{dropped} row(s) had no valid date and were skipped.")

    if df.empty:
        load_warns.append("No data rows remain after filtering.")
        return df, load_warns

    df = df.sort_values("session_date").reset_index(drop=True)
    if "row_id" not in df.columns:
        df["row_id"] = df.index + 1

    return df, load_warns


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def get_raw_df():
    """Return the loaded dataframe from session state, or None."""
    return st.session_state.get("raw_df", None)


def get_filtered_df():
    """Return the date+filter-applied dataframe from session state, or None."""
    return st.session_state.get("filtered_df", None)


def get_filters():
    """Return current filter values from session state."""
    return {
        "date_from":  st.session_state.get("date_from",  None),
        "date_to":    st.session_state.get("date_to",    None),
        "f_county":   st.session_state.get("f_county",   []),
        "f_trainer":  st.session_state.get("f_trainer",  []),
        "f_module":   st.session_state.get("f_module",   []),
        "f_level":    st.session_state.get("f_level",    []),
    }


def apply_filters(raw_df: pd.DataFrame) -> pd.DataFrame:
    f = get_filters()
    df = raw_df.copy()

    # Guarantee session_date is tz-naive datetime before .dt.date access
    df["session_date"] = pd.to_datetime(df["session_date"], errors="coerce").dt.tz_localize(None)

    if f["date_from"] and f["date_to"]:
        df = df[(df["session_date"].dt.date >= f["date_from"]) &
                (df["session_date"].dt.date <= f["date_to"])]
    if f["f_county"]:
        df = df[df["county"].isin(f["f_county"])]
    if f["f_trainer"]:
        df = df[df["trainer_name"].isin(f["f_trainer"])]
    if f["f_module"]:
        df = df[df["module"].isin(f["f_module"])]
    if f["f_level"] and "level" in df.columns:
        df = df[df["level"].isin(f["f_level"])]
    return df.reset_index(drop=True)


def no_data_screen():
    """Standard screen shown when no file has been uploaded yet."""
    st.markdown(f"""
    <div style="text-align:center;padding:90px 40px;">
        <div style="font-family:'Playfair Display',serif;font-size:32px;
                    font-weight:700;color:{NAVY};margin-bottom:14px;">
            TcnAfrica Field Report Dashboard
        </div>
        <div style="font-size:15px;color:{MUTED};max-width:500px;
                    margin:0 auto 32px;">
            Upload your Kobo Excel export on the
            <b>🏠 Home</b> page to get started.
        </div>
        <div style="font-size:48px;">📋</div>
    </div>
    """, unsafe_allow_html=True)


def attendance_note_box():
    """Render the standard attendance disclaimer box."""
    st.markdown(
        f'<div class="att-note">'
        f'⚠️ <b>Attendance figures = session-attendances, not unique people.</b> '
        f'The same learner attending multiple sessions is counted each time. '
        f'No unique learner ID exists in the Kobo export.'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# KPI CARD HTML
# ─────────────────────────────────────────────────────────────────────────────

def kpi(label, value, tag, tag_cls, sub, card_cls="", note=""):
    note_html = (f'<div class="kpi-note">{note}</div>' if note else "")
    return (
        f'<div class="kpi-card {card_cls}">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-tag {tag_cls}">{tag}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'{note_html}</div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────────────────────────────────────

BASE = dict(plot_bgcolor=WHITE, paper_bgcolor=WHITE,
            font=dict(family="Source Sans 3", color=NAVY))
_M  = dict(l=20, r=20, t=50, b=40)
_ML = dict(l=20, r=20, t=70, b=60)


def fig_trend(df):
    t = (df.groupby(df["session_date"].dt.date)
           .agg(attended=("attended", "sum")).reset_index())
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=t["session_date"], y=t["attended"], mode="lines+markers",
        line=dict(color=NAVY, width=2.5),
        marker=dict(color=GOLD, size=6, line=dict(color=NAVY, width=1.5)),
        fill="tozeroy", fillcolor="rgba(15,30,53,0.06)",
        hovertemplate="<b>%{x}</b><br>Session-attendances: %{y}<extra></extra>",
    ))
    fig.update_layout(**BASE, margin=_M,
        title=dict(text="Session-Attendance Trend Over Time",
                   font=dict(family="Playfair Display", size=15, color=NAVY)),
        xaxis=dict(gridcolor="#ede5d5", tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#ede5d5", tickfont=dict(size=11),
                   title="Session-attendances"),
        height=280, showlegend=False)
    return fig


def fig_monthly(df):
    df2 = df.copy()
    df2["month"] = df2["session_date"].dt.to_period("M").astype(str)
    m = df2.groupby("month").agg(
        sessions=("row_id",   "count"),
        attended=("attended", "sum")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=m["month"], y=m["sessions"], name="Sessions",
                         marker_color=NAVY, yaxis="y", offsetgroup=1,
                         hovertemplate="<b>%{x}</b><br>Sessions: %{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=m["month"], y=m["attended"], name="Session-Attendances",
                             mode="lines+markers",
                             line=dict(color=GOLD, width=2.5),
                             marker=dict(color=GOLD, size=7), yaxis="y2",
                             hovertemplate="<b>%{x}</b><br>Session-attendances: %{y}<extra></extra>"))
    fig.update_layout(**BASE, margin=_ML,
        title=dict(text="Monthly Sessions & Session-Attendances",
                   font=dict(family="Playfair Display", size=15, color=NAVY)),
        xaxis=dict(tickangle=-45, tickfont=dict(size=10), gridcolor="#ede5d5"),
        yaxis=dict(title="Sessions", gridcolor="#ede5d5", tickfont=dict(size=11)),
        yaxis2=dict(title="Session-Attendances", overlaying="y", side="right",
                    tickfont=dict(size=11), showgrid=False),
        legend=dict(orientation="h", y=1.18, x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12)),
        height=340)
    return fig


def fig_county(df):
    c = (df.groupby("county")["attended"].sum()
           .reset_index().sort_values("attended", ascending=True))
    fig = go.Figure(go.Bar(
        x=c["attended"], y=c["county"], orientation="h",
        marker_color=NAVY, text=c["attended"], textposition="outside",
        textfont=dict(size=11),
        hovertemplate="<b>%{y}</b><br>Session-attendances: %{x}<extra></extra>"))
    fig.update_layout(**BASE, margin=_M,
        title=dict(text="Session-Attendances by County",
                   font=dict(family="Playfair Display", size=15, color=NAVY)),
        xaxis=dict(gridcolor="#ede5d5", tickfont=dict(size=11),
                   title="Session-attendances"),
        yaxis=dict(gridcolor=WHITE, tickfont=dict(size=12, color=NAVY)),
        height=max(200, len(c) * 48 + 80))
    return fig


def fig_module_donut(df):
    m = (df.groupby("module")["attended"].sum()
           .reset_index().sort_values("attended", ascending=False))
    m = m[m["module"] != ""]
    fig = go.Figure(go.Pie(
        labels=m["module"], values=m["attended"], hole=0.62,
        marker=dict(colors=[NAVY, GOLD, GREEN, RED, MUTED][:len(m)],
                    line=dict(color=WHITE, width=3)),
        textinfo="label+percent",
        textfont=dict(family="Source Sans 3", size=12),
        hovertemplate="<b>%{label}</b><br>Session-attendances: %{value}<br>%{percent}<extra></extra>"))
    fig.update_layout(**BASE, margin=_M, showlegend=False, height=230)
    return fig


def fig_fees(df):
    df2 = df.copy()
    df2["month"] = df2["session_date"].dt.to_period("M").astype(str)
    f = df2.groupby("month").agg(fee=("fee_received",   "sum"),
                                  grad=("graduation_fee", "sum")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=f["month"], y=f["fee"],
                         name="Fee Received", marker_color=NAVY))
    fig.add_trace(go.Bar(x=f["month"], y=f["grad"],
                         name="Graduation Fee", marker_color=GOLD))
    fig.update_layout(**BASE, margin=_ML, barmode="stack",
        title=dict(text="Monthly Collections (KES)",
                   font=dict(family="Playfair Display", size=15, color=NAVY)),
        xaxis=dict(tickangle=-45, tickfont=dict(size=10), gridcolor="#ede5d5"),
        yaxis=dict(gridcolor="#ede5d5", tickfont=dict(size=11)),
        legend=dict(orientation="h", y=1.18, x=0, bgcolor="rgba(0,0,0,0)",
                    font=dict(size=12)),
        height=310)
    return fig


def fig_trainers(df, top_n=15):
    t = (df.groupby("trainer_name")["attended"].sum()
           .reset_index().sort_values("attended", ascending=True).tail(top_n))
    t = t[t["trainer_name"] != ""]
    fig = go.Figure(go.Bar(
        x=t["attended"], y=t["trainer_name"], orientation="h",
        marker_color=GOLD, text=t["attended"], textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{y}</b><br>Session-attendances: %{x}<extra></extra>"))
    fig.update_layout(**BASE, margin=_M,
        title=dict(text=f"Top {top_n} Trainers by Session-Attendances",
                   font=dict(family="Playfair Display", size=15, color=NAVY)),
        xaxis=dict(gridcolor="#ede5d5", tickfont=dict(size=11),
                   title="Session-attendances"),
        yaxis=dict(gridcolor=WHITE, tickfont=dict(size=10)),
        height=max(260, len(t) * 30 + 80))
    return fig
