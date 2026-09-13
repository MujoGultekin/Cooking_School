import os

SECRET_KEY = os.environ.get("SECRET_KEY", "culinary-academy-secret-key")
DATABASE = "culinary_academy.db"

# Simulated day and time settings for testing
SIMULATED_DAY = "Monday"
SIMULATED_TIME = "11:00"  # Format: "HH:MM" (e.g., 09:00, 14:30)