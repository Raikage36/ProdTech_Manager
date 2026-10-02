
# ui/disciplinary_ui.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
from datetime import datetime
from modules.database_manager import fetch_all, execute_query
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from collections import Counter

class DisciplinaryUI(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.refresh_records()

    def create_widgets(self):
        # --- Title ---
        tb.Label(self, text="⚖️ Disciplinary Management", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=15, pady=10)

        # --- Summary Cards ---
        summary_frame = tb.Frame(self)
        summary_frame.pack(fill=X, padx=15, pady=10)

        self.summary_labels = {}
        for i, label in enumerate(["Total Cases", "Warnings", "Suspensions", "Terminations"]):
            frame = tb.Labelframe(summary_frame, text=label, bootstyle="dark")
            frame.grid(row=0, column=i, padx=10, ipadx=25, ipady=10)
            lbl = tb.Label(frame, text="0", font=("Segoe UI", 18, "bold"))
            lbl.pack()
            self.summary_labels[label] = lbl

        # --- Disciplinary Form ---
        form_frame = tb.Labelframe(self, text="Record New Incident", bootstyle="dark")
        form_frame.pack(fill=X, padx=15, pady=10)

        tb.Label(form_frame, text="Agent Name:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.agent_combo = tb.Combobox(form_frame, values=self.get_agent_names(), state="readonly", width=30)
        self.agent_combo.grid(row=0, column=1, padx=10, pady=5)

        tb.Label(form_frame, text="Incident Date:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.incident_date = tb.DateEntry(form_frame, bootstyle="info", width=15)
        self.incident_date.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        tb.Label(form_frame, text="Reason:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.reason_entry = tb.Entry(form_frame, width=40)
        self.reason_entry.grid(row=2, column=1, padx=10, pady=5)

        tb.Label(form_frame, text="Action Taken:").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.action_combo = tb.Combobox(
            form_frame, values=["Warning", "Suspension", "Termination"], state="readonly", width=28
        )
        self.action_combo.grid(row=3, column=1, padx=10, pady=5)

        tb.Button(form_frame, text="Submit Record", bootstyle="danger", command=self.submit_record).grid(
            row=4, column=1, pady=10, sticky="w"
        )

        # --- Records Table ---
        table_frame = tb.Labelframe(self, text="Disciplinary Records", bootstyle="dark")
        table_frame.pack(fill=BOTH, expand=True, padx=15, pady=10)

        cols = ("Agent Name", "Incident Date", "Reason", "Action Taken")
        self.table = tb.Treeview(table_frame, columns=cols, show="headings", height=10)
        for col in cols:
            self.table.heading(col, text=col)
            self.table.column(col, width=200, anchor="center")
        self.table.pack(fill=BOTH, expand=True)

        # --- Chart ---
        chart_frame = tb.Labelframe(self, text="Incident Breakdown", bootstyle="dark")
        chart_frame.pack(fill=BOTH, expand=True, padx=15, pady=15)
        self.chart_frame = chart_frame

    def get_agent_names(self):
        """Fetch all agent names for dropdown."""
        try:
            rows = fetch_all("SELECT name FROM agents ORDER BY name ASC")
            return [r[0] for r in rows]
        except Exception:
            return []

    def submit_record(self):
        """Add a new disciplinary record to the database."""
        name = self.agent_combo.get()
        date = self.incident_date.entry.get()
        reason = self.reason_entry.get()
        action = self.action_combo.get()

        if not all([name, date, reason, action]):
            messagebox.showwarning("Missing Data", "Please fill in all fields.")
            return

        try:
            execute_query(
                "INSERT INTO disciplinary (agent_id, incident_date, reason, action_taken) "
                "SELECT id, ?, ?, ? FROM agents WHERE name = ?",
                (date, reason, action, name),
            )
            messagebox.showinfo("Success", "Incident recorded successfully.")
            self.refresh_records()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add record:\n{e}")

    def refresh_records(self):
        """Load all disciplinary data."""
        try:
            rows = fetch_all(
                "SELECT a.name, d.incident_date, d.reason, d.action_taken "
                "FROM disciplinary d JOIN agents a ON d.agent_id = a.id ORDER BY d.incident_date DESC"
            )

            self.table.delete(*self.table.get_children())
            for row in rows:
                self.table.insert("", "end", values=row)

            # Update summaries
            total = len(rows)
            self.summary_labels["Total Cases"].config(text=str(total))
            counts = Counter(r[3] for r in rows)
            self.summary_labels["Warnings"].config(text=str(counts.get("Warning", 0)))
            self.summary_labels["Suspensions"].config(text=str(counts.get("Suspension", 0)))
            self.summary_labels["Terminations"].config(text=str(counts.get("Termination", 0)))

            self.display_chart(counts)
        except Exception as e:
            messagebox.showerror("Error", f"Could not refresh disciplinary data:\n{e}")

    def display_chart(self, counts):
        """Display a pie chart of actions taken."""
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        if not counts:
            tb.Label(self.chart_frame, text="No disciplinary data to display.", bootstyle="secondary").pack()
            return

        labels = list(counts.keys())
        sizes = list(counts.values())

        fig = Figure(figsize=(4.5, 2.5), dpi=100)
        ax = fig.add_subplot()
        ax.pie(
            sizes,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops=dict(width=0.4),
        )
        ax.set_facecolor("#222")
        fig.patch.set_facecolor("#222")
        ax.set_title("Disciplinary Action Distribution", color="white")

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)