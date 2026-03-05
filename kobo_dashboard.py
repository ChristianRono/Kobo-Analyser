"""
TcnAfrica Field Report Dashboard — Streamlit App
================================================
Run with:  streamlit run kobo_dashboard.py

Requirements:
    pip install streamlit pandas openpyxl plotly reportlab kaleido
"""

import io
import tempfile
import warnings
from datetime import date, datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

warnings.filterwarnings("ignore")

try:
    import kaleido  # noqa: F401
    HAS_KALEIDO = True
except ImportError:
    HAS_KALEIDO = False

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
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TcnAfrica · Field Report Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
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
    color:{NAVY}; font-weight:700; line-height:1; margin-bottom:8px;
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
.sec-title {{
    font-family:'Playfair Display',serif; font-size:17px;
    font-weight:600; color:{NAVY}; margin-bottom:2px;
}}
.sec-sub {{ font-size:12px; color:{MUTED}; margin-bottom:10px; }}
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
# DATA LOADING
# ─────────────────────────────────────────────────────────────────────────────

# Maps normalised header text → internal column name
HEADER_ALIASES = {
    "start":                              "start_dt",
    "end":                                "end_dt",
    "enter a date and time":              "session_date",
    "enter facilitators name":            "trainer_name",
    "enter county":                       "county",
    "enter class name (bomet county)":    "class_bomet",
    "enter class name (kericho county)":  "class_kericho",
    "enter class name (narok county)":    "class_narok",
    "type in ward name":                  "ward",
    "expected class hours":               "class_hours",
    "select class level":                 "level",
    "select module":                      "module",
    "type in lesson taught":              "lesson",
    "type in field assignment":           "assignment",
    "total number of learners":           "total_learners",
    "learners that attended class":       "attended",
    "absent learners":                    "absent",
    "total fee received":                 "fee_received",
    "transaction code (if fee sent)":     "transaction_code",
    "graduation fee (if received)":       "graduation_fee",
    "enter tla (actual amount)":          "tla_amount",
    "class requirement":                  "class_requirement",
    "other comment":                      "remarks",
    "_submission_time":                   "submission_time",
    "_submitted_by":                      "submitted_by",
    "_id":                                "row_id",
    "_index":                             "row_index",
}


def _norm(h) -> str:
    """Lowercase + strip for fuzzy header matching."""
    import re
    if h is None:
        return ""
    return re.sub(r"\s+", " ", str(h).strip().lower())


def _coerce_date(val):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return pd.NaT
    if isinstance(val, (datetime, date)):
        return pd.Timestamp(val)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return pd.to_datetime(str(val).strip(), format=fmt)
        except Exception:
            pass
    try:
        return pd.to_datetime(str(val).strip(), infer_datetime_format=True, dayfirst=True)
    except Exception:
        return pd.NaT


def _coerce_num(series: pd.Series) -> pd.Series:
    import re
    def clean(v):
        s = re.sub(r"[^\d.\-]", "", str(v).strip())
        return s if s else "0"
    return pd.to_numeric(series.apply(clean), errors="coerce").fillna(0)


