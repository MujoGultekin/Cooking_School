import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
UPLOAD_FOLDER = os.path.join("static", "uploads")


def allowed_file(filename):
    """Checks if the file extension is supported."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_quest_image(file_storage):
    """Saves an uploaded image with a unique filename and returns the web URL path."""
    if not file_storage or file_storage.filename == "":
        return False, "No file selected."

    if not allowed_file(file_storage.filename):
        return False, "Invalid file format. Allowed: png, jpg, jpeg, gif, webp."

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    original_filename = secure_filename(file_storage.filename)
    name, ext = os.path.splitext(original_filename)

    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

    file_storage.save(file_path)

    web_path = f"/static/uploads/{unique_filename}"
    return True, web_path