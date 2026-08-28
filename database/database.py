import os
import sqlite3

# Proje ana dizinini ve veritabanı dosya yolunu belirleme
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE = os.path.join(BASE_DIR, "culinary.db")


def get_db():
    """Veritabanı bağlantısı açar ve Row factory ile FOREIGN KEY kısıtlamalarını etkinleştirir."""
    conn = sqlite3.connect(DATABASE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def close_db(conn):
    """Açık olan veritabanı bağlantısını kapatır."""
    if conn:
        conn.close()