@st.cache_data(show_spinner="Loading data…")
def load_data(file_bytes: bytes) -> tuple:
    """Load any Kobo Excel export robustly. Returns (df, warnings_list)."""
    load_warns = []
    buf = io.BytesIO(file_bytes)

    # Read everything as strings to avoid Excel type coercion problems
    raw = pd.read_excel(buf, header=None, dtype=object)

    # ── Find header row (search first 6 rows) ──────────────────────────────
    header_idx = None
    for i in range(min(6, len(raw))):
        vals = [_norm(v) for v in raw.iloc[i]]
        if any(v in ("start", "end") or "county" in v or "facilitator" in v
               or "date and time" in v for v in vals):
            header_idx = i
            break
    if header_idx is None:
        header_idx = 0
        load_warns.append("Header row not auto-detected; assuming row 1.")

    raw_headers = list(raw.iloc[header_idx])
    data = raw.iloc[header_idx + 1:].reset_index(drop=True)

    # ── Map headers ────────────────────────────────────────────────────────
    col_map = {}
    used_internals: set = set()
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
        if matched and matched not in used_internals:
            col_map[i] = matched
            used_internals.add(matched)

    data.columns = [col_map.get(i, f"_x{i}") for i in range(len(data.columns))]
    # keep only mapped columns
    keep = [c for c in data.columns if not c.startswith("_x")]
    df = data[keep].copy()

    # ── Dates ──────────────────────────────────────────────────────────────
    for dc in ["session_date", "start_dt", "end_dt", "submission_time"]:
        if dc in df.columns:
            df[dc] = df[dc].apply(_coerce_date)

    # Fallback: derive session_date from start_dt
    if "session_date" not in df.columns or df["session_date"].isna().all():
        if "start_dt" in df.columns and df["start_dt"].notna().any():
            df["session_date"] = df["start_dt"]
            load_warns.append("Used 'start' timestamp as session date.")
        else:
            load_warns.append(
                "WARNING: No date column found. "
                "Expected 'Enter a date and time' in the header row."
            )
            df["session_date"] = pd.NaT

    # ── Numerics ───────────────────────────────────────────────────────────
    for nc in ["total_learners", "attended", "absent",
               "fee_received", "graduation_fee", "tla_amount"]:
        if nc in df.columns:
            df[nc] = _coerce_num(df[nc])
        else:
            df[nc] = 0.0

    # ── Text ───────────────────────────────────────────────────────────────
    BAD = {"nan", "none", "nat", ""}
    for tc in ["trainer_name", "county", "ward", "module", "level",
               "lesson", "assignment", "remarks",
               "class_bomet", "class_kericho", "class_narok"]:
        if tc in df.columns:
            df[tc] = (df[tc].astype(str).str.strip()
                           .apply(lambda x: "" if x.lower() in BAD else x))

    # Title-case trainer names to merge duplicates caused by typos
    if "trainer_name" in df.columns:
        df["trainer_name"] = df["trainer_name"].str.title().str.strip()

    # Merge county-specific class columns into one
    def pick_class(row):
        for col in ["class_bomet", "class_kericho", "class_narok"]:
            v = row.get(col, "")
            if v and v.lower() not in BAD:
                return v
        return ""
    df["class_name"] = df.apply(pick_class, axis=1)

    # ── Drop fully-empty rows ──────────────────────────────────────────────
    df = df.dropna(how="all").reset_index(drop=True)

    # ── Drop rows with no valid date ───────────────────────────────────────
    n_before = len(df)
    df = df[df["session_date"].notna() & (df["session_date"] != pd.NaT)].copy()
    dropped = n_before - len(df)
    if dropped:
        load_warns.append(f"{dropped} row(s) had no valid date and were skipped.")

    if df.empty:
        load_warns.append(
            "No data rows remain after filtering. "
            "Possible causes: wrong file format, all rows empty, "
            "or date column not recognised."
        )
        return df, load_warns

    df = df.sort_values("session_date").reset_index(drop=True)

    if "row_id" not in df.columns:
        df["row_id"] = df.index + 1

    return df, load_warns


# ─────────────────────────────────────────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────────────────────────────────────────

BASE = dict(
    plot_bgcolor=WHITE, paper_bgcolor=WHITE,
    font=dict(family="Source Sans 3", color=NAVY),
)

# Default margin used by most charts
_M = dict(l=20, r=20, t=50, b=40)
# Wider top margin for charts that have a horizontal legend above the plot
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
    ))
    fig.update_layout(**BASE, margin=_M,
        title=dict(text="Attendance Trend Over Time",
                   font=dict(family="Playfair Display", size=15, color=NAVY)),
        xaxis=dict(gridcolor="#ede5d5", tickfont=dict(size=11)),
        yaxis=dict(gridcolor="#ede5d5", tickfont=dict(size=11)),
        height=280, showlegend=False)
    return fig


