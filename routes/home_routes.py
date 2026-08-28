from flask import Blueprint, render_template

from dao.class_dao import get_all_cooking_classes, get_class_by_id

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    """Ana sayfa: Tüm yemek kurslarını ve puan ortalamalarını listeler."""
    classes = get_all_cooking_classes()
    return render_template("index.html", classes=classes)


@home_bp.route("/class/<int:class_id>")
def class_detail(class_id):
    """Kurs detay sayfası: Seanslar, kontenjanlar ve şef detayları yer alır."""
    class_data, sessions = get_class_by_id(class_id)
    if not class_data:
        return render_template("404.html"), 404

    return render_template("class_detail.html", class_data=class_data, sessions=sessions)