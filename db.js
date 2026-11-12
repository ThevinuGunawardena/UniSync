/**
 * UniSync Database Service (db.js)
 * High-performance data layer supporting:
 * 1. Live SQLite REST backend (when server.py is running)
 * 2. In-Browser IndexedDB database via Dexie.js (for offline/static hosting on IIS/GitHub Pages)
 * 3. Unified asynchronous interface with backup, restore, and demo data seeding.
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.UniSyncDB = factory();
    }
}(typeof self !== 'undefined' ? self : this, function () {

    const KDU_INITIAL_SEEDS = {
        users: [
            { id: 'DICT240047', name: 'Thevinu Gunawardena', email: 'thevinu@kdu.ac.lk', password: 'Mokoyako', role: 'student', department: 'Department of Computer Science', degree: 'BSc (Hons) in Software Engineering', intake: 'Intake 41' },
            { id: 'DICT240048', name: 'Kamal Silva', email: 'kamal.s@kdu.ac.lk', password: 'password123', role: 'student', department: 'Department of Computer Science', degree: 'BSc (Hons) in Computer Science', intake: 'Intake 41' },
            { id: 'DICT240049', name: 'Nimali Perera', email: 'nimali.p@kdu.ac.lk', password: 'password123', role: 'student', department: 'Department of Information Technology', degree: 'BSc (Hons) in Information Technology', intake: 'Intake 41' },
            { id: 'LEC001', name: 'Dr. Asela Silva', email: 'asela.s@kdu.ac.lk', password: 'Secure123', role: 'lecturer', department: 'Faculty of Computing', degree: 'Senior Lecturer - Software Engineering', intake: 'Faculty' },
            { id: 'LEC002', name: 'Prof. K. Fernando', email: 'fernando.k@kdu.ac.lk', password: 'Secure123', role: 'lecturer', department: 'Faculty of Computing', degree: 'Professor & Head of Computing', intake: 'Faculty' },
            { id: 'ADM001', name: 'Eng. Rohan Dissanayake', email: 'admin@kdu.ac.lk', password: 'Admin123', role: 'admin', department: 'Faculty of Computing', degree: 'Dean & Chief Systems Administrator', intake: 'Administration' }
        ],
        semesters: [
            { id: 'sem-1-thevinu', user_id: 'DICT240047', name: 'Semester 1' },
            { id: 'sem-2-thevinu', user_id: 'DICT240047', name: 'Semester 2' }
        ],
        courses: [
            { id: 'c1', user_id: 'DICT240047', semester_id: 'sem-1-thevinu', code: 'CS1013', name: 'Programming Fundamentals', credits: 3, grade: 'A (4.0)' },
            { id: 'c2', user_id: 'DICT240047', semester_id: 'sem-1-thevinu', code: 'CS1023', name: 'Mathematics for Computing', credits: 3, grade: 'A- (3.7)' },
            { id: 'c3', user_id: 'DICT240047', semester_id: 'sem-1-thevinu', code: 'CS1032', name: 'Professional Development & Ethics', credits: 2, grade: 'A (4.0)' },
            { id: 'c4', user_id: 'DICT240047', semester_id: 'sem-2-thevinu', code: 'CS2013', name: 'Data Structures & Algorithms', credits: 3, grade: 'A (4.0)' },
            { id: 'c5', user_id: 'DICT240047', semester_id: 'sem-2-thevinu', code: 'CS2023', name: 'Database Management Systems', credits: 3, grade: 'B+ (3.3)' },
            { id: 'c6', user_id: 'DICT240047', semester_id: 'sem-2-thevinu', code: 'CS2033', name: 'Object-Oriented Software Engineering', credits: 3, grade: 'A (4.0)' }
        ],
        assignments: [
            { id: 'a1', title: 'Database Normalization & ERD Project', course: 'CS2023 - Database Management Systems', description: 'Design 3NF relational schema with SQL DDL scripts, triggers, and foreign keys.', due_date: getOffsetDate(3), weight: 25, status: 'pending', created_by: 'LEC001' },
            { id: 'a2', title: 'Binary Search Trees & AVL Balancing', course: 'CS2013 - Data Structures & Algorithms', description: 'Implement self-balancing AVL tree in C++ with unit test coverage.', due_date: getOffsetDate(7), weight: 20, status: 'pending', created_by: 'LEC001' },
            { id: 'a3', title: 'Software Architecture Case Study', course: 'CS2033 - Object-Oriented Software Engineering', description: 'Comparative analysis between monolithic and microservices architectures in enterprise apps.', due_date: getOffsetDate(14), weight: 15, status: 'pending', created_by: 'LEC002' },
            { id: 'a4', title: 'Programming Lab Practical 04', course: 'CS1013 - Programming Fundamentals', description: 'Dynamic memory allocation and pointer arithmetic exercises in C++.', due_date: getOffsetDate(-2), weight: 10, status: 'completed', created_by: 'LEC001' }
        ],
        timetable: [
            { id: 'Mon-P1', day: 'Mon', slot: '08:30 - 10:30', slot_index: 1, subject: 'CS2013: Data Structures', hall: 'FOC Lab 2', lecturer: 'Dr. Asela Silva', color: 'indigo' },
            { id: 'Mon-P2', day: 'Mon', slot: '10:45 - 12:45', slot_index: 2, subject: 'CS2023: Database Systems', hall: 'Auditorium B', lecturer: 'Prof. K. Fernando', color: 'emerald' },
            { id: 'Tue-P2', day: 'Tue', slot: '10:45 - 12:45', slot_index: 2, subject: 'CS2033: OOSE Lecture', hall: 'LH-04', lecturer: 'Dr. Asela Silva', color: 'blue' },
            { id: 'Tue-P3', day: 'Tue', slot: '13:30 - 15:30', slot_index: 3, subject: 'CS2013: Lab Session', hall: 'FOC Lab 1', lecturer: 'Lab Instructor', color: 'indigo' },
            { id: 'Wed-P1', day: 'Wed', slot: '08:30 - 10:30', slot_index: 1, subject: 'CS2023: SQL Practical', hall: 'Database Lab', lecturer: 'Prof. K. Fernando', color: 'emerald' },
            { id: 'Wed-P3', day: 'Wed', slot: '13:30 - 15:30', slot_index: 3, subject: 'Mathematics Tutorial', hall: 'LH-02', lecturer: 'Dept Faculty', color: 'purple' },
            { id: 'Thu-P2', day: 'Thu', slot: '10:45 - 12:45', slot_index: 2, subject: 'CS2033: Software Architecture', hall: 'LH-04', lecturer: 'Dr. Asela Silva', color: 'blue' },
            { id: 'Thu-P3', day: 'Thu', slot: '13:30 - 15:30', slot_index: 3, subject: 'Self Study & Research', hall: 'Library / FOC', lecturer: 'Self', color: 'gray' },
            { id: 'Fri-P1', day: 'Fri', slot: '08:30 - 10:30', slot_index: 1, subject: 'Professional Ethics Seminar', hall: 'Auditorium A', lecturer: 'Guest Lecturer', color: 'amber' },
            { id: 'Fri-P2', day: 'Fri', slot: '10:45 - 12:45', slot_index: 2, subject: 'Project Mentoring', hall: 'Staff Room 3', lecturer: 'Dr. Asela Silva', color: 'rose' }
        ],
        notes: [
            { id: 'n1', user_id: 'DICT240047', title: 'Database Indexing & B-Trees', content: 'B-Tree indexes support efficient equality and range queries (BETWEEN, <, >). Hash indexes are O(1) for exact matches but do not support range scans.', category: 'Lecture Notes' },
            { id: 'n2', user_id: 'DICT240047', title: 'Mid-Semester Exam Checklist', content: '1. Master AVL tree rotations (LL, RR, LR, RL).\n2. Practice SQL subqueries, JOINs and Group By.\n3. Review SOLID principles and Factory design pattern.', category: 'Exam Prep' }
        ]
    };

    function getOffsetDate(days) {
        const d = new Date();
        d.setDate(d.getDate() + days);
        return d.toISOString().split('T')[0];
    }

    class DatabaseManager {
        constructor() {
            this.mode = 'detecting'; // 'server' | 'indexeddb'
            this.dexie = null;
            this.apiUrl = '';
            this.eventListeners = {};
        }

        async init() {
            // Check if server is available at current origin or standard local ports
            const candidates = ['', 'http://localhost:8080', 'http://127.0.0.1:8080', 'http://localhost:8000'];
            for (const base of candidates) {
                try {
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 800);
                    const resp = await fetch(`${base}/api/health`, { signal: controller.signal });
                    clearTimeout(timeoutId);

                    if (resp.ok) {
                        const health = await resp.json();
                        if (health.status === 'online') {
                            this.mode = 'server';
                            this.apiUrl = base;
                            console.log('UniSync DB: Connected to SQLite REST server at ' + (base || 'current origin'), health);
                            this._emit('modeChanged', { mode: 'server', info: health });
                            return { mode: 'server', health };
                        }
                    }
                } catch (e) {
                    // Try next candidate
                }
            }

            // Fallback to IndexedDB with Dexie
            this.mode = 'indexeddb';
            this.apiUrl = '';
            console.log('UniSync DB: Server not detected. Initializing in-browser IndexedDB (Dexie).');

            if (typeof Dexie !== 'undefined') {
                this.dexie = new Dexie('UniSyncDatabase');
                this.dexie.version(1).stores({
                    users: 'id, role, email',
                    semesters: 'id, user_id',
                    courses: 'id, user_id, semester_id, code',
                    assignments: 'id, status, due_date, course',
                    timetable: 'id, day, slot_index',
                    notes: 'id, user_id, category, updated_at'
                });

                await this._seedIndexedDBIfEmpty();
            } else {
                console.warn('Dexie library not loaded; falling back to memory/localStorage.');
            }

            this._emit('modeChanged', { mode: 'indexeddb' });
            return { mode: 'indexeddb' };
        }

        async _seedIndexedDBIfEmpty() {
            if (!this.dexie) return;
            const count = await this.dexie.users.count();
            if (count === 0) {
                console.log('UniSync DB: Seeding initial KDU portal records into IndexedDB...');
                await this.dexie.users.bulkAdd(KDU_INITIAL_SEEDS.users);
                await this.dexie.semesters.bulkAdd(KDU_INITIAL_SEEDS.semesters);
                await this.dexie.courses.bulkAdd(KDU_INITIAL_SEEDS.courses);
                await this.dexie.assignments.bulkAdd(KDU_INITIAL_SEEDS.assignments);
                await this.dexie.timetable.bulkAdd(KDU_INITIAL_SEEDS.timetable);
                await this.dexie.notes.bulkAdd(KDU_INITIAL_SEEDS.notes);
            }
        }

        on(event, callback) {
            if (!this.eventListeners[event]) this.eventListeners[event] = [];
            this.eventListeners[event].push(callback);
        }

        _emit(event, data) {
            const list = this.eventListeners[event] || [];
            list.forEach(cb => cb(data));
        }

        // ================= AUTHENTICATION =================
        async login(id, password, role) {
            id = (id || '').trim();
            password = (password || '').trim();

            if (this.mode === 'server') {
                try {
                    const resp = await fetch(`${this.apiUrl}/api/auth/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ id, password, role })
                    });
                    const res = await resp.json();
                    if (res.success) return { success: true, user: res.user };
                    return { success: false, error: res.error || 'Invalid credentials' };
                } catch (e) {
                    console.error('Login error on server:', e);
                }
            }

            // IndexedDB fallback
            if (this.dexie) {
                const user = await this.dexie.users.get(id);
                if (user && user.password === password && user.role === role) {
                    const { password: _, ...userSafe } = user;
                    return { success: true, user: userSafe };
                }
                return { success: false, error: 'Invalid User ID or Password' };
            }

            // LocalStorage fallback
            const localAccs = JSON.parse(localStorage.getItem('unisync_mock_accounts') || '[]');
            const found = localAccs.find(a => a.id === id && a.password === password && a.role === role);
            if (found) return { success: true, user: found };
            return { success: false, error: 'User not found.' };
        }

        async signup(userObj) {
            if (this.mode === 'server') {
                try {
                    const resp = await fetch(`${this.apiUrl}/api/auth/signup`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(userObj)
                    });
                    const res = await resp.json();
                    if (res.success) return { success: true, user: res.user };
                    return { success: false, error: res.error || 'Registration failed' };
                } catch (e) {
                    console.error('Signup error on server:', e);
                }
            }

            if (this.dexie) {
                const existing = await this.dexie.users.get(userObj.id);
                if (existing) return { success: false, error: 'User ID already registered.' };

                await this.dexie.users.add(userObj);

                // If student, create default semester 1 and first course
                if (userObj.role === 'student') {
                    const semId = `sem-1-${userObj.id}`;
                    await this.dexie.semesters.add({ id: semId, user_id: userObj.id, name: 'Semester 1' });
                    await this.dexie.courses.add({
                        id: `c-${userObj.id}-1`,
                        user_id: userObj.id,
                        semester_id: semId,
                        code: 'CS1013',
                        name: 'Programming Fundamentals',
                        credits: 3,
                        grade: 'A (4.0)'
                    });
                }
                return { success: true, user: userObj };
            }

            return { success: false, error: 'Storage engine unavailable' };
        }

        // ================= USERS (LECTURER VIEW) =================
        async getUsers(role = null) {
            if (this.mode === 'server') {
                const url = role ? `${this.apiUrl}/api/users?role=${encodeURIComponent(role)}` : `${this.apiUrl}/api/users`;
                const resp = await fetch(url);
                return await resp.json();
            }

            if (this.dexie) {
                if (role) {
                    return await this.dexie.users.where('role').equals(role).toArray();
                }
                return await this.dexie.users.toArray();
            }
            return [];
        }

        async deleteUser(userId) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/users/${encodeURIComponent(userId)}`, { method: 'DELETE' });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.users.delete(userId);
                await this.dexie.courses.where('user_id').equals(userId).delete();
                await this.dexie.semesters.where('user_id').equals(userId).delete();
                await this.dexie.notes.where('user_id').equals(userId).delete();
                return { success: true, deleted: userId };
            }
        }

        // ================= SEMESTERS =================
        async getSemesters(userId) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/semesters?user_id=${encodeURIComponent(userId)}`);
                return await resp.json();
            }

            if (this.dexie) {
                return await this.dexie.semesters.where('user_id').equals(userId).toArray();
            }
            return [];
        }

        async saveSemester(sem) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/semesters`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(sem)
                });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.semesters.put(sem);
                return { success: true, id: sem.id };
            }
        }

        async deleteSemester(id) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/semesters/${encodeURIComponent(id)}`, { method: 'DELETE' });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.courses.where('semester_id').equals(id).delete();
                await this.dexie.semesters.delete(id);
                return { success: true, deleted: id };
            }
        }

        // ================= COURSES =================
        async getCourses(userId, semesterId = null) {
            if (this.mode === 'server') {
                let url = `${this.apiUrl}/api/courses?user_id=${encodeURIComponent(userId)}`;
                if (semesterId) url += `&semester_id=${encodeURIComponent(semesterId)}`;
                const resp = await fetch(url);
                return await resp.json();
            }

            if (this.dexie) {
                if (semesterId) {
                    return await this.dexie.courses.where({ user_id: userId, semester_id: semesterId }).toArray();
                }
                return await this.dexie.courses.where('user_id').equals(userId).toArray();
            }
            return [];
        }

        async saveCourse(course) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/courses`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(course)
                });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.courses.put(course);
                return { success: true, id: course.id };
            }
        }

        async deleteCourse(id) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/courses/${encodeURIComponent(id)}`, { method: 'DELETE' });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.courses.delete(id);
                return { success: true, deleted: id };
            }
        }

        // ================= ASSIGNMENTS =================
        async getAssignments() {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/assignments`);
                return await resp.json();
            }

            if (this.dexie) {
                return await this.dexie.assignments.toArray();
            }
            return [];
        }

        async saveAssignment(assignment) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/assignments`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(assignment)
                });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.assignments.put(assignment);
                return { success: true, id: assignment.id };
            }
        }

        async deleteAssignment(id) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/assignments/${encodeURIComponent(id)}`, { method: 'DELETE' });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.assignments.delete(id);
                return { success: true, deleted: id };
            }
        }

        async toggleAssignmentStatus(id) {
            const list = await this.getAssignments();
            const a = list.find(x => x.id === id);
            if (a) {
                a.status = a.status === 'completed' ? 'pending' : 'completed';
                await this.saveAssignment(a);
                return a;
            }
            return null;
        }

        // ================= TIMETABLE =================
        async getTimetable() {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/timetable`);
                return await resp.json();
            }

            if (this.dexie) {
                return await this.dexie.timetable.toArray();
            }
            return [];
        }

        async saveTimetableSlot(slot) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/timetable`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(slot)
                });
                return await resp.json();
            }

            if (this.dexie) {
                if (!slot.subject || slot.subject.trim() === '') {
                    await this.dexie.timetable.delete(slot.id);
                } else {
                    await this.dexie.timetable.put(slot);
                }
                return { success: true, id: slot.id };
            }
        }

        // ================= NOTES =================
        async getNotes(userId) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/notes?user_id=${encodeURIComponent(userId)}`);
                return await resp.json();
            }

            if (this.dexie) {
                return await this.dexie.notes.where('user_id').equals(userId).toArray();
            }
            return [];
        }

        async saveNote(note) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/notes`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(note)
                });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.notes.put(note);
                return { success: true, id: note.id };
            }
        }

        async deleteNote(id) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/notes/${encodeURIComponent(id)}`, { method: 'DELETE' });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.notes.delete(id);
                return { success: true, deleted: id };
            }
        }

        // ================= BACKUP, RESTORE & STATS =================
        async exportBackup() {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/backup`);
                return await resp.json();
            }

            if (this.dexie) {
                return {
                    version: '1.0',
                    exported_at: new Date().toISOString(),
                    users: await this.dexie.users.toArray(),
                    semesters: await this.dexie.semesters.toArray(),
                    courses: await this.dexie.courses.toArray(),
                    assignments: await this.dexie.assignments.toArray(),
                    timetable: await this.dexie.timetable.toArray(),
                    notes: await this.dexie.notes.toArray()
                };
            }
            return null;
        }

        async importBackup(data) {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/restore`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                return await resp.json();
            }

            if (this.dexie) {
                if (data.users) { await this.dexie.users.clear(); await this.dexie.users.bulkAdd(data.users); }
                if (data.semesters) { await this.dexie.semesters.clear(); await this.dexie.semesters.bulkAdd(data.semesters); }
                if (data.courses) { await this.dexie.courses.clear(); await this.dexie.courses.bulkAdd(data.courses); }
                if (data.assignments) { await this.dexie.assignments.clear(); await this.dexie.assignments.bulkAdd(data.assignments); }
                if (data.timetable) { await this.dexie.timetable.clear(); await this.dexie.timetable.bulkAdd(data.timetable); }
                if (data.notes) { await this.dexie.notes.clear(); await this.dexie.notes.bulkAdd(data.notes); }
                return { success: true, message: 'IndexedDB restored successfully.' };
            }
        }

        async resetToDemo() {
            if (this.mode === 'server') {
                const resp = await fetch(`${this.apiUrl}/api/reset`, { method: 'POST' });
                return await resp.json();
            }

            if (this.dexie) {
                await this.dexie.users.clear();
                await this.dexie.semesters.clear();
                await this.dexie.courses.clear();
                await this.dexie.assignments.clear();
                await this.dexie.timetable.clear();
                await this.dexie.notes.clear();
                await this._seedIndexedDBIfEmpty();
                return { success: true, message: 'Reset to initial demo data.' };
            }
        }

        async getStats() {
            if (this.mode === 'server') {
                const [users, assignments, timetable] = await Promise.all([
                    this.getUsers(),
                    this.getAssignments(),
                    this.getTimetable()
                ]);
                return {
                    mode: 'SQLite Server (Live)',
                    users: users.length,
                    assignments: assignments.length,
                    timetable: timetable.length
                };
            }

            if (this.dexie) {
                return {
                    mode: 'IndexedDB (Browser)',
                    users: await this.dexie.users.count(),
                    semesters: await this.dexie.semesters.count(),
                    courses: await this.dexie.courses.count(),
                    assignments: await this.dexie.assignments.count(),
                    timetable: await this.dexie.timetable.count(),
                    notes: await this.dexie.notes.count()
                };
            }

            return { mode: 'Local' };
        }
    }

    return new DatabaseManager();
}));
