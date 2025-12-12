"""
vacation_logic.py
-----------------

Handles all vacation-related logic for ProdTech Manager:
✅ Add new vacation requests
✅ Calculate used and remaining days
✅ Update vacation status
✅ Generate monthly or per-agent summaries
"""

from datetime import datetime
from modules.database_manager import (
    fetch_all,
    execute_query,
    insert_vacation,
    get_vacations,
)

# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------

def calculate_days(start_date: str, end_date: str) -> int:
    """
    Calculate total vacation days (inclusive).
    Example: 2025-12-10 to 2025-12-12 → 3 days
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        return (end - start).days + 1
    except Exception as e:
        print(f"[VACATION ERROR] Invalid date range: {e}")
        return 0

# ---------------------------------------------------------
# Core Logic
# ---------------------------------------------------------

def add_vacation(agent_id: int, start_date: str, end_date: str, reason: str):
    """
    Create a new vacation entry.
    Automatically calculates total days.
    Default status: Pending
    """
    total_days = calculate_days(start_date, end_date)

    print(f"🗓 Adding vacation: Agent {agent_id}, {total_days} days from {start_date} to {end_date}")

    insert_vacation(
        agent_id=agent_id,
        start_date=start_date,
        end_date=end_date,
        total_days=total_days,
        status="Pending",
        reason=reason
    )

def approve_vacation(vacation_id: int):
    """Approve a vacation request."""
    execute_query(
        "UPDATE vacations SET status = 'Approved' WHERE id = ?",
        (vacation_id,)
    )
    print(f"✅ Vacation ID {vacation_id} approved.")

def reject_vacation(vacation_id: int, reason: str):
    """Reject a vacation request with reason."""
    execute_query(
        "UPDATE vacations SET status = 'Rejected', reason = ? WHERE id = ?",
        (reason, vacation_id)
    )
    print(f"❌ Vacation ID {vacation_id} rejected for reason: {reason}")

def mark_vacation_used(vacation_id: int, days_used: int):
    """Update how many days from a vacation have been used."""
    execute_query(
        "UPDATE vacations SET days_used = ? WHERE id = ?",
        (days_used, vacation_id)
    )
    print(f"🔄 Updated vacation ID {vacation_id}: {days_used} days used.")

# ---------------------------------------------------------
# Retrieval Functions
# ---------------------------------------------------------

def get_all_vacations():
    """Return all vacation requests (for the dashboard)."""
    return get_vacations()

def get_agent_vacations(agent_id: int):
    """Get all vacations for a specific agent."""
    return get_vacations(agent_id=agent_id)

def get_pending_vacations():
    """List all pending vacation requests."""
    return fetch_all("SELECT * FROM vacations WHERE status = 'Pending' ORDER BY start_date ASC")

def get_vacation_summary():
    """
    Generate a global summary of all vacation statuses.
    Returns dict like:
    {
        "total": 25,
        "approved": 10,
        "pending": 5,
        "rejected": 3
    }
    """
    summary = {"total": 0, "approved": 0, "pending": 0, "rejected": 0}

    data = fetch_all("SELECT status, COUNT(*) FROM vacations GROUP BY status")

    for status, count in data:
        status_key = status.lower()
        if status_key in summary:
            summary[status_key] = count
        summary["total"] += count

    return summary

# ---------------------------------------------------------
# Report Export (optional use in dashboard)
# ---------------------------------------------------------

def export_vacations_to_excel(filename="vacation_report.xlsx"):
    """
    Export vacation data to Excel file.
    """
    import pandas as pd

    data = fetch_all("SELECT * FROM vacations")
    columns = ["id", "agent_id", "start_date", "end_date", "total_days", "days_used", "status", "reason"]

    df = pd.DataFrame(data, columns=columns)
    df.to_excel(filename, index=False)
    print(f"📁 Vacation report saved to {filename}")

# ---------------------------------------------------------
# Test Run (for manual validation)
# ---------------------------------------------------------
if __name__ == "__main__":
    print("Running vacation logic tests...")
    print(get_vacation_summary())
