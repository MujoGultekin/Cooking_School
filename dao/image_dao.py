import os
from werkzeug.utils import secure_filename

# İzin verilen resim uzantıları
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# Yükleme klasörü (static/uploads)
UPLOAD_FOLDER = os.path.join("static", "uploads")


def allowed_file(filename):
    """Dosya uzantısının izin verilen formatta olup olmadığını kontrol eder."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_quest_image(file_storage):
    """
    Yüklenen görseli güvenli bir şekilde static/uploads klasörüne kaydeder
    ve HTML'de kullanılacak dosya yolunu (URL) döndürür.
    """
    if not file_storage or file_storage.filename == "":
        return False, "No file selected."

    if not allowed_file(file_storage.filename):
        return False, "Invalid file format. Allowed: png, jpg, jpeg, gif, webp."

    # Yükleme klasörü yoksa otomatik oluştur
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    filename = secure_filename(file_storage.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    # Dosyayı kaydet
    file_storage.save(file_path)

    # Veritabanı ve HTML için static URL yolunu döndür (örn: /static/uploads/pasta1.jpg)
    web_path = f"/static/uploads/{filename}"
    return True, web_path