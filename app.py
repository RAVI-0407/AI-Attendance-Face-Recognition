"""
app.py  –  AI-Based Classroom Attendance System
Main Flask web application: all routes, file uploads, CSV export.
"""

import os
import io
import csv
from datetime import date
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, jsonify, send_file)

import database as db
import face_utils as fu

# ── App Configuration ──────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "attendai-secret-key-2024")

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'student_photos')
ALLOWED_EXT   = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER']      = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


with app.app_context():
    db.init_db()


# ══ DASHBOARD ══════════════════════════════════════════════════════════════
@app.route('/')
def index():
    return render_template('index.html',
                           stats=db.get_stats(),
                           today=date.today().isoformat(),
                           sessions=db.get_sessions()[:8],
                           fr_available=fu.is_fr_available())


# ══ STUDENT REGISTRATION ═══════════════════════════════════════════════════
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name   = request.form.get('name', '').strip()
        roll   = request.form.get('roll_number', '').strip().upper()
        dept   = request.form.get('department', '').strip()
        year   = request.form.get('year', '').strip()
        sec    = request.form.get('section', '').strip().upper()

        if not all([name, roll, dept, year, sec]):
            flash("All fields are required.", "error")
            return redirect(url_for('register'))

        photo = request.files.get('photo')
        if not photo or not allowed_file(photo.filename):
            flash("Upload a valid image (JPG/PNG/WEBP).", "error")
            return redirect(url_for('register'))

        image_bytes = photo.read()
        enc, err    = fu.encode_face_from_bytes(image_bytes)
        if err:
            flash(f"Face detection failed: {err}", "error")
            return redirect(url_for('register'))

        from PIL import Image
        fname = f"{roll}.jpg"
        path  = os.path.join(UPLOAD_FOLDER, fname)
        pil   = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        pil.thumbnail((400, 400))
        pil.save(path, "JPEG", quality=85)

        ok, msg = db.add_student(name, roll, dept, year, sec,
                                 f"student_photos/{fname}", enc)
        flash(msg, "success" if ok else "error")
        return redirect(url_for('students') if ok else url_for('register'))

    return render_template('register.html')


# ══ STUDENT LIST ═══════════════════════════════════════════════════════════
@app.route('/students')
def students():
    dept    = request.args.get('department', '')
    year    = request.args.get('year', '')
    section = request.args.get('section', '')
    lst = db.get_all_students(dept or None, year or None, section or None)
    return render_template('students.html', students=lst,
                           filters={'department': dept, 'year': year, 'section': section})


@app.route('/students/delete/<int:sid>', methods=['POST'])
def delete_student(sid):
    s = db.get_student_by_id(sid)
    if s:
        p = os.path.join(app.root_path, 'static', s.get('photo_path', ''))
        if os.path.exists(p):
            os.remove(p)
        db.delete_student(sid)
        flash("Student deleted.", "info")
    return redirect(url_for('students'))


# ══ MARK ATTENDANCE ════════════════════════════════════════════════════════
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if request.method == 'POST':
        subject  = request.form.get('subject', '').strip()
        dept     = request.form.get('department', '').strip()
        year     = request.form.get('year', '').strip()
        section  = request.form.get('section', '').strip().upper()
        att_date = request.form.get('date', date.today().isoformat())

        if not all([subject, dept, year, section]):
            flash("Fill all session fields.", "error")
            return redirect(url_for('attendance'))

        photo = request.files.get('photo')
        if not photo or not allowed_file(photo.filename):
            flash("Upload a valid classroom photo.", "error")
            return redirect(url_for('attendance'))

        image_bytes     = photo.read()
        all_enc         = db.get_all_encodings()
        class_students  = db.get_all_students(dept, year, section)
        class_ids       = {s['id'] for s in class_students}
        class_enc       = [e for e in all_enc if e['id'] in class_ids]

        if not class_enc:
            flash("No registered students for this class.", "error")
            return redirect(url_for('attendance'))

        results     = fu.recognize_faces_in_image(image_bytes, class_enc)
        session_id  = db.create_session(att_date, subject, dept, year, section)
        present_ids = set()

        for r in results:
            if r['status'] == 'Present':
                db.mark_attendance(session_id, r['student_id'], 'Present', r['confidence'])
                present_ids.add(r['student_id'])

        for s in class_students:
            if s['id'] not in present_ids:
                db.mark_attendance(session_id, s['id'], 'Absent', 0.0)

        flash(f"Done! {len(present_ids)} present / {len(class_students)} total.", "success")
        return redirect(url_for('session_detail', session_id=session_id))

    return render_template('attendance.html', today=date.today().isoformat())


# ══ SESSION DETAIL + EDIT ══════════════════════════════════════════════════
@app.route('/session/<int:session_id>')
def session_detail(session_id):
    sess = db.get_session_by_id(session_id)
    if not sess:
        flash("Session not found.", "error")
        return redirect(url_for('index'))
    records = db.get_attendance_for_session(session_id)
    present = sum(1 for r in records if r['status'] == 'Present')
    absent  = len(records) - present
    pct     = round(present / len(records) * 100, 1) if records else 0
    return render_template('session_detail.html', session=sess,
                           records=records, present=present,
                           absent=absent, pct=pct)


@app.route('/session/<int:session_id>/update', methods=['POST'])
def update_attendance(session_id):
    data   = request.json
    status = data.get('status')
    if status not in ('Present', 'Absent'):
        return jsonify({'error': 'Invalid status'}), 400
    db.update_attendance_status(session_id, data.get('student_id'), status)
    return jsonify({'ok': True})


# ══ REPORTS & CSV ══════════════════════════════════════════════════════════
@app.route('/reports')
def reports():
    return render_template('reports.html', sessions=db.get_sessions())


@app.route('/reports/export/<int:session_id>')
def export_session_csv(session_id):
    sess    = db.get_session_by_id(session_id)
    records = db.get_attendance_for_session(session_id)
    buf     = io.StringIO()
    w       = csv.writer(buf)
    w.writerow(['Roll Number', 'Name', 'Department', 'Year',
                'Section', 'Date', 'Subject', 'Status', 'Confidence (%)'])
    for r in records:
        conf = f"{r['confidence'] * 100:.1f}" if r['confidence'] else "0.0"
        w.writerow([r['roll_number'], r['name'], r['department'],
                    r['year'], r['section'], sess['date'],
                    sess['subject'], r['status'], conf])
    buf.seek(0)
    fname = f"attendance_{sess['date']}_{sess['subject'].replace(' ', '_')}.csv"
    return send_file(io.BytesIO(buf.getvalue().encode()),
                     mimetype='text/csv', as_attachment=True,
                     download_name=fname)


@app.route('/api/stats')
def api_stats():
    return jsonify(db.get_stats())


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
