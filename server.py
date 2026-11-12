#!/usr/bin/env python3
"""
UniSync - University Portal Backend Server
Provides REST API endpoints backed by a robust SQLite database (unisync.db),
and serves the static web application.

Usage:
    python3 server.py [port]
Default port is 5000.
"""

import sys
import os
import json
import sqlite3
import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "unisync.db")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_database():
    """Initializes tables and populates default demo data if not already present."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('student', 'lecturer', 'admin')),
        department TEXT DEFAULT 'Faculty of Computing',
        degree TEXT DEFAULT 'BSc (Hons) in Software Engineering',
        intake TEXT DEFAULT 'Intake 41',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS semesters (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS courses (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        semester_id TEXT NOT NULL,
        code TEXT NOT NULL,
        name TEXT NOT NULL,
        credits INTEGER NOT NULL DEFAULT 3,
        grade TEXT NOT NULL DEFAULT 'A (4.0)',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(semester_id) REFERENCES semesters(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS assignments (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        course TEXT NOT NULL,
        description TEXT DEFAULT '',
        due_date TEXT NOT NULL,
        weight INTEGER NOT NULL DEFAULT 20,
        status TEXT NOT NULL DEFAULT 'pending',
        created_by TEXT DEFAULT 'LEC001',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS timetable (
        id TEXT PRIMARY KEY,
        day TEXT NOT NULL,
        slot TEXT NOT NULL,
        slot_index INTEGER NOT NULL,
        subject TEXT NOT NULL,
        hall TEXT DEFAULT '',
        lecturer TEXT DEFAULT '',
        color TEXT DEFAULT 'indigo',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS notes (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """)

    # Check if users exist; if not, seed demo data
    cursor.execute("SELECT COUNT(*) as count FROM users")
    if cursor.fetchone()["count"] == 0:
        seed_demo_data(cursor)

    conn.commit()
    conn.close()


