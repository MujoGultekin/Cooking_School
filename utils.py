from datetime import datetime, timedelta
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

# Haftanın günleri haritası (1: Pazartesi, 7: Pazar)
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
    """'14:00' formatındaki saat stringini dakikaya çevirir."""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except (ValueError, AttributeError):
        return 0


def get_next_session_datetime(session_day, session_start_time):
    """
    Seansın gün adı ve saatine göre en yakın geçmiş veya gelecek 
    tam datetime objesini hesaplar.
    """
    now = datetime.now()
    current_day_idx = now.isoweekday()  # 1 (Mon) - 7 (Sun)
    target_day_idx = DAYS_ORDER.get(session_day, 1)

    # Saat ve dakikayı ayır
    hours, minutes = map(int, session_start_time.split(":"))

    # Eğer seans günü BUGÜN ise
    if target_day_idx == current_day_idx:
        today_session_dt = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        # Seans bugün geçmiş bir saatte mi kaldı yoksa gelecek bir saatte mi?
        return today_session_dt

    # Farklı günse gün farkını hesapla
    day_diff = target_day_idx - current_day_idx
    if day_diff < 0:
        day_diff += 7

    target_date = now.date() + timedelta(days=day_diff)
    return datetime.combine(target_date, datetime.min.time()).replace(hour=hours, minute=minutes)


def can_cancel_enrollment(session_day, session_start_time):
    """
    Gerçek zamana göre 12 saat kuralı:
    Dersin başlama zamanına en az 12 saat varsa True döner.
    """
    now = datetime.now()
    session_dt = get_next_session_datetime(session_day, session_start_time)

    # Ders zaten geçmişte kaldıysa iptal edilemez!
    if now >= session_dt:
        return False
    
    # Kalan süre farkı
    time_difference = session_dt - now

    # En az 12 saat (43200 saniye) var mı?
    return time_difference.total_seconds() >= 12 * 3600


def is_session_past(session_day, session_start_time):
    """Ders saatinin geçip geçmediğini gerçek zamana göre kontrol eder."""
    now = datetime.now()
    session_dt = get_next_session_datetime(session_day, session_start_time)
    
    # Eğer seans zamanı şu andan önceyse bitmiştir
    return now > session_dt


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