from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class StudentBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    student_id: str = Field(min_length=1, max_length=30)
    email: EmailStr
    course: str = Field(min_length=2, max_length=100)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class StudentOut(StudentBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AttendanceItem(BaseModel):
    student_id: int
    status: str

class AttendanceBulk(BaseModel):
    date: date
    records: list[AttendanceItem]

class AttendanceOut(BaseModel):
    student_id: int
    status: str
    date: date
