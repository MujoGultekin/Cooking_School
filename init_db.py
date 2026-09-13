from werkzeug.security import generate_password_hash
from database.database import close_db, get_db

DEFAULT_PASSWORD = generate_password_hash("password123")

def init_database():
    conn = get_db()
    cursor = conn.cursor()

    # Load table schemas from schema.sql
    with open("schema.sql", "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    # 1. USERS (2 Managers, 4 Students)
    cursor.executescript(f"""
        INSERT INTO users (email, first_name, last_name, password, role) VALUES
        ('chef.mario@culinary.com', 'Mario', 'Rossi', '{DEFAULT_PASSWORD}', 'Manager'),
        ('chef.gordon@culinary.com', 'Gordon', 'Freeman', '{DEFAULT_PASSWORD}', 'Manager'),
        ('student.alice@gmail.com', 'Alice', 'Smith', '{DEFAULT_PASSWORD}', 'Student'),
        ('student.bob@gmail.com', 'Bob', 'Jones', '{DEFAULT_PASSWORD}', 'Student'),
        ('student.charlie@gmail.com', 'Charlie', 'Brown', '{DEFAULT_PASSWORD}', 'Student'),
        ('student.diana@gmail.com', 'Diana', 'Prince', '{DEFAULT_PASSWORD}', 'Student');
    """)

    # 2. COOKING CLASSES (Various cuisines, difficulties, and dietary categories)
    cursor.executescript("""
        INSERT INTO cooking_classes (manager_id, title, cuisine, difficulty, duration, dietary_category, chef_name, ingredients, description, photo_1, photo_2, photo_3) VALUES
        (1, 'Mastering Fresh Pasta', 'Italian', 'Intermediate', 120, 'Standard', 'Chef Alessandro Porcelli', 
         'Type 00 Flour, Eggs, Extra Virgin Olive Oil, Parmigiano Reggiano, Fresh Basil', 
         'Learn the ancient art of making fresh handmade Italian pasta from scratch with authentic techniques.',
         '/static/uploads/pasta1.jpg', '/static/uploads/pasta2.jpg', '/static/uploads/pasta3.jpg'),

        (1, 'Authentic Ramen & Gyoza', 'Japanese', 'Advanced', 150, 'Standard', 'Chef Kenji Sato', 
         'Ramen Noodles, Pork Belly, Soy Sauce, Mirin, Nori Seaweed, Green Onions', 
         'Dive deep into Japanese broth making and crispy gyoza techniques.',
         '/static/uploads/ramen1.jpg', '/static/uploads/ramen2.jpg', '/static/uploads/ramen3.jpg'),

        (2, 'Plant-Based Mexican Feast', 'Mexican', 'Beginner', 90, 'Vegan', 'Chef Ernesto Sanchez', 
         'Avocado, Black Beans, Corn Tortillas, Cilantro, Lime, Jalapeno', 
         'A fresh and vibrant look into traditional Mexican flavors without any animal products.',
         '/static/uploads/taco1.jpg', '/static/uploads/taco2.jpg', '/static/uploads/taco3.jpg'),

        (2, 'Gluten-Free French Pastry', 'French', 'Intermediate', 105, 'Gluten-free', 'Chef Ernesto Sanchez', 
         'Almond Flour, Egg Whites, Sugar, Dark Chocolate, Butter, Vanilla', 
         'Master delicate French macarons and choux pastry completely gluten-free.',
         '/static/uploads/pastry1.jpg', '/static/uploads/pastry2.jpg', '/static/uploads/pastry3.jpg');
    """)

    # 3. CLASS SESSIONS (Completed past sessions and active upcoming sessions)
    cursor.executescript("""
        INSERT INTO class_sessions (id, class_id, day_of_week, start_time, kitchen_name, max_capacity) VALUES
        -- Past completed sessions (historical data)
        (10, 1, 'Sunday', '09:00', 'Kitchen Alpha', 10),  -- Completed Pasta session
        (20, 3, 'Sunday', '12:00', 'Kitchen Beta', 10),   -- Completed Taco session

        -- Active simulation sessions (currently enrolled)
        (1, 1, 'Monday', '10:00', 'Kitchen Alpha', 2),    -- ID 1: Mon 10:00 (Pasta)
        (2, 3, 'Wednesday', '16:00', 'Kitchen Beta', 10),  -- ID 2: Wed 16:00 (Taco)
        (3, 1, 'Friday', '11:00', 'Kitchen Alpha', 10),   -- ID 3: Fri 11:00
        (4, 2, 'Thursday', '18:00', 'Kitchen Main', 2),   -- ID 4: Thu 18:00
        (5, 1, 'Monday', '12:00', 'Kitchen Sigma', 10);  -- ID 5: Mon 12:00 (Fresh Pasta)
    """)

    # 4. ENROLLMENTS
    cursor.executescript("""
        INSERT INTO enrollments (student_id, session_id) VALUES
        -- Past completed class enrollments
        (3, 10), (4, 20),

        -- Current active enrollments (for testing - no ratings yet)
        (3, 1), (4, 1), -- Alice and Bob enrolled in Mon 10:00 Pasta
        (3,5),          -- Alice enrolled in Mond 12:00 Pasta
        (3, 2),         -- Alice enrolled in Wed 16:00 Taco
        (3, 4), (4, 4); -- Alice and Bob enrolled in Thu 18:00 Ramen
    """)

    # 5. WAITING LIST (For testing full capacity logic)
    cursor.executescript("""
        INSERT INTO waiting_list (student_id, session_id) VALUES
        (5, 4); -- Charlie in 1st spot on waitlist (Session 4 is full)
    """)

    # 6. RATINGS & REVIEWS
    cursor.executescript("""
        INSERT INTO ratings (student_id, session_id, score) VALUES
        -- Ratings for old completed sessions only (Session 10 & 20)
        (3, 10, 5), -- Alice rated past Sunday session 5/5
        (4, 20, 4); -- Bob rated past Sunday session 4/5
        
        -- NOTE: Session 1 and 2 (active sessions) intentionally left unrated
    """)

    conn.commit()
    close_db(conn)
    print("Database initialized successfully with test data!")

if __name__ == "__main__":
    init_database()