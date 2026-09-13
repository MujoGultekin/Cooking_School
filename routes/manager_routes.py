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
    """Restricts access to users with the Manager role."""
    if current_user.role != "Manager":
        flash("Access denied. Manager privileges required.", "danger")
        return redirect(url_for("home.index"))


@manager_bp.route("/dashboard")
def dashboard():
    """Manager Dashboard: displays active classes, sessions, and summary metrics."""
    classes = get_manager_classes(current_user.id) or []
    raw_stats = get_manager_statistics(current_user.id) or {}

    stats = {}
    if isinstance(raw_stats, dict):
        stats = dict(raw_stats)
    else:
        try:
            stats = dict(raw_stats)
        except Exception:
            stats = {}

    total_sessions = 0
    total_enrollments = 0
    total_waiting = 0
    cuisine_counter = Counter()

    best_class_title = None
    highest_rating = -1.0

    for item in classes:
        item_dict = dict(item) if not isinstance(item, dict) else item

        cls_obj = item_dict.get("class")
        if cls_obj:
            cls_dict = dict(cls_obj) if not isinstance(cls_obj, dict) else cls_obj
        else:
            cls_dict = item_dict

        cuisine = cls_dict.get("cuisine")
        title = cls_dict.get("title")

        try:
            rating = float(cls_dict.get("avg_rating") or 0.0)
        except (ValueError, TypeError):
            rating = 0.0

        sessions = item_dict.get("sessions", [])
        total_sessions += len(sessions)

        class_enrollments = 0
        for s in sessions:
            s_dict = dict(s) if not isinstance(s, dict) else s
            enrolled = s_dict.get("enrolled_count", 0) or 0
            waiting = s_dict.get("waiting_students", []) or []

            total_enrollments += enrolled
            total_waiting += len(waiting) if isinstance(waiting, (list, tuple)) else 0
            class_enrollments += enrolled

        if cuisine and class_enrollments > 0:
            cuisine_counter[cuisine] += class_enrollments
        elif cuisine:
            cuisine_counter.setdefault(cuisine, 0)

        if rating > highest_rating:
            highest_rating = rating
            best_class_title = title
        elif best_class_title is None and title:
            best_class_title = title

    stats["total_classes"] = len(classes)
    stats["total_sessions"] = total_sessions
    stats["total_enrollments"] = total_enrollments
    stats["total_waiting"] = total_waiting

    most_common = cuisine_counter.most_common(1)
    if most_common:
        stats["popular_cuisine"] = most_common[0][0]
    else:
        stats["popular_cuisine"] = "N/A"

    if not stats.get("top_rated_class") or stats.get("top_rated_class") == "N/A":
        if best_class_title:
            if highest_rating > 0:
                stats["top_rated_class"] = f"{best_class_title} (⭐ {highest_rating:.1f})"
            else:
                stats["top_rated_class"] = best_class_title
        else:
            stats["top_rated_class"] = "N/A"

    return render_template("manager/dashboard.html", classes=classes, stats=stats)


@manager_bp.route("/class/create", methods=["GET", "POST"])
def create_class():
    """Handles creating a new Cooking Class."""
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        cuisine = request.form.get("cuisine", "").strip()
        difficulty = request.form.get("difficulty", "").strip()
        duration = request.form.get("duration", type=int)
        dietary_category = request.form.get("dietary_category", "").strip()
        chef_name = request.form.get("chef_name", "").strip()
        ingredients = request.form.get("ingredients", "").strip()
        description = request.form.get("description", "").strip()

        ing_list = [i.strip() for i in ingredients.split(",") if i.strip()]
        if len(ing_list) < 4:
            flash("Please enter at least 4 main ingredients (separated by commas).", "danger")
            return render_template("manager/create_class.html")

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
    """Edits a class (allowed only if no sessions have been scheduled yet)."""
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
    """Adds a new scheduled time slot for an existing cooking class."""
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
    """Cancels a session (allowed only if no students are currently enrolled)."""
    ok, msg = delete_class_session(session_id)
    flash(msg, "success" if ok else "danger")
    return redirect(url_for("manager.dashboard"))