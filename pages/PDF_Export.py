"""
Page 4 — PDF Export: generate styled report with selectable sections.
"""

import io
import tempfile
from datetime import datetime

import pandas as pd
import streamlit as st

from utils import (
    CREAM, GOLD, GREEN, MUTED, NAVY, RED, WHITE,
    get_filtered_df, inject_css, no_data_screen,
    sidebar_divider, sidebar_logo, sidebar_user,
    fig_trend, fig_monthly, fig_county, fig_fees,
    ATTENDANCE_NOTE_SHORT,
)

try:
    import kaleido  # noqa: F401
    HAS_KALEIDO = True
except ImportError:
    HAS_KALEIDO = False

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

st.set_page_config(
    page_title="TcnAfrica · PDF Export",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

with st.sidebar:
    sidebar_logo()
    sidebar_divider()
    st.markdown(
        f'<div style="font-size:11px;color:{MUTED};padding:4px 0;">'
        f'Filters are set on the 🏠 Home page.<br>'
        f'The PDF reflects the current filtered dataset.</div>',
        unsafe_allow_html=True,
    )
    sidebar_divider()
    sidebar_user()

df = get_filtered_df()
if df is None or df.empty:
    no_data_screen()
    st.stop()

d_from = st.session_state.get("date_from")
d_to   = st.session_state.get("date_to")

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="sec-title" style="font-size:24px;">📄 PDF Export</div>'
    f'<div class="sec-sub">Generate a styled report for the current filtered dataset</div>',
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)

