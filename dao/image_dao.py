import os
import uuid  # Benzersiz isim üretmek için ekledik
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
    Yüklenen görseli güvenli ve benzersiz bir isimle static/uploads klasörüne kaydeder
    ve HTML'de kullanılacak dosya yolunu (URL) döndürür.
    """
    if not file_storage or file_storage.filename == "":
        return False, "No file selected."

    if not allowed_file(file_storage.filename):
        return False, "Invalid file format. Allowed: png, jpg, jpeg, gif, webp."

    # Yükleme klasörü yoksa otomatik oluştur
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    # 1. Dosya adını temizle (örn: roma1.jpeg)
    original_filename = secure_filename(file_storage.filename)
    
    # 2. İsim ve uzantıyı ayır ('roma1' ve '.jpeg')
    name, ext = os.path.splitext(original_filename)

    # 3. Benzersiz rastgele bir isim oluştur (örn: roma1_f8c3a1b2.jpeg)
    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"

    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    
    # Dosyayı kaydet
    file_storage.save(file_path)

    # Veritabanı ve HTML için benzersiz static URL yolunu döndür
    web_path = f"/static/uploads/{unique_filename}"
    return True, web_path