from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user
from config import SIMULATED_CURRENT_DAY, SIMULATED_CURRENT_TIME

# Haftanın günlerini sıraya koymak için indeks haritası
DAYS_ORDER = {
    "Monday": 1,
    "Tuesday": 2,
    "Wednesday": 3,
    "Thursday": 4,
    "Friday": 5,
    "Saturday": 6,
    "Sunday": 7,
}


def parse_time_to_minutes(time_str):
    """'14:00' formatındaki saat stringini gece yarısından itibaren toplam dakikaya çevirir."""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except (ValueError, AttributeError):
        return 0


def can_cancel_enrollment(session_day, session_start_time):
    """
    Sınav kuralı: Öğrenci ders saatinden en az 12 saat önce iptal edebilir.
    Simüle edilen gün: SIMULATED_CURRENT_DAY, simüle edilen saat: SIMULATED_CURRENT_TIME.
    """
    current_day_idx = DAYS_ORDER.get(SIMULATED_CURRENT_DAY, 4)
    session_day_idx = DAYS_ORDER.get(session_day, 1)

    current_minutes = parse_time_to_minutes(SIMULATED_CURRENT_TIME)
    session_minutes = parse_time_to_minutes(session_start_time)

    # Gün farkını hesapla (haftalık döngü için)
    day_diff = session_day_idx - current_day_idx
    if day_diff < 0:
        day_diff += 7

    # Toplam kalan süre (saat cinsinden)
    total_hours_left = (day_diff * 24) + ((session_minutes - current_minutes) / 60.0)

    # En az 12 saat kalmışsa iptal izni ver
    return total_hours_left >= 12.0


def is_session_past(session_day, session_start_time):
    """Seansın simüle edilen zamana göre geçmişte kalıp kalmadığını kontrol eder (Puanlama için)."""
    current_day_idx = DAYS_ORDER.get(SIMULATED_CURRENT_DAY, 4)
    session_day_idx = DAYS_ORDER.get(session_day, 1)

    if session_day_idx < current_day_idx:
        return True
    elif session_day_idx == current_day_idx:
        current_minutes = parse_time_to_minutes(SIMULATED_CURRENT_TIME)
        session_minutes = parse_time_to_minutes(session_start_time)
        return session_minutes <= current_minutes

    return False

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "student":
            flash("This page is reserved for students only.", "danger")
            return redirect(url_for("home.index"))
        return f(*args, **kwargs)

    return decorated_function


def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "manager":
            flash("Access denied. Manager privileges required.", "danger")
            return redirect(url_for("home.index"))
        return f(*args, **kwargs)

    return decorated_function