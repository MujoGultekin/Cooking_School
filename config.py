import os

SECRET_KEY = os.environ.get("SECRET_KEY", "culinary-academy-secret-key")
DATABASE = "culinary_academy.db"

# Simüle Edilen Gün ve Saat Bilgisi
SIMULATED_DAY = "Monday"
SIMULATED_TIME = "09:00"  # Format: "HH:MM" (Örn: 09:00, 14:30)