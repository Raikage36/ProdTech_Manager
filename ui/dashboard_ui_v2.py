# ui/dashboard_ui_v2.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from modules.database_manager import fetch_all
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class DashboardUI(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=0, column=0, sticky="nsew")
        self.create_widgets()
        self.refresh_dashboard()

    # ------------------- UI Layout -------------------
    def create_widgets(self):
        tb.Label(self, text="📊 Operations Dashboard", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        # Summary cards
        self.card_frame = tb.Frame(self)
        self.card_frame.pack(fill=X, padx=15, pady=10)
        self.summary_labels = {}

        for i, label in enumerate(["Total Agents", "Departments", "Present", "Absent", "Leave"]):
            lf = tb.Labelframe(self.card_frame, text=label, bootstyle="light")
            lf.grid(row=0, column=i, padx=10, ipadx=20, ipady=10)
            val = tb.Label(lf, text="0", font=("Segoe UI", 18, "bold"))
            val.pack()
            self.summary_labels[label] = val

        # Chart area
        self.chart_frame = tb.Frame(self)
        self.chart_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)

        # Recent disciplinary
        self.disciplinary_frame = tb.Labelframe(self, text="Recent Disciplinary Actions", bootstyle="light")
        self.disciplinary_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)

        cols = ("Agent Name", "Date", "Reason", "Action Taken")
        self.table = tb.Treeview(self.disciplinary_frame, columns=cols, show="headings", height=5)
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=200, anchor="center")
        self.table.pack(fill=BOTH, expand=True)

    # ------------------- Refresh Dashboard -------------------
    def refresh_dashboard(self):
        self.update_summary()
        self.display_charts()
        self.load_recent_disciplinary()

    # ------------------- Summary Cards -------------------
    def update_summary(self):
        agents, departments = fetch_all("SELECT COUNT(*), COUNT(DISTINCT department) FROM agents")[0]

        attendance_counts = dict(fetch_all("SELECT status, COUNT(*) FROM attendance GROUP BY status"))
        present = attendance_counts.get("Present", 0)
        absent = attendance_counts.get("Absent", 0)
        leave = attendance_counts.get("Leave", 0)

        self.summary_labels["Total Agents"].config(text=str(agents))
        self.summary_labels["Departments"].config(text=str(departments))
        self.summary_labels["Present"].config(text=str(present))
        self.summary_labels["Absent"].config(text=str(absent))
        self.summary_labels["Leave"].config(text=str(leave))

    # ------------------- Charts -------------------
    def display_charts(self):
        for w in self.chart_frame.winfo_children():
            w.destroy()

        # Job Title Distribution
        jt_data = fetch_all("SELECT job_title, COUNT(*) FROM agents WHERE job_title != '' GROUP BY job_title")
        if jt_data:
            titles, counts = zip(*jt_data)
            fig = Figure(figsize=(4, 3))
            ax = fig.add_subplot()
            ax.bar(titles, counts, color="#007bff")
            ax.set_title("Job Title Distribution")
            ax.tick_params(axis='x', rotation=45)
            fig.patch.set_facecolor("#f8f9fa")
            ax.set_facecolor("#f8f9fa")
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=True, padx=5)

        # Shift Distribution
        shift_data = fetch_all("SELECT shift_type, COUNT(*) FROM agents WHERE shift_type != '' GROUP BY shift_type")
        if shift_data:
            shifts, counts = zip(*shift_data)
            fig = Figure(figsize=(4, 3))
            ax = fig.add_subplot()
            ax.pie(counts, labels=shifts, startangle=90)
            ax.set_title("Shift Dominance Overview")
            fig.patch.set_facecolor("#f8f9fa")
            ax.set_facecolor("#f8f9fa")
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=True, padx=5)

        # Attendance Trend
        trend_data = fetch_all("SELECT date, COUNT(*) FROM attendance GROUP BY date ORDER BY date ASC")
        if trend_data:
            dates = [t[0] for t in trend_data]
            counts = [t[1] for t in trend_data]
            fig = Figure(figsize=(4, 3))
            ax = fig.add_subplot()
            ax.plot(dates, counts, marker="o", color="#28a745")
            ax.set_title("Attendance Trend (3-Month Cycle)")
            ax.set_xlabel("Date")
            ax.set_ylabel("Records Logged")
            fig.patch.set_facecolor("#f8f9fa")
            ax.set_facecolor("#f8f9fa")
            ax.grid(alpha=0.3)
            canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(side=LEFT, fill=BOTH, expand=True, padx=5)

    # ------------------- Disciplinary -------------------
    def load_recent_disciplinary(self):
        self.table.delete(*self.table.get_children())
        rows = fetch_all("""
            SELECT a.name, d.incident_date, d.reason, d.action_taken
            FROM disciplinary d
            JOIN agents a ON a.id = d.agent_id
            ORDER BY d.incident_date DESC
            LIMIT 5
        """)
        for r in rows:
            self.table.insert("", "end", values=r)