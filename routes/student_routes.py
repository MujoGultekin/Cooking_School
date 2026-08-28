from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from dao.enrollment_dao import (
    cancel_enrollment,
    enroll_or_join_waiting_list,
    get_student_enrollments,
    get_student_waiting_list,
    leave_waiting_list,
)
from dao.rating_dao import add_class_rating
from utils import can_cancel_enrollment, is_session_past  # Simüle zaman fonksiyonları

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.before_request
@login_required
def check_student_role():
    """Yalnızca Student rolündeki kullanıcıların bu rotalara erişmesini sağlar."""
    if current_user.role != "Student":
        flash("Access denied. Student privileges required.", "danger")
        return redirect(url_for("home.index"))


@student_bp.route("/profile")
def profile():
    """Öğrenci profili: Aktif kayıtlar, geçmiş dersler ve bekleme listesi durumu."""
    enrollments = get_student_enrollments(current_user.id)
    waiting_sessions = get_student_waiting_list(current_user.id)
    
    return render_template(
        "student/profile.html", 
        enrollments=enrollments, 
        waiting_sessions=waiting_sessions
    )


@student_bp.route("/enroll/<int:session_id>", methods=["POST"])
def enroll(session_id):
    """Derse kayıt olma veya doluluğa göre Bekleme Listesine eklenme rotası."""
    ok, msg = enroll_or_join_waiting_list(current_user.id, session_id)
    flash(msg, "success" if ok else "danger")
    return redirect(request.referrer or url_for("home.index"))


@student_bp.route("/cancel/<int:session_id>", methods=["POST"])
@login_required
def cancel(session_id):
    """Derse 12 saat kala yapılan iptal işlemi (Otomatik FIFO bekleme listesi tetiklenir)."""
    # Form verilerini request üzerinden çekiyoruz
    day_of_week = request.form.get("day_of_week")
    start_time = request.form.get("start_time")

    if not can_cancel_enrollment(day_of_week, start_time):
        flash("Enrollment cannot be cancelled less than 12 hours before start time.", "danger")
        return redirect(url_for("student.profile"))

    ok, msg = cancel_enrollment(current_user.id, session_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("student.profile"))


@student_bp.route("/waiting-list/leave/<int:session_id>", methods=["POST"])
def leave_waiting(session_id):
    """Öğrencinin bekleme listesinden kendi isteğiyle ayrılması."""
    ok, msg = leave_waiting_list(current_user.id, session_id)
    flash(msg, "info" if ok else "danger")
    return redirect(url_for("student.profile"))


@student_bp.route("/rate/<int:session_id>", methods=["POST"])
def rate_session(session_id):
    """Tamamlanmış bir ders için 1-5 arası puan verme işlemi."""
    score = request.form.get("score", type=int)
    if not score or not (1 <= score <= 5):
        flash("Rating score must be between 1 and 5.", "danger")
        return redirect(url_for("student.profile"))

    ok, msg = add_class_rating(current_user.id, session_id, score)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("student.profile"))