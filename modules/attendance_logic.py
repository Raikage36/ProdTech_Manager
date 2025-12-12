# Example logic snippet

from datetime import datetime, timedelta

SHIFT_PATTERNS = {
    "A": {"work_days": 3, "work_nights": 3, "rest_days": 3},
    "B": {"work_days": 3, "work_nights": 3, "rest_days": 3},
    "C": {"work_days": 3, "work_nights": 3, "rest_days": 3},
    "Classic": {"work_days": 5, "rest_days": 2},
    "Extended": {"work_days": 10, "rest_days": 4},
}

def get_shift_status(shift_type, start_date, current_date=None):
    """Return whether the agent is working day, night, or resting."""
    if current_date is None:
        current_date = datetime.now().date()

    pattern = SHIFT_PATTERNS.get(shift_type)
    if not pattern:
        return "Unknown"

    total_cycle = sum(pattern.values())
    days_elapsed = (current_date - start_date).days % total_cycle

    if shift_type in ["A", "B", "C"]:
        if days_elapsed < pattern["work_days"]:
            return "Day Shift"
        elif days_elapsed < pattern["work_days"] + pattern["work_nights"]:
            return "Night Shift"
        else:
            return "Rest"
    elif shift_type == "Classic":
        weekday = current_date.weekday()
        return "Working" if weekday < 5 else "Rest"
    elif shift_type == "Extended":
        return "Working" if days_elapsed < 10 else "Rest"
