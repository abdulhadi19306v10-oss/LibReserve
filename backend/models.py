from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric, Table
from sqlalchemy.orm import relationship
import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)  # Student/Faculty/Librarian ID
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, nullable=False)  # Student, Faculty, Librarian, Library Admin, System Admin
    status = Column(String, default="Active")  # Active, Suspended
    
    # Relationships
    reservations = relationship("Reservation", back_populates="user")
    loans = relationship("Loan", back_populates="user")
    fines = relationship("Fine", back_populates="user")
    course_reserves = relationship("CourseReserve", back_populates="faculty")
    book_requests = relationship("BookRequest", back_populates="faculty")

class Book(Base):
    __tablename__ = "books"
    
    isbn = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    category = Column(String, nullable=False)
    language = Column(String, nullable=False)
    publication_year = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    available_copies = Column(Integer, nullable=False)
    
    # Relationships
    reservations = relationship("Reservation", back_populates="book")
    loans = relationship("Loan", back_populates="book")
    course_reserves = relationship("CourseReserve", back_populates="book")

class Reservation(Base):
    __tablename__ = "reservations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    isbn = Column(String, ForeignKey("books.isbn"), nullable=False)
    request_date = Column(DateTime, default=datetime.datetime.utcnow)
    pickup_date = Column(DateTime, nullable=False)
    status = Column(String, default="Pending")  # Pending, Approved, Rejected, Completed, Cancelled, Expired
    rejection_reason = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reservations")
    book = relationship("Book", back_populates="reservations")

class Loan(Base):
    __tablename__ = "loans"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    isbn = Column(String, ForeignKey("books.isbn"), nullable=False)
    issue_date = Column(DateTime, default=datetime.datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    return_date = Column(DateTime, nullable=True)
    status = Column(String, default="Active")  # Active, Returned, Overdue
    
    # Relationships
    user = relationship("User", back_populates="loans")
    book = relationship("Book", back_populates="loans")
    fines = relationship("Fine", back_populates="loan")

class Fine(Base):
    __tablename__ = "fines"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    loan_id = Column(Integer, ForeignKey("loans.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default="Unpaid")  # Unpaid, Paid
    
    # Relationships
    loan = relationship("Loan", back_populates="fines")
    user = relationship("User", back_populates="fines")

class CourseReserve(Base):
    __tablename__ = "course_reserves"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    faculty_id = Column(String, ForeignKey("users.id"), nullable=False)
    isbn = Column(String, ForeignKey("books.isbn"), nullable=False)
    course_name = Column(String, nullable=False)
    
    # Relationships
    faculty = relationship("User", back_populates="course_reserves")
    book = relationship("Book", back_populates="course_reserves")

class BookRequest(Base):
    __tablename__ = "book_requests"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    faculty_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    author = Column(String, nullable=False)
    status = Column(String, default="Pending")  # Pending, Approved, Rejected
    
    # Relationships
    faculty = relationship("User", back_populates="book_requests")

class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    actor_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    status = Column(String, nullable=False)
