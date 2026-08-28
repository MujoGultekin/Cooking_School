from database.database import close_db, get_db

def get_manager_statistics(manager_id):
    conn = get_db()
    cursor = conn.cursor()

    # 1. Toplam Kurs ve Seans Sayısı
    cursor.execute("""
        SELECT COUNT(DISTINCT c.id) AS total_classes, COUNT(s.id) AS total_sessions
        FROM cooking_classes c
        LEFT JOIN class_sessions s ON c.id = s.class_id
        WHERE c.manager_id = ?
    """, (manager_id,))
    counts = cursor.fetchone()

    # 2. Toplam Kayıt Sayısı
    cursor.execute("""
        SELECT COUNT(e.id) AS total_enrollments
        FROM enrollments e
        JOIN class_sessions s ON e.session_id = s.id
        JOIN cooking_classes c ON s.class_id = c.id
        WHERE c.manager_id = ?
    """, (manager_id,))
    enrollments = cursor.fetchone()["total_enrollments"]

    # 3. Bekleme Listesindeki Toplam Öğrenci
    cursor.execute("""
        SELECT COUNT(w.id) AS total_waiting
        FROM waiting_list w
        JOIN class_sessions s ON w.session_id = s.id
        JOIN cooking_classes c ON s.class_id = c.id
        WHERE c.manager_id = ?
    """, (manager_id,))
    waiting = cursor.fetchone()["total_waiting"]

    # 4. En Popüler Mutfak (Cuisine)
    cursor.execute("""
        SELECT c.cuisine, COUNT(e.id) AS total
        FROM enrollments e
        JOIN class_sessions s ON e.session_id = s.id
        JOIN cooking_classes c ON s.class_id = c.id
        WHERE c.manager_id = ?
        GROUP BY c.cuisine ORDER BY total DESC LIMIT 1
    """, (manager_id,))
    top_cuisine_row = cursor.fetchone()
    top_cuisine = top_cuisine_row["cuisine"] if top_cuisine_row else "N/A"

    # 5. En Yüksek Puan Ortalamasına Sahip Kurs
    cursor.execute("""
        SELECT c.title, AVG(r.score) AS avg_rating
        FROM ratings r
        JOIN class_sessions s ON r.session_id = s.id
        JOIN cooking_classes c ON s.class_id = c.id
        WHERE c.manager_id = ?
        GROUP BY c.id ORDER BY avg_rating DESC LIMIT 1
    """, (manager_id,))
    top_rated_row = cursor.fetchone()
    top_rated_class = top_rated_row["title"] if top_rated_row else "N/A"

    # 6. Genel Ortalama Puan (Şablonun aradığı eksik alan!)
    cursor.execute("""
        SELECT AVG(r.score) AS avg_score
        FROM ratings r
        JOIN class_sessions s ON r.session_id = s.id
        JOIN cooking_classes c ON s.class_id = c.id
        WHERE c.manager_id = ?
    """, (manager_id,))
    avg_score_row = cursor.fetchone()
    avg_school_rating = round(avg_score_row["avg_score"], 1) if (avg_score_row and avg_score_row["avg_score"]) else 0.0

    close_db(conn)
    
    return {
        "total_classes": counts["total_classes"],
        "total_sessions": counts["total_sessions"],
        "total_enrollments": enrollments,
        "total_waiting": waiting,
        "top_cuisine": top_cuisine,
        "top_rated_class": top_rated_class,
        "avg_school_rating": avg_school_rating  # Eksik olan attribute buraya eklendi
    }