"""
Page 3 — Record Inspector: search, full detail, image viewer, GPS.
"""

import base64
import json

import pandas as pd
import requests
import streamlit as st

from utils import (
    CREAM, GOLD, GREEN, MUTED, NAVY, RED, WHITE,
    get_api_token, get_filtered_df, inject_css, no_data_screen,
    sidebar_divider, sidebar_logo, sidebar_user,
)

KOBO_SERVER = "https://kobo.humanitarianresponse.info"

# Map internal column names → Kobo question xpaths
PHOTO_XPATH_MAP = {
    "payment_photo_url":    "group_qm5qq25/TAKE_PHOTO_OF_PAYMENT_INFORMATION",
    "attendance_photo_url": "group_es1rh04/CLASS_ATTENDANCE",
}


def resolve_image_url(url_col: str, attachments) -> str:
    """
    Match attachment by question_xpath — most reliable Kobo API approach.
    The download_url in the attachment object is already a full authenticated URL.
    """
    if not attachments or not isinstance(attachments, list):
        return ""

    xpath = PHOTO_XPATH_MAP.get(url_col, "")

    for att in attachments:
        if not isinstance(att, dict):
            continue
        if att.get("is_deleted"):
            continue
        if xpath and att.get("question_xpath") == xpath:
            return att.get("download_url", "")

    # Fallback: return first non-deleted attachment
    for att in attachments:
        if isinstance(att, dict) and not att.get("is_deleted"):
            return att.get("download_url", "")

    return ""


