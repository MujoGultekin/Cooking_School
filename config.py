import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.environ.get("SECRET_KEY") or "culinary-academy-secret-key-2026"
DATABASE = os.path.join(BASE_DIR, "culinary.db")

# Sınav için simüle edilmiş gün ve saat
SIMULATED_CURRENT_DAY = "Thursday"
SIMULATED_CURRENT_TIME = "14:00"