import datetime
from database import SessionLocal, engine, Base
from models import User, Book, Reservation, Loan, Fine, CourseReserve, BookRequest, SystemLog
from auth import hash_password

def seed_data():
    # Recreate tables
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 1. Seed Users
        users = [
            User(
                id="2025(s)-SE-5",
                email="abdulhadi@uet.edu.pk",
                password_hash=hash_password("student123"),
                first_name="Abdul",
                last_name="Hadi",
                role="Student",
                status="Active"
            ),
            User(
                id="2025(s)-SE-4",
                email="irfan@uet.edu.pk",
                password_hash=hash_password("student123"),
                first_name="Muhammad",
                last_name="Irfan",
                role="Student",
                status="Active"
            ),
            User(
                id="2025(s)-SE-30",
                email="arslan@uet.edu.pk",
                password_hash=hash_password("student123"),
                first_name="Arslan",
                last_name="Liaqat",
                role="Student",
                status="Active"
            ),
            User(
                id="2025(s)-SE-10",
                email="suspended_student@uet.edu.pk",
                password_hash=hash_password("student123"),
                first_name="John",
                last_name="Doe",
                role="Student",
                status="Suspended"
            ),
            User(
                id="FAC-101",
                email="zeeshan@uet.edu.pk",
                password_hash=hash_password("faculty123"),
                first_name="Zeeshan",
                last_name="Ramzan",
                role="Faculty",
                status="Active"
            ),
            User(
                id="LIB-201",
                email="librarian@uet.edu.pk",
                password_hash=hash_password("lib123"),
                first_name="Sarah",
                last_name="Connor",
                role="Librarian",
                status="Active"
            ),
            User(
                id="LADM-301",
                email="libadmin@uet.edu.pk",
                password_hash=hash_password("admin123"),
                first_name="Alice",
                last_name="Smith",
                role="Library Admin",
                status="Active"
            ),
            User(
                id="SADM-401",
                email="sysadmin@uet.edu.pk",
                password_hash=hash_password("sys123"),
                first_name="Bob",
                last_name="Johnson",
                role="System Admin",
                status="Active"
            )
        ]
        db.add_all(users)
        
        # 2. Seed Books
        books = [
            Book(
                isbn="978-0131103627",
                title="The C Programming Language",
                author="Brian W. Kernighan, Dennis M. Ritchie",
                category="Computer Science",
                language="English",
                publication_year=1988,
                quantity=5,
                available_copies=5
            ),
            Book(
                isbn="978-0201633610",
                title="Design Patterns: Elements of Reusable Object-Oriented Software",
                author="Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides",
                category="Computer Science",
                language="English",
                publication_year=1994,
                quantity=3,
                available_copies=2  # 1 copy reserved/loaned
            ),
            Book(
                isbn="978-0132350884",
                title="Clean Code",
                author="Robert C. Martin",
                category="Computer Science",
                language="English",
                publication_year=2008,
                quantity=4,
                available_copies=3  # 1 copy on loan
            ),
            Book(
                isbn="978-0073523323",
                title="Database System Concepts",
                author="Abraham Silberschatz",
                category="Computer Science",
                language="English",
                publication_year=2010,
                quantity=6,
                available_copies=6
            ),
            Book(
                isbn="978-0471154969",
                title="Advanced Calculus",
                author="Gerald B. Folland",
                category="Mathematics",
                language="English",
                publication_year=2002,
                quantity=2,
                available_copies=2
            ),
            Book(
                isbn="978-0199535569",
                title="The Odyssey",
                author="Homer",
                category="Literature",
                language="English",
                publication_year=2008,
                quantity=3,
                available_copies=3
            ),
            Book(
                isbn="978-0321563842",
                title="The C++ Programming Language",
                author="Bjarne Stroustrup",
                category="Computer Science",
                language="English",
                publication_year=2013,
                quantity=8,
                available_copies=7  # 1 copy reserved
            ),
            Book(
                isbn="978-0521190541",
                title="Quantum Mechanics",
                author="David J. Griffiths",
                category="Physics",
                language="English",
                publication_year=2016,
                quantity=4,
                available_copies=4
            ),
            Book(
                isbn="978-0135957059",
                title="The Pragmatic Programmer",
                author="David Thomas, Andrew Hunt",
                category="Computer Science",
                language="English",
                publication_year=2019,
                quantity=4,
                available_copies=4
            ),
            Book(
                isbn="978-0262033848",
                title="Introduction to Algorithms",
                author="Thomas H. Cormen, Charles E. Leiserson, Ronald L. Rivest, Clifford Stein",
                category="Computer Science",
                language="English",
                publication_year=2009,
                quantity=10,
                available_copies=10
            ),
            Book(
                isbn="978-0134053004",
                title="Introduction to Electrodynamics",
                author="David J. Griffiths",
                category="Physics",
                language="English",
                publication_year=2017,
                quantity=2,
                available_copies=2
            ),
            Book(
                isbn="978-0060935467",
                title="To Kill a Mockingbird",
                author="Harper Lee",
                category="Literature",
                language="English",
                publication_year=2002,
                quantity=3,
                available_copies=3
            ),
            Book(
                isbn="978-0321146533",
                title="Linear Algebra and Its Applications",
                author="David C. Lay",
                category="Mathematics",
                language="English",
                publication_year=2002,
                quantity=6,
                available_copies=6
            )
        ]
        db.add_all(books)
        db.commit()  # Commit to assign PKs and relations
        
        # 3. Seed Reservations
        now = datetime.datetime.utcnow()
        reservations = [
            Reservation(
                user_id="2025(s)-SE-5",
                isbn="978-0321563842",  # C++
                request_date=now - datetime.timedelta(hours=5),
                pickup_date=now + datetime.timedelta(days=2),
                status="Pending"
            ),
            Reservation(
                user_id="FAC-101",
                isbn="978-0201633610",  # Design Patterns
                request_date=now - datetime.timedelta(days=1),
                pickup_date=now + datetime.timedelta(days=1),
                status="Approved"
            ),
            Reservation(
                user_id="2025(s)-SE-4",
                isbn="978-0132350884",  # Clean Code
                request_date=now - datetime.timedelta(days=3),
                pickup_date=now - datetime.timedelta(days=1),
                status="Rejected",
                rejection_reason="Patron has outstanding fine."
            )
        ]
        db.add_all(reservations)
        
        # 4. Seed Loans
        loans = [
            Loan(
                user_id="2025(s)-SE-5",
                isbn="978-0132350884",  # Clean Code
                issue_date=now - datetime.timedelta(days=4),
                due_date=now + datetime.timedelta(days=3),
                status="Active"
            ),
            # Overdue loan
            Loan(
                user_id="2025(s)-SE-4",
                isbn="978-0201633610",  # Design Patterns
                issue_date=now - datetime.timedelta(days=10),
                due_date=now - datetime.timedelta(days=3),
                status="Overdue"
            )
        ]
        db.add_all(loans)
        db.commit()
        
        # 5. Seed Fines
        # Fine is associated with Loan ID 2 (Design Patterns overdue)
        overdue_loan = db.query(Loan).filter(Loan.status == "Overdue").first()
        if overdue_loan:
            fine = Fine(
                loan_id=overdue_loan.id,
                user_id=overdue_loan.user_id,
                amount=150.00,  # Rs. 150 fine
                status="Unpaid"
            )
            db.add(fine)
            
        # 6. Course Reserves
        course_reserves = [
            CourseReserve(
                faculty_id="FAC-101",
                isbn="978-0073523323",  # Database Concepts
                course_name="CS-301: Database Management Systems"
            )
        ]
        db.add_all(course_reserves)
        
        # 7. Book Requests
        book_requests = [
            BookRequest(
                faculty_id="FAC-101",
                title="Introduction to Algorithms",
                author="Thomas H. Cormen",
                status="Pending"
            )
        ]
        db.add_all(book_requests)
        
        # 8. System Logs
        logs = [
            SystemLog(
                actor_id="SADM-401",
                action="System initialized and seed data populated.",
                status="Success"
            ),
            SystemLog(
                actor_id="LADM-301",
                action="Updated fine policy to Rs. 50 per day.",
                status="Success"
            )
        ]
        db.add_all(logs)
        
        db.commit()
        print("Database seeded successfully with test records!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
