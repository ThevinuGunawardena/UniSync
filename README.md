# UniSync 2.0 - Academic Management Portal

**General Sir John Kotelawala Defence University (KDU) — Faculty of Computing**

UniSync 2.0 is a modern, responsive academic management platform designed for students, lecturers, and system administrators. It features a complete relational database layer supporting both a live **SQLite REST backend** (`server.py` + `unisync.db`) and an in-browser **IndexedDB database** (via Dexie.js) for offline and static hosting (e.g. on IIS / GitHub Pages).

---

## 🚀 Key Features

### 1. 🎓 Student Experience
- **Smart Academic Dashboard:** Live overview of upcoming deadlines, weekly schedule, cumulative GPA, and course credits.
- **Advanced GPA Calculator & Course Manager:**
  - Track individual semesters and course grades.
  - Official KDU grade scale with instant CGPA recalculation.
  - Honors classification badges (First Class, Second Upper, Second Lower, Pass, Academic Notice).
- **Course Assignment Tracker:**
  - Filter by All, Pending, and Completed.
  - Live deadline countdown badges ("Due in 2 days", "Due Today!", "Overdue").
  - Instant checkbox completion toggle.
- **Weekly Lecture Timetable:**
  - 4 academic periods (08:30–10:30, 10:45–12:45, 13:30–15:30, 15:30–17:30) across Monday–Friday.
  - Highlights current day, displays module, lecture hall/lab, and lecturer.
- **Study Notes Pad:**
  - Multi-note manager with debounced auto-saving directly to the database.
- **Academic Calculator:** Safe arithmetic evaluator with calculation history tape.
- **Quick Shortcuts:** Direct access to Student Outlook Webmail and Google Classroom.

### 2. 👨‍🏫 Lecturer Portal
- **Faculty Dashboard:** Live metrics on enrolled students and course assignments.
- **Assignment Publishing Center:** Create and publish assignments with titles, course codes, deadlines, weights, and detailed instructions.
- **Enrolled Student Directory:** Real-time roster loaded directly from the database with search and batch information.
- **Interactive Timetable Editor:** One-click slot editor to assign subjects, venues, lecturers, and color tags.

### 3. 🛡️ System Administration
- **Master User Directory:** Inspect and manage all user accounts (students, lecturers, admins).
- **User Management:** Create new user accounts or delete accounts with full cascading database consistency.
- **Database Control Center:** Live engine status, table counts, full JSON backup export, backup restoration, and demo reset.

### 4. 🤖 AI Academic Copilot
- Integrated academic assistant powered by Google Gemini (customizable API key stored locally).
- Quick prompt chips for data structures, normalization, and study scheduling.
- Built-in intelligent academic fallback engine when offline or before configuring an API key.

---

## 💾 Database Architecture

UniSync uses a **dual-engine database architecture**:

| Mode | Technology | When Used |
| :--- | :--- | :--- |
| **Server Mode (Default)** | Python 3 + SQLite3 (`unisync.db`) | When running `python3 server.py` (Port 8080 or specified) |
| **Client Mode (Fallback)** | Dexie.js + Browser IndexedDB | When hosted statically (IIS, GitHub Pages) or opened directly via browser |

### Database Schema

1. **`users`**: `id` (PK), `name`, `email`, `password`, `role` (student/lecturer/admin), `department`, `degree`, `intake`, `created_at`
2. **`semesters`**: `id` (PK), `user_id` (FK), `name`, `created_at`
3. **`courses`**: `id` (PK), `user_id` (FK), `semester_id` (FK), `code`, `name`, `credits`, `grade`, `created_at`
4. **`assignments`**: `id` (PK), `title`, `course`, `description`, `due_date`, `weight`, `status`, `created_by`, `created_at`
5. **`timetable`**: `id` (PK), `day`, `slot`, `slot_index`, `subject`, `hall`, `lecturer`, `color`, `updated_at`
6. **`notes`**: `id` (PK), `user_id` (FK), `title`, `content`, `category`, `updated_at`

---

## ⚡ Quick Start

### 1. Running with Python SQLite Server (Recommended)

No external `pip` dependencies required! UniSync runs entirely on Python's built-in standard library:

```bash
# Start the server (runs on port 8080 by default)
python3 server.py

# Or specify a custom port
python3 server.py 8080
```

Open your browser to:
👉 **`http://localhost:8080`**

### 2. Running as a Static Web Application (IndexedDB)

Simply open `index.html` in any web browser, or serve it with any web server (IIS, Apache, Nginx, or GitHub Pages). The app automatically connects to IndexedDB via `db.js`.

---

## 🔑 Demo Credentials

| Role | User ID | Password | Name |
| :--- | :--- | :--- | :--- |
| **Student** | `DICT240047` | `Mokoyako` | Thevinu Gunawardena (BSc SE, Intake 41) |
| **Student** | `DICT240048` | `password123` | Kamal Silva (BSc CS, Intake 41) |
| **Student** | `DICT240049` | `password123` | Nimali Perera (BSc IT, Intake 41) |
| **Lecturer** | `LEC001` | `Secure123` | Dr. Asela Silva (Senior Lecturer) |
| **Lecturer** | `LEC002` | `Secure123` | Prof. K. Fernando (Head of Computing) |
| **Admin** | `ADM001` | `Admin123` | Eng. Rohan Dissanayake (System Admin) |

*(Quick-fill buttons are provided on the login screen for instant one-click login.)*

---

## 📦 REST API Endpoints

- `GET /api/health` — Check server status & database connection
- `POST /api/auth/login` — Authenticate user credentials
- `POST /api/auth/signup` — Register new user
- `GET /api/users?role=[student|lecturer|admin]` — Fetch user accounts
- `DELETE /api/users/:id` — Delete a user account (Admin only)
- `GET /api/semesters?user_id=...` — Fetch student semesters
- `POST /api/semesters` — Create/update semester
- `DELETE /api/semesters/:id` — Delete semester and its courses
- `GET /api/courses?user_id=...` — Fetch courses
- `POST /api/courses` — Add/update course
- `DELETE /api/courses/:id` — Remove course
- `GET /api/assignments` — Fetch all published assignments
- `POST /api/assignments` — Publish or edit assignment
- `DELETE /api/assignments/:id` — Delete assignment
- `GET /api/timetable` — Fetch weekly lecture timetable
- `POST /api/timetable` — Update lecture timetable slot
- `GET /api/notes?user_id=...` — Fetch student study notes
- `POST /api/notes` — Create/update note
- `DELETE /api/notes/:id` — Delete note
- `GET /api/backup` — Export full database as JSON
- `POST /api/restore` — Restore database from JSON backup
- `POST /api/reset` — Reset database to pristine demo seeds