def seed_demo_data(cursor):
    """Inserts realistic sample records for KDU portal demo."""
    # 1. Users
    users = [
        ('DICT240047', 'Thevinu Gunawardena', 'thevinu@kdu.ac.lk', 'Mokoyako', 'student', 'Department of Computer Science', 'BSc (Hons) in Software Engineering', 'Intake 41'),
        ('DICT240048', 'Kamal Silva', 'kamal.s@kdu.ac.lk', 'password123', 'student', 'Department of Computer Science', 'BSc (Hons) in Computer Science', 'Intake 41'),
        ('DICT240049', 'Nimali Perera', 'nimali.p@kdu.ac.lk', 'password123', 'student', 'Department of Information Technology', 'BSc (Hons) in Information Technology', 'Intake 41'),
        ('LEC001', 'Dr. Asela Silva', 'asela.s@kdu.ac.lk', 'Secure123', 'lecturer', 'Faculty of Computing', 'Senior Lecturer - Software Engineering', 'Faculty'),
        ('LEC002', 'Prof. K. Fernando', 'fernando.k@kdu.ac.lk', 'Secure123', 'lecturer', 'Faculty of Computing', 'Professor & Head of Computing', 'Faculty'),
        ('ADM001', 'Eng. Rohan Dissanayake', 'admin@kdu.ac.lk', 'Admin123', 'admin', 'Faculty of Computing', 'Dean & Chief Systems Administrator', 'Administration')
    ]
    cursor.executemany(
        "INSERT INTO users (id, name, email, password, role, department, degree, intake) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        users
    )

    # 2. Semesters for Thevinu (DICT240047)
    semesters = [
        ('sem-1-thevinu', 'DICT240047', 'Semester 1'),
        ('sem-2-thevinu', 'DICT240047', 'Semester 2')
    ]
    cursor.executemany(
        "INSERT INTO semesters (id, user_id, name) VALUES (?, ?, ?)",
        semesters
    )

    # 3. Courses for Thevinu
    courses = [
        ('c1', 'DICT240047', 'sem-1-thevinu', 'CS1013', 'Programming Fundamentals', 3, 'A (4.0)'),
        ('c2', 'DICT240047', 'sem-1-thevinu', 'CS1023', 'Mathematics for Computing', 3, 'A- (3.7)'),
        ('c3', 'DICT240047', 'sem-1-thevinu', 'CS1032', 'Professional Development & Ethics', 2, 'A (4.0)'),
        ('c4', 'DICT240047', 'sem-2-thevinu', 'CS2013', 'Data Structures & Algorithms', 3, 'A (4.0)'),
        ('c5', 'DICT240047', 'sem-2-thevinu', 'CS2023', 'Database Management Systems', 3, 'B+ (3.3)'),
        ('c6', 'DICT240047', 'sem-2-thevinu', 'CS2033', 'Object-Oriented Software Engineering', 3, 'A (4.0)')
    ]
    cursor.executemany(
        "INSERT INTO courses (id, user_id, semester_id, code, name, credits, grade) VALUES (?, ?, ?, ?, ?, ?, ?)",
        courses
    )

    # 4. Assignments
    today = datetime.date.today()
    assignments = [
        ('a1', 'Database Normalization & ERD Project', 'CS2023 - Database Management Systems',
         'Design 3NF relational schema with SQL DDL scripts, triggers, and foreign keys.',
         (today + datetime.timedelta(days=3)).strftime("%Y-%m-%d"), 25, 'pending', 'LEC001'),
        ('a2', 'Binary Search Trees & AVL Balancing', 'CS2013 - Data Structures & Algorithms',
         'Implement self-balancing AVL tree in C++ with comprehensive unit test coverage.',
         (today + datetime.timedelta(days=7)).strftime("%Y-%m-%d"), 20, 'pending', 'LEC001'),
        ('a3', 'Software Architecture Case Study', 'CS2033 - Object-Oriented Software Engineering',
         'Comparative analysis between monolithic and microservices architectures in enterprise apps.',
         (today + datetime.timedelta(days=14)).strftime("%Y-%m-%d"), 15, 'pending', 'LEC002'),
        ('a4', 'Programming Lab Practical 04', 'CS1013 - Programming Fundamentals',
         'Submitted laboratory exercises on dynamic memory allocation and pointer arithmetic.',
         (today - datetime.timedelta(days=2)).strftime("%Y-%m-%d"), 10, 'completed', 'LEC001')
    ]
    cursor.executemany(
        "INSERT INTO assignments (id, title, course, description, due_date, weight, status, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        assignments
    )

    # 5. Timetable (4 periods: 08:30-10:30, 10:45-12:45, 13:30-15:30, 15:30-17:30)
    slots = [
        ('Mon', '08:30 - 10:30', 1, 'CS2013: Data Structures', 'FOC Lab 2', 'Dr. Asela Silva', 'indigo'),
        ('Mon', '10:45 - 12:45', 2, 'CS2023: Database Systems', 'Auditorium B', 'Prof. K. Fernando', 'emerald'),
        ('Tue', '10:45 - 12:45', 2, 'CS2033: OOSE Lecture', 'LH-04', 'Dr. Asela Silva', 'blue'),
        ('Tue', '13:30 - 15:30', 3, 'CS2013: Lab Session', 'FOC Lab 1', 'Lab Instructor', 'indigo'),
        ('Wed', '08:30 - 10:30', 1, 'CS2023: SQL Practical', 'Database Lab', 'Prof. K. Fernando', 'emerald'),
        ('Wed', '13:30 - 15:30', 3, 'Mathematics Tutorial', 'LH-02', 'Dept Faculty', 'purple'),
        ('Thu', '10:45 - 12:45', 2, 'CS2033: Software Architecture', 'LH-04', 'Dr. Asela Silva', 'blue'),
        ('Thu', '13:30 - 15:30', 3, 'Self Study & Research', 'Library / FOC', 'Self', 'gray'),
        ('Fri', '08:30 - 10:30', 1, 'Professional Ethics Seminar', 'Auditorium A', 'Guest Lecturer', 'amber'),
        ('Fri', '10:45 - 12:45', 2, 'Project Mentoring', 'Staff Room 3', 'Dr. Asela Silva', 'rose')
    ]
    for day, slot, idx, subj, hall, lec, color in slots:
        tid = f"{day}-P{idx}"
        cursor.execute(
            "INSERT INTO timetable (id, day, slot, slot_index, subject, hall, lecturer, color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (tid, day, slot, idx, subj, hall, lec, color)
        )

    # 6. Notes
    notes = [
        ('n1', 'DICT240047', 'Database Indexing & B-Trees',
         'B-Tree indexes support efficient equality and range queries (BETWEEN, <, >). Hash indexes are O(1) for exact matches but do not support range scans.',
         'Lecture Notes'),
        ('n2', 'DICT240047', 'Mid-Semester Exam Checklist',
         '1. Master AVL tree rotations (LL, RR, LR, RL).\n2. Practice SQL subqueries, JOINs and Group By.\n3. Review SOLID principles and Factory design pattern.',
         'Exam Prep')
    ]
    cursor.executemany(
        "INSERT INTO notes (id, user_id, title, content, category) VALUES (?, ?, ?, ?, ?)",
        notes
    )


class UniSyncHandler(SimpleHTTPRequestHandler):
    """Handles REST API calls and static file requests."""

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            raw = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw)
        return {}

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if not path.startswith("/api/"):
            # Serve static files (index.html, etc.)
            return super().do_GET()

        conn = get_db()
        cursor = conn.cursor()

        try:
            # 1. Health check
            if path == "/api/health":
                cursor.execute("SELECT COUNT(*) as u_count FROM users")
                u_cnt = cursor.fetchone()["u_count"]
                self._send_json({
                    "status": "online",
                    "database": "sqlite",
                    "path": DB_PATH,
                    "users_count": u_cnt,
                    "timestamp": datetime.datetime.now().isoformat()
                })

            # 2. Get Users (student roster for lecturer)
            elif path == "/api/users":
                role_filter = query.get("role", [None])[0]
                if role_filter:
                    cursor.execute("SELECT id, name, email, role, department, degree, intake, created_at FROM users WHERE role = ? ORDER BY id ASC", (role_filter,))
                else:
                    cursor.execute("SELECT id, name, email, role, department, degree, intake, created_at FROM users ORDER BY id ASC")
                users = [dict(r) for r in cursor.fetchall()]
                self._send_json(users)

            # 3. Get Semesters
            elif path == "/api/semesters":
                user_id = query.get("user_id", [None])[0]
                if user_id:
                    cursor.execute("SELECT * FROM semesters WHERE user_id = ? ORDER BY created_at ASC", (user_id,))
                else:
                    cursor.execute("SELECT * FROM semesters ORDER BY created_at ASC")
                semesters = [dict(r) for r in cursor.fetchall()]
                self._send_json(semesters)

            # 4. Get Courses
            elif path == "/api/courses":
                user_id = query.get("user_id", [None])[0]
                sem_id = query.get("semester_id", [None])[0]
                if user_id and sem_id:
                    cursor.execute("SELECT * FROM courses WHERE user_id = ? AND semester_id = ? ORDER BY code ASC", (user_id, sem_id))
                elif user_id:
                    cursor.execute("SELECT * FROM courses WHERE user_id = ? ORDER BY code ASC", (user_id,))
                else:
                    cursor.execute("SELECT * FROM courses ORDER BY code ASC")
                courses = [dict(r) for r in cursor.fetchall()]
                self._send_json(courses)

            # 5. Get Assignments
            elif path == "/api/assignments":
                cursor.execute("SELECT * FROM assignments ORDER BY due_date ASC")
                assignments = [dict(r) for r in cursor.fetchall()]
                self._send_json(assignments)

            # 6. Get Timetable
            elif path == "/api/timetable":
                cursor.execute("SELECT * FROM timetable ORDER BY day, slot_index ASC")
                rows = [dict(r) for r in cursor.fetchall()]
                self._send_json(rows)

            # 7. Get Notes
            elif path == "/api/notes":
                user_id = query.get("user_id", [None])[0]
                if user_id:
                    cursor.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY updated_at DESC", (user_id,))
                else:
                    cursor.execute("SELECT * FROM notes ORDER BY updated_at DESC")
                notes = [dict(r) for r in cursor.fetchall()]
                self._send_json(notes)

            # 8. Full Database Backup
            elif path == "/api/backup":
                cursor.execute("SELECT id, name, email, role, department, degree, intake, created_at FROM users")
                users = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT * FROM semesters")
                semesters = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT * FROM courses")
                courses = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT * FROM assignments")
                assignments = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT * FROM timetable")
                timetable = [dict(r) for r in cursor.fetchall()]
                cursor.execute("SELECT * FROM notes")
                notes = [dict(r) for r in cursor.fetchall()]

                self._send_json({
                    "version": "1.0",
                    "exported_at": datetime.datetime.now().isoformat(),
                    "users": users,
                    "semesters": semesters,
                    "courses": courses,
                    "assignments": assignments,
                    "timetable": timetable,
                    "notes": notes
                })

            else:
                self._send_json({"error": "Endpoint not found"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)
        finally:
            conn.close()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if not path.startswith("/api/"):
            return self._send_json({"error": "Bad request"}, 400)

        conn = get_db()
        cursor = conn.cursor()

        try:
            data = self._read_json()

            # 1. Login
            if path == "/api/auth/login":
                user_id = (data.get("id") or "").strip()
                password = (data.get("password") or "").strip()
                role = (data.get("role") or "").strip()

                cursor.execute("SELECT id, name, email, role, department, degree, intake FROM users WHERE id = ? AND password = ? AND role = ?",
                               (user_id, password, role))
                user = cursor.fetchone()
                if user:
                    self._send_json({"success": True, "user": dict(user)})
                else:
                    self._send_json({"success": False, "error": "Invalid User ID or Password."}, 401)

            # 2. Signup
            elif path == "/api/auth/signup":
                user_id = (data.get("id") or "").strip()
                name = (data.get("name") or "").strip()
                email = (data.get("email") or "").strip()
                password = (data.get("password") or "").strip()
                role = (data.get("role") or "student").strip()
                department = data.get("department", "Faculty of Computing")
                degree = data.get("degree", "BSc in Computing" if role == 'student' else "Academic Staff")
                intake = data.get("intake", "Intake 41" if role == 'student' else "Faculty")

                if not user_id or not name or not password:
                    return self._send_json({"error": "Missing required fields"}, 400)

                cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
                if cursor.fetchone():
                    return self._send_json({"error": "User ID already exists"}, 409)

                cursor.execute(
                    "INSERT INTO users (id, name, email, password, role, department, degree, intake) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (user_id, name, email, password, role, department, degree, intake)
                )

                # If student, create default semester 1
                if role == "student":
                    sem_id = f"sem-1-{user_id}"
                    cursor.execute("INSERT INTO semesters (id, user_id, name) VALUES (?, ?, ?)",
                                   (sem_id, user_id, "Semester 1"))
                    # Default course
                    c_id = f"c-{user_id}-1"
                    cursor.execute("INSERT INTO courses (id, user_id, semester_id, code, name, credits, grade) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (c_id, user_id, sem_id, "CS1013", "Programming Fundamentals", 3, "A (4.0)"))

                conn.commit()
                self._send_json({"success": True, "user": {
                    "id": user_id, "name": name, "email": email, "role": role,
                    "department": department, "degree": degree, "intake": intake
                }})

            # 3. Add / Update Assignment
            elif path == "/api/assignments":
                aid = data.get("id") or f"a{int(datetime.datetime.now().timestamp() * 1000)}"
                title = data.get("title", "New Assignment")
                course = data.get("course", "General")
                desc = data.get("description", "")
                due_date = data.get("due_date", datetime.date.today().strftime("%Y-%m-%d"))
                weight = int(data.get("weight", 20))
                status = data.get("status", "pending")
                created_by = data.get("created_by", "LEC001")

                cursor.execute("""
                    INSERT INTO assignments (id, title, course, description, due_date, weight, status, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        course = excluded.course,
                        description = excluded.description,
                        due_date = excluded.due_date,
                        weight = excluded.weight,
                        status = excluded.status
                """, (aid, title, course, desc, due_date, weight, status, created_by))
                conn.commit()
                self._send_json({"success": True, "id": aid})

            # 4. Save Timetable Slot
            elif path == "/api/timetable":
                day = data.get("day")
                slot_index = int(data.get("slot_index", 1))
                slot_label = data.get("slot", "")
                tid = data.get("id") or f"{day}-P{slot_index}"
                subject = data.get("subject", "").strip()
                hall = data.get("hall", "")
                lecturer = data.get("lecturer", "")
                color = data.get("color", "indigo")

                if subject == "":
                    # Empty subject deletes or clears slot
                    cursor.execute("DELETE FROM timetable WHERE id = ?", (tid,))
                else:
                    cursor.execute("""
                        INSERT INTO timetable (id, day, slot, slot_index, subject, hall, lecturer, color, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ON CONFLICT(id) DO UPDATE SET
                            subject = excluded.subject,
                            hall = excluded.hall,
                            lecturer = excluded.lecturer,
                            color = excluded.color,
                            slot = excluded.slot,
                            updated_at = CURRENT_TIMESTAMP
                    """, (tid, day, slot_label, slot_index, subject, hall, lecturer, color))
                conn.commit()
                self._send_json({"success": True, "id": tid})

            # 5. Add Semester
            elif path == "/api/semesters":
                sid = data.get("id") or f"sem-{int(datetime.datetime.now().timestamp() * 1000)}"
                user_id = data.get("user_id")
                name = data.get("name", "Semester")
                cursor.execute("INSERT INTO semesters (id, user_id, name) VALUES (?, ?, ?)", (sid, user_id, name))
                conn.commit()
                self._send_json({"success": True, "id": sid})

            # 6. Add / Update Course
            elif path == "/api/courses":
                cid = data.get("id") or f"c-{int(datetime.datetime.now().timestamp() * 1000)}"
                user_id = data.get("user_id")
                semester_id = data.get("semester_id")
                code = data.get("code", "CS101")
                name = data.get("name", "Course Name")
                credits = int(data.get("credits", 3))
                grade = data.get("grade", "A (4.0)")

                cursor.execute("""
                    INSERT INTO courses (id, user_id, semester_id, code, name, credits, grade)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        code = excluded.code,
                        name = excluded.name,
                        credits = excluded.credits,
                        grade = excluded.grade
                """, (cid, user_id, semester_id, code, name, credits, grade))
                conn.commit()
                self._send_json({"success": True, "id": cid})

            # 7. Add / Update Note
            elif path == "/api/notes":
                nid = data.get("id") or f"n-{int(datetime.datetime.now().timestamp() * 1000)}"
                user_id = data.get("user_id")
                title = data.get("title", "Untitled Note")
                content = data.get("content", "")
                category = data.get("category", "General")

                cursor.execute("""
                    INSERT INTO notes (id, user_id, title, content, category, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET
                        title = excluded.title,
                        content = excluded.content,
                        category = excluded.category,
                        updated_at = CURRENT_TIMESTAMP
                """, (nid, user_id, title, content, category))
                conn.commit()
                self._send_json({"success": True, "id": nid})

            # 8. Restore from backup
            elif path == "/api/restore":
                backup = data
                if "users" in backup:
                    cursor.execute("DELETE FROM users")
                    for u in backup["users"]:
                        cursor.execute("INSERT OR REPLACE INTO users (id, name, email, password, role, department, degree, intake) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                       (u["id"], u["name"], u["email"], u.get("password", "password123"), u["role"], u.get("department", ""), u.get("degree", ""), u.get("intake", "")))
                if "semesters" in backup:
                    cursor.execute("DELETE FROM semesters")
                    for s in backup["semesters"]:
                        cursor.execute("INSERT OR REPLACE INTO semesters (id, user_id, name) VALUES (?, ?, ?)",
                                       (s["id"], s["user_id"], s["name"]))
                if "courses" in backup:
                    cursor.execute("DELETE FROM courses")
                    for c in backup["courses"]:
                        cursor.execute("INSERT OR REPLACE INTO courses (id, user_id, semester_id, code, name, credits, grade) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                       (c["id"], c["user_id"], c["semester_id"], c["code"], c["name"], c["credits"], c["grade"]))
                if "assignments" in backup:
                    cursor.execute("DELETE FROM assignments")
                    for a in backup["assignments"]:
                        cursor.execute("INSERT OR REPLACE INTO assignments (id, title, course, description, due_date, weight, status, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                       (a["id"], a["title"], a["course"], a.get("description", ""), a["due_date"], a["weight"], a["status"], a.get("created_by", "LEC001")))
                if "timetable" in backup:
                    cursor.execute("DELETE FROM timetable")
                    for t in backup["timetable"]:
                        cursor.execute("INSERT OR REPLACE INTO timetable (id, day, slot, slot_index, subject, hall, lecturer, color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                                       (t["id"], t["day"], t["slot"], t["slot_index"], t["subject"], t.get("hall", ""), t.get("lecturer", ""), t.get("color", "indigo")))
                if "notes" in backup:
                    cursor.execute("DELETE FROM notes")
                    for n in backup["notes"]:
                        cursor.execute("INSERT OR REPLACE INTO notes (id, user_id, title, content, category) VALUES (?, ?, ?, ?, ?)",
                                       (n["id"], n["user_id"], n["title"], n["content"], n.get("category", "General")))

                conn.commit()
                self._send_json({"success": True, "message": "Database restored successfully"})

            # 9. Reset database to default seed
            elif path == "/api/reset":
                cursor.execute("DELETE FROM notes")
                cursor.execute("DELETE FROM courses")
                cursor.execute("DELETE FROM semesters")
                cursor.execute("DELETE FROM assignments")
                cursor.execute("DELETE FROM timetable")
                cursor.execute("DELETE FROM users")
                seed_demo_data(cursor)
                conn.commit()
                self._send_json({"success": True, "message": "Database reset to initial demo seeds"})

            else:
                self._send_json({"error": "Endpoint not found"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)
        finally:
            conn.close()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if not path.startswith("/api/"):
            return self._send_json({"error": "Bad request"}, 400)

        conn = get_db()
        cursor = conn.cursor()

        try:
            # Delete assignment
            if path.startswith("/api/assignments/"):
                aid = path.replace("/api/assignments/", "").strip()
                cursor.execute("DELETE FROM assignments WHERE id = ?", (aid,))
                conn.commit()
                self._send_json({"success": True, "deleted": aid})

            # Delete course
            elif path.startswith("/api/courses/"):
                cid = path.replace("/api/courses/", "").strip()
                cursor.execute("DELETE FROM courses WHERE id = ?", (cid,))
                conn.commit()
                self._send_json({"success": True, "deleted": cid})

            # Delete semester
            elif path.startswith("/api/semesters/"):
                sid = path.replace("/api/semesters/", "").strip()
                cursor.execute("DELETE FROM semesters WHERE id = ?", (sid,))
                conn.commit()
                self._send_json({"success": True, "deleted": sid})

            # Delete note
            elif path.startswith("/api/notes/"):
                nid = path.replace("/api/notes/", "").strip()
                cursor.execute("DELETE FROM notes WHERE id = ?", (nid,))
                conn.commit()
                self._send_json({"success": True, "deleted": nid})

            # Delete user (Admin only)
            elif path.startswith("/api/users/"):
                uid = path.replace("/api/users/", "").strip()
                cursor.execute("DELETE FROM users WHERE id = ?", (uid,))
                conn.commit()
                self._send_json({"success": True, "deleted": uid})

            else:
                self._send_json({"error": "Endpoint not found"}, 404)

        except Exception as e:
            self._send_json({"error": str(e)}, 500)
        finally:
            conn.close()


def run_server():
    init_database()
    global PORT
    server_address = ("", PORT)
    httpd = None
    for try_port in [PORT, 8080, 8081, 8000, 3000]:
        try:
            httpd = HTTPServer(("", try_port), UniSyncHandler)
            PORT = try_port
            break
        except OSError:
            continue
    if not httpd:
        print("Error: Could not bind to any suitable port.")
        sys.exit(1)

    print(f"==================================================")
    print(f"UniSync SQLite Server running at http://localhost:{PORT}")
    print(f"Database: {DB_PATH}")
    print(f"Serving web application and REST API endpoints.")
    print(f"Press Ctrl+C to stop.")
    print(f"==================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
