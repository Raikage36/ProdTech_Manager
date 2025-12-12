# ui/attendance_ui.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, StringVar
from datetime import datetime
from modules.database_manager import execute_query, fetch_all
from ttkbootstrap.toast import ToastNotification
from modules import report_generator


class AttendanceUI(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.df = pd.DataFrame()
        self.create_widgets()
        self.refresh_table()
        self.refresh_charts()

    # -----------------------------------------------------------
    # 🧱 LAYOUT
    # -----------------------------------------------------------
    def create_widgets(self):
        # Title
        tb.Label(self, text="📅 Attendance Manager", font=("Segoe UI", 20, "bold")).pack(
            anchor="w", padx=15, pady=(15, 5)
        )

        # Notebook (Tabs)
        self.notebook = tb.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Tabs
        self.records_tab = tb.Frame(self.notebook)
        self.insights_tab = tb.Frame(self.notebook)

        self.notebook.add(self.records_tab, text="📋 Records")
        self.notebook.add(self.insights_tab, text="📊 Insights")

        # -----------------------------------------------------------
        # 📋 RECORDS TAB
        # -----------------------------------------------------------
        self.create_records_tab()

        # -----------------------------------------------------------
        # 📊 INSIGHTS TAB
        # -----------------------------------------------------------
        self.create_insights_tab()

    # -----------------------------------------------------------
    # RECORDS TAB
    # -----------------------------------------------------------
    def create_records_tab(self):
        # Toolbar
        ribbon = tb.Frame(self.records_tab, bootstyle="dark")
        ribbon.pack(fill=X, padx=10, pady=5)

        buttons = [
            ("🗓️ Add Record", self.add_attendance_window),
            ("💾 Save", self.save_changes),
            ("📂 Import Excel", self.import_excel),
            ("📤 Export Excel", self.export_excel_report),
            ("🧾 Export PDF", self.export_pdf_report),
            ("🗑️ Delete", self.delete_record),
            ("🔄 Refresh", self.refresh_table),
        ]
        for txt, cmd in buttons:
            tb.Button(ribbon, text=txt, bootstyle="secondary", command=cmd).pack(
                side=LEFT, padx=5, pady=3
            )

        # Table
        cols = [
            "ID", "Name", "Department", "Section", "Shift", "Employer",
            "Date", "Status", "Reason"
        ]
        self.table = tb.Treeview(
            self.records_tab, columns=cols, show="headings", height=22, bootstyle="dark"
        )
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=130, anchor="center")

        self.table.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Bindings
        self.table.bind("<Double-1>", self.start_inline_edit)
        self.table.bind("<Button-3>", self.show_context_menu)

    # -----------------------------------------------------------
    # INSIGHTS TAB
    # -----------------------------------------------------------
    def create_insights_tab(self):
        self.chart_frame = tb.Frame(self.insights_tab)
        self.chart_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.refresh_charts()

    # -----------------------------------------------------------
    # CRUD FUNCTIONS
    # -----------------------------------------------------------
    def refresh_table(self):
        for row in self.table.get_children():
            self.table.delete(row)

        rows = fetch_all("""
            SELECT att.id, a.name, a.department, a.section, a.shift_type,
                   a.employer, att.date, att.status, att.reason
            FROM attendance att
            JOIN agents a ON a.id = att.agent_id
            ORDER BY att.date DESC
        """)
        self.df = pd.DataFrame(
            rows,
            columns=[
                "ID", "Name", "Department", "Section", "Shift", "Employer",
                "Date", "Status", "Reason",
            ],
        )
        for r in rows:
            self.table.insert("", "end", values=r)
        self.refresh_charts()

    def add_attendance_window(self):
        win = tb.Toplevel(self)
        win.title("Add Attendance Record")
        win.geometry("400x400")

        fields = {
            "Name": None, "Date": None, "Status": None, "Reason": None
        }
        tb.Label(win, text="Add New Attendance Record", font=("Segoe UI", 12, "bold")).pack(
            pady=10
        )

        for f in fields.keys():
            tb.Label(win, text=f, font=("Segoe UI", 10)).pack(anchor="w", padx=15, pady=5)
            if f == "Status":
                var = StringVar(value="Present")
                cb = tb.Combobox(
                    win, textvariable=var,
                    values=["Present", "Absent", "Leave"], state="readonly"
                )
                cb.pack(fill=X, padx=15)
                fields[f] = var
            elif f == "Date":
                e = tb.Entry(win)
                e.insert(0, datetime.today().strftime("%Y-%m-%d"))
                e.pack(fill=X, padx=15)
                fields[f] = e
            else:
                e = tb.Entry(win)
                e.pack(fill=X, padx=15)
                fields[f] = e

        def save_record():
            name = fields["Name"].get()
            date = fields["Date"].get()
            status = fields["Status"].get()
            reason = fields["Reason"].get()
            agent = fetch_all("SELECT id FROM agents WHERE name=?", (name,))
            if not agent:
                messagebox.showwarning("Agent Not Found", f"{name} not found.")
                return
            execute_query(
                "INSERT INTO attendance (agent_id, date, status, reason) VALUES (?, ?, ?, ?)",
                (agent[0][0], date, status, reason),
            )
            win.destroy()
            self.refresh_table()
            ToastNotification(title="Added", message=f"Attendance for {name} recorded.").show_toast()

        tb.Button(win, text="Save", bootstyle="success", command=save_record).pack(pady=10)

    def start_inline_edit(self, event):
        region = self.table.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.table.identify_row(event.y)
        col = self.table.identify_column(event.x)
        if col == "#1":
            return
        col_index = int(col.replace("#", "")) - 1
        col_name = self.table["columns"][col_index]
        if col_name in ["Name", "Department", "Section", "Shift", "Employer"]:
            return
        x, y, width, height = self.table.bbox(row_id, col)
        value = self.table.item(row_id, "values")[col_index]
        entry = tb.Entry(self.table)
        entry.insert(0, value)
        entry.place(x=x, y=y, width=width, height=height)
        entry.focus()

        def save_edit(event=None):
            new_val = entry.get()
            entry.destroy()
            vals = list(self.table.item(row_id, "values"))
            vals[col_index] = new_val
            self.table.item(row_id, values=vals)
            execute_query(
                f"UPDATE attendance SET {col_name.lower()}=? WHERE id=?", (new_val, vals[0])
            )
            self.refresh_charts()
            ToastNotification(title="Updated", message=f"{col_name} updated.").show_toast()

        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", lambda e: entry.destroy())

    def show_context_menu(self, event):
        item = self.table.identify_row(event.y)
        if not item:
            return
        self.table.selection_set(item)
        menu = tb.Menu(self, tearoff=0)
        menu.add_command(label="✏️ Edit Record", command=self.inline_edit_from_menu)
        menu.add_command(label="🗑️ Delete Record", command=self.delete_record)
        menu.tk_popup(event.x_root, event.y_root)

    def inline_edit_from_menu(self):
        selection = self.table.selection()
        if selection:
            self.start_inline_edit(event=None)

    def delete_record(self):
        sel = self.table.selection()
        if not sel:
            messagebox.showwarning("Select Record", "Please select a record to delete.")
            return
        confirm = messagebox.askyesno("Confirm", "Delete selected record(s)?")
        if not confirm:
            return
        for s in sel:
            vals = self.table.item(s, "values")
            execute_query("DELETE FROM attendance WHERE id=?", (vals[0],))
            self.table.delete(s)
        self.refresh_charts()
        ToastNotification(title="Deleted", message="Record(s) deleted.").show_toast()

    # -----------------------------------------------------------
    # IMPORT / EXPORT
    # -----------------------------------------------------------
    def import_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if not path:
            return
        df = pd.read_excel(path)
        for _, row in df.iterrows():
            name, date, status, reason = row["Name"], row["Date"], row["Status"], row["Reason"]
            agent = fetch_all("SELECT id FROM agents WHERE name=?", (name,))
            if agent:
                execute_query(
                    "INSERT INTO attendance (agent_id, date, status, reason) VALUES (?, ?, ?, ?)",
                    (agent[0][0], str(date)[:10], status, reason),
                )
        self.refresh_table()
        ToastNotification(title="Imported", message="Attendance imported successfully.").show_toast()

    def export_excel_report(self):
        path = report_generator.export_attendance_excel("Attendance_Report")
        if path:
            ToastNotification(title="Exported", message=f"Excel saved at {path}").show_toast()

    def export_pdf_report(self):
        path = report_generator.export_attendance_pdf("Attendance_Report")
        if path:
            ToastNotification(title="Exported", message=f"PDF saved at {path}").show_toast()

    def save_changes(self):
        ToastNotification(title="Saved", message="All changes saved.").show_toast()

    # -----------------------------------------------------------
    # CHARTS
    # -----------------------------------------------------------
    def refresh_charts(self):
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        df = fetch_all("""
            SELECT a.shift_type, att.status
            FROM attendance att
            JOIN agents a ON a.id = att.agent_id
        """)
        if not df:
            tb.Label(self.chart_frame, text="No data to display", font=("Segoe UI", 12)).pack(pady=50)
            return

        data = pd.DataFrame(df, columns=["Shift", "Status"])

        # Pie chart for status distribution
        fig, axs = plt.subplots(1, 2, figsize=(10, 4))
        status_counts = data["Status"].value_counts()
        axs[0].pie(status_counts, labels=status_counts.index, autopct="%1.1f%%", startangle=90)
        axs[0].set_title("Attendance Status Distribution")

        # Bar chart for shift distribution
        pivot = data.pivot_table(index="Shift", columns="Status", aggfunc=len, fill_value=0)
        pivot.plot(kind="bar", stacked=True, ax=axs[1])
        axs[1].set_title("Attendance by Shift")
        axs[1].set_xlabel("Shift")
        axs[1].set_ylabel("Count")

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=BOTH, expand=True)
