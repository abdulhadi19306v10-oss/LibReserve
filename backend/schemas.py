from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserRegister(BaseModel):
    id: str  # Student ID, Faculty ID, Librarian ID, etc.
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str  # Student, Faculty, Librarian, Library Admin, System Admin

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    role: str
    status: str

    class Config:
        from_attributes = True

class BookResponse(BaseModel):
    isbn: str
    title: str
    author: str
    category: str
    language: str
    publication_year: int
    quantity: int
    available_copies: int

    class Config:
        from_attributes = True

class BookCreate(BaseModel):
    isbn: str
    title: str
    author: str
    category: str
    language: str
    publication_year: int
    quantity: int

class ReservationCreate(BaseModel):
    isbn: str
    pickup_date: str  # YYYY-MM-DD

class ReservationAction(BaseModel):
    action: str  # Approve, Reject
    reason: Optional[str] = None

class ReservationResponse(BaseModel):
    id: int
    user_id: str
    isbn: str
    request_date: datetime
    pickup_date: datetime
    status: str
    rejection_reason: Optional[str]
    book_title: Optional[str] = None
    patron_name: Optional[str] = None

    class Config:
        from_attributes = True

class LoanResponse(BaseModel):
    id: int
    user_id: str
    isbn: str
    issue_date: datetime
    due_date: datetime
    return_date: Optional[datetime]
    status: str
    book_title: Optional[str] = None
    patron_name: Optional[str] = None

    class Config:
        from_attributes = True

class FineResponse(BaseModel):
    id: int
    loan_id: int
    user_id: str
    amount: float
    status: str
    book_title: Optional[str] = None

    class Config:
        from_attributes = True

class CourseReserveCreate(BaseModel):
    isbn: str
    course_name: str

class CourseReserveResponse(BaseModel):
    id: int
    faculty_id: str
    isbn: str
    course_name: str
    book_title: Optional[str] = None

    class Config:
        from_attributes = True

class BookRequestCreate(BaseModel):
    title: str
    author: str

class BookRequestResponse(BaseModel):
    id: int
    faculty_id: str
    title: str
    author: str
    status: str

    class Config:
        from_attributes = True

class SystemLogResponse(BaseModel):
    id: int
    timestamp: datetime
    actor_id: Optional[str]
    action: str
    status: str

    class Config:
        from_attributes = True
