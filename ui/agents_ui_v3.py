# ui/agents_ui_v2.py
import os
import pandas as pd
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, simpledialog
from modules.database_manager import transaction

COLUMNS = ["ID", "Name", "Department", "Section", "Shift", "Roster Type",
           "Job Title", "Email", "Phone Num", "Employer"]

class AgentsUI(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.grid(row=0, column=0, sticky="nsew")
        self.master_file = None
        self.df = pd.DataFrame()
        self.create_widgets()

    # ---------------- UI ----------------
    def create_widgets(self):
        tb.Label(self, text="👥 Agents Manager", font=("Segoe UI", 20, "bold")).pack(anchor="w", padx=15, pady=(15, 10))

        # Ribbon toolbar
        ribbon = tb.Frame(self, bootstyle="light")
        ribbon.pack(fill=X, padx=10, pady=5)

        buttons = [
            ("📘 Load Master File", self.load_master_file),
            ("💾 Save Changes", self.save_changes),
            ("➕ Add Agent", self.add_agent),
            ("🗑️ Delete Agent", self.delete_agent),
            ("🔍 Search", self.search_agent),
            ("🔄 Refresh", self.refresh_table)
        ]
        for txt, cmd in buttons:
            tb.Button(ribbon, text=txt, bootstyle="secondary", command=cmd).pack(side=LEFT, padx=5, pady=3)

        # Table
        self.table = tb.Treeview(self, columns=COLUMNS, show="headings", height=20)
        for c in COLUMNS:
            self.table.heading(c, text=c)
            self.table.column(c, width=150, anchor="center")
        self.table.pack(fill=BOTH, expand=True, padx=15, pady=10)

        self.table.bind("<Double-1>", self.on_double_click)

    # ---------------- Load Master File ----------------
    def load_master_file(self):
        path = filedialog.askopenfilename(
            title="Select Master Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls")]
        )
        if not path:
            return
        try:
            df = pd.read_excel(path)
            for col in COLUMNS:
                if col not in df.columns:
                    df[col] = ""

            self.master_file = path
            self.df = df[COLUMNS].reset_index(drop=True)
            self.refresh_table()
            messagebox.showinfo("Master File Loaded", f"{len(self.df)} agents imported.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load Excel file:\n{e}")

    # ---------------- Table Refresh ----------------
    def refresh_table(self):
        self.show_rows(self.df)

    def show_rows(self, df):
        """Fill the table; each row's iid is its DataFrame index so edits/deletes map back exactly."""
        self.table.delete(*self.table.get_children())
        for idx, values in zip(df.index, df.to_numpy().tolist()):
            self.table.insert("", "end", iid=str(idx), values=values)

    # ---------------- Editing ----------------
    def on_double_click(self, event):
        item_id = self.table.identify_row(event.y)
        col = self.table.identify_column(event.x)
        if not item_id or col == "#1":  # Don't edit ID
            return
        col_index = int(col.replace("#", "")) - 1
        col_name = self.table["columns"][col_index]
        old_value = self.table.item(item_id, "values")[col_index]
        new_value = simpledialog.askstring("Edit", f"Enter new value for {col_name}:", initialvalue=old_value)
        if new_value is not None:
            vals = list(self.table.item(item_id, "values"))
            vals[col_index] = new_value
            self.table.item(item_id, values=vals)
            # Update DataFrame
            self.df.at[int(item_id), col_name] = new_value

    # ---------------- Add / Delete ----------------
    def add_agent(self):
        new_data = {}
        for field in COLUMNS[1:]:
            val = simpledialog.askstring("New Agent", f"Enter {field}:")
            new_data[field] = val if val else ""
        new_id = self.df["ID"].max() + 1 if not self.df.empty else 1
        new_data["ID"] = new_id
        self.df = pd.concat([self.df, pd.DataFrame([new_data])], ignore_index=True)
        self.refresh_table()

    def delete_agent(self):
        selected = self.table.selection()
        if not selected:
            messagebox.showwarning("Select Agent", "Please select a record to delete.")
            return
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected agent(s)?")
        if not confirm:
            return
        self.df = self.df.drop(index=[int(sel) for sel in selected])
        self.table.delete(*selected)

    # ---------------- Search ----------------
    def search_agent(self):
        term = simpledialog.askstring("Search", "Enter keyword (Name / Department / Shift):")
        if not term:
            return
        term = term.lower()
        text = self.df.astype(str).apply(lambda col: col.str.lower())
        mask = text.apply(lambda col: col.str.contains(term, regex=False)).any(axis=1)
        self.show_rows(self.df[mask])

    # ---------------- Save Changes ----------------
    def save_changes(self):
        if self.df.empty:
            messagebox.showwarning("No Data", "No agents to save.")
            return
        if not self.master_file:
            messagebox.showwarning("No File", "Please load a master file first.")
            return
        try:
            # Save to Excel
            self.df.to_excel(self.master_file, index=False)
            # Sync to database in one transaction (all-or-nothing)
            data = self.df[COLUMNS].astype(object)
            data = data.where(data.notna(), None)
            rows = [(int(r[0]), *r[1:]) for r in data.itertuples(index=False, name=None)]
            # Upsert instead of DELETE-all, which the foreign keys reject once agents have records
            with transaction() as conn:
                conn.executemany("""
                    INSERT INTO agents (id, name, department, section, shift_type, roster_type, job_title, email, phone, employer)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        name = excluded.name, department = excluded.department, section = excluded.section,
                        shift_type = excluded.shift_type, roster_type = excluded.roster_type,
                        job_title = excluded.job_title, email = excluded.email, phone = excluded.phone,
                        employer = excluded.employer
                """, rows)
                conn.execute("CREATE TEMP TABLE keep_ids (id INTEGER PRIMARY KEY)")
                conn.executemany("INSERT OR IGNORE INTO keep_ids VALUES (?)", [(r[0],) for r in rows])
                conn.execute("DELETE FROM agents WHERE id NOT IN (SELECT id FROM keep_ids)")
            messagebox.showinfo("Saved", "All changes saved to Excel and database successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save data:\n{e}")