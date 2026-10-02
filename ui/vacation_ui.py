"""
vacation_ui.py
--------------

Vacation management user interface for ProdTech Manager.

Features:
✅ View all vacation requests
✅ Add new requests
✅ Approve / Reject requests
✅ Search by agent name
✅ Auto-refresh display
"""

import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from datetime import datetime

from modules import vacation_logic
from modules.database_manager import fetch_all, get_agents

class VacationUI(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.create_widgets()
        self.populate_table()

    # ---------------------------------------------------------
    # UI Construction
    # ---------------------------------------------------------
    def create_widgets(self):
        # Title bar
        title_label = tb.Label(
            self,
            text="Vacation Management",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-primary",
            anchor="w",
            padding=10
        )
        title_label.pack(fill=X)

        # Toolbar frame
        toolbar = tb.Frame(self)
        toolbar.pack(fill=X, padx=10, pady=5)

        tb.Button(toolbar, text="Add Request", bootstyle="success-outline", command=self.add_vacation).pack(side=LEFT, padx=5)
        tb.Button(toolbar, text="Approve", bootstyle="info-outline", command=self.approve_vacation).pack(side=LEFT, padx=5)
        tb.Button(toolbar, text="Reject", bootstyle="danger-outline", command=self.reject_vacation).pack(side=LEFT, padx=5)
        tb.Button(toolbar, text="Export Excel", bootstyle="secondary-outline", command=self.export_excel).pack(side=LEFT, padx=5)
        tb.Button(toolbar, text="Refresh", bootstyle="light", command=self.populate_table).pack(side=LEFT, padx=5)

        # Search bar
        search_frame = tb.Frame(self)
        search_frame.pack(fill=X, padx=10, pady=5)

        tb.Label(search_frame, text="Search by Agent Name:", font=("Segoe UI", 10)).pack(side=LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tb.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=LEFT)
        search_entry.bind("<Return>", lambda e: self.search_vacation())

        # Table (Treeview)
        self.tree = tb.Treeview(
            self,
            columns=("id", "agent_id", "name", "start_date", "end_date", "total_days", "days_used", "status", "reason"),
            show="headings",
            height=15
        )
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Define columns
        headings = {
            "id": "ID",
            "agent_id": "Agent ID",
            "name": "Agent Name",
            "start_date": "Start Date",
            "end_date": "End Date",
            "total_days": "Total Days",
            "days_used": "Days Used",
            "status": "Status",
            "reason": "Reason"
        }

        for col, label in headings.items():
            self.tree.heading(col, text=label)
            self.tree.column(col, anchor=CENTER, width=110)

        # Right-click menu
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Approve", command=self.approve_vacation)
        self.menu.add_command(label="Reject", command=self.reject_vacation)
        self.menu.add_separator()
        self.menu.add_command(label="Refresh", command=self.populate_table)

        self.tree.bind("<Button-3>", self.show_context_menu)

    # ---------------------------------------------------------
    # Data Operations
    # ---------------------------------------------------------
    def populate_table(self):
        """Load vacation data into the tree."""
        self.tree.delete(*self.tree.get_children())

        rows = fetch_all("""
            SELECT v.id, v.agent_id, COALESCE(a.name, 'Unknown'), v.start_date, v.end_date,
                   v.total_days, v.days_used, v.status, v.reason
            FROM vacations v
            LEFT JOIN agents a ON a.id = v.agent_id
            ORDER BY v.start_date DESC
        """)
        for row in rows:
            self.tree.insert("", END, values=row)

    def search_vacation(self):
        """Search vacations by agent name."""
        search_text = self.search_var.get().lower()
        for row in self.tree.get_children():
            values = self.tree.item(row, "values")
            name = str(values[2]).lower()
            self.tree.detach(row) if search_text not in name else self.tree.reattach(row, "", END)

    def show_context_menu(self, event):
        """Show right-click menu."""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------
    def add_vacation(self):
        """Open window to add new vacation request."""
        win = tb.Toplevel(self)
        win.title("Add Vacation Request")
        win.geometry("400x400")
        win.resizable(False, False)

        tb.Label(win, text="Agent:", font=("Segoe UI", 10)).pack(pady=5)
        agents = get_agents()
        self.agent_var = tk.StringVar()
        agent_combo = ttk.Combobox(win, textvariable=self.agent_var, values=[a[1] for a in agents], state="readonly")
        agent_combo.pack(pady=5, fill=X, padx=20)

        tb.Label(win, text="Start Date (YYYY-MM-DD):", font=("Segoe UI", 10)).pack(pady=5)
        self.start_var = tk.StringVar()
        tb.Entry(win, textvariable=self.start_var).pack(pady=5, fill=X, padx=20)

        tb.Label(win, text="End Date (YYYY-MM-DD):", font=("Segoe UI", 10)).pack(pady=5)
        self.end_var = tk.StringVar()
        tb.Entry(win, textvariable=self.end_var).pack(pady=5, fill=X, padx=20)

        tb.Label(win, text="Reason:", font=("Segoe UI", 10)).pack(pady=5)
        self.reason_var = tk.StringVar()
        tb.Entry(win, textvariable=self.reason_var).pack(pady=5, fill=X, padx=20)

        def save_request():
            agent_name = self.agent_var.get()
            agent_id = next((a[0] for a in agents if a[1] == agent_name), None)
            if not agent_id:
                messagebox.showerror("Error", "Select a valid agent.")
                return

            vacation_logic.add_vacation(agent_id, self.start_var.get(), self.end_var.get(), self.reason_var.get())
            messagebox.showinfo("Success", "Vacation request added successfully!")
            win.destroy()
            self.populate_table()

        tb.Button(win, text="Save", bootstyle="success", command=save_request).pack(pady=10)
        tb.Button(win, text="Cancel", bootstyle="secondary", command=win.destroy).pack(pady=5)

    def approve_vacation(self):
        """Approve selected vacation."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Entry", "Please select a vacation record to approve.")
            return
        vac_id = self.tree.item(selected[0])["values"][0]
        vacation_logic.approve_vacation(vac_id)
        messagebox.showinfo("Approved", "Vacation approved successfully!")
        self.populate_table()

    def reject_vacation(self):
        """Reject selected vacation."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select Entry", "Please select a vacation record to reject.")
            return
        vac_id = self.tree.item(selected[0])["values"][0]

        reason = tk.simpledialog.askstring("Rejection Reason", "Enter reason for rejection:")
        if not reason:
            messagebox.showwarning("Required", "Rejection reason cannot be empty.")
            return

        vacation_logic.reject_vacation(vac_id, reason)
        messagebox.showinfo("Rejected", "Vacation rejected successfully!")
        self.populate_table()

    def export_excel(self):
        """Export vacation data to Excel file."""
        try:
            vacation_logic.export_vacations_to_excel()
            messagebox.showinfo("Export", "Vacation data exported successfully to Excel.")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Error exporting data: {e}")