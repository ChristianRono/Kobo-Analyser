# TcnAfrica Field Report Dashboard

A professional Streamlit dashboard for analysing Kobo field training reports.

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run kobo_dashboard.py
```
The dashboard opens automatically in your browser at http://localhost:8501

---

## How to Use

1. **Upload your file** — Click "Upload Kobo Excel Export" in the sidebar and select any `.xlsx` file exported from Kobo in the same format as your sample file.

2. **Set date range** — Use the "From" and "To" date pickers to filter from a single day up to multiple years of data.

3. **Apply filters** — Optionally filter by County, Trainer, or Module to drill into specific subsets.

4. **Read the dashboard** — The page auto-updates with:
   - KPI cards (sessions, attendance, counties, collections)
   - Attendance bar chart per session (M vs F)
   - Gender split donut chart
   - Attendance trend over time
   - County attendance bar chart
   - Full sessions table (scrollable)
   - County breakdown with progress bars
   - Field notes from trainers
   - Trainer leaderboard
   - Module breakdown
   - Collections by payment method

5. **Export PDF** — Click "⬇ Export PDF Report" in the sidebar. A styled PDF with all metrics, tables, and charts (if kaleido is installed) will be generated and a download button will appear.

---

## Excel File Format

The app expects Kobo Excel exports with this column layout (0-indexed):

| Col | Field            |
|-----|------------------|
| 0   | submitted_date   |
| 2   | trainer_name     |
| 3   | session_date     |
| 4   | county           |
| 5   | sub_county       |
| 6   | church_name      |
| 7   | venue            |
| 8   | class_number     |
| 9   | level            |
| 10  | module           |
| 11  | units_topics     |
| 12  | assignment       |
| 13  | total_attendance |
| 14  | male_count       |
| 15  | female_count     |
| 18  | absent_count     |
| 21  | payment_method   |
| 23  | amount_received  |
| 24  | amount_expected  |
| 26  | remarks          |

The first two rows (title + blank) are automatically skipped.

---

## Notes

- `kaleido` is optional but required for charts in the PDF export. Without it, the PDF still works with all tables and metrics.
- The app caches loaded data — re-uploading the same file is fast.
- Date filtering uses `session_date` (the actual training date), not the Kobo submission date.
