"""
database.py  –  SQLite database setup and all helper functions.
Handles students, sessions, and attendance records.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'attendance.db')


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    c    = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            roll_number   TEXT UNIQUE NOT NULL,
            department    TEXT NOT NULL,
            year          TEXT NOT NULL,
            section       TEXT NOT NULL,
            photo_path    TEXT,
            face_encoding BLOB,
            registered_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            date       TEXT NOT NULL,
            subject    TEXT NOT NULL,
            department TEXT NOT NULL,
            year       TEXT NOT NULL,
            section    TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(date, subject, department, year, section)
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            status     TEXT NOT NULL DEFAULT 'Absent',
            confidence REAL DEFAULT 0.0,
            marked_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            UNIQUE(session_id, student_id)
        )
    """)

    conn.commit()
    conn.close()
    print("[DB] Database initialised successfully.")


# ── Student helpers ────────────────────────────────────────────────────────

def add_student(name, roll_number, department, year, section,
                photo_path, face_encoding_bytes):
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO students
                (name, roll_number, department, year, section, photo_path, face_encoding)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, roll_number, department, year, section,
              photo_path, face_encoding_bytes))
        conn.commit()
        return True, "Student registered successfully."
    except sqlite3.IntegrityError:
        return False, f"Roll number '{roll_number}' already exists."
    finally:
        conn.close()


def get_all_students(department=None, year=None, section=None):
    conn   = get_db()
    query  = "SELECT * FROM students WHERE 1=1"
    params = []
    if department:
        query += " AND department=?"; params.append(department)
    if year:
        query += " AND year=?";       params.append(year)
    if section:
        query += " AND section=?";    params.append(section)
    rows = conn.execute(query + " ORDER BY name", params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_student_by_id(student_id):
    conn = get_db()
    row  = conn.execute("SELECT * FROM students WHERE id=?",
                        (student_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_encodings():
    """Return all students that have a stored face encoding."""
    conn = get_db()
    rows = conn.execute("""
        SELECT id, name, roll_number, face_encoding
        FROM students WHERE face_encoding IS NOT NULL
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_student(student_id):
    conn = get_db()
    conn.execute("DELETE FROM students WHERE id=?", (student_id,))
    conn.commit()
    conn.close()


# ── Session helpers ────────────────────────────────────────────────────────

def create_session(date_str, subject, department, year, section):
    conn = get_db()
    try:
        cur = conn.execute("""
            INSERT INTO sessions (date, subject, department, year, section)
            VALUES (?, ?, ?, ?, ?)
        """, (date_str, subject, department, year, section))
        sid = cur.lastrowid
        conn.commit()
        return sid
    except sqlite3.IntegrityError:
        row = conn.execute("""
            SELECT id FROM sessions
            WHERE date=? AND subject=? AND department=? AND year=? AND section=?
        """, (date_str, subject, department, year, section)).fetchone()
        return row['id'] if row else None
    finally:
        conn.close()


def get_sessions():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM sessions ORDER BY date DESC, created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_session_by_id(session_id):
    conn = get_db()
    row  = conn.execute("SELECT * FROM sessions WHERE id=?",
                        (session_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


# ── Attendance helpers ─────────────────────────────────────────────────────

def mark_attendance(session_id, student_id, status, confidence=0.0):
    conn = get_db()
    conn.execute("""
        INSERT INTO attendance (session_id, student_id, status, confidence)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(session_id, student_id) DO UPDATE SET
            status=excluded.status,
            confidence=excluded.confidence,
            marked_at=CURRENT_TIMESTAMP
    """, (session_id, student_id, status, confidence))
    conn.commit()
    conn.close()


def get_attendance_for_session(session_id):
    conn = get_db()
    rows = conn.execute("""
        SELECT a.id, a.status, a.confidence, a.marked_at,
               s.id   AS student_id,
               s.name, s.roll_number, s.photo_path,
               s.department, s.year, s.section
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        WHERE a.session_id = ?
        ORDER BY s.roll_number
    """, (session_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_attendance_status(session_id, student_id, status):
    conn = get_db()
    conn.execute("""
        UPDATE attendance SET status=?, marked_at=CURRENT_TIMESTAMP
        WHERE session_id=? AND student_id=?
    """, (status, session_id, student_id))
    conn.commit()
    conn.close()


# ── Stats helper ───────────────────────────────────────────────────────────

def get_stats():
    conn            = get_db()
    total_students  = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_sessions  = conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    total_present   = conn.execute(
        "SELECT COUNT(*) FROM attendance WHERE status='Present'"
    ).fetchone()[0]
    total_records   = conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0]
    conn.close()
    pct = round(total_present / total_records * 100, 1) if total_records else 0
    return {
        'total_students': total_students,
        'total_sessions': total_sessions,
        'total_present':  total_present,
        'total_records':  total_records,
        'attendance_pct': pct,
    }
