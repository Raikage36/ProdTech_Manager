# main.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import messagebox
from modules.database_manager import migrate_database
migrate_database()
# ------------------------------
# UI MODULE IMPORTS
# ------------------------------
from ui.dashboard_ui_v2 import DashboardUI
from ui.agents_ui_v3 import AgentsUI
from ui.attendance_ui_v3_1 import AttendanceUI
from ui.vacation_ui import VacationUI
from ui.disciplinary_ui import DisciplinaryUI


class ProdTechManager(tb.Window):
    """Main Application for ProdTech Manager"""

    def __init__(self):
        super().__init__(themename="cyborg")
        self.title("ProdTech Manager")
        self.state("zoomed")
        self.minsize(1200, 700)
        self.configure(bg="#1E1E1E")

        self.active_frame = None
        self.frames = {}

        self.setup_ui()

    # ----------------------------------------------------------
    # 🧱 UI Setup
    # ----------------------------------------------------------
    def setup_ui(self):
        # Sidebar
        self.sidebar = tb.Frame(self, bootstyle="dark", width=250)
        self.sidebar.pack(side=LEFT, fill=Y)

        tb.Label(
            self.sidebar,
            text="⚙️ ProdTech Manager",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(20, 30))

        # Sidebar Buttons
        menu_items = [
            ("📊 Dashboard", "Dashboard"),
            ("👥 Agents", "Agents"),
            ("📅 Attendance", "Attendance"),
            ("🏖 Vacation", "Vacation"),
            ("⚖️ Disciplinary", "Disciplinary"),
            ("📂 Forms", "Forms"),
            ("🚪 Exit", "Exit"),
        ]

        for icon, name in menu_items:
            tb.Button(
                self.sidebar,
                text=icon,
                bootstyle="dark-outline",
                command=lambda n=name: self.switch_frame(n),
                width=22
            ).pack(pady=5)

        # Main Content Area
        self.main_frame = tb.Frame(self, bootstyle="dark")
        self.main_frame.pack(side=LEFT, fill=BOTH, expand=True)

        # Initialize All Modules
        self.frames = {
            "Dashboard": DashboardUI(self.main_frame),
            "Agents": AgentsUI(self.main_frame),
            "Attendance": AttendanceUI(self.main_frame),
            "Vacation": VacationUI(self.main_frame),
            "Disciplinary": DisciplinaryUI(self.main_frame),
        }

        # Start on Dashboard
        self.switch_frame("Dashboard")

    # ----------------------------------------------------------
    # 🔄 Frame Switcher
    # ----------------------------------------------------------
    def switch_frame(self, name):
        if name == "Exit":
            self.confirm_exit()
            return

        # Hide previous frame
        if self.active_frame:
            try:
                self.active_frame.grid_forget()
            except Exception:
                self.active_frame.pack_forget()

        # Show new one
        frame = self.frames.get(name)
        if frame:
            # Place using grid to avoid mixing geometry managers across siblings
            try:
                frame.grid(row=0, column=0, sticky="nsew")
            except Exception:
                frame.pack(fill=BOTH, expand=True)
            self.active_frame = frame

    # ----------------------------------------------------------
    # 🚪 Exit Confirmation
    # ----------------------------------------------------------
    def confirm_exit(self):
        if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit ProdTech Manager?"):
            self.destroy()


# ----------------------------------------------------------
# 🚀 Launch App
# ----------------------------------------------------------
if __name__ == "__main__":
    app = ProdTechManager()
    app.mainloop()
