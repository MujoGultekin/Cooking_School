from database.database import close_db, get_db


def enroll_or_join_waiting_list(student_id, session_id):
    conn = get_db()
    cursor = conn.cursor()

    try:
        # 1. Seans bilgilerini ve mevcut kayıt sayısını çek
        cursor.execute(
            """
            SELECT day_of_week, start_time, max_capacity, 
                   (SELECT COUNT(*) FROM enrollments WHERE session_id = ?) as enrolled_count
            FROM class_sessions 
            WHERE id = ?
        """,
            (session_id, session_id),
        )
        session = cursor.fetchone()

        if not session:
            return False, "Session not found."

        target_day = session["day_of_week"]
        target_time = session["start_time"]

        # 2. Daha önce BU SEANSA kayıt olunmuş mu kontrolü
        cursor.execute(
            "SELECT id FROM enrollments WHERE student_id = ? AND session_id = ?",
            (student_id, session_id),
        )
        if cursor.fetchone():
            return False, "You are already enrolled in this session."

        # 3. ZAMAN ÇAKIŞMASI KONTROLÜ (TIME CONFLICT)
        cursor.execute(
            """
            SELECT e.id 
            FROM enrollments e
            JOIN class_sessions s ON e.session_id = s.id
            WHERE e.student_id = ? 
              AND LOWER(TRIM(s.day_of_week)) = LOWER(TRIM(?))
              AND SUBSTR(TRIM(s.start_time), 1, 5) = SUBSTR(TRIM(?), 1, 5)
        """,
            (student_id, target_day, target_time),
        )
        if cursor.fetchone():
            return (
                False,
                f"You already have another class scheduled on {target_day} at {target_time[:5]}.",
            )

        # 4. HAFTALIK MAKSİMUM 4 SEANS LİMİTİ KONTROLÜ (EKLENEN KISIM)
        cursor.execute(
            "SELECT COUNT(*) as total_enrolled FROM enrollments WHERE student_id = ?",
            (student_id,),
        )
        total_enrolled = cursor.fetchone()["total_enrolled"]
        if total_enrolled >= 4:
            return (
                False,
                "Weekly enrollment limit reached. You cannot enroll in more than 4 sessions per week.",
            )

        # 5. Kontenjan kontrolü
        if session["enrolled_count"] < session["max_capacity"]:
            # Kontenjan var -> Kaydet
            cursor.execute(
                "INSERT INTO enrollments (student_id, session_id) VALUES (?, ?)",
                (student_id, session_id),
            )
            conn.commit()
            msg = "Successfully enrolled in the class!"
        else:
            # Kontenjan dolu -> Bekleme listesine al
            cursor.execute(
                "SELECT id FROM waiting_list WHERE student_id = ? AND session_id = ?",
                (student_id, session_id),
            )
            if cursor.fetchone():
                return (
                    False,
                    "You are already on the waiting list for this session.",
                )

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
    """Kayıt iptal edilir. Bekleme listesinde çakışması olmayan ilk öğrenci otomatik kaydolur."""
    conn = get_db()
    cursor = conn.cursor()

    try:
        # İptal edilen seansın detaylarını al
        cursor.execute(
            "SELECT day_of_week, start_time FROM class_sessions WHERE id = ?",
            (session_id,),
        )
        session_info = cursor.fetchone()

        # Kaydı sil
        cursor.execute(
            "DELETE FROM enrollments WHERE student_id = ? AND session_id = ?",
            (student_id, session_id),
        )

        if session_info:
            target_day = session_info["day_of_week"]
            target_time = session_info["start_time"]

            # Bekleme listesindeki öğrencileri sırayla getir (FIFO)
            cursor.execute(
                """
                SELECT id, student_id FROM waiting_list 
                WHERE session_id = ? ORDER BY joined_at ASC
            """,
                (session_id,),
            )
            waiting_students = cursor.fetchall()

            for student in waiting_students:
                candidate_id = student["student_id"]

                # Aday öğrencinin aynı saatte başka çakışan dersi var mı kontrol et
                cursor.execute(
                    """
                    SELECT e.id FROM enrollments e
                    JOIN class_sessions s ON e.session_id = s.id
                    WHERE e.student_id = ? 
                      AND LOWER(TRIM(s.day_of_week)) = LOWER(TRIM(?))
                      AND SUBSTR(TRIM(s.start_time), 1, 5) = SUBSTR(TRIM(?), 1, 5)
                """,
                    (candidate_id, target_day, target_time),
                )

                if not cursor.fetchone():
                    # Çakışması yoksa derse aktar
                    cursor.execute(
                        "INSERT INTO enrollments (student_id, session_id) VALUES (?, ?)",
                        (candidate_id, session_id),
                    )
                    cursor.execute(
                        "DELETE FROM waiting_list WHERE id = ?",
                        (student["id"],),
                    )
                    break

        conn.commit()
        return True, "Enrollment cancelled successfully."
    except Exception as e:
        conn.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        close_db(conn)


def get_student_enrollments(student_id):
    """Öğrencinin aktif olarak kaydolduğu tüm ders seanslarını ve puanını getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT e.id AS enrollment_id, s.id AS session_id, s.day_of_week, s.start_time, s.kitchen_name,
               c.title AS class_title, c.cuisine,
               r.score AS user_score
        FROM enrollments e
        JOIN class_sessions s ON e.session_id = s.id
        JOIN cooking_classes c ON s.class_id = c.id
        LEFT JOIN ratings r ON r.session_id = s.id AND r.student_id = e.student_id
        WHERE e.student_id = ?
        ORDER BY 
            CASE s.day_of_week
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END, s.start_time
    """,
        (student_id,),
    )
    enrollments = cursor.fetchall()
    close_db(conn)
    return enrollments


def get_student_waiting_list(student_id):
    """Öğrencinin bekleme listesinde olduğu dersleri ve sırasını getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
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
    """,
        (student_id,),
    )
    waiting_list = cursor.fetchall()
    close_db(conn)
    return waiting_list


def leave_waiting_list(student_id, session_id):
    """Öğrenciyi bekleme listesinden kendi isteğiyle çıkarır."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM waiting_list WHERE student_id = ? AND session_id = ?",
        (student_id, session_id),
    )
    conn.commit()
    close_db(conn)
    return True, "Removed from waiting list successfully."