def fig_monthly(df):
    df2 = df.copy()
    df2["month"] = df2["session_date"].dt.to_period("M").astype(str)
    m = df2.groupby("month").agg(
        sessions=("row_id", "count"),
        attended=("attended", "sum")).reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=m["month"], y=m["sessions"], name="Sessions",
                         marker_color=NAVY, yaxis="y", offsetgroup=1))
    fig.add_trace(go.Scatter(x=m["month"], y=m["attended"], name="Attendance",
                             mode="lines+markers",
                             line=dict(color=GOLD, width=2.5),
                             marker=dict(color=GOLD, size=7), yaxis="y2"))
    fig.update_layout(**BASE, margin=_ML,
        title=dict(text="Monthly Sessions & Attendance",
                   font=dict(family="Playfair Display", size=15, color=NAVY)),
        xaxis=dict(tickangle=-45, tickfont=dict(size=10), gridcolor="#ede5d5"),
        yaxis=dict(title="Sessions", gridcolor="#ede5d5", tickfont=dict(size=11)),
        yaxis2=dict(title="Attendance", overlaying="y", side="right",
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
        textfont=dict(size=11)))
    fig.update_layout(**BASE, margin=_M,
        title=dict(text="Attendance by County",
                   font=dict(family="Playfair Display", size=15, color=NAVY)),
        xaxis=dict(gridcolor="#ede5d5", tickfont=dict(size=11)),
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
        textfont=dict(family="Source Sans 3", size=12)))
    fig.update_layout(**BASE, margin=_M, showlegend=False, height=230)
    return fig


def fig_fees(df):
    df2 = df.copy()
    df2["month"] = df2["session_date"].dt.to_period("M").astype(str)
    f = df2.groupby("month").agg(fee=("fee_received", "sum"),
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
        textfont=dict(size=10)))
    fig.update_layout(**BASE, margin=_M,
        title=dict(text=f"Top {top_n} Trainers by Attendance",
                   font=dict(family="Playfair Display", size=15, color=NAVY)),
        xaxis=dict(gridcolor="#ede5d5", tickfont=dict(size=11)),
        yaxis=dict(gridcolor=WHITE, tickfont=dict(size=10)),
        height=max(260, len(t) * 30 + 80))
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# KPI CARD HTML
# ─────────────────────────────────────────────────────────────────────────────

def kpi(label, value, tag, tag_cls, sub, card_cls=""):
    return (f'<div class="kpi-card {card_cls}">'
            f'<div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div>'
            f'<div class="kpi-tag {tag_cls}">{tag}</div>'
            f'<div class="kpi-sub">{sub}</div></div>')


# ─────────────────────────────────────────────────────────────────────────────
# PDF EXPORT
# ─────────────────────────────────────────────────────────────────────────────

