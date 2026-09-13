from collections import Counter
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
from dao.image_dao import save_quest_image
from dao.stats_dao import get_manager_statistics

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
    """Yönetici paneli: Açılan kurslar, seanslar ve 5 temel istatistik göstergesi."""
    classes = get_manager_classes(current_user.id) or []
    stats = get_manager_statistics(current_user.id) or {}

    # sqlite3.Row dönüyorsa dict'e çevirelim veya güvenli erişim sağlayalım
    if isinstance(stats, dict):
        stats = dict(stats)
    else:
        try:
            stats = dict(stats)
        except Exception:
            stats = {}

    # 1. Toplam Ders ve Seans Sayısı
    stats["total_classes"] = len(classes)
    stats["total_sessions"] = sum(len(item.get("sessions", []) if isinstance(item, dict) else item["sessions"]) for item in classes)

    # 2. Toplam Kayıt Sayısı (Total Enrollments)
    total_enrollments = 0
    total_waiting = 0
    
    for item in classes:
        # item dictionary mi sqlite3.Row mu kontrol et
        sessions = item["sessions"] if isinstance(item, (dict, list)) and "sessions" in item else (item.get("sessions", []) if isinstance(item, dict) else [])
        for s in sessions:
            s_dict = dict(s) if not isinstance(s, dict) else s
            total_enrollments += s_dict.get("enrolled_count", 0)
            waiting = s_dict.get("waiting_students", [])
            total_waiting += len(waiting) if waiting else 0

    stats["total_enrollments"] = total_enrollments

    # 3. Bekleme Listesindeki Toplam Öğrenci Sayısı
    stats["total_waiting"] = total_waiting

    # 4. En Popüler Mutfak Türü (Most Popular Cuisine)
    if "popular_cuisine" not in stats or not stats["popular_cuisine"]:
        cuisine_counter = Counter()
        for item in classes:
            # sqlite3.Row erişimi için
            item_dict = dict(item) if not isinstance(item, dict) else item
            
            # cuisine verisini alma (item["cuisine"] veya item["class"]["cuisine"])
            cuisine = None
            if "cuisine" in item_dict:
                cuisine = item_dict["cuisine"]
            elif "class" in item_dict and isinstance(item_dict["class"], (dict, tuple)):
                c_obj = dict(item_dict["class"]) if not isinstance(item_dict["class"], dict) else item_dict["class"]
                cuisine = c_obj.get("cuisine")
            
            if cuisine:
                sessions = item_dict.get("sessions", [])
                class_enrollments = sum(
                    (dict(s) if not isinstance(s, dict) else s).get("enrolled_count", 0) 
                    for s in sessions
                )
                cuisine_counter[cuisine] += class_enrollments

        most_common = cuisine_counter.most_common(1)
        stats["popular_cuisine"] = most_common[0][0] if most_common and most_common[0][1] > 0 else "N/A"

    # 5. En Yüksek Puanlı Yemek Dersi (Highest Average Rating)
    if "top_rated_class" not in stats or not stats["top_rated_class"]:
        best_class = None
        highest_rating = -1.0
        for item in classes:
            item_dict = dict(item) if not isinstance(item, dict) else item
            
            title = item_dict.get("title")
            rating = item_dict.get("avg_rating", 0) or 0

            if not title and "class" in item_dict:
                c_obj = dict(item_dict["class"]) if not isinstance(item_dict["class"], dict) else item_dict["class"]
                title = c_obj.get("title")
                rating = c_obj.get("avg_rating", 0) or 0

            if rating and rating > highest_rating and rating > 0:
                highest_rating = rating
                best_class = title

        stats["top_rated_class"] = f"{best_class} (⭐ {highest_rating:.1f})" if best_class else "N/A"

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