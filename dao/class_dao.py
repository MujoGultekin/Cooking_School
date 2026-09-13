from database.database import close_db, get_db
from utils import is_session_past  # <--- Tarih/saat kontrolü eklendi


def get_all_cooking_classes():
    """Ana sayfa için tüm kursları ortalama puanlarıyla ve oluşturan Manager adı ile getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, 
               (u.first_name || ' ' || u.last_name) AS manager_name,
               AVG(r.score) AS avg_rating,
               COUNT(r.id) AS total_ratings
        FROM cooking_classes c
        JOIN users u ON c.manager_id = u.id
        LEFT JOIN class_sessions s ON c.id = s.class_id
        LEFT JOIN ratings r ON s.id = r.session_id
        GROUP BY c.id
        ORDER BY c.id DESC
    """)
    classes = cursor.fetchall()
    close_db(conn)
    return classes


def get_class_by_id(class_id):
    """Kurs detay sayfasında kursun tüm bilgilerini, Manager adını ve seanslarını dinamik zaman kontrolüyle getirir."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT c.*, 
               u.first_name AS manager_first_name, 
               u.last_name AS manager_last_name,
               (u.first_name || ' ' || u.last_name) AS manager_name,
               AVG(r.score) AS avg_rating,
               COUNT(r.id) AS total_ratings
        FROM cooking_classes c
        JOIN users u ON c.manager_id = u.id
        LEFT JOIN class_sessions s ON c.id = s.class_id
        LEFT JOIN ratings r ON s.id = r.session_id
        WHERE c.id = ?
        GROUP BY c.id
    """,
        (class_id,),
    )
    class_data = cursor.fetchone()

    if not class_data:
        close_db(conn)
        return None, []

    cursor.execute(
        """
        SELECT id, class_id, day_of_week, start_time, kitchen_name, max_capacity
        FROM class_sessions
        WHERE class_id = ?
        ORDER BY 
            CASE day_of_week
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END, start_time
    """,
        (class_id,),
    )
    sessions_raw = cursor.fetchall()

    sessions = []
    for s in sessions_raw:
        s_dict = dict(s)
        day = s_dict["day_of_week"]
        time_str = s_dict["start_time"]
        session_id = s_dict["id"]
        max_cap = s_dict["max_capacity"]

        # Seansın zamanı geçmiş mi kontrol et
        is_past = is_session_past(day, time_str)
        s_dict["is_past"] = is_past

        if is_past:
            # Ders saati geçtiyse YENİ HAFTA DÖNGÜSÜ İÇİN KAPASİTE TAZELENİR (0/MAX Boş)
            s_dict["enrolled_count"] = 0
            s_dict["available_slots"] = max_cap
            s_dict["waiting_count"] = 0
        else:
            # Gelecekteki aktif seans ise veritabanındaki kayıtları say
            cursor.execute(
                "SELECT COUNT(*) FROM enrollments WHERE session_id = ?",
                (session_id,),
            )
            enrolled = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM waiting_list WHERE session_id = ?",
                (session_id,),
            )
            waiting = cursor.fetchone()[0]

            s_dict["enrolled_count"] = enrolled
            s_dict["available_slots"] = max_cap - enrolled
            s_dict["waiting_count"] = waiting

        sessions.append(s_dict)

    close_db(conn)
    return class_data, sessions


def get_manager_classes(manager_id):
    """Yöneticinin açtığı kursları, seanslarını ve seansa kayıtlı öğrencilerin bilgilerini getirir."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM cooking_classes WHERE manager_id = ?", (manager_id,)
    )
    classes = cursor.fetchall()

    manager_data = []
    for c in classes:
        cursor.execute(
            """
            SELECT s.*, 
                   COUNT(e.id) AS enrolled_count,
                   (s.max_capacity - COUNT(e.id)) AS available_slots
            FROM class_sessions s
            LEFT JOIN enrollments e ON s.id = e.session_id
            WHERE s.class_id = ?
            GROUP BY s.id
        """,
            (c["id"],),
        )
        sessions = cursor.fetchall()

        sessions_with_students = []
        for s in sessions:
            s_dict = dict(s)

            # Seansa kayıtlı olan öğrencilerin ad, soyad ve e-postasını çek
            cursor.execute(
                """
                SELECT u.first_name, u.last_name, u.email 
                FROM enrollments e
                JOIN users u ON e.student_id = u.id
                WHERE e.session_id = ?
            """,
                (s["id"],),
            )
            s_dict["students"] = cursor.fetchall()

            # Bekleme listesindeki öğrencileri sırayla çek
            cursor.execute(
                """
                SELECT u.first_name, u.last_name, u.email 
                FROM waiting_list w
                JOIN users u ON w.student_id = u.id
                WHERE w.session_id = ?
                ORDER BY w.joined_at ASC
            """,
                (s["id"],),
            )
            s_dict["waiting_students"] = cursor.fetchall()

            sessions_with_students.append(s_dict)

        # Dersi düzenleyip düzenleyemeyeceğini kontrol et
        can_edit = len(sessions) == 0

        manager_data.append({
            "class": c,
            "sessions": sessions_with_students,
            "can_edit": can_edit,
        })

    close_db(conn)
    return manager_data


def create_cooking_class(
    manager_id,
    title,
    cuisine,
    difficulty,
    duration,
    dietary_category,
    chef_name,
    ingredients,
    description,
    photo_1,
    photo_2,
    photo_3,
):
    """Yeni yemek kursu açar."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO cooking_classes (manager_id, title, cuisine, difficulty, duration, dietary_category, chef_name, ingredients, description, photo_1, photo_2, photo_3)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                manager_id,
                title,
                cuisine,
                difficulty,
                duration,
                dietary_category,
                chef_name,
                ingredients,
                description,
                photo_1,
                photo_2,
                photo_3,
            ),
        )
        conn.commit()
        close_db(conn)
        return True, "Cooking class created successfully!"
    except Exception as e:
        close_db(conn)
        return False, f"Failed to create class: {str(e)}"


