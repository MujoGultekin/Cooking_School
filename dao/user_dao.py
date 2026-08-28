from werkzeug.security import check_password_hash, generate_password_hash
from database.database import close_db, get_db

def get_user_by_id(user_id):
    """ID ile kullanıcı nesnesi verisini getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    close_db(conn)
    return user

def get_user_by_email(email):
    """Email adresi ile kullanıcı getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    close_db(conn)
    return user

def check_login(email, password):
    """Kullanıcı giriş kontrolü yapar."""
    user = get_user_by_email(email)
    if user and check_password_hash(user["password"], password):
        return user
    return None

def create_user(email, first_name, last_name, password, role="Student"):
    """
    Yeni kullanıcı kaydı oluşturur.
    Role: 'Manager' veya 'Student' olabilir.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Email eşsiz olmalı
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        close_db(conn)
        return False, "An account with this email address already exists."

    hashed_password = generate_password_hash(password)
    try:
        cursor.execute("""
            INSERT INTO users (email, first_name, last_name, password, role)
            VALUES (?, ?, ?, ?, ?)
        """, (email, first_name, last_name, hashed_password, role))
        conn.commit()
        close_db(conn)
        return True, "Account created successfully!"
    except Exception as e:
        close_db(conn)
        return False, f"Database error: {str(e)}"