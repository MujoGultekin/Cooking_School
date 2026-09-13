from database.database import close_db, get_db
from utils import is_session_past


def get_active_enrollments_count(cursor, student_id):
    """Counts active (non-past) enrollments for a given student."""
    cursor.execute(
        """
        SELECT s.day_of_week, s.start_time 
        FROM enrollments e
        JOIN class_sessions s ON e.session_id = s.id
        WHERE e.student_id = ?
    """,
        (student_id,),
    )
    student_enrollments = cursor.fetchall()

    active_count = 0
    for item in student_enrollments:
        if not is_session_past(item["day_of_week"], item["start_time"]):
            active_count += 1

    return active_count


def enroll_or_join_waiting_list(student_id, session_id):
    """Enrolls student in session or assigns to waiting list if capacity is reached."""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT day_of_week, start_time, max_capacity 
            FROM class_sessions 
            WHERE id = ?
        """,
            (session_id,),
        )
        session = cursor.fetchone()

        if not session:
            return False, "Session not found."

        target_day = session["day_of_week"]
        target_time = session["start_time"]
        max_capacity = session["max_capacity"]

        is_past = is_session_past(target_day, target_time)

        if is_past:
            enrolled_count = 0
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM enrollments WHERE session_id = ?",
                (session_id,),
            )
            enrolled_count = cursor.fetchone()[0]

        if not is_past:
            cursor.execute(
                "SELECT id FROM enrollments WHERE student_id = ? AND session_id = ?",
                (student_id, session_id),
            )
            if cursor.fetchone():
                return False, "You are already enrolled in this session."

        cursor.execute(
            """
            SELECT s.day_of_week, s.start_time 
            FROM enrollments e
            JOIN class_sessions s ON e.session_id = s.id
            WHERE e.student_id = ? 
              AND LOWER(TRIM(s.day_of_week)) = LOWER(TRIM(?))
              AND SUBSTR(TRIM(s.start_time), 1, 5) = SUBSTR(TRIM(?), 1, 5)
        """,
            (student_id, target_day, target_time),
        )
        conflicting_classes = cursor.fetchall()

        for conf in conflicting_classes:
            if not is_session_past(conf["day_of_week"], conf["start_time"]):
                return (
                    False,
                    f"You already have another class scheduled on {target_day} at {target_time[:5]}.",
                )

        active_enrolled_count = get_active_enrollments_count(cursor, student_id)
        if active_enrolled_count >= 4:
            return (
                False,
                "Weekly enrollment limit reached. You cannot enroll in more than 4 active sessions per week.",
            )

        if enrolled_count < max_capacity:
            cursor.execute(
                "SELECT id FROM enrollments WHERE student_id = ? AND session_id = ?",
                (student_id, session_id),
            )
            existing_enrollment = cursor.fetchone()

            if existing_enrollment:
                msg = "Successfully enrolled in the class for the upcoming session!"
            else:
                cursor.execute(
                    "INSERT INTO enrollments (student_id, session_id) VALUES (?, ?)",
                    (student_id, session_id),
                )
                msg = "Successfully enrolled in the class!"

            conn.commit()
        else:
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
    """Cancels enrollment and promotes eligible candidate from waiting list."""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT day_of_week, start_time FROM class_sessions WHERE id = ?",
            (session_id,),
        )
        session_info = cursor.fetchone()

        cursor.execute(
            "DELETE FROM enrollments WHERE student_id = ? AND session_id = ?",
            (student_id, session_id),
        )

        if session_info:
            target_day = session_info["day_of_week"]
            target_time = session_info["start_time"]

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

                active_count = get_active_enrollments_count(cursor, candidate_id)
                if active_count >= 4:
                    continue

                cursor.execute(
                    """
                    SELECT s.day_of_week, s.start_time FROM enrollments e
                    JOIN class_sessions s ON e.session_id = s.id
                    WHERE e.student_id = ? 
                      AND LOWER(TRIM(s.day_of_week)) = LOWER(TRIM(?))
                      AND SUBSTR(TRIM(s.start_time), 1, 5) = SUBSTR(TRIM(?), 1, 5)
                """,
                    (candidate_id, target_day, target_time),
                )
                conflicting_classes = cursor.fetchall()

                has_conflict = False
                for conf in conflicting_classes:
                    if not is_session_past(conf["day_of_week"], conf["start_time"]):
                        has_conflict = True
                        break

                if not has_conflict:
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
    """Retrieves all class enrollments and associated details for a student."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT e.id AS enrollment_id, s.id AS session_id, s.day_of_week, s.start_time, s.kitchen_name,
               c.title AS class_title, c.cuisine, c.chef_name, c.duration,
               (u.first_name || ' ' || u.last_name) AS manager_name,
               r.score AS user_score
        FROM enrollments e
        JOIN class_sessions s ON e.session_id = s.id
        JOIN cooking_classes c ON s.class_id = c.id
        JOIN users u ON c.manager_id = u.id
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
    """Retrieves waiting list entries and queue positions for a student."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT w.id AS waiting_id, w.session_id, s.day_of_week, s.start_time,
               c.title AS class_title, c.chef_name, c.duration,
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
    """Removes a student from a session waiting list."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM waiting_list WHERE student_id = ? AND session_id = ?",
        (student_id, session_id),
    )
    conn.commit()
    close_db(conn)
    return True, "Removed from waiting list successfully."