def generate_pdf(df, d_from, d_to, figs,
                 include_notes=True, include_rawdata=True):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    def sty(name, **kw):
        return ParagraphStyle(name, **kw)

    rl_navy  = colors.HexColor(NAVY)
    rl_gold  = colors.HexColor(GOLD)
    rl_cream = colors.HexColor(CREAM)
    rl_muted = colors.HexColor(MUTED)
    rl_white = colors.white

    title_s  = sty("T",  fontName="Helvetica-Bold", fontSize=22,
                   textColor=rl_navy, spaceAfter=8, spaceBefore=4)
    gold_s   = sty("G",  fontName="Helvetica-Bold", fontSize=15,
                   textColor=rl_gold, spaceAfter=8, spaceBefore=4)
    sub_s    = sty("S",  fontName="Helvetica", fontSize=10,
                   textColor=rl_muted, spaceAfter=16, spaceBefore=2)
    sec_s    = sty("Sc", fontName="Helvetica-Bold", fontSize=13,
                   textColor=rl_navy, spaceBefore=14, spaceAfter=4)
    body_s   = sty("B",  fontName="Helvetica", fontSize=10,
                   textColor=rl_navy, spaceAfter=4)
    small_s  = sty("Sm", fontName="Helvetica", fontSize=8,
                   textColor=rl_muted, spaceAfter=2)
    note_s   = sty("N",  fontName="Helvetica-Oblique", fontSize=9,
                   textColor=colors.HexColor("#3a4f6a"),
                   backColor=rl_cream, spaceAfter=4, spaceBefore=2,
                   leftIndent=8, rightIndent=8)
    foot_s   = sty("F",  fontName="Helvetica", fontSize=8,
                   textColor=rl_muted, alignment=TA_CENTER, spaceBefore=6)

    story = []

    # Header
    story.append(Paragraph("TcnAfrica", title_s))
    story.append(Paragraph("Field Training Report", gold_s))
    story.append(Paragraph(
        f"Period: {d_from.strftime('%d %b %Y')} — {d_to.strftime('%d %b %Y')}  ·  "
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}", sub_s))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=rl_gold, spaceAfter=14))

    # KPI summary
    total_sessions  = len(df)
    total_learners  = int(df["total_learners"].sum())
    total_attended  = int(df["attended"].sum())
    att_rate = f"{total_attended/total_learners*100:.1f}%" if total_learners else "—"
    fee_total  = df["fee_received"].sum()
    grad_total = df["graduation_fee"].sum()

    kd = [["Metric", "Value"],
          ["Total Sessions",        str(total_sessions)],
          ["Total Enrolled",        f"{total_learners:,}"],
          ["Total Attendance",      f"{total_attended:,}"],
          ["Attendance Rate",       att_rate],
          ["Counties",              str(df["county"].nunique())],
          ["Trainers Active",       str(df["trainer_name"].nunique())],
          ["Fee Received (KES)",    f"{fee_total:,.0f}"],
          ["Graduation Fee (KES)",  f"{grad_total:,.0f}"],
          ["Total Collected (KES)", f"{fee_total + grad_total:,.0f}"]]

    def base_table(data, col_widths):
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), rl_navy),
            ("TEXTCOLOR",     (0, 0), (-1, 0), rl_white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1,-1), 9),
            ("ROWBACKGROUNDS",(0, 1), (-1,-1), [rl_cream, rl_white]),
            ("GRID",          (0, 0), (-1,-1), 0.4, colors.HexColor("#d8cfc0")),
            ("TOPPADDING",    (0, 0), (-1,-1), 5),
            ("BOTTOMPADDING", (0, 0), (-1,-1), 5),
            ("LEFTPADDING",   (0, 0), (-1,-1), 8),
            ("TEXTCOLOR",     (0, 1), (-1,-1), rl_navy),
            ("FONTNAME",      (0, 1), (0, -1), "Helvetica-Bold"),
        ]))
        return t

    # ── PAGE 1: KPI Summary ───────────────────────────────────────────────
    story.append(Paragraph("Summary", sec_s))
    story.append(base_table(kd, ["48%", "52%"]))
    story.append(Spacer(1, 18))

    # ── PAGE 1–2: Charts ──────────────────────────────────────────────────
    if HAS_KALEIDO:
        from reportlab.platypus import Image as RLImage
        for key, title, export_h, display_h in [
            ("trend",   "Attendance Trend Over Time",    340, 7.0),
            ("monthly", "Monthly Sessions & Attendance", 380, 7.8),
            ("fees",    "Monthly Collections (KES)",     360, 7.2),
            ("county",  "Attendance by County",          360, 7.2),
        ]:
            if key in figs:
                story.append(Paragraph(title, sec_s))
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    figs[key].write_image(tmp.name, width=800, height=export_h, scale=2)
                    story.append(RLImage(tmp.name, width=17*cm, height=display_h*cm))
                story.append(Spacer(1, 12))
    else:
        story.append(Paragraph(
            "Install kaleido (pip install kaleido) to include charts in the PDF.", small_s))

    # ── PAGE 3: County & Trainer summaries ───────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("County Summary", sec_s))
    cs = df.groupby("county").agg(
        Sessions=("row_id",        "count"),
        Enrolled=("total_learners","sum"),
        Attended=("attended",      "sum"),
        Absent  =("absent",        "sum"),
        Fee_KES =("fee_received",  "sum"),
    ).reset_index()
    cs.columns = ["County", "Sessions", "Enrolled", "Attended", "Absent", "Fee (KES)"]
    cs["Fee (KES)"] = cs["Fee (KES)"].apply(lambda x: f"{float(x):,.0f}")
    cd = [list(cs.columns)] + [[str(v) for v in r] for r in cs.values.tolist()]
    story.append(base_table(cd, [3.5*cm, 2.3*cm, 2.3*cm, 2.3*cm, 2*cm, 3.1*cm]))

    story.append(Spacer(1, 18))
    story.append(Paragraph("Module Summary", sec_s))
    ms = df[df["module"] != ""].groupby("module").agg(
        Sessions=("row_id",   "count"),
        Attended=("attended", "sum"),
        Absent  =("absent",   "sum"),
    ).reset_index().sort_values("Attended", ascending=False)
    ms.columns = ["Module", "Sessions", "Attended", "Absent"]
    md = [list(ms.columns)] + [[str(v) for v in r] for r in ms.values.tolist()]
    story.append(base_table(md, [5*cm, 3*cm, 3*cm, 3*cm]))

    story.append(Spacer(1, 18))
    story.append(Paragraph("Trainer Summary", sec_s))
    ts = df[df["trainer_name"] != ""].groupby("trainer_name").agg(
        Sessions=("row_id",       "count"),
        Attended=("attended",     "sum"),
        Fee_KES =("fee_received", "sum"),
    ).reset_index().sort_values("Attended", ascending=False)
    ts.columns = ["Trainer", "Sessions", "Attended", "Fee (KES)"]
    ts["Fee (KES)"] = ts["Fee (KES)"].apply(lambda x: f"{float(x):,.0f}")
    ttd = [list(ts.columns)] + [[str(v) for v in r] for r in ts.values.tolist()]
    story.append(base_table(ttd, [6*cm, 2.8*cm, 2.8*cm, 4*cm]))

    # ── PAGE 4: Field Notes ───────────────────────────────────────────────
    if include_notes:
        notes = df[
            df["remarks"].str.strip().str.lower()
              .apply(lambda x: x not in ["", "nan", "none", "n/a", "no", "nil"])
        ].reset_index(drop=True)

        if not notes.empty:
            story.append(PageBreak())
            story.append(Paragraph("Field Notes from Trainers", sec_s))
            story.append(Paragraph(
                f"{len(notes)} remarks recorded in the selected period.", body_s))
            story.append(Spacer(1, 6))
            for _, row in notes.iterrows():
                dt = row["session_date"].strftime("%d %b %Y") if pd.notna(row["session_date"]) else ""
                story.append(Paragraph(
                    f"<b>{row['trainer_name']}</b>  ·  {row['county']}  ·  {dt}", body_s))
                story.append(Paragraph(f"\"{row['remarks']}\"", note_s))
                story.append(Spacer(1, 4))

    # ── LAST PAGE(S): Raw session data ────────────────────────────────────
    if include_rawdata:
        story.append(PageBreak())
        story.append(Paragraph("Session Submissions — Full Data", sec_s))
        story.append(Paragraph(
            f"All {total_sessions:,} sessions in the selected date range, "
            f"sorted by session date.", body_s))
        story.append(Spacer(1, 6))

        disp_cols = ["session_date", "trainer_name", "county", "class_name",
                     "ward", "module", "level", "attended", "absent", "fee_received"]
        disp = df[[c for c in disp_cols if c in df.columns]].copy()
        disp["session_date"] = disp["session_date"].dt.strftime("%d %b %Y")
        col_headers = [c.replace("_", " ").title() for c in disp.columns]
        td = [col_headers] + [[str(v) for v in r] for r in disp.values.tolist()]
        widths = [2.2*cm, 3.2*cm, 1.8*cm, 2*cm,
                  2*cm, 1.8*cm, 1.5*cm, 1.2*cm, 1.2*cm, 2*cm]
        st_tbl = Table(td, colWidths=widths[:len(disp.columns)], repeatRows=1)
        st_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), rl_navy),
            ("TEXTCOLOR",     (0, 0), (-1, 0), rl_white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1,-1), 7),
            ("ROWBACKGROUNDS",(0, 1), (-1,-1), [rl_cream, rl_white]),
            ("GRID",          (0, 0), (-1,-1), 0.3, colors.HexColor("#d8cfc0")),
            ("TOPPADDING",    (0, 0), (-1,-1), 3),
            ("BOTTOMPADDING", (0, 0), (-1,-1), 3),
            ("LEFTPADDING",   (0, 0), (-1,-1), 4),
            ("TEXTCOLOR",     (0, 1), (-1,-1), rl_navy),
        ]))
        story.append(st_tbl)

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=rl_gold))
    story.append(Paragraph(
        f"TcnAfrica Field Report Dashboard  ·  Confidential  ·  "
        f"Generated {datetime.now().strftime('%d %b %Y %H:%M')}", foot_s))

    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"""
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

    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;'
                f'letter-spacing:.12em;color:{MUTED};font-weight:600;'
                f'margin-bottom:6px;">📂 Data Source</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Upload Kobo Excel Export (.xlsx)",
                                type=["xlsx", "xls"],
                                label_visibility="collapsed")

    st.markdown(f"<hr style='border-color:#1a2f4a;margin:14px 0;'>",
                unsafe_allow_html=True)

    raw_df   = None
    date_from = date_to = None
    f_county = f_trainer = f_module = f_level = []

    if uploaded:
        raw_df, load_warns = load_data(uploaded.read())

        if raw_df is None or raw_df.empty:
            st.error("No data loaded. Check the warnings below and verify your file format.")
            for w in (load_warns or []):
                st.warning(w)
        else:
            # Show any non-critical warnings
            for w in load_warns:
                st.warning(w, icon="⚠️")

            valid = raw_df["session_date"].dropna()
            min_d, max_d = valid.min().date(), valid.max().date()

            st.markdown(f'<div style="font-size:10px;text-transform:uppercase;'
                        f'letter-spacing:.12em;color:{MUTED};font-weight:600;'
                        f'margin-bottom:6px;">📅 Date Range</div>',
                        unsafe_allow_html=True)
            date_from = st.date_input("From", value=min_d,
                                      min_value=min_d, max_value=max_d)
            date_to   = st.date_input("To",   value=max_d,
                                      min_value=min_d, max_value=max_d)

            st.markdown(f"<hr style='border-color:#1a2f4a;margin:14px 0;'>",
                        unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:10px;text-transform:uppercase;'
                        f'letter-spacing:.12em;color:{MUTED};font-weight:600;'
                        f'margin-bottom:6px;">🔍 Filters</div>',
                        unsafe_allow_html=True)

            f_county  = st.multiselect("County",
                            sorted(raw_df["county"].replace("", pd.NA).dropna().unique()),
                            default=[])
            f_trainer = st.multiselect("Trainer",
                            sorted(raw_df["trainer_name"].replace("", pd.NA).dropna().unique()),
                            default=[])
            f_module  = st.multiselect("Module",
                            sorted(raw_df["module"].replace("", pd.NA).dropna().unique()),
                            default=[])
            if "level" in raw_df.columns:
                f_level = st.multiselect("Level",
                              sorted(raw_df["level"].replace("", pd.NA).dropna().unique()),
                              default=[])
    else:
        st.markdown(f'<div style="font-size:12px;color:{MUTED};">'
                    f'Upload a file to begin.</div>', unsafe_allow_html=True)

    st.markdown(f"<hr style='border-color:#1a2f4a;margin:14px 0;'>",
                unsafe_allow_html=True)
    st.markdown(f'<div style="font-size:10px;text-transform:uppercase;'
                f'letter-spacing:.12em;color:{MUTED};font-weight:600;'
                f'margin-bottom:8px;">📄 PDF Contents</div>',
                unsafe_allow_html=True)
    pdf_include_notes   = st.checkbox("Include Field Notes",   value=True,
                                      disabled=(raw_df is None or raw_df.empty))
    pdf_include_rawdata = st.checkbox("Include Raw Data Table", value=True,
                                      disabled=(raw_df is None or raw_df.empty))

    st.markdown(f"<hr style='border-color:#1a2f4a;margin:14px 0;'>",
                unsafe_allow_html=True)
    export_btn = st.button("⬇  Export PDF Report",
                           disabled=(raw_df is None or raw_df.empty))

    st.markdown(f"""
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


