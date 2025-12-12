# modules/report_generator.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF
from modules.database_manager import fetch_all

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "tfm_logo.png")

# Create subdirectories if they don’t exist
os.makedirs(os.path.join(REPORTS_DIR, "Attendance"), exist_ok=True)
os.makedirs(os.path.join(REPORTS_DIR, "Disciplinary"), exist_ok=True)

# -----------------------------
# Utility: Save Attendance Data
# -----------------------------
def export_attendance_excel(month_name="December 2025"):
    """Exports attendance data from database to Excel."""
    try:
        data = fetch_all("""
            SELECT a.name, a.department, att.date, att.status, att.reason
            FROM attendance att
            JOIN agents a ON a.id = att.agent_id
            ORDER BY a.name, att.date
        """)

        if not data:
            print("⚠️ No attendance data found.")
            return None

        df = pd.DataFrame(data, columns=["Name", "Department", "Date", "Status", "Reason"])
        file_path = os.path.join(REPORTS_DIR, "Attendance", f"Attendance_Report_{month_name}.xlsx")
        df.to_excel(file_path, index=False)
        print(f"✅ Attendance Excel exported: {file_path}")
        return file_path

    except Exception as e:
        print(f"❌ Error exporting attendance Excel: {e}")
        return None

# --------------------------
# Utility: Save PDF Reports
# --------------------------
class PDFReport(FPDF):
    def header(self):
        # Logo
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 30)
        # Header text
        self.set_font("Helvetica", "B", 14)
        self.cell(0, 10, "Tenke Fungurume Mining", ln=1, align="R")
        self.set_font("Helvetica", "", 11)
        self.cell(0, 6, self.title_text, ln=1, align="R")
        self.cell(0, 6, "Production & Technology Departments", ln=1, align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.cell(0, 10, f"Generated on {date_str} — Confidential / Internal Use Only", 0, 0, "C")

def export_attendance_pdf(month_name="December 2025"):
    """Generate formal PDF report for attendance."""
    try:
        pdf = PDFReport(orientation="P", unit="mm", format="A4")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.title_text = f"Attendance Report — {month_name}"
        pdf.add_page()

        # --- Attendance Summary ---
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Attendance Summary", ln=1)

        counts = fetch_all("""
            SELECT status, COUNT(*) FROM attendance GROUP BY status
        """)
        total = sum([row[1] for row in counts]) if counts else 1

        pdf.set_font("Helvetica", "", 11)
        for status, count in counts:
            pdf.cell(0, 8, f"{status}: {count} ({(count/total)*100:.1f}%)", ln=1)

        pdf.ln(5)

        # --- Attendance Trend Chart ---
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Attendance Trend (3-Month)", ln=1)
        trend_data = fetch_all("""
            SELECT date, COUNT(*) FROM attendance GROUP BY date ORDER BY date ASC
        """)
        if trend_data:
            dates = [row[0] for row in trend_data]
            counts = [row[1] for row in trend_data]
            fig, ax = plt.subplots(figsize=(5, 2.5))
            ax.plot(dates, counts, marker="o", color="#1f77b4")
            ax.set_xlabel("Date")
            ax.set_ylabel("Records")
            ax.grid(True, alpha=0.3)
            chart_path = os.path.join(REPORTS_DIR, "Attendance", "temp_trend.png")
            fig.savefig(chart_path, bbox_inches="tight", dpi=100)
            plt.close(fig)
            pdf.image(chart_path, x=20, w=170)
            os.remove(chart_path)

        pdf.ln(10)

        # --- Shift Distribution Chart ---
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Shift Distribution Overview", ln=1)
        shift_data = fetch_all("SELECT shift_type FROM agents")
        if shift_data:
            import collections
            counter = collections.Counter([s[0] for s in shift_data])
            labels, values = zip(*counter.items())
            fig, ax = plt.subplots(figsize=(4.5, 3))
            ax.pie(values, labels=labels, startangle=90)
            chart_path = os.path.join(REPORTS_DIR, "Attendance", "temp_pie.png")
            fig.savefig(chart_path, bbox_inches="tight", dpi=100)
            plt.close(fig)
            pdf.image(chart_path, x=25, w=160)
            os.remove(chart_path)

        # --- Disciplinary Report Section ---
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Disciplinary Summary", ln=1)
        pdf.set_font("Helvetica", "", 11)
        disciplinary = fetch_all("""
            SELECT a.name, d.incident_date, d.reason, d.action_taken
            FROM disciplinary d
            JOIN agents a ON a.id = d.agent_id
            ORDER BY d.incident_date DESC
        """)
        if disciplinary:
            for name, date, reason, action in disciplinary:
                pdf.multi_cell(0, 6, f"• {date} — {name}: {reason} ({action})")
        else:
            pdf.cell(0, 8, "No disciplinary actions recorded this month.", ln=1)

        # --- Save PDF ---
        file_path = os.path.join(REPORTS_DIR, "Attendance", f"Attendance_Report_{month_name}.pdf")
        pdf.output(file_path)
        print(f"✅ PDF report generated: {file_path}")
        return file_path

    except Exception as e:
        print(f"❌ Error exporting PDF: {e}")
        return None