def can_edit_class(class_id):
    """Dersin henüz hiç seansı yoksa True döner (Düzenlenebilir)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as count FROM class_sessions WHERE class_id = ?",
        (class_id,),
    )
    count = cursor.fetchone()["count"]
    close_db(conn)
    return count == 0


def update_cooking_class(
    class_id,
    title,
    cuisine,
    difficulty,
    duration,
    dietary_category,
    chef_name,
    ingredients,
    description,
):
    """Ders bilgilerini günceller. Seansı varsa güncellenmez."""
    if not can_edit_class(class_id):
        return (
            False,
            "Cannot edit class because class sessions have already been scheduled for it.",
        )

    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE cooking_classes 
            SET title = ?, cuisine = ?, difficulty = ?, duration = ?, 
                dietary_category = ?, chef_name = ?, ingredients = ?, description = ?
            WHERE id = ?
        """,
            (
                title,
                cuisine,
                difficulty,
                duration,
                dietary_category,
                chef_name,
                ingredients,
                description,
                class_id,
            ),
        )
        conn.commit()
        close_db(conn)
        return True, "Class updated successfully!"
    except Exception as e:
        close_db(conn)
        return False, f"Failed to update class: {str(e)}"


def create_class_session(
    class_id, day_of_week, start_time, kitchen_name, max_capacity=10
):
    """Kursa yeni seans ekler. Mutfak, gün ve saat çakışmasını kontrol eder."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        clean_kitchen = kitchen_name.strip()
        clean_day = day_of_week.strip()
        clean_time = start_time.strip()

        cursor.execute(
            """
            SELECT id FROM class_sessions 
            WHERE LOWER(TRIM(kitchen_name)) = LOWER(?) 
              AND LOWER(TRIM(day_of_week)) = LOWER(?) 
              AND SUBSTR(TRIM(start_time), 1, 5) = SUBSTR(TRIM(?), 1, 5)
        """,
            (clean_kitchen, clean_day, clean_time),
        )

        existing_session = cursor.fetchone()
        if existing_session:
            close_db(conn)
            return (
                False,
                f"The kitchen '{clean_kitchen}' is already booked on {clean_day} at {clean_time[:5]}.",
            )

        cursor.execute(
            """
            INSERT INTO class_sessions (class_id, day_of_week, start_time, kitchen_name, max_capacity)
            VALUES (?, ?, ?, ?, ?)
        """,
            (class_id, clean_day, clean_time, clean_kitchen, max_capacity),
        )

        conn.commit()
        close_db(conn)
        return True, "Session added successfully!"

    except Exception as e:
        close_db(conn)
        return False, f"Failed to add session: {str(e)}"


def delete_class_session(session_id):
    """Seansı siler/iptal eder. Ancak kaydolmuş öğrenci varsa engel olur."""
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Seansa kayıtlı öğrenci sayısını kontrol et
        cursor.execute(
            "SELECT COUNT(*) as count FROM enrollments WHERE session_id = ?",
            (session_id,),
        )
        enrolled_count = cursor.fetchone()["count"]

        if enrolled_count > 0:
            close_db(conn)
            return (
                False,
                "Cannot delete or modify session because students have already enrolled in it.",
            )

        # Öğrenci yoksa seansı ve varsa bekleme listesini temizle
        cursor.execute(
            "DELETE FROM waiting_list WHERE session_id = ?", (session_id,)
        )
        cursor.execute(
            "DELETE FROM class_sessions WHERE id = ?", (session_id,)
        )

        conn.commit()
        close_db(conn)
        return True, "Session cancelled successfully!"

    except Exception as e:
        close_db(conn)
        return False, f"Failed to cancel session: {str(e)}"