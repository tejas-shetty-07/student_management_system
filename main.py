from datetime import date
from pathlib import Path
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Attendance, Student
from schemas import AttendanceBulk, StudentCreate, StudentOut, StudentUpdate

Base.metadata.create_all(bind=engine)
app = FastAPI(title="CampusDesk Student Management API", version="1.0.0")

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "database": "SQLite"}

@app.get("/api/students", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return db.query(Student).order_by(Student.id.asc()).all()

@app.post("/api/students", response_model=StudentOut, status_code=201)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    student = Student(**payload.model_dump())
    db.add(student)
    try:
        db.commit()
        db.refresh(student)
        return student
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Student ID or email already exists.")

@app.put("/api/students/{student_pk}", response_model=StudentOut)
def update_student(student_pk: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_pk).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    for key, value in payload.model_dump().items():
        setattr(student, key, value)
    try:
        db.commit()
        db.refresh(student)
        return student
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Student ID or email already belongs to another student.")

@app.delete("/api/students/{student_pk}", status_code=204)
def delete_student(student_pk: int, db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == student_pk).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
    db.delete(student)
    db.commit()
    return None

@app.get("/api/attendance")
def get_attendance(date_value: date = Query(alias="date"), db: Session = Depends(get_db)):
    rows = db.query(Attendance).filter(Attendance.date == date_value).all()
    return [{"student_id": r.student_id, "status": r.status, "date": r.date} for r in rows]

@app.post("/api/attendance/bulk")
def save_attendance(payload: AttendanceBulk, db: Session = Depends(get_db)):
    for item in payload.records:
        if item.status not in ("Present", "Absent"):
            raise HTTPException(status_code=422, detail="Status must be Present or Absent.")
        student = db.query(Student).filter(Student.id == item.student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail=f"Student {item.student_id} not found.")
        row = db.query(Attendance).filter(
            Attendance.student_id == item.student_id, Attendance.date == payload.date
        ).first()
        if row:
            row.status = item.status
        else:
            db.add(Attendance(student_id=item.student_id, date=payload.date, status=item.status))
    db.commit()
    return {"message": "Attendance saved", "saved": len(payload.records), "date": payload.date}

def attendance_rows(db: Session):
    return db.query(
        Student.id, Student.name, Student.student_id, Student.email, Student.course,
        func.sum(case((Attendance.status == "Present", 1), else_=0)).label("present"),
        func.sum(case((Attendance.status == "Absent", 1), else_=0)).label("absent"),
        func.count(Attendance.id).label("total")
    ).outerjoin(Attendance, Attendance.student_id == Student.id).group_by(Student.id).order_by(Student.name).all()

def make_report(db: Session):
    rows = attendance_rows(db)
    result = []
    for r in rows:
        present, absent, total = int(r.present or 0), int(r.absent or 0), int(r.total or 0)
        result.append({
            "id": r.id, "name": r.name, "student_id": r.student_id,
            "email": r.email, "course": r.course, "present": present,
            "absent": absent, "total": total,
            "percentage": round(present / total * 100) if total else 0
        })
    return result

@app.get("/api/attendance/percentages")
def attendance_percentages(db: Session = Depends(get_db)):
    return make_report(db)

@app.get("/api/dashboard")
def dashboard(db: Session = Depends(get_db)):
    total_students = db.query(Student).count()
    today_rows = db.query(Attendance).filter(Attendance.date == date.today()).all()
    present = sum(1 for r in today_rows if r.status == "Present")
    absent = sum(1 for r in today_rows if r.status == "Absent")
    marked = present + absent
    all_present = db.query(Attendance).filter(Attendance.status == "Present").count()
    all_entries = db.query(Attendance).count()
    return {
        "total_students": total_students, "present_today": present,
        "absent_today": absent, "marked_today": marked,
        "unmarked_today": max(total_students - marked, 0),
        "today_rate": round(present / marked * 100) if marked else 0,
        "average_attendance": round(all_present / all_entries * 100) if all_entries else 0
    }

@app.get("/api/reports")
def reports(db: Session = Depends(get_db)):
    rows = make_report(db)
    entries = sum(r["total"] for r in rows)
    present = sum(r["present"] for r in rows)
    return {
        "total_students": len(rows), "total_entries": entries,
        "overall_rate": round(present / entries * 100) if entries else 0,
        "students": rows
    }
