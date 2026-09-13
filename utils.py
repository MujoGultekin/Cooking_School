from datetime import datetime, timedelta
from functools import wraps
from flask import current_app, flash, redirect, url_for
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


def get_current_simulated_datetime():
    """
    config['SIMULATED_DAY'] ve config['SIMULATED_TIME'] değerlerini okur,
    tam ve net simüle edilmiş datetime objesini oluşturur.
    """
    now = datetime.now()
    
    try:
        simulated_day_str = current_app.config.get("SIMULATED_DAY", "Monday")
        simulated_time_str = current_app.config.get("SIMULATED_TIME", "09:00")
    except RuntimeError:
        return now

    # Saat ve Dakikayı Ayır
    try:
        sim_hour, sim_minute = map(int, simulated_time_str.split(":"))
    except (ValueError, AttributeError):
        sim_hour, sim_minute = 9, 0

    target_day_idx = DAYS_ORDER.get(simulated_day_str, now.isoweekday())
    current_day_idx = now.isoweekday()

    # Gün farkını hesapla
    day_diff = target_day_idx - current_day_idx
    simulated_date = now.date() + timedelta(days=day_diff)

    # Gün ve Saati Birleştir
    return datetime.combine(simulated_date, datetime.min.time()).replace(
        hour=sim_hour, minute=sim_minute, second=0, microsecond=0
    )


def parse_time_to_minutes(time_str):
    """'14:00' formatındaki saat stringini dakikaya çevirir."""
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except (ValueError, AttributeError):
        return 0


def get_next_session_datetime(session_day, session_start_time):
    """
    Seansın gün adı ve saatine göre simüle edilen zamandan 
    sonraki İLK GELECEK seans tarihini/saatini hesaplar.
    """
    sim_now = get_current_simulated_datetime()
    current_day_idx = sim_now.isoweekday()  # 1 (Mon) - 7 (Sun)
    target_day_idx = DAYS_ORDER.get(session_day, 1)

    # Saat ve dakikayı al
    hours, minutes = map(int, session_start_time.split(":"))

    # Hedef güne kaç gün var?
    day_diff = target_day_idx - current_day_idx

    # Eğer seans günü BUGÜN ise:
    if day_diff == 0:
        today_session_dt = sim_now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
        # Eğer seans saati simüle edilen saatten ÖNCE kaldıysa, 
        # bu seans gelecek haftanın seansıdır (+7 gün)!
        if today_session_dt <= sim_now:
            return today_session_dt + timedelta(days=7)
        return today_session_dt

    # Eğer seans günü haftanın geçmiş bir günüyse (Örn: Bugün Çarşamba, Seans Pazartesi)
    if day_diff < 0:
        day_diff += 7

    target_date = sim_now.date() + timedelta(days=day_diff)
    return datetime.combine(target_date, datetime.min.time()).replace(hour=hours, minute=minutes)


def can_cancel_enrollment(session_day, session_start_time):
    """
    Simüle zamana göre 12 saat kuralı:
    Simüle edilen saat ile Ders Saati arasında EN AZ 12 SAAT var mı?
    """
    sim_now = get_current_simulated_datetime()
    session_dt = get_next_session_datetime(session_day, session_start_time)

    # Ders zaten geçmiş bir saatte/günde kaldıysa iptal edilemez
    if sim_now >= session_dt:
        return False
    
    # Kalan süre (Kayıtlı Ders Saati - Simüle Anı)
    time_difference = session_dt - sim_now

    # Kalan süre 12 saatten (12 * 3600 saniye) fazla/eşit mi?
    return time_difference.total_seconds() >= 12 * 3600


def is_session_past(session_day, session_start_time):
    """
    Simüle edilen zaman, seansın gün ve saatini geçtiyse True (Completed) döner.
    """
    if not session_day or not session_start_time:
        return False

    # 1. Simüle zamanı al (Örn: Pazartesi 11:00)
    sim_now = get_current_simulated_datetime()
    sim_day_idx = sim_now.isoweekday()  # 1 (Pazartesi) - 7 (Pazar)
    target_day_idx = DAYS_ORDER.get(session_day, 1)

    # 2. Saat formatını güvenli şekilde ayrıştır (Örn: "10:00:00" -> 10 ve 00)
    time_parts = str(session_start_time).strip().split(":")
    session_hour = int(time_parts[0])
    session_minute = int(time_parts[1])

    # 3. Gün Kıyaslaması:
    # Simüle gün, ders gününden ilerideyse (Örn: Perşembe > Pazartesi) -> BİTTİ
    if sim_day_idx > target_day_idx:
        return True

    # Simüle gün, ders gününden gerideyse (Örn: Pazartesi < Çarşamba) -> BİTMEDİ
    if sim_day_idx < target_day_idx:
        return False

    # 4. Aynı Gündeysek Saat Kıyaslaması (Örn: İkisi de Pazartesi):
    # Toplam dakikaya çevirip net kıyaslıyoruz
    sim_total_minutes = sim_now.hour * 60 + sim_now.minute
    session_total_minutes = session_hour * 60 + session_minute

    # Simüle saat (11:00 = 660 dk) >= Ders saati (10:00 = 600 dk) -> BİTTİ (True)
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