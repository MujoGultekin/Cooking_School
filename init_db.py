from werkzeug.security import generate_password_hash
from database.database import close_db, get_db

DEFAULT_PASSWORD = generate_password_hash("password123")

def init_database():
    conn = get_db()
    cursor = conn.cursor()

    # Tablo yapılarını schema.sql'den yükle
    with open("schema.sql", "r", encoding="utf-8") as f:
        cursor.executescript(f.read())

    # 1. KULLANICILAR (2 Manager, 4 Student)
    cursor.executescript(f"""
        INSERT INTO users (email, first_name, last_name, password, role) VALUES
        ('chef.mario@culinary.com', 'Mario', 'Rossi', '{DEFAULT_PASSWORD}', 'Manager'),
        ('chef.gordon@culinary.com', 'Gordon', 'Ramsay', '{DEFAULT_PASSWORD}', 'Manager'),
        ('student.alice@gmail.com', 'Alice', 'Smith', '{DEFAULT_PASSWORD}', 'Student'),
        ('student.bob@gmail.com', 'Bob', 'Jones', '{DEFAULT_PASSWORD}', 'Student'),
        ('student.charlie@gmail.com', 'Charlie', 'Brown', '{DEFAULT_PASSWORD}', 'Student'),
        ('student.diana@gmail.com', 'Diana', 'Prince', '{DEFAULT_PASSWORD}', 'Student');
    """)

    # 2. YEMEK KURSLARI (Farklı mutfaklar, zorluklar ve kategoriler)
    cursor.executescript("""
        INSERT INTO cooking_classes (manager_id, title, cuisine, difficulty, duration, dietary_category, chef_name, ingredients, description, photo_1, photo_2, photo_3) VALUES
        (1, 'Mastering Fresh Pasta', 'Italian', 'Intermediate', 120, 'Standard', 'Chef Mario Rossi', 
         'Type 00 Flour, Eggs, Extra Virgin Olive Oil, Parmigiano Reggiano, Fresh Basil', 
         'Learn the ancient art of making fresh handmade Italian pasta from scratch with authentic techniques.',
         '/static/uploads/pasta1.jpg', '/static/uploads/pasta2.jpg', '/static/uploads/pasta3.jpg'),

        (1, 'Authentic Ramen & Gyoza', 'Japanese', 'Advanced', 150, 'Standard', 'Chef Kenji Sato', 
         'Ramen Noodles, Pork Belly, Soy Sauce, Mirin, Nori Seaweed, Green Onions', 
         'Dive deep into Japanese broth making and crispy gyoza techniques.',
         '/static/uploads/ramen1.jpg', '/static/uploads/ramen2.jpg', '/static/uploads/ramen3.jpg'),

        (2, 'Plant-Based Mexican Feast', 'Mexican', 'Beginner', 90, 'Vegan', 'Chef Gordon Ramsay', 
         'Avocado, Black Beans, Corn Tortillas, Cilantro, Lime, Jalapeno', 
         'A fresh and vibrant look into traditional Mexican flavors without any animal products.',
         '/static/uploads/taco1.jpg', '/static/uploads/taco2.jpg', '/static/uploads/taco3.jpg'),

        (2, 'Gluten-Free French Pastry', 'French', 'Intermediate', 105, 'Gluten-free', 'Chef Gordon Ramsay', 
         'Almond Flour, Egg Whites, Sugar, Dark Chocolate, Butter, Vanilla', 
         'Master delicate French macarons and choux pastry completely gluten-free.',
         '/static/uploads/pastry1.jpg', '/static/uploads/pastry2.jpg', '/static/uploads/pastry3.jpg');
    """)

    # 3. DERS SEANSLARI (Geçmiş Tamamlanmış ve Aktif Seanslar)
    cursor.executescript("""
        INSERT INTO class_sessions (id, class_id, day_of_week, start_time, kitchen_name, max_capacity) VALUES
        -- Geçmişte Kalmış ve Puanlaması Çoktan Bitmiş Seanslar (Tarihi eski)
        (10, 1, 'Sunday', '09:00', 'Kitchen Alpha', 10),  -- Çoktan tamamlanmış Pasta Seansı
        (20, 3, 'Sunday', '12:00', 'Kitchen Beta', 10),   -- Çoktan tamamlanmış Taco Seansı

        -- Aktif Simülasyon Seansları (Şu an kayıtlı oldukları)
        (1, 1, 'Monday', '10:00', 'Kitchen Alpha', 2),    -- ID 1: Pazartesi 10:00 (Pasta)
        (2, 3, 'Wednesday', '16:00', 'Kitchen Beta', 10),  -- ID 2: Çarşamba 16:00 (Taco)
        (3, 1, 'Friday', '11:00', 'Kitchen Alpha', 10),   -- ID 3: Cuma 11:00
        (4, 2, 'Thursday', '18:00', 'Kitchen Main', 2);   -- ID 4: Perşembe 18:00
    """)

    # 4. KAYITLAR (Enrollments)
    cursor.executescript("""
        INSERT INTO enrollments (student_id, session_id) VALUES
        -- Eski tamamlanmış ders kayıtları
        (3, 10), (4, 20),

        -- ŞU ANKİ AKTİF KAYITLAR (Simüle edilecek dersler - Puanları HENÜZ YOK)
        (3, 1), (4, 1), -- Alice ve Bob Monday 10:00 Pasta dersinde
        (3, 2);         -- Alice Wednesday 16:00 Taco dersinde
    """)

    # 5. BEKLEME LİSTESİ (Waiting List - Prova Finale Testi İçin)
    cursor.executescript("""
        INSERT INTO waiting_list (student_id, session_id) VALUES
        (5, 4); -- Charlie, Session 4 dolduğu için 1. sırada beklemede
    """)

    # 6. DERS DEĞERLENDİRMELERİ (Ratings)
    cursor.executescript("""
        INSERT INTO ratings (student_id, session_id, score) VALUES
        -- Sadece çoktan bitmiş ESKİ seansların puanları (Session 10 ve 20)
        (3, 10, 5), -- Alice eski Pazar dersine 5 puan vermişti
        (4, 20, 4); -- Bob eski Pazar dersine 4 puan vermişti
        
        -- DIKKAT: Session 1 ve Session 2 (Aktif dersler) için BURAYA HIÇBIR KAYIT EKLENMEDI!
    """)

    conn.commit()
    close_db(conn)
    print("Database initialized successfully with test data!")

if __name__ == "__main__":
    init_database()