from typing import Optional
from pydantic import BaseModel, Field

class RecommendRequest(BaseModel):
    department: str
    grade: int = Field(ge=1, le=5)
    target_credits: int = Field(ge=12, le=22)
    prefer_remote: bool = False
    prefer_required: bool = False

class CourseOut(BaseModel):
    course_code: str
    course_name: str
    section: Optional[str] = None
    course_type: Optional[str] = None
    credits: int
    hours: Optional[int] = None
    professor: Optional[str] = None
    class_time: Optional[str] = None
    remarks: Optional[str] = None
    category: str

class RecommendResponse(BaseModel):
    department: str
    grade: int
    target_credits: int
    total_credits: int
    courses: list[CourseOut]
    message: str
