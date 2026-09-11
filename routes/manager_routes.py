from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from dao.class_dao import (
    can_edit_class,
    create_class_session,
    create_cooking_class,
    delete_class_session,
    get_class_by_id,
    get_manager_classes,
    update_cooking_class,
)
from dao.image_dao import save_quest_image  # Görsel yükleme yardımcısı
from dao.stats_dao import get_manager_statistics
from utils import manager_required

manager_bp = Blueprint("manager", __name__, url_prefix="/manager")


@manager_bp.before_request
@login_required
def check_manager_role():
    """Yalnızca Manager rolündeki kullanıcıların bu rotalara erişmesini sağlar."""
    if current_user.role != "Manager":
        flash("Access denied. Manager privileges required.", "danger")
        return redirect(url_for("home.index"))


@manager_bp.route("/dashboard")
def dashboard():
    """Yönetici paneli: Açılan kurslar, seanslar ve Prova Finale istatistikleri."""
    classes = get_manager_classes(current_user.id)
    stats = get_manager_statistics(current_user.id)
    return render_template("manager/dashboard.html", classes=classes, stats=stats)


@manager_bp.route("/class/create", methods=["GET", "POST"])
def create_class():
    """Yeni Yemek Kursu oluşturma rotası."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        cuisine = request.form.get("cuisine", "").strip()
        difficulty = request.form.get("difficulty", "").strip()
        duration = request.form.get("duration", type=int)
        dietary_category = request.form.get("dietary_category", "").strip()
        chef_name = request.form.get("chef_name", "").strip()
        ingredients = request.form.get("ingredients", "").strip()
        description = request.form.get("description", "").strip()

        # En az 4 malzeme kontrolü (virgülle ayrılmış)
        ing_list = [i.strip() for i in ingredients.split(",") if i.strip()]
        if len(ing_list) < 4:
            flash("Please enter at least 4 main ingredients (separated by commas).", "danger")
            return render_template("manager/create_class.html")

        # 3 adet tanıtım fotoğrafının yüklenmesi
        photos = []
        for i in range(1, 4):
            file = request.files.get(f"photo_{i}")
            ok, result = save_quest_image(file)
            if not ok:
                flash(f"Photo {i} error: {result}", "danger")
                return render_template("manager/create_class.html")
            photos.append(result)

        ok, msg = create_cooking_class(
            manager_id=current_user.id,
            title=title,
            cuisine=cuisine,
            difficulty=difficulty,
            duration=duration,
            dietary_category=dietary_category,
            chef_name=chef_name,
            ingredients=ingredients,
            description=description,
            photo_1=photos[0],
            photo_2=photos[1],
            photo_3=photos[2],
        )

        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("manager.dashboard"))

    return render_template("manager/create_class.html")


@manager_bp.route("/class/edit/<int:class_id>", methods=["GET", "POST"])
def edit_class(class_id):
    """Ders düzenleme rotası (yalnızca hiç seans açılmamışsa izin verir)."""
    if not can_edit_class(class_id):
        flash("You cannot edit this class because class sessions have already been scheduled for it.", "warning")
        return redirect(url_for("manager.dashboard"))

    class_data, _ = get_class_by_id(class_id)
    if not class_data:
        flash("Class not found.", "danger")
        return redirect(url_for("manager.dashboard"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        cuisine = request.form.get("cuisine", "").strip()
        difficulty = request.form.get("difficulty", "").strip()
        duration = request.form.get("duration", type=int)
        dietary_category = request.form.get("dietary_category", "").strip()
        chef_name = request.form.get("chef_name", "").strip()
        ingredients = request.form.get("ingredients", "").strip()
        description = request.form.get("description", "").strip()

        ok, msg = update_cooking_class(
            class_id, title, cuisine, difficulty, duration, dietary_category, chef_name, ingredients, description
        )
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("manager.dashboard"))

    return render_template("manager/edit_class.html", class_data=class_data)


@manager_bp.route("/session/create/<int:class_id>", methods=["GET", "POST"])
def create_session(class_id):
    """Mevcut bir kursa yeni ders seansı ekleme rotası."""
    if request.method == "POST":
        day_of_week = request.form.get("day_of_week")
        start_time = request.form.get("start_time")
        kitchen_name = request.form.get("kitchen_name", "").strip()
        max_capacity = request.form.get("max_capacity", type=int, default=10)

        ok, msg = create_class_session(class_id, day_of_week, start_time, kitchen_name, max_capacity)
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("manager.dashboard"))

    return render_template("manager/create_session.html", class_id=class_id)


@manager_bp.route("/session/delete/<int:session_id>", methods=["POST"])
def cancel_session(session_id):
    """Seansı iptal etme / silme rotası (yalnızca hiç kayıtlı öğrenci yoksa izin verir)."""
    ok, msg = delete_class_session(session_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("manager.dashboard"))