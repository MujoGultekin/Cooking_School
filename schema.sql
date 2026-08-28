PRAGMA FOREIGN_KEYS = ON;

DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS waiting_list;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS class_sessions;
DROP TABLE IF EXISTS cooking_classes;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('Manager', 'Student'))
);

CREATE TABLE cooking_classes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    manager_id INTEGER NOT NULL,
    title TEXT NOT NULL UNIQUE,
    cuisine TEXT NOT NULL,
    difficulty TEXT NOT NULL CHECK(difficulty IN ('Beginner', 'Intermediate', 'Advanced')),
    duration INTEGER NOT NULL,
    dietary_category TEXT NOT NULL CHECK(dietary_category IN ('Standard', 'Vegetarian', 'Vegan', 'Gluten-free')),
    chef_name TEXT NOT NULL,
    ingredients TEXT NOT NULL, -- Virgülle ayrılmış en az 4 malzeme
    description TEXT NOT NULL,
    photo_1 TEXT NOT NULL,
    photo_2 TEXT NOT NULL,
    photo_3 TEXT NOT NULL,
    FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE class_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_id INTEGER NOT NULL,
    day_of_week TEXT NOT NULL CHECK(day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    start_time TEXT NOT NULL, -- HH:MM formatında
    kitchen_name TEXT NOT NULL,
    max_capacity INTEGER NOT NULL DEFAULT 10,
    FOREIGN KEY (class_id) REFERENCES cooking_classes(id) ON DELETE CASCADE
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES class_sessions(id) ON DELETE CASCADE,
    UNIQUE(student_id, session_id)
);

CREATE TABLE ratings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    score INTEGER NOT NULL CHECK(score BETWEEN 1 AND 5),
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES class_sessions(id) ON DELETE CASCADE,
    UNIQUE(student_id, session_id)
);

CREATE TABLE waiting_list (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    session_id INTEGER NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (session_id) REFERENCES class_sessions(id) ON DELETE CASCADE,
    UNIQUE(student_id, session_id)
);