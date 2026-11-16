# CampusDesk — Student Management System

A responsive student administration website built with HTML, CSS, JavaScript, FastAPI and SQLite.

## Features
- Dashboard with student and daily attendance statistics
- Create, edit, delete and search student records
- Filter students by course
- Mark daily attendance as Present or Absent, including bulk marking
- Attendance percentages and per-student reports
- Export student directory and attendance report as CSV
- SQLite database created automatically on first run

## Project structure
```text
student_management_system/
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
└── backend/
    ├── main.py
    ├── database.py
    ├── models.py
    ├── schemas.py
    └── requirements.txt
```

## Run on Windows
1. Install Python 3.10 or newer.
2. Open Command Prompt in the `backend` folder.
3. (Recommended) Create and activate a virtual environment:
   ```bat
   python -m venv venv
   venv\\Scripts\\activate
   ```
4. Install dependencies:
   ```bat
   pip install -r requirements.txt
   ```
5. Start the server:
   ```bat
   uvicorn main:app --reload
   ```
6. Open **http://127.0.0.1:8000** in your browser.
7. API documentation is available at **http://127.0.0.1:8000/docs**.

The SQLite file `backend/student_management.db` is generated automatically when the backend starts. Keep the backend running while using the website.

## Notes
- Student ID and email must be unique.
- Attendance is unique per student per date. Saving again updates that student's status for the selected date.
- A student deletion also removes their attendance history.
- This starter project does not include authentication or role-based access. Add those before deploying it publicly.