st.set_page_config(
    page_title="TcnAfrica · Record Inspector",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

with st.sidebar:
    sidebar_logo()
    sidebar_divider()

    st.markdown(
        f'<div style="font-size:10px;text-transform:uppercase;letter-spacing:.12em;'
        f'color:{MUTED};font-weight:600;margin-bottom:6px;">🔑 Kobo API Token</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div style="font-size:11px;color:{MUTED};margin-bottom:8px;">'
        f'Required to display attached images.<br>'
        f'Token is loaded automatically from your environment.<br>'
        f'Paste below to override for this session.</div>',
        unsafe_allow_html=True,
    )
    kobo_token = st.text_input(
        "API Token",
        type="password",
        value=st.session_state.get("kobo_token_override") or get_api_token(),
        placeholder="Loaded from env — or paste to override…",
        key="kobo_token",
    )

    sidebar_divider()
    st.markdown(
        f'<div style="font-size:11px;color:{MUTED};padding:4px 0;">'
        f'Search filters below apply only to this page. '
        f'Data filters are set on 🏠 Home.</div>',
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
st.markdown(
    f'<div class="sec-title" style="font-size:24px;">🔍 Record Inspector</div>'
    f'<div class="sec-sub">Search any session record, view full details and attached images</div>',
    unsafe_allow_html=True,
)
st.markdown("<hr>", unsafe_allow_html=True)

# ── Search controls ───────────────────────────────────────────────────────────
si1, si2, si3 = st.columns([2, 2, 2])
with si1:
    search_trainer = st.text_input("Filter by trainer name",
                                   placeholder="e.g. Langat", key="ri_trainer")
with si2:
    search_county = st.selectbox(
        "Filter by county",
        ["All"] + sorted(df["county"].replace("", pd.NA).dropna().unique().tolist()),
        key="ri_county",
    )
with si3:
    search_date = st.date_input("Filter by date", value=None, key="ri_date")

# ── Apply search ──────────────────────────────────────────────────────────────
ri_df = df.copy()
if search_trainer:
    ri_df = ri_df[ri_df["trainer_name"].str.lower()
                    .str.contains(search_trainer.lower(), na=False)]
if search_county != "All":
    ri_df = ri_df[ri_df["county"] == search_county]
if search_date:
    ri_df = ri_df[ri_df["session_date"].dt.date == search_date]

ri_df = ri_df.reset_index(drop=True)

st.markdown(
    f'<div style="font-size:12px;color:{MUTED};margin:6px 0 4px;">'
    f'{len(ri_df):,} record(s) found</div>',
    unsafe_allow_html=True,
)

if ri_df.empty:
    st.info("No records match your search. Try adjusting the filters above.")
    st.stop()

# ── Results preview table ─────────────────────────────────────────────────────
list_cols = {
    "session_date": "Date", "trainer_name": "Trainer",
    "county": "County",     "class_name":   "Class",
    "module": "Module",     "attended":     "Attendances*",
    "fee_received": "Fee (KES)",
}
ri_show = ri_df[[c for c in list_cols if c in ri_df.columns]].rename(columns=list_cols).copy()
if "Date" in ri_show.columns:
    ri_show["Date"] = pd.to_datetime(ri_show["Date"]).dt.strftime("%d %b %Y")

st.dataframe(ri_show, use_container_width=True,
             height=min(280, (len(ri_show) + 1) * 38),
             hide_index=True)
st.caption("* Session-attendances, not unique learners")

# ── Record selector ───────────────────────────────────────────────────────────
st.markdown(
    f'<div class="sec-title" style="font-size:15px;margin-top:14px;">'
    f'Select a record to inspect</div>',
    unsafe_allow_html=True,
)


def make_label(row):
    dt = row["session_date"].strftime("%d %b %Y") if pd.notna(row["session_date"]) else "?"
    return f"{dt}  ·  {row['trainer_name']}  ·  {row['county']}  ·  {row.get('class_name', '')}"


ri_df["_label"] = ri_df.apply(make_label, axis=1)
selected_label = st.selectbox("Record", ri_df["_label"].tolist(),
                               label_visibility="collapsed", key="ri_select")
rec_idx = ri_df[ri_df["_label"] == selected_label].index[0]
rec = ri_df.loc[rec_idx]
dt_str = rec["session_date"].strftime("%d %B %Y") if pd.notna(rec["session_date"]) else "—"

st.markdown("<hr>", unsafe_allow_html=True)

# ── Detail + Image columns ────────────────────────────────────────────────────
rd1, rd2 = st.columns([3, 2])

with rd1:
    st.markdown(
        f'<div class="sec-title">Record Detail</div>'
        f'<div class="sec-sub">Full field data for this submission</div>',
        unsafe_allow_html=True,
    )

    def detail_row(label, value, highlight=False):
        val_str = str(value).strip()
        empty = val_str.lower() in ("", "nan", "none", "n/a", "0", "0.0")
        display = val_str if not empty else "—"
        colour = NAVY if (highlight and not empty) else ("#3a4f6a" if not empty else MUTED)
        weight = "700" if highlight else "400"
        style  = f"font-style:italic;color:{MUTED};" if empty else f"color:{colour};font-weight:{weight};"
        return (
            f'<div style="display:flex;justify-content:space-between;'
            f'padding:7px 0;border-bottom:1px solid #ede5d5;">'
            f'<span style="font-size:11px;text-transform:uppercase;letter-spacing:0.08em;'
            f'color:{MUTED};font-weight:600;min-width:150px;">{label}</span>'
            f'<span style="font-size:13px;{style}text-align:right;flex:1;">{display}</span>'
            f'</div>'
        )

    html = f'<div style="background:{WHITE};border-radius:10px;padding:18px 20px;border:1px solid #d8cfc0;">'
    html += detail_row("Session Date",      dt_str,                                   highlight=True)
    html += detail_row("Trainer",           rec.get("trainer_name", ""),              highlight=True)
    html += detail_row("County",            rec.get("county", ""))
    html += detail_row("Class",             rec.get("class_name", ""))
    html += detail_row("Ward",              rec.get("ward", ""))
    html += detail_row("Level",             rec.get("level", ""))
    html += detail_row("Module",            rec.get("module", ""))
    html += detail_row("Lesson Taught",     rec.get("lesson", ""))
    html += detail_row("Assignment",        rec.get("assignment", ""))
    html += detail_row("Class Hours",       rec.get("class_hours", ""))
    html += detail_row("Total Enrolled",    int(rec.get("total_learners", 0)))
    html += detail_row("Attendances*",      int(rec.get("attended", 0)),              highlight=True)
    html += detail_row("Absent",            int(rec.get("absent", 0)))
    html += detail_row("Fee Received",      f"KES {rec.get('fee_received', 0):,.0f}", highlight=True)
    html += detail_row("Graduation Fee",    f"KES {rec.get('graduation_fee', 0):,.0f}")
    html += detail_row("TLA Amount",        f"KES {rec.get('tla_amount', 0):,.0f}")
    html += detail_row("Transaction",       rec.get("transaction_code", ""))
    html += detail_row("Class Requirement", rec.get("class_requirement", ""))
    html += detail_row("Remarks",           rec.get("remarks", ""))
    if "row_id" in rec.index:
        html += detail_row("Record ID",     rec.get("row_id", ""))
    if "uuid" in rec.index:
        html += detail_row("UUID",          rec.get("uuid", ""))
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    st.caption("* Session-attendances, not unique learners")

with rd2:
    st.markdown(
        f'<div class="sec-title">Attached Images</div>'
        f'<div class="sec-sub">Payment & attendance photos</div>',
        unsafe_allow_html=True,
    )

    # ── Resolve attachments for this record ───────────────────────────────
    raw_attachments = rec.get("attachments", [])
    if isinstance(raw_attachments, str):
        try:
            raw_attachments = json.loads(raw_attachments)
        except Exception:
            raw_attachments = []
    if not isinstance(raw_attachments, list):
        raw_attachments = []

    # Build image list by matching question_xpath
    img_entries = []
    for url_col, label in [("payment_photo_url",    "Payment Photo"),
                            ("attendance_photo_url", "Attendance Photo")]:
        resolved = resolve_image_url(url_col, raw_attachments)
        if resolved:
            img_entries.append((label, resolved))

    if not img_entries:
        st.markdown(
            f'<div style="background:{WHITE};border-radius:10px;padding:40px 20px;'
            f'border:1px solid #d8cfc0;text-align:center;">'
            f'<div style="font-size:36px;margin-bottom:10px;">📷</div>'
            f'<div style="font-size:13px;color:{MUTED};">No image attached to this record.</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        for img_label, img_url in img_entries:
            st.markdown(
                f'<div style="font-size:11px;text-transform:uppercase;'
                f'letter-spacing:0.1em;color:{MUTED};font-weight:600;'
                f'margin:12px 0 6px;">{img_label}</div>',
                unsafe_allow_html=True,
            )

            if not kobo_token:
                st.markdown(
                    f'<div style="background:{WHITE};border-radius:10px;padding:18px;'
                    f'border:1px solid #d8cfc0;margin-bottom:10px;">'
                    f'<div style="font-size:13px;color:{NAVY};margin-bottom:8px;">'
                    f'🔒 No API token found. Set <code>KOBO_API_TOKEN</code> in your '
                    f'.env file or Streamlit secrets.</div>'
                    f'<div style="font-size:11px;color:{MUTED};margin-bottom:8px;">'
                    f'Or open the URL directly (requires Kobo login in browser):</div>'
                    f'<a href="{img_url}" target="_blank" '
                    f'style="font-size:11px;color:{GOLD};word-break:break-all;">'
                    f'{img_url[:72]}…</a></div>',
                    unsafe_allow_html=True,
                )
            else:
                with st.spinner(f"Loading {img_label}…"):
                    try:
                        resp = requests.get(
                            img_url,
                            headers={"Authorization": f"Token {kobo_token.strip()}"},
                            timeout=15,
                        )
                        if resp.status_code == 200:
                            ctype = resp.headers.get("Content-Type", "image/jpeg")
                            b64   = base64.b64encode(resp.content).decode()
                            st.markdown(
                                f'<div style="background:{WHITE};border-radius:10px;'
                                f'padding:12px;border:1px solid #d8cfc0;margin-bottom:8px;">'
                                f'<img src="data:{ctype};base64,{b64}" '
                                f'style="width:100%;border-radius:6px;" '
                                f'title="Click to open full size" '
                                f'onclick="window.open(this.src)"/>'
                                f'<div style="font-size:10px;color:{MUTED};margin-top:6px;'
                                f'text-align:center;">Click image to open full size</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                            st.download_button(
                                label=f"⬇ Download {img_label}",
                                data=resp.content,
                                file_name=(f"{rec.get('trainer_name', 'record')}_"
                                           f"{dt_str}_{img_label.replace(' ', '_')}.jpg"),
                                mime=ctype,
                                key=f"dl_{url_col}_{rec_idx}",
                            )
                        elif resp.status_code == 401:
                            st.error("❌ Invalid API token. Check credentials in sidebar or your .env file.")
                        elif resp.status_code == 403:
                            st.error("❌ Access denied — you may not have permission for this asset.")
                        elif resp.status_code == 404:
                            st.warning("⚠️ Image not found — it may have been deleted from Kobo.")
                        else:
                            st.error(f"❌ HTTP {resp.status_code} — could not load image.")
                    except requests.exceptions.Timeout:
                        st.error("⏱ Request timed out. Check your connection.")
                    except requests.exceptions.ConnectionError:
                        st.error("🌐 Could not connect to the Kobo server.")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")

    # ── GPS ───────────────────────────────────────────────────────────────
    try:
        lat_f = float(rec.get("latitude",  0))
        lon_f = float(rec.get("longitude", 0))
        has_gps = (lat_f != 0.0 or lon_f != 0.0) and not (pd.isna(lat_f) or pd.isna(lon_f))
    except (TypeError, ValueError):
        has_gps = False

    if has_gps:
        st.markdown(
            f'<div class="sec-title" style="margin-top:18px;font-size:14px;">'
            f'📍 GPS Location</div>',
            unsafe_allow_html=True,
        )
        map_url = f"https://www.google.com/maps?q={lat_f},{lon_f}&z=14"
        st.markdown(
            f'<div style="background:{WHITE};border-radius:10px;padding:16px 18px;'
            f'border:1px solid #d8cfc0;">'
            f'<div style="font-size:13px;color:{NAVY};margin-bottom:10px;">'
            f'Lat: <b>{lat_f:.6f}</b>  ·  Lon: <b>{lon_f:.6f}</b></div>'
            f'<a href="{map_url}" target="_blank" '
            f'style="display:inline-block;background:{NAVY};color:{GOLD};'
            f'font-size:12px;font-weight:700;padding:7px 16px;'
            f'border-radius:6px;text-decoration:none;">'
            f'📍 Open in Google Maps</a></div>',
            unsafe_allow_html=True,
        )