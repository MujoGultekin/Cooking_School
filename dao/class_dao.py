from database.database import close_db, get_db

def get_all_cooking_classes():
    """Ana sayfa için tüm kursları ortalama puanlarıyla getirir."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.*, 
               COALESCE(AVG(r.score), 0) AS avg_rating,
               COUNT(DISTINCT r.id) AS total_ratings
        FROM cooking_classes c
        LEFT JOIN class_sessions s ON c.id = s.class_id
        LEFT JOIN ratings r ON s.id = r.session_id
        GROUP BY c.id
        ORDER BY c.id DESC
    """)
    classes = cursor.fetchall()
    close_db(conn)
    return classes

def get_class_by_id(class_id):
    """Kurs detay sayfasında kursun tüm bilgilerini ve seanslarını getirir."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.*, u.first_name AS manager_first_name, u.last_name AS manager_last_name,
               COALESCE(AVG(r.score), 0) AS avg_rating
        FROM cooking_classes c
        JOIN users u ON c.manager_id = u.id
        LEFT JOIN class_sessions s ON c.id = s.class_id
        LEFT JOIN ratings r ON s.id = r.session_id
        WHERE c.id = ?
        GROUP BY c.id
    """, (class_id,))
    class_data = cursor.fetchone()

    if not class_data:
        close_db(conn)
        return None, []

    # Kurse ait seansları ve kayıtlı/kalan kontenjan sayılarını getir
    cursor.execute("""
        SELECT s.*, 
               COUNT(e.id) AS enrolled_count,
               (s.max_capacity - COUNT(e.id)) AS available_slots,
               (SELECT COUNT(*) FROM waiting_list w WHERE w.session_id = s.id) AS waiting_count
        FROM class_sessions s
        LEFT JOIN enrollments e ON s.id = e.session_id
        WHERE s.class_id = ?
        GROUP BY s.id
        ORDER BY 
            CASE s.day_of_week
                WHEN 'Monday' THEN 1 WHEN 'Tuesday' THEN 2 WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4 WHEN 'Friday' THEN 5 WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END, s.start_time
    """, (class_id,))
    sessions = cursor.fetchall()

    close_db(conn)
    return class_data, sessions

def get_manager_classes(manager_id):
    """Yöneticinin açtığı kursları ve bu kurslara ait seans detaylarını getirir."""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM cooking_classes WHERE manager_id = ?", (manager_id,))
    classes = cursor.fetchall()
    
    manager_data = []
    for c in classes:
        cursor.execute("""
            SELECT s.*, 
                   COUNT(e.id) AS enrolled_count,
                   (s.max_capacity - COUNT(e.id)) AS available_slots
            FROM class_sessions s
            LEFT JOIN enrollments e ON s.id = e.session_id
            WHERE s.class_id = ?
            GROUP BY s.id
        """, (c["id"],))
        sessions = cursor.fetchall()
        manager_data.append({"class": c, "sessions": sessions})

    close_db(conn)
    return manager_data

def create_cooking_class(manager_id, title, cuisine, difficulty, duration, dietary_category, chef_name, ingredients, description, photo_1, photo_2, photo_3):
    """Yeni yemek kursu açar."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO cooking_classes (manager_id, title, cuisine, difficulty, duration, dietary_category, chef_name, ingredients, description, photo_1, photo_2, photo_3)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (manager_id, title, cuisine, difficulty, duration, dietary_category, chef_name, ingredients, description, photo_1, photo_2, photo_3))
        conn.commit()
        close_db(conn)
        return True, "Cooking class created successfully!"
    except Exception as e:
        close_db(conn)
        return False, f"Failed to create class: {str(e)}"

def create_class_session(class_id, day_of_week, start_time, kitchen_name, max_capacity=10):
    """Kursa yeni seans ekler."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO class_sessions (class_id, day_of_week, start_time, kitchen_name, max_capacity)
            VALUES (?, ?, ?, ?, ?)
        """, (class_id, day_of_week, start_time, kitchen_name, max_capacity))
        conn.commit()
        close_db(conn)
        return True, "Session added successfully!"
    except Exception as e:
        close_db(conn)
        return False, f"Failed to add session: {str(e)}"