# ── Section toggles ───────────────────────────────────────────────────────────
st.markdown(
    f'<div class="sec-title">Report Contents</div>'
    f'<div class="sec-sub">Choose which sections to include</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)
with col1:
    inc_summary  = st.checkbox("✅ KPI Summary",           value=True)
    inc_charts   = st.checkbox("📊 Charts",                value=True)
    inc_county   = st.checkbox("🗺️ County Summary",        value=True)
    inc_module   = st.checkbox("📚 Module Summary",        value=True)
with col2:
    inc_trainer  = st.checkbox("👤 Trainer Summary",       value=True)
    inc_notes    = st.checkbox("📝 Field Notes",           value=True)
    inc_rawdata  = st.checkbox("📋 Raw Session Data",      value=False)

if not HAS_KALEIDO and inc_charts:
    st.warning(
        "⚠️ kaleido is not installed — charts will be excluded from the PDF. "
        "Run `pip install kaleido` to enable chart export.",
        icon="⚠️",
    )

st.markdown("<hr>", unsafe_allow_html=True)

# ── Preview stats ─────────────────────────────────────────────────────────────
st.markdown(
    f'<div class="sec-title">Report Preview</div>'
    f'<div class="sec-sub">This PDF will cover the data below</div>',
    unsafe_allow_html=True,
)

p1, p2, p3, p4 = st.columns(4)
with p1:
    st.metric("Sessions", f"{len(df):,}")
with p2:
    st.metric("Session-Attendances*", f"{int(df['attended'].sum()):,}")
with p3:
    st.metric("Counties", df["county"].nunique())
with p4:
    st.metric("Date Range",
              f"{d_from.strftime('%d %b %Y') if d_from else '—'} → "
              f"{d_to.strftime('%d %b %Y') if d_to else '—'}")

st.caption(f"* {ATTENDANCE_NOTE_SHORT}")
st.markdown("<hr>", unsafe_allow_html=True)

# ── Generate PDF ──────────────────────────────────────────────────────────────
def generate_pdf(df, d_from, d_to,
                 inc_summary, inc_charts, inc_county,
                 inc_module, inc_trainer, inc_notes, inc_rawdata):

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    rl_navy  = colors.HexColor(NAVY)
    rl_gold  = colors.HexColor(GOLD)
    rl_cream = colors.HexColor(CREAM)
    rl_white = colors.white
    rl_muted = colors.HexColor(MUTED)

    def sty(name, **kw):
        return ParagraphStyle(name, **kw)

    title_s = sty("T",  fontName="Helvetica-Bold",    fontSize=22,
                  textColor=rl_navy,  spaceAfter=8,  spaceBefore=4)
    gold_s  = sty("G",  fontName="Helvetica-Bold",    fontSize=15,
                  textColor=rl_gold,  spaceAfter=8,  spaceBefore=4)
    sub_s   = sty("S",  fontName="Helvetica",         fontSize=10,
                  textColor=rl_muted, spaceAfter=16, spaceBefore=2)
    sec_s   = sty("Sc", fontName="Helvetica-Bold",    fontSize=13,
                  textColor=rl_navy,  spaceBefore=14, spaceAfter=4)
    body_s  = sty("B",  fontName="Helvetica",         fontSize=10,
                  textColor=rl_navy,  spaceAfter=4)
    small_s = sty("Sm", fontName="Helvetica",         fontSize=8,
                  textColor=rl_muted, spaceAfter=2)
    note_s  = sty("N",  fontName="Helvetica-Oblique", fontSize=9,
                  textColor=colors.HexColor("#3a4f6a"),
                  backColor=rl_cream, spaceAfter=4, spaceBefore=2,
                  leftIndent=8, rightIndent=8)
    att_s   = sty("A",  fontName="Helvetica-Oblique", fontSize=8,
                  textColor=colors.HexColor("#7a5a10"),
                  backColor=colors.HexColor("#fdf3d8"),
                  spaceAfter=6, leftIndent=6, rightIndent=6)
    foot_s  = sty("F",  fontName="Helvetica",         fontSize=8,
                  textColor=rl_muted, alignment=TA_CENTER, spaceBefore=6)

    def base_table(data, col_widths):
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0,0), (-1,0), rl_navy),
            ("TEXTCOLOR",      (0,0), (-1,0), rl_white),
            ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",       (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [rl_cream, rl_white]),
            ("GRID",           (0,0), (-1,-1), 0.4, colors.HexColor("#d8cfc0")),
            ("TOPPADDING",     (0,0), (-1,-1), 5),
            ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
            ("LEFTPADDING",    (0,0), (-1,-1), 8),
            ("TEXTCOLOR",      (0,1), (-1,-1), rl_navy),
            ("FONTNAME",       (0,1), (0,-1),  "Helvetica-Bold"),
        ]))
        return t

    story = []
    total_sessions = len(df)
    total_enrolled = int(df["total_learners"].sum())
    total_attended = int(df["attended"].sum())
    att_rate = f"{total_attended/total_enrolled*100:.1f}%" if total_enrolled else "—"
    fee_total  = df["fee_received"].sum()
    grad_total = df["graduation_fee"].sum()

    # ── Cover / Header ────────────────────────────────────────────────────
    story.append(Paragraph("TcnAfrica", title_s))
    story.append(Paragraph("Field Training Report", gold_s))
    story.append(Paragraph(
        f"Period: {d_from.strftime('%d %b %Y') if d_from else '—'} — {d_to.strftime('%d %b %Y') if d_to else '—'}  ·  "
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}", sub_s))
    story.append(HRFlowable(width="100%", thickness=2, color=rl_gold, spaceAfter=14))
    story.append(Paragraph(
        f"⚠ Attendance note: All attendance figures represent session-attendances "
        f"(total bodies per session), not unique individuals. "
        f"Repeat learners are counted each time they attend.", att_s))

    # ── KPI Summary ───────────────────────────────────────────────────────
    if inc_summary:
        story.append(Paragraph("Summary", sec_s))
        kd = [
            ["Metric", "Value"],
            ["Total Sessions",              str(total_sessions)],
            ["Total Enrolled",              f"{total_enrolled:,}"],
            ["Total Session-Attendances",   f"{total_attended:,}"],
            ["Attendance Rate",             att_rate],
            ["Counties",                    str(df["county"].nunique())],
            ["Trainers Active",             str(df["trainer_name"].nunique())],
            ["Fee Received (KES)",          f"{fee_total:,.0f}"],
            ["Graduation Fee (KES)",        f"{grad_total:,.0f}"],
            ["Total Collected (KES)",       f"{fee_total + grad_total:,.0f}"],
        ]
        story.append(base_table(kd, ["52%", "48%"]))
        story.append(Spacer(1, 18))

    # ── Charts ────────────────────────────────────────────────────────────
    if inc_charts and HAS_KALEIDO:
        from reportlab.platypus import Image as RLImage
        for key, title, make_fig, export_h, display_h in [
            ("trend",   "Session-Attendance Trend Over Time",   fig_trend,   340, 7.0),
            ("monthly", "Monthly Sessions & Session-Attendances", fig_monthly, 380, 7.8),
            ("fees",    "Monthly Collections (KES)",            fig_fees,    360, 7.2),
            ("county",  "Session-Attendances by County",        fig_county,  360, 7.2),
        ]:
            fig = make_fig(df)
            story.append(Paragraph(title, sec_s))
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                fig.write_image(tmp.name, width=800, height=export_h, scale=2)
                story.append(RLImage(tmp.name, width=17*cm, height=display_h*cm))
            story.append(Spacer(1, 12))

    # ── County Summary ────────────────────────────────────────────────────
    if inc_county:
        story.append(PageBreak())
        story.append(Paragraph("County Summary", sec_s))
        cs = df.groupby("county").agg(
            Sessions   =("row_id",         "count"),
            Enrolled   =("total_learners", "sum"),
            Attendances=("attended",        "sum"),
            Absent     =("absent",          "sum"),
            Fee_KES    =("fee_received",    "sum"),
        ).reset_index()
        cs.columns = ["County","Sessions","Enrolled","Session-Attendances*","Absent","Fee (KES)"]
        cs["Fee (KES)"] = cs["Fee (KES)"].apply(lambda x: f"{float(x):,.0f}")
        cd = [list(cs.columns)] + [[str(v) for v in r] for r in cs.values.tolist()]
        story.append(base_table(cd, [3.2*cm, 2.2*cm, 2.2*cm, 3.5*cm, 2*cm, 3.4*cm]))
        story.append(Paragraph("* Session-attendances, not unique learners.", small_s))
        story.append(Spacer(1, 18))

    # ── Module Summary ────────────────────────────────────────────────────
    if inc_module:
        story.append(Paragraph("Module Summary", sec_s))
        ms = df[df["module"] != ""].groupby("module").agg(
            Sessions   =("row_id",   "count"),
            Attendances=("attended", "sum"),
            Absent     =("absent",   "sum"),
        ).reset_index().sort_values("Attendances", ascending=False)
        ms.columns = ["Module","Sessions","Session-Attendances*","Absent"]
        md = [list(ms.columns)] + [[str(v) for v in r] for r in ms.values.tolist()]
        story.append(base_table(md, [5*cm, 3*cm, 4.5*cm, 3*cm]))
        story.append(Paragraph("* Session-attendances, not unique learners.", small_s))
        story.append(Spacer(1, 18))

    # ── Trainer Summary ───────────────────────────────────────────────────
    if inc_trainer:
        story.append(Paragraph("Trainer Summary", sec_s))
        ts = df[df["trainer_name"] != ""].groupby("trainer_name").agg(
            Sessions   =("row_id",       "count"),
            Attendances=("attended",     "sum"),
            Fee_KES    =("fee_received", "sum"),
        ).reset_index().sort_values("Attendances", ascending=False)
        ts.columns = ["Trainer","Sessions","Session-Attendances*","Fee (KES)"]
        ts["Fee (KES)"] = ts["Fee (KES)"].apply(lambda x: f"{float(x):,.0f}")
        ttd = [list(ts.columns)] + [[str(v) for v in r] for r in ts.values.tolist()]
        story.append(base_table(ttd, [6*cm, 2.8*cm, 4*cm, 3.7*cm]))
        story.append(Paragraph("* Session-attendances, not unique learners.", small_s))

    # ── Field Notes ───────────────────────────────────────────────────────
    if inc_notes:
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
                dt = (row["session_date"].strftime("%d %b %Y")
                      if pd.notna(row["session_date"]) else "")
                story.append(Paragraph(
                    f"<b>{row['trainer_name']}</b>  ·  {row['county']}  ·  {dt}", body_s))
                story.append(Paragraph(f"\"{row['remarks']}\"", note_s))
                story.append(Spacer(1, 4))

    # ── Raw Data ──────────────────────────────────────────────────────────
    if inc_rawdata:
        story.append(PageBreak())
        story.append(Paragraph("Session Submissions — Full Data", sec_s))
        story.append(Paragraph(
            f"All {total_sessions:,} sessions in selected range, sorted by date.", body_s))
        story.append(Spacer(1, 6))

        disp_cols = ["session_date","trainer_name","county","class_name",
                     "ward","module","level","attended","absent","fee_received"]
        disp = df[[c for c in disp_cols if c in df.columns]].copy()
        disp["session_date"] = disp["session_date"].dt.strftime("%d %b %Y")
        # rename attended column
        disp = disp.rename(columns={"attended": "Attend.*"})
        col_headers = [c.replace("_"," ").title() for c in disp.columns]
        td = [col_headers] + [[str(v) for v in r] for r in disp.values.tolist()]
        widths = [2.2*cm,3.2*cm,1.8*cm,2*cm,2*cm,1.8*cm,1.5*cm,1.3*cm,1.2*cm,2*cm]
        st_tbl = Table(td, colWidths=widths[:len(disp.columns)], repeatRows=1)
        st_tbl.setStyle(TableStyle([
            ("BACKGROUND",     (0,0), (-1,0), rl_navy),
            ("TEXTCOLOR",      (0,0), (-1,0), rl_white),
            ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",       (0,0), (-1,-1), 7),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [rl_cream, rl_white]),
            ("GRID",           (0,0), (-1,-1), 0.3, colors.HexColor("#d8cfc0")),
            ("TOPPADDING",     (0,0), (-1,-1), 3),
            ("BOTTOMPADDING",  (0,0), (-1,-1), 3),
            ("LEFTPADDING",    (0,0), (-1,-1), 4),
            ("TEXTCOLOR",      (0,1), (-1,-1), rl_navy),
        ]))
        story.append(st_tbl)
        story.append(Paragraph("* Session-attendances, not unique learners.", small_s))

    # ── Footer ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=rl_gold))
    story.append(Paragraph(
        f"TcnAfrica Field Report Dashboard  ·  Confidential  ·  "
        f"Generated {datetime.now().strftime('%d %b %Y %H:%M')}", foot_s))

    doc.build(story)
    return buf.getvalue()


# ── Export button ─────────────────────────────────────────────────────────────
if st.button("⬇  Generate PDF Report", type="primary"):
    with st.spinner("Building PDF…"):
        pdf_bytes = generate_pdf(
            df, d_from, d_to,
            inc_summary, inc_charts, inc_county,
            inc_module, inc_trainer, inc_notes, inc_rawdata,
        )

    fname = (f"TcnAfrica_Report_"
             f"{d_from.strftime('%Y%m%d') if d_from else 'all'}_"
             f"{d_to.strftime('%Y%m%d') if d_to else 'all'}.pdf")

    st.success("✅ PDF ready!")
    st.download_button(
        label="📥 Download PDF",
        data=pdf_bytes,
        file_name=fname,
        mime="application/pdf",
    )
