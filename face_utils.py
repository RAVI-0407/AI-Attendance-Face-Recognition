"""
face_utils.py  –  Face encoding and recognition using dlib / face_recognition.
Falls back to mock mode if the library is not installed (for demo purposes).
"""

import io
import pickle
import numpy as np

try:
    import face_recognition
    FR_AVAILABLE = True
except ImportError:
    FR_AVAILABLE = False
    print("[WARN] face_recognition not installed – running in mock mode.")

from PIL import Image, ImageDraw


# ── Encode a single face from image bytes ─────────────────────────────────

def encode_face_from_bytes(image_bytes: bytes):
    """
    Detect and encode the primary face in the image.
    Returns (encoding_bytes, error_message).
    encoding_bytes = pickle-serialised 128-d numpy array, or None on failure.
    """
    if not FR_AVAILABLE:
        mock = np.random.rand(128).astype(np.float64)
        return pickle.dumps(mock), None

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Downscale large images for speed
        if max(img.size) > 1200:
            img.thumbnail((1200, 1200), Image.LANCZOS)

        arr  = np.array(img)
        locs = face_recognition.face_locations(arr, model="hog")

        if not locs:
            return None, "No face detected. Please upload a clear frontal photo."

        # Use the largest (closest) face if multiple detected
        if len(locs) > 1:
            areas = [(b - t) * (r - l) for t, r, b, l in locs]
            locs  = [locs[int(np.argmax(areas))]]

        encs = face_recognition.face_encodings(arr, locs)
        if not encs:
            return None, "Could not compute face encoding. Use a higher-resolution photo."

        return pickle.dumps(encs[0]), None

    except Exception as e:
        return None, f"Encoding error: {e}"


# ── Recognise all faces in a classroom image ──────────────────────────────

def recognize_faces_in_image(image_bytes: bytes,
                              known_encodings: list,
                              tolerance: float = 0.50):
    """
    Detect every face in the classroom photo and match against enrolled students.

    known_encodings: list of dicts – {id, name, roll_number, face_encoding (bytes)}

    Returns list of dicts:
        {student_id, name, roll_number, status, confidence, location}
    """
    if not FR_AVAILABLE:
        # Mock: mark ~2/3 of students present for demo
        results = []
        for i, k in enumerate(known_encodings):
            results.append({
                'student_id':  k['id'],
                'name':        k['name'],
                'roll_number': k['roll_number'],
                'status':      'Present' if i % 3 != 2 else 'Absent',
                'confidence':  round(float(np.random.uniform(0.70, 0.98)), 3),
                'location':    None,
            })
        return results

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        if max(img.size) > 1600:
            img.thumbnail((1600, 1600), Image.LANCZOS)

        arr      = np.array(img)
        locs     = face_recognition.face_locations(arr, model="hog")

        if not locs:
            return []

        unknowns   = face_recognition.face_encodings(arr, locs)
        known_vecs = []
        for k in known_encodings:
            try:
                known_vecs.append(pickle.loads(k['face_encoding']))
            except Exception:
                known_vecs.append(None)

        results_map  = {}   # student_id → best match dict
        matched_ids  = set()

        for unk_enc, loc in zip(unknowns, locs):
            distances = []
            for kv in known_vecs:
                if kv is None:
                    distances.append(1.0)
                else:
                    distances.append(
                        float(face_recognition.face_distance([kv], unk_enc)[0])
                    )

            best_i   = int(np.argmin(distances))
            best_d   = distances[best_i]

            if best_d <= tolerance:
                student  = known_encodings[best_i]
                sid      = student['id']
                conf     = round(1.0 - best_d, 3)
                t, r, b, l = loc

                if sid not in results_map or conf > results_map[sid]['confidence']:
                    results_map[sid] = {
                        'student_id':  sid,
                        'name':        student['name'],
                        'roll_number': student['roll_number'],
                        'status':      'Present',
                        'confidence':  conf,
                        'location':    {'top': t, 'right': r, 'bottom': b, 'left': l},
                    }
                matched_ids.add(sid)

        # All unmatched enrolled students → Absent
        for k in known_encodings:
            if k['id'] not in matched_ids:
                results_map[k['id']] = {
                    'student_id':  k['id'],
                    'name':        k['name'],
                    'roll_number': k['roll_number'],
                    'status':      'Absent',
                    'confidence':  0.0,
                    'location':    None,
                }

        return list(results_map.values())

    except Exception as e:
        print(f"[ERROR] recognize_faces_in_image: {e}")
        return []


# ── Annotate image with bounding boxes ────────────────────────────────────

def draw_annotations(image_bytes: bytes, results: list) -> bytes:
    """Draw green/red boxes with student names on the classroom image."""
    try:
        img  = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        draw = ImageDraw.Draw(img)

        for r in results:
            loc = r.get('location')
            if not loc:
                continue
            color = "#22c55e" if r['status'] == 'Present' else "#ef4444"
            t, ri, b, l = loc['top'], loc['right'], loc['bottom'], loc['left']
            draw.rectangle([(l, t), (ri, b)], outline=color, width=3)
            label = (f"{r['name']} ({r['confidence']:.0%})"
                     if r['status'] == 'Present' else r['name'])
            draw.rectangle([(l, t - 22), (ri, t)], fill=color)
            draw.text((l + 3, t - 18), label, fill="white")

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except Exception as e:
        print(f"[WARN] draw_annotations: {e}")
        return image_bytes


def is_fr_available() -> bool:
    return FR_AVAILABLE
