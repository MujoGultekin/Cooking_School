from database.database import close_db, get_db

def enroll_or_join_waiting_list(student_id, session_id):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Kontenjan kontrolü
        cursor.execute(
            """
            SELECT max_capacity, 
                   (SELECT COUNT(*) FROM enrollments WHERE session_id = ?) as enrolled_count
            FROM class_sessions 
            WHERE id = ?
        """,
            (session_id, session_id),
        )
        session = cursor.fetchone()

        if not session:
            return False, "Session not found."

        # Daha önce kayıt olunmuş mu kontrolü
        cursor.execute(
            "SELECT id FROM enrollments WHERE student_id = ? AND session_id = ?",
            (student_id, session_id),
        )
        if cursor.fetchone():
            return False, "You are already enrolled in this session."

        if session["enrolled_count"] < session["max_capacity"]:
            # Ders kontenjanında yer var -> Kayıt Et
            cursor.execute(
                "INSERT INTO enrollments (student_id, session_id) VALUES (?, ?)",
                (student_id, session_id),
            )
            conn.commit()
            msg = "Successfully enrolled in the class!"
        else:
            # Kontenjan dolu -> Bekleme listesine ekle
            cursor.execute(
                "SELECT id FROM waiting_list WHERE student_id = ? AND session_id = ?",
                (student_id, session_id),
            )
            if cursor.fetchone():
                return False, "You are already on the waiting list for this session."

            cursor.execute(
                "INSERT INTO waiting_list (student_id, session_id) VALUES (?, ?)",
                (student_id, session_id),
            )
            conn.commit()
            msg = "Session is full. You have been added to the waiting list!"

        return True, msg

    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        close_db(conn)


def cancel_enrollment(student_id, session_id):
    """
    Kayıt iptal edilir.
    Bekleme listesinde öğrenci varsa ilk sıradaki kişi otomatik derse geçirilir.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Kaydı sil
    cursor.execute("DELETE FROM enrollments WHERE student_id = ? AND session_id = ?", (student_id, session_id))

    # Bekleme listesindeki ilk öğrenciyi çek (FIFO)
    cursor.execute("""
        SELECT id, student_id FROM waiting_list 
        WHERE session_id = ? ORDER BY joined_at ASC LIMIT 1
    """, (session_id,))
    next_student = cursor.fetchone()

    if next_student:
        # İlk kişiyi derse kaydet ve listeden çıkar
        cursor.execute("INSERT INTO enrollments (student_id, session_id) VALUES (?, ?)", (next_student["student_id"], session_id))
        cursor.execute("DELETE FROM waiting_list WHERE id = ?", (next_student["id"],))

    conn.commit()
    close_db(conn)
    return True, "Enrollment cancelled successfully."

def get_student_enrollments(student_id):
    """Öğrencinin aktif olarak kaydolduğu tüm ders seanslarını getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.id AS enrollment_id, s.id AS session_id, s.day_of_week, s.start_time, s.kitchen_name,
               c.title AS class_title, c.cuisine
        FROM enrollments e
        JOIN class_sessions s ON e.session_id = s.id
        JOIN cooking_classes c ON s.class_id = c.id
        WHERE e.student_id = ?
        ORDER BY 
            CASE s.day_of_week
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END, s.start_time
    """, (student_id,))
    enrollments = cursor.fetchall()
    close_db(conn)
    return enrollments


def get_student_waiting_list(student_id):
    """
    Öğrencinin bekleme listesinde olduğu dersleri 
    ve kaçıncı sırada (FIFO) olduğunu hesaplayarak getirir.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT w.id AS waiting_id, w.session_id, s.day_of_week, s.start_time,
               c.title AS class_title,
               (
                   SELECT COUNT(*) + 1 
                   FROM waiting_list w2 
                   WHERE w2.session_id = w.session_id AND w2.joined_at < w.joined_at
               ) AS position
        FROM waiting_list w
        JOIN class_sessions s ON w.session_id = s.id
        JOIN cooking_classes c ON s.class_id = c.id
        WHERE w.student_id = ?
        ORDER BY w.joined_at ASC
    """, (student_id,))
    waiting_list = cursor.fetchall()
    close_db(conn)
    return waiting_list


def leave_waiting_list(student_id, session_id):
    """Öğrenciyi bekleme listesinden kendi isteğiyle çıkarır."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM waiting_list WHERE student_id = ? AND session_id = ?", (student_id, session_id))
    conn.commit()
    close_db(conn)
    return True, "Removed from waiting list successfully."