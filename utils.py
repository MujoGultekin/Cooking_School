from datetime import datetime, timedelta
from functools import wraps
from flask import config, current_app, flash, redirect, url_for
from flask_login import current_user

from config import SIMULATED_DAY, SIMULATED_TIME

# Map weekday names to index (1: Monday, 7: Sunday)
DAYS_ORDER = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 7,
}


def get_current_simulated_datetime():
    """Builds and returns the full datetime object based on simulated config settings."""
    now = datetime.now()
    
    try:
        simulated_day_str = getattr(config, "SIMULATED_DAY", "Monday")
        simulated_time_str = getattr(config, "SIMULATED_TIME", "11:00")
    except RuntimeError:
        # Fallback to current system time if app context is missing
        return now

    # Parse hours and minutes
    try:
        sim_hour, sim_minute = map(int, simulated_time_str.split(":"))
    except (ValueError, AttributeError):
        # Default fallback time
        sim_hour, sim_minute = 9, 0

    target_day_idx = DAYS_ORDER.get(simulated_day_str, now.isoweekday())
    current_day_idx = now.isoweekday()

    # Calculate day difference to target date
    day_diff = target_day_idx - current_day_idx
    simulated_date = now.date() + timedelta(days=day_diff)

    # Combine simulated date and time components
    return datetime.combine(simulated_date, datetime.min.time()).replace(
        hour=sim_hour, minute=sim_minute, second=0, microsecond=0
    )


def parse_time_to_minutes(time_str):
    """Converts a 'HH:MM' string to total minutes from midnight."""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except (ValueError, AttributeError):
        return 0


def get_next_session_datetime(session_day, session_start_time):
    """Calculates the next upcoming datetime for a session relative to current simulated time."""
    sim_now = get_current_simulated_datetime()
    current_day_idx = sim_now.isoweekday()  # 1 (Mon) - 7 (Sun)
    target_day_idx = DAYS_ORDER.get(session_day, 1)

    # Extract target session hour and minute
    hours, minutes = map(int, session_start_time.split(":"))

    # Days remaining until the target session day
    day_diff = target_day_idx - current_day_idx

    # If the session takes place today
    if day_diff == 0:
        today_session_dt = sim_now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        # If the session time has already passed today, schedule for next week (+7 days)
        if today_session_dt <= sim_now:
            return today_session_dt + timedelta(days=7)
        return today_session_dt

    # If the session day was earlier this week (e.g., today is Wed, session is Mon)
    if day_diff < 0:
        day_diff += 7

    target_date = sim_now.date() + timedelta(days=day_diff)
    return datetime.combine(target_date, datetime.min.time()).replace(hour=hours, minute=minutes)


def can_cancel_enrollment(session_day, session_start_time):
    """Checks if there is at least a 12-hour window left before session starts."""
    sim_now = get_current_simulated_datetime()
    session_dt = get_next_session_datetime(session_day, session_start_time)

    # Cannot cancel if the session has already passed
    if sim_now >= session_dt:
        return False
    
    # Calculate time remaining
    time_difference = session_dt - sim_now

    # Return True only if at least 12 hours (43,200 seconds) remain
    return time_difference.total_seconds() >= 12 * 3600


def is_session_past(session_day, session_start_time):
    """Returns True if the session has passed relative to current simulated time."""
    if not session_day or not session_start_time:
        return False

    # Get current simulated status
    sim_now = get_current_simulated_datetime()
    sim_day_idx = sim_now.isoweekday()  # 1 (Mon) - 7 (Sun)
    target_day_idx = DAYS_ORDER.get(session_day, 1)

    # Safely parse start time (e.g. "10:00:00")
    time_parts = str(session_start_time).strip().split(":")
    session_hour = int(time_parts[0])
    session_minute = int(time_parts[1])

    # 1. Day comparison (e.g., Thu > Mon means session is completed)
    if sim_day_idx > target_day_idx:
        return True

    # Session is in the future if current day is earlier in the week
    if sim_day_idx < target_day_idx:
        return False

    # 2. Time comparison for the same day
    sim_total_minutes = sim_now.hour * 60 + sim_now.minute
    session_total_minutes = session_hour * 60 + session_minute

    # Completed if simulated minute mark is past or equal to session start
    return sim_total_minutes >= session_total_minutes


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.lower() != "student":
            flash("This page is reserved for students only.", "danger")
            return redirect(url_for("home.index"))
        return f(*args, **kwargs)

    return decorated_function


def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role.lower() != "manager":
            flash("Access denied. Manager privileges required.", "danger")
            return redirect(url_for("home.index"))
        return f(*args, **kwargs)

    return decorated_function