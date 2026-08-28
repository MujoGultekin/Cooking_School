from database.database import close_db, get_db

def add_class_rating(student_id, session_id, score):
    """
    Öğrencinin geçmiş ders seansı için puanını kaydeder.
    Her öğrenci bir seansa yalnızca bir kez puan verebilir.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Öğrencinin bu seansa gerçekten kayıtlı olup olmadığını doğrula
    cursor.execute("""
        SELECT id FROM enrollments 
        WHERE student_id = ? AND session_id = ?
    """, (student_id, session_id))
    enrollment = cursor.fetchone()

    if not enrollment:
        close_db(conn)
        return False, "You can only rate sessions you have attended."

    try:
        cursor.execute("""
            INSERT INTO ratings (student_id, session_id, score)
            VALUES (?, ?, ?)
        """, (student_id, session_id, score))
        conn.commit()
        close_db(conn)
        return True, "Thank you for rating the class!"
    except Exception:
        close_db(conn)
        return False, "You have already rated this session."

def get_student_rating_for_session(student_id, session_id):
    """Öğrencinin ilgili seansa önceden puan verip vermediğini kontrol eder."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT score FROM ratings WHERE student_id = ? AND session_id = ?", (student_id, session_id))
    rating = cursor.fetchone()
    close_db(conn)
    return rating["score"] if rating else None