# ─────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────

if raw_df is None or raw_df.empty:
    st.markdown(f"""
    <div style="text-align:center;padding:90px 40px;">
        <div style="font-family:'Playfair Display',serif;font-size:32px;
                    font-weight:700;color:{NAVY};margin-bottom:14px;">
            TcnAfrica Field Report Dashboard
        </div>
        <div style="font-size:15px;color:{MUTED};max-width:500px;margin:0 auto 32px;">
            Upload your Kobo Excel export (.xlsx) from the sidebar to begin.
            Supports any date range — from a single day to multiple years.
        </div>
        <div style="font-size:48px;">📋</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────────────────────

df = raw_df.copy()
if date_from and date_to:
    df = df[(df["session_date"].dt.date >= date_from) &
            (df["session_date"].dt.date <= date_to)]
if f_county:
    df = df[df["county"].isin(f_county)]
if f_trainer:
    df = df[df["trainer_name"].isin(f_trainer)]
if f_module:
    df = df[df["module"].isin(f_module)]
if f_level and "level" in df.columns:
    df = df[df["level"].isin(f_level)]

if df.empty:
    st.warning("No records match the selected filters. Try adjusting the date range or filters.")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────────────────────────────────────

n_sessions  = len(df)
n_enrolled  = int(df["total_learners"].sum())
n_attended  = int(df["attended"].sum())
n_absent    = int(df["absent"].sum())
att_rate    = f"{n_attended/n_enrolled*100:.1f}%" if n_enrolled else "—"
n_counties  = df["county"].nunique()
n_trainers  = df["trainer_name"].nunique()
fee_total   = df["fee_received"].sum()
grad_total  = df["graduation_fee"].sum()
collected   = fee_total + grad_total
county_str  = " · ".join(sorted(df["county"].replace("", pd.NA).dropna().unique()))


# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────

h1, h2 = st.columns([3, 1])
with h1:
    d1 = date_from.strftime("%d %b %Y") if date_from else ""
    d2 = date_to.strftime("%d %b %Y")   if date_to   else ""
    st.markdown(
        f'<div class="sec-title" style="font-size:24px;">Field Training Report</div>'
        f'<div class="sec-sub">{d1} — {d2}  ·  Kobo Collect  ·  {n_sessions:,} sessions</div>',
        unsafe_allow_html=True)
with h2:
    st.markdown(
        f'<div style="text-align:right;padding-top:10px;">'
        f'<span class="status-pill">● &nbsp;{n_sessions:,} records loaded</span>'
        f'</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────────────────────────────────────

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(kpi("Sessions", f"{n_sessions:,}", "Kobo submissions",
                    "tag-blue", "in selected range", "kpi-navy"),
                unsafe_allow_html=True)
with k2:
    st.markdown(kpi("Attendance", f"{n_attended:,}", f"Rate: {att_rate}",
                    "tag-green", f"of {n_enrolled:,} enrolled", "kpi-green"),
                unsafe_allow_html=True)
with k3:
    ab_pct = f"{n_absent/n_enrolled*100:.1f}%" if n_enrolled else "—"
    st.markdown(kpi("Absent", f"{n_absent:,}", f"{ab_pct} of enrolled",
                    "tag-red", "across all sessions", "kpi-red"),
                unsafe_allow_html=True)
with k4:
    st.markdown(kpi("Counties", str(n_counties), county_str[:40],
                    "tag-gold", f"{n_trainers} trainers active"),
                unsafe_allow_html=True)
with k5:
    st.markdown(kpi("Collected", f"{collected:,.0f}",
                    "KES total", "tag-blue",
                    f"Fee {fee_total:,.0f} + Grad {grad_total:,.0f}", "kpi-navy"),
                unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# CHARTS — ROW 1
# ─────────────────────────────────────────────────────────────────────────────

all_figs = {}
c1, c2 = st.columns(2)
with c1:
    f = fig_trend(df);     all_figs["trend"]   = f
    st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})
with c2:
    f = fig_monthly(df);   all_figs["monthly"] = f
    st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
# CHARTS — ROW 2
# ─────────────────────────────────────────────────────────────────────────────

c3, c4, c5 = st.columns([2, 1, 2])
with c3:
    f = fig_county(df);         all_figs["county"]  = f
    st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})
with c4:
    st.markdown('<div class="sec-title">Module Split</div>'
                '<div class="sec-sub">By attendance</div>', unsafe_allow_html=True)
    f = fig_module_donut(df);   all_figs["modules"] = f
    st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})
with c5:
    f = fig_fees(df);           all_figs["fees"]    = f
    st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
# TRAINER LEADERBOARD  +  SUMMARY TABLES
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("<hr>", unsafe_allow_html=True)
lt1, lt2 = st.columns([2, 1])

with lt1:
    st.markdown('<div class="sec-title">Trainer Leaderboard</div>'
                '<div class="sec-sub">By total attendance in selected range</div>',
                unsafe_allow_html=True)
    f = fig_trainers(df, top_n=min(15, n_trainers))
    all_figs["trainers"] = f
    st.plotly_chart(f, use_container_width=True, config={"displayModeBar": False})

with lt2:
    st.markdown('<div class="sec-title">County Summary</div>'
                '<div class="sec-sub">Sessions, attendance & fees</div>',
                unsafe_allow_html=True)
    ct = df.groupby("county").agg(
        Sessions=("row_id",       "count"),
        Attended=("attended",     "sum"),
        Absent  =("absent",       "sum"),
        Fee_KES =("fee_received", "sum"),
    ).reset_index().sort_values("Attended", ascending=False)
    ct.columns = ["County", "Sessions", "Attended", "Absent", "Fee (KES)"]
    ct["Fee (KES)"] = ct["Fee (KES)"].apply(lambda x: f"{x:,.0f}")
    st.dataframe(ct, use_container_width=True, hide_index=True, height=200)

    st.markdown('<div class="sec-title" style="margin-top:16px;">Module Summary</div>',
                unsafe_allow_html=True)
    mt = df.groupby("module").agg(
        Sessions=("row_id",   "count"),
        Attended=("attended", "sum"),
    ).reset_index().sort_values("Attended", ascending=False)
    mt = mt[mt["module"] != ""]
    st.dataframe(mt, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────────────────
# SESSIONS TABLE  +  FIELD NOTES
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("<hr>", unsafe_allow_html=True)
tb1, tb2 = st.columns([3, 2])

with tb1:
    st.markdown(f'<div class="sec-title">Session Submissions</div>'
                f'<div class="sec-sub">All {n_sessions:,} records — scrollable</div>',
                unsafe_allow_html=True)
    show = {
        "session_date": "Date", "trainer_name": "Trainer",
        "county": "County",     "class_name": "Class",
        "ward": "Ward",         "module": "Module",
        "level": "Level",       "attended": "Attended",
        "absent": "Absent",     "fee_received": "Fee (KES)",
        "remarks": "Notes",
    }
    disp = df[[c for c in show if c in df.columns]].rename(columns=show).copy()
    if "Date" in disp.columns:
        disp["Date"] = pd.to_datetime(disp["Date"]).dt.strftime("%d %b %Y")
    st.dataframe(disp, use_container_width=True,
                 height=min(520, (n_sessions + 1) * 38),
                 hide_index=True)

with tb2:
    notes_df = df[
        df["remarks"].str.strip().str.lower()
          .apply(lambda x: x not in ["", "nan", "none", "n/a", "no", "nil"])
    ].reset_index(drop=True)

    n_notes = len(notes_df)
    NOTES_PER_PAGE = 8

    st.markdown(
        f'<div class="sec-title">Field Notes</div>'
        f'<div class="sec-sub">{n_notes} trainer remarks in range</div>',
        unsafe_allow_html=True)

    if notes_df.empty:
        st.markdown(f'<div style="font-size:13px;color:{MUTED};padding:14px 0;">'
                    f'No remarks recorded in this period.</div>',
                    unsafe_allow_html=True)
    else:
        # Pagination
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
        page_notes = notes_df.iloc[start_i : start_i + NOTES_PER_PAGE]

        # Scrollable fixed-height container
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
            f'<div style="height:460px;overflow-y:auto;padding-right:6px;'
            f'scrollbar-width:thin;scrollbar-color:{GOLD} {CREAM};">'
            f'{notes_html}</div>',
            unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# PDF EXPORT
# ─────────────────────────────────────────────────────────────────────────────

if export_btn:
    with st.spinner("Building PDF report…"):
        pdf_bytes = generate_pdf(df, date_from, date_to, all_figs,
                                 include_notes=pdf_include_notes,
                                 include_rawdata=pdf_include_rawdata)

    fname = (f"TcnAfrica_Report_"
             f"{date_from.strftime('%Y%m%d')}_"
             f"{date_to.strftime('%Y%m%d')}.pdf")
    st.sidebar.download_button(
        label="📥 Download PDF",
        data=pdf_bytes,
        file_name=fname,
        mime="application/pdf",
    )
    st.sidebar.success("PDF ready — click above to download.")
    if not HAS_KALEIDO:
        st.sidebar.info(
            "Install kaleido for charts in the PDF:\n  pip install kaleido")