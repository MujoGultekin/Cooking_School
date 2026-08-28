from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user

from dao.user_dao import check_login, create_user
from models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Kullanıcı giriş fonksiyonu."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template("auth/login.html")

        user_row = check_login(email, password)
        if user_row:
            user = User(
                user_id=user_row["id"],
                email=user_row["email"],
                first_name=user_row["first_name"],
                last_name=user_row["last_name"],
                role=user_row["role"],
            )
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("home.index"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Yeni kullanıcı (Manager veya Student) kayıt fonksiyonu."""
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        role = request.form.get("role", "Student").strip()

        if not all([email, first_name, last_name, password, confirm_password]):
            flash("Please fill in all fields.", "danger")
            return render_template("auth/register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template("auth/register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if role not in ["Manager", "Student"]:
            flash("Invalid role selected.", "danger")
            return render_template("auth/register.html")

        ok, message = create_user(email, first_name, last_name, password, role)
        flash(message, "success" if ok else "danger")
        if ok:
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    """Oturum kapatma fonksiyonu."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("home.index"))