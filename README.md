# 🎓 AI-Based Classroom Attendance System
### *Automated Face Recognition Attendance — No More Manual Roll Calls*

## 📌 Table of Contents

- [About the Project](#-about-the-project)
- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [How to Use](#-how-to-use)
- [Accuracy Results](#-accuracy-results)
- [Screenshots](#-screenshots)
- [Author](#-author)


## 🚀 About the Project

Traditional classroom attendance is **time-consuming**, **error-prone**, and **easily manipulated** through proxy attendance. This system solves all three problems using **AI-powered face recognition**.

Upload a single classroom photo → the system **automatically detects every face**, matches them against enrolled students, and marks **Present / Absent** in seconds — saving up to **8 minutes per session**.

<br/>

| ❌ Before (Manual) | ✅ After (AttendAI) |
|---|---|
| 5–10 min per session | Under 30 seconds |
| Proxy attendance possible | Biometric verification |
| Paper registers / Excel | Auto-stored in database |
| No insights | Dashboard with analytics |
| Physical contact (fingerprint) | Completely contactless |


## ✨ Key Features

<br/>

🧑‍🎓 &nbsp; **Student Registration** — Enrol students with name, roll number, department, and a face photo  
🤖 &nbsp; **AI Face Detection** — Detects all faces in a classroom photo using HOG + dlib ResNet  
✅ &nbsp; **Auto Attendance** — Marks Present / Absent for every enrolled student automatically  
✏️ &nbsp; **Manual Correction** — Teachers can toggle any result with one click  
📊 &nbsp; **Live Dashboard** — View total students, sessions, attendance percentage at a glance  
📥 &nbsp; **CSV Export** — Download any session's attendance as an Excel-compatible CSV  
🗂️ &nbsp; **Session History** — All past sessions stored and searchable  
🔒 &nbsp; **Local Storage** — All data stays on your server — no cloud dependency  


## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TEACHER (Browser)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP Request
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  FLASK WEB SERVER                           │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│   │  Register   │  │   Attendance │  │  Reports/Export  │  │
│   │   Routes    │  │    Routes    │  │     Routes       │  │
│   └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘  │
└──────────┼────────────────┼───────────────────┼────────────┘
           │                │                   │
           ▼                ▼                   ▼
┌──────────────────┐  ┌───────────────┐  ┌───────────────────┐
│   face_utils.py  │  │  face_utils   │  │   database.py     │
│  encode_face()   │  │  recognize()  │  │  get_attendance() │
│  128-d embedding │  │  match faces  │  │  export_csv()     │
└──────────────────┘  └───────────────┘  └───────────────────┘
           │                │                   │
           └────────────────┴───────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │     SQLite Database     │
              │  students  │ attendance │
              │  sessions  │  encodings │
              └─────────────────────────┘
```

<br/>

**Face Recognition Pipeline:**

```
Classroom Photo  →  HOG Face Detector  →  128-d Face Encoding
       ↓
Compare with enrolled student encodings (Euclidean Distance)
       ↓
Distance < 0.5  →  PRESENT  ✅
Distance ≥ 0.5  →  ABSENT   ❌
```


## 🛠️ Tech Stack

| Category | Technology | Version | Purpose |
|---|---|---|---|
| **Backend** | Python Flask | 3.x / 2.3+ | Web server & routing |
| **AI Engine** | face_recognition (dlib) | 1.3.0 | Face encoding & matching |
| **Model** | ResNet-34 (dlib) | Pre-trained | 128-d face embeddings |
| **Image Processing** | Pillow (PIL) | 10.x | Resize, annotate images |
| **Numerical** | NumPy | 1.24+ | Distance calculations |
| **Database** | SQLite3 | Built-in | Student & attendance storage |
| **Data Export** | csv module | Built-in | CSV report generation |
| **Frontend** | HTML5 + CSS3 + JS | — | Teacher dashboard UI |
| **Fonts** | Google Fonts | — | Syne + DM Sans typography |


## 📁 Project Structure

```
attendance_system/
│
├── 📄 app.py                      # Main Flask application — all routes
├── 📄 database.py                 # SQLite models, CRUD operations
├── 📄 face_utils.py               # AI face recognition engine
├── 📄 requirements.txt            # Python dependencies
├── 📄 README.md                   # Project documentation
├── 📄 .gitignore                  # Git ignore rules
│
├── 📂 templates/                  # Jinja2 HTML templates
│   ├── base.html                  # Base layout with sidebar navigation
│   ├── index.html                 # Dashboard with stats & recent sessions
│   ├── register.html              # Student registration form
│   ├── students.html              # Student list with filters
│   ├── attendance.html            # Attendance marking form
│   ├── session_detail.html        # Results view with manual correction
│   └── reports.html               # All sessions & CSV export
│
├── 📂 static/
│   ├── css/style.css              # Full dark-theme dashboard styles
│   └── js/main.js                 # AJAX updates & UI interactions
│
└── 📂 instance/                   # Auto-created at runtime
    └── attendance.db              # SQLite database file
```

## 📖 How to Use

<br/>

**Step 1 — Register Students**
1. Go to **Register Student** from the sidebar
2. Fill in name, roll number, department, year, section
3. Upload a clear frontal face photo
4. Click **Register Student** — face encoding is saved automatically

<br/>

**Step 2 — Mark Attendance**
1. Go to **Mark Attendance** from the sidebar
2. Enter subject name, date, department, year, section
3. Upload a classroom photo
4. Click **Detect Faces & Mark Attendance**
5. System auto-detects all faces and marks Present / Absent

<br/>

**Step 3 — Review & Correct**
1. Results page shows every student with Present/Absent badge
2. Click **Toggle** next to any student to correct their status
3. Confidence score shown for each recognised face

<br/>

**Step 4 — Export Report**
1. Go to **Reports** from the sidebar
2. Find the session and click **⬇ CSV**
3. Open the downloaded file in Excel

## 📊 Accuracy Results

| Test Scenario | Faces Tested | Correctly Identified | Accuracy |
|---|---|---|---|
| Ideal lighting, frontal | 10 | 10 | **100.0%** |
| Mixed lighting conditions | 15 | 14 | **93.3%** |
| Slight occlusion (mask) | 8 | 6 | **75.0%** |
| Side profile (> 30°) | 5 | 3 | **60.0%** |
| Low resolution (< 200px) | 6 | 4 | **66.7%** |
| **Overall Average** | **44** | **37** | **84.1%** |

<br/>

| Metric | Value |
|---|---|
| Precision | 97.4% |
| Recall | 90.5% |
| F1-Score | 93.8% |
| Model (dlib LFW benchmark) | 99.38% |

<br/>

> 💡 **Tip:** For best accuracy, ensure good lighting and that all student faces are clearly visible and facing the camera.

<br/>

## 📸 Screenshots

| Dashboard | Register Student |
|---|---|
| Stats cards, recent sessions, quick actions | Name, roll, department, photo upload |

| Mark Attendance | Session Detail |
|---|---|
| Upload classroom photo, session details | Present/Absent badges, confidence scores, toggle button |

