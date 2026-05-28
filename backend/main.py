from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os
import shutil
import datetime
import random

from database import engine, Base, get_db
from models import User, Book, Reservation, Loan, Fine, CourseReserve, BookRequest, SystemLog
from auth import hash_password, verify_password
import schemas

# Initialize database tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LibReserve API")

# CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to create system logs
def log_action(db: Session, actor_id: str, action: str, log_status: str = "Success"):
    log_entry = SystemLog(actor_id=actor_id, action=action, status=log_status)
    db.add(log_entry)
    db.commit()

# ==========================================
# AUTH ENDPOINTS
# ==========================================

@app.post("/api/auth/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserRegister, db: Session = Depends(get_db)):
    db_user_email = db.query(User).filter(User.email == user_data.email).first()
    if db_user_email:
        raise HTTPException(status_code=400, detail="Email is already registered.")
        
    db_user_id = db.query(User).filter(User.id == user_data.id).first()
    if db_user_id:
        raise HTTPException(status_code=400, detail="University ID is already registered.")
    
    # Capitalize role properly
    role = user_data.role.strip()
    if role not in ["Student", "Faculty", "Librarian", "Library Admin", "System Admin"]:
        raise HTTPException(status_code=400, detail="Invalid user role selected.")
        
    new_user = User(
        id=user_data.id,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=role,
        status="Active"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    log_action(db, new_user.id, f"User registered as {new_user.role}")
    return new_user

@app.post("/api/auth/login", response_model=schemas.UserResponse)
def login(login_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.password_hash):
        log_action(db, None, f"Failed login attempt for email {login_data.email}", "Failed")
        raise HTTPException(status_code=400, detail="Invalid email or password.")
        
    if user.status == "Suspended":
        log_action(db, user.id, f"Blocked login attempt for suspended user", "Blocked")
        raise HTTPException(status_code=403, detail="Your account has been suspended. Please contact the Library Administrator.")
        
    log_action(db, user.id, f"User logged in successfully")
    return user

# ==========================================
# CATALOG (BOOK) ENDPOINTS
# ==========================================

@app.get("/api/catalog/books", response_model=list[schemas.BookResponse])
def get_books(search: str = "", category: str = "", db: Session = Depends(get_db)):
    query = db.query(Book)
    if search:
        query = query.filter(
            Book.title.like(f"%{search}%") | 
            Book.author.like(f"%{search}%") | 
            Book.isbn.like(f"%{search}%")
        )
    if category:
        query = query.filter(Book.category == category)
    return query.all()

@app.post("/api/catalog/books", response_model=schemas.BookResponse)
def add_book(book_data: schemas.BookCreate, actor_id: str = None, db: Session = Depends(get_db)):
    db_book = db.query(Book).filter(Book.isbn == book_data.isbn).first()
    if db_book:
        raise HTTPException(status_code=400, detail="Book with this ISBN already exists.")
        
    new_book = Book(
        isbn=book_data.isbn,
        title=book_data.title,
        author=book_data.author,
        category=book_data.category,
        language=book_data.language,
        publication_year=book_data.publication_year,
        quantity=book_data.quantity,
        available_copies=book_data.quantity
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    
    log_action(db, actor_id, f"Added new book to catalog: {new_book.title} (ISBN: {new_book.isbn})")
    return new_book

@app.delete("/api/catalog/books/{isbn}")
def delete_book(isbn: str, actor_id: str = None, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.isbn == isbn).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
        
    # Check if there are active loans
    active_loans = db.query(Loan).filter(Loan.isbn == isbn, Loan.status.in_(["Active", "Overdue"])).first()
    if active_loans:
        raise HTTPException(status_code=400, detail="Cannot delete book that currently has active loans.")
        
    log_action(db, actor_id, f"Removed book from catalog: {book.title} (ISBN: {book.isbn})")
    db.delete(book)
    db.commit()
    return {"message": "Book deleted successfully."}

# ==========================================
# RESERVATION ENDPOINTS
# ==========================================

@app.post("/api/reservations/reserve", response_model=schemas.ReservationResponse)
def reserve_book(req: schemas.ReservationCreate, user_id: str = None, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if user.status == "Suspended":
        raise HTTPException(status_code=403, detail="Suspended users cannot reserve books.")
        
    # Check open reservations limit (e.g. max 3 pending/approved reservations for students, 5 for faculty)
    max_res = 5 if user.role == "Faculty" else 3
    active_res_count = db.query(Reservation).filter(
        Reservation.user_id == user_id, 
        Reservation.status.in_(["Pending", "Approved"])
    ).count()
    if active_res_count >= max_res:
        raise HTTPException(status_code=400, detail=f"Reservation limit reached. Maximum active reservations: {max_res}")
        
    # Check outstanding unpaid fines
    unpaid_fines = db.query(Fine).filter(Fine.user_id == user_id, Fine.status == "Unpaid").count()
    if unpaid_fines > 0:
        raise HTTPException(status_code=400, detail="Cannot reserve books. You have outstanding unpaid library fines.")

    book = db.query(Book).filter(Book.isbn == req.isbn).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
        
    if book.available_copies <= 0:
        raise HTTPException(status_code=400, detail="No copies of this book are currently available for reservation.")
        
    # Check if user already has an active loan of this book
    active_loan = db.query(Loan).filter(
        Loan.user_id == user_id, 
        Loan.isbn == req.isbn,
        Loan.status.in_(["Active", "Overdue"])
    ).first()
    if active_loan:
        raise HTTPException(status_code=400, detail="You already have an active loan for this book.")
        
    # Parse pickup date
    try:
        pickup_date = datetime.datetime.strptime(req.pickup_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pickup date format. Use YYYY-MM-DD.")
        
    if pickup_date.date() < datetime.date.today():
        raise HTTPException(status_code=400, detail="Pickup date cannot be in the past.")
        
    # Create reservation and hold a copy
    book.available_copies -= 1
    new_res = Reservation(
        user_id=user_id,
        isbn=req.isbn,
        pickup_date=pickup_date,
        status="Pending"
    )
    db.add(new_res)
    db.commit()
    db.refresh(new_res)
    
    log_action(db, user_id, f"Placed pending reservation on '{book.title}'")
    return new_res

@app.get("/api/reservations/my-reservations", response_model=list[schemas.ReservationResponse])
def get_my_reservations(user_id: str = None, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
        
    reservations = db.query(Reservation).filter(Reservation.user_id == user_id).order_by(Reservation.request_date.desc()).all()
    # Populate extra attributes for serialization
    for r in reservations:
        r.book_title = r.book.title
    return reservations

@app.get("/api/reservations/pending", response_model=list[schemas.ReservationResponse])
def get_pending_reservations(db: Session = Depends(get_db)):
    reservations = db.query(Reservation).filter(Reservation.status == "Pending").order_by(Reservation.request_date.asc()).all()
    for r in reservations:
        r.book_title = r.book.title
        r.patron_name = f"{r.user.first_name} {r.user.last_name} ({r.user.role})"
    return reservations

@app.post("/api/reservations/action/{id}", response_model=schemas.ReservationResponse)
def reservation_action(id: int, act: schemas.ReservationAction, actor_id: str = None, db: Session = Depends(get_db)):
    res = db.query(Reservation).filter(Reservation.id == id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation request not found.")
        
    if res.status != "Pending":
        raise HTTPException(status_code=400, detail=f"Cannot change action on reservation with status '{res.status}'")
        
    if act.action == "Approve":
        res.status = "Approved"
        log_action(db, actor_id, f"Approved reservation #{id} for '{res.book.title}' (Patron: {res.user.id})")
    elif act.action == "Reject":
        res.status = "Rejected"
        res.rejection_reason = act.reason or "Does not meet library policies."
        # Release the copy
        res.book.available_copies += 1
        log_action(db, actor_id, f"Rejected reservation #{id} for '{res.book.title}'. Reason: {res.rejection_reason}")
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'Approve' or 'Reject'.")
        
    db.commit()
    db.refresh(res)
    res.book_title = res.book.title
    res.patron_name = f"{res.user.first_name} {res.user.last_name}"
    return res

@app.post("/api/reservations/cancel/{id}", response_model=schemas.ReservationResponse)
def cancel_reservation(id: int, user_id: str = None, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
        
    res = db.query(Reservation).filter(Reservation.id == id, Reservation.user_id == user_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found or does not belong to you.")
        
    if res.status != "Pending":
        raise HTTPException(status_code=400, detail="Only Pending reservations can be cancelled.")
        
    res.status = "Cancelled"
    res.book.available_copies += 1
    db.commit()
    db.refresh(res)
    res.book_title = res.book.title
    
    log_action(db, user_id, f"Cancelled pending reservation #{id} for '{res.book.title}'")
    return res

# ==========================================
# LOAN & FINE ENDPOINTS
# ==========================================

@app.get("/api/loans/my-loans", response_model=list[schemas.LoanResponse])
def get_my_loans(user_id: str = None, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
        
    loans = db.query(Loan).filter(Loan.user_id == user_id).order_by(Loan.issue_date.desc()).all()
    for l in loans:
        l.book_title = l.book.title
    return loans

@app.get("/api/loans/my-fines", response_model=list[schemas.FineResponse])
def get_my_fines(user_id: str = None, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
        
    fines = db.query(Fine).filter(Fine.user_id == user_id).order_by(Fine.status.desc()).all()
    for f in fines:
        f.book_title = f.loan.book.title
    return fines

@app.post("/api/loans/issue")
def issue_book(reservation_id: int, actor_id: str = None, db: Session = Depends(get_db)):
    res = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Approved reservation not found.")
        
    if res.status != "Approved":
        raise HTTPException(status_code=400, detail=f"Cannot issue. Reservation status is '{res.status}' (expected 'Approved')")
        
    # Check user suspension status
    if res.user.status == "Suspended":
        raise HTTPException(status_code=400, detail="Cannot issue book. The patron account is currently suspended.")
        
    # Create active loan
    issue_date = datetime.datetime.utcnow()
    # Loan duration: Faculty gets 30 days, students get 14 days
    days = 30 if res.user.role == "Faculty" else 14
    due_date = issue_date + datetime.timedelta(days=days)
    
    new_loan = Loan(
        user_id=res.user_id,
        isbn=res.isbn,
        issue_date=issue_date,
        due_date=due_date,
        status="Active"
    )
    res.status = "Completed"
    db.add(new_loan)
    db.commit()
    
    log_action(db, actor_id, f"Issued book '{res.book.title}' to patron {res.user_id}")
    return {"message": "Book issued successfully.", "due_date": due_date.strftime("%Y-%m-%d")}

@app.post("/api/loans/return")
def return_book(isbn: str, user_id: str, actor_id: str = None, db: Session = Depends(get_db)):
    # Find active loan
    loan = db.query(Loan).filter(
        Loan.isbn == isbn, 
        Loan.user_id == user_id, 
        Loan.status.in_(["Active", "Overdue"])
    ).first()
    
    if not loan:
        raise HTTPException(status_code=404, detail="No active loan record found for this book and user.")
        
    # Return copies
    book = db.query(Book).filter(Book.isbn == isbn).first()
    book.available_copies += 1
    
    now = datetime.datetime.utcnow()
    loan.return_date = now
    loan.status = "Returned"
    
    # Calculate Overdue Fines
    fine_amount = 0.0
    if now > loan.due_date:
        overdue_days = (now - loan.due_date).days
        if overdue_days > 0:
            fine_amount = float(overdue_days * 50.00)  # Rs. 50 fine per day
            new_fine = Fine(
                loan_id=loan.id,
                user_id=user_id,
                amount=fine_amount,
                status="Unpaid"
            )
            db.add(new_fine)
            
    db.commit()
    log_action(db, actor_id, f"Returned book '{book.title}' from user {user_id}. Fine accrued: Rs. {fine_amount}")
    return {
        "message": "Book returned successfully.", 
        "fine_accrued": fine_amount
    }

@app.post("/api/loans/pay-fine/{id}")
def pay_fine(id: int, user_id: str = None, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
        
    fine = db.query(Fine).filter(Fine.id == id, Fine.user_id == user_id).first()
    if not fine:
        raise HTTPException(status_code=404, detail="Fine record not found or does not belong to you.")
        
    if fine.status == "Paid":
        return {"message": "Fine has already been paid."}
        
    fine.status = "Paid"
    db.commit()
    
    log_action(db, user_id, f"Paid outstanding fine #{id} of Rs. {fine.amount:.2f}")
    return {"message": "Fine paid successfully."}

# ==========================================
# FACULTY UTILITIES
# ==========================================

@app.post("/api/faculty/course-reserves", response_model=schemas.CourseReserveResponse)
def add_course_reserve(req: schemas.CourseReserveCreate, user_id: str = None, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "Faculty":
        raise HTTPException(status_code=403, detail="Only faculty members can designate course reserves.")
        
    book = db.query(Book).filter(Book.isbn == req.isbn).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found.")
        
    # Check if already added
    exist = db.query(CourseReserve).filter(CourseReserve.isbn == req.isbn).first()
    if exist:
         raise HTTPException(status_code=400, detail="This book is already in course reserves.")
         
    new_cr = CourseReserve(
        faculty_id=user_id,
        isbn=req.isbn,
        course_name=req.course_name
    )
    db.add(new_cr)
    db.commit()
    db.refresh(new_cr)
    new_cr.book_title = book.title
    
    log_action(db, user_id, f"Designated '{book.title}' as Course Reserve for '{req.course_name}'")
    return new_cr

@app.get("/api/faculty/course-reserves", response_model=list[schemas.CourseReserveResponse])
def get_course_reserves(db: Session = Depends(get_db)):
    cr_list = db.query(CourseReserve).all()
    for cr in cr_list:
        cr.book_title = cr.book.title
    return cr_list

@app.post("/api/faculty/purchase-requests", response_model=schemas.BookRequestResponse)
def create_purchase_request(req: schemas.BookRequestCreate, user_id: str = None, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required.")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != "Faculty":
        raise HTTPException(status_code=403, detail="Only faculty members can make purchase requests.")
        
    new_req = BookRequest(
        faculty_id=user_id,
        title=req.title,
        author=req.author,
        status="Pending"
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    
    log_action(db, user_id, f"Requested book purchase: '{req.title}' by {req.author}")
    return new_req

@app.get("/api/faculty/purchase-requests", response_model=list[schemas.BookRequestResponse])
def get_purchase_requests(user_id: str = None, db: Session = Depends(get_db)):
    query = db.query(BookRequest)
    if user_id:
        query = query.filter(BookRequest.faculty_id == user_id)
    return query.order_by(BookRequest.id.desc()).all()

# ==========================================
# LIBRARY ADMIN ENDPOINTS
# ==========================================

@app.get("/api/lib-admin/users", response_model=list[schemas.UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(User).filter(User.role.in_(["Student", "Faculty"])).all()

@app.post("/api/lib-admin/users/{id}/toggle-status")
def toggle_user_status(id: str, actor_id: str = None, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
        
    if user.status == "Active":
        user.status = "Suspended"
    else:
        user.status = "Active"
        
    db.commit()
    log_action(db, actor_id, f"Toggled user status of {user.id} to {user.status}")
    return {"message": f"User status updated to {user.status}.", "status": user.status}

@app.get("/api/lib-admin/dashboard-stats")
def get_lib_admin_stats(db: Session = Depends(get_db)):
    total_branches = 4  # Main, Engineering, Science, Literature
    active_users = db.query(User).filter(User.status == "Active").count()
    catalog_items = db.query(Book).count()
    
    # Sum paid fines for revenue
    fine_sum = db.query(Fine).filter(Fine.status == "Paid").all()
    annual_revenue = float(sum(f.amount for f in fine_sum))
    
    # 5-month circulation analytics
    # Returning dummy historical stats for chart rendering: January to May
    circulation_data = [
        {"month": "Jan", "issues": 120, "returns": 95},
        {"month": "Feb", "issues": 150, "returns": 110},
        {"month": "Mar", "issues": 180, "returns": 160},
        {"month": "Apr", "issues": 210, "returns": 195},
        {"month": "May", "issues": 245, "returns": 230}
    ]
    
    # List of branches
    branches = [
        {"id": 1, "name": "UET Main Library", "status": "Active", "staff": 12},
        {"id": 2, "name": "Engineering Branch Library", "status": "Active", "staff": 4},
        {"id": 3, "name": "Basic Sciences Library", "status": "Active", "staff": 3},
        {"id": 4, "name": "UET KSK Campus Library", "status": "Active", "staff": 5}
    ]
    
    return {
        "total_branches": total_branches,
        "active_users": active_users,
        "catalog_items": catalog_items,
        "annual_revenue": annual_revenue,
        "circulation_data": circulation_data,
        "branches": branches
    }

# ==========================================
# SYSTEM ADMIN ENDPOINTS
# ==========================================

@app.get("/api/sys-admin/logs", response_model=list[schemas.SystemLogResponse])
def get_system_logs(db: Session = Depends(get_db)):
    return db.query(SystemLog).order_by(SystemLog.timestamp.desc()).limit(100).all()

@app.get("/api/sys-admin/stats")
def get_server_stats(db: Session = Depends(get_db)):
    uptime = "99.98%"
    concurrent_users = random.randint(10, 45)
    query_load = f"{random.randint(2, 12)} QPS"
    security_alerts = db.query(User).filter(User.status == "Suspended").count()
    
    # CPU and RAM history at 5-minute intervals
    now = datetime.datetime.now()
    resource_usage = []
    for i in range(5):
        time_str = (now - datetime.timedelta(minutes=i*5)).strftime("%H:%M")
        resource_usage.append({
            "time": time_str,
            "cpu": f"{random.randint(10, 40)}%",
            "ram": f"{random.randint(40, 60)}%"
        })
        
    return {
        "uptime": uptime,
        "query_load": query_load,
        "concurrent_users": concurrent_users,
        "security_alerts": security_alerts,
        "resource_usage": resource_usage
    }

@app.post("/api/sys-admin/backup")
def backup_database(actor_id: str = None, db: Session = Depends(get_db)):
    try:
        from database import DB_PATH
        backup_path = DB_PATH + ".bak"
        
        # Close database connection explicitly to ensure file consistency
        db.close()
        shutil.copyfile(DB_PATH, backup_path)
        
        # Log success in new session
        db_new = next(get_db())
        log_action(db_new, actor_id, f"Created database backup file successfully.")
        db_new.close()
        
        return {"message": "Backup created successfully.", "filename": os.path.basename(backup_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database backup failed: {e}")

@app.post("/api/sys-admin/restore")
def restore_database(actor_id: str = None, db: Session = Depends(get_db)):
    try:
        from database import DB_PATH
        backup_path = DB_PATH + ".bak"
        if not os.path.exists(backup_path):
            raise HTTPException(status_code=404, detail="No backup file found to restore from.")
            
        db.close()
        engine.dispose() # Release handles to sqlite file
        shutil.copyfile(backup_path, DB_PATH)
        
        db_new = next(get_db())
        log_action(db_new, actor_id, f"Restored database from backup file.")
        db_new.close()
        
        return {"message": "Database restored successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database restore failed: {e}")

# ==========================================
# STATIC FILES SERVING & ROUTING
# ==========================================

# Resolve frontend path relative to this backend module
FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
    "frontend"
)

# Route to serve main UI files
@app.get("/")
def read_root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/login")
def read_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/dashboard/{role}")
def read_dashboard(role: str):
    role_file_map = {
        "student": "student.html",
        "faculty": "faculty.html",
        "librarian": "librarian.html",
        "lib_admin": "lib_admin.html",
        "sys_admin": "sys_admin.html"
    }
    filename = role_file_map.get(role.lower())
    if not filename:
        return RedirectResponse(url="/login")
        
    dashboard_path = os.path.join(FRONTEND_DIR, "dashboards", filename)
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return RedirectResponse(url="/login")

# Mount directories (must be mounted after custom route definitions so it doesn't hijack routes)
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")
