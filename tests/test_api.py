import urllib.request
import json
import time
import subprocess
import os
import sys

def make_request(url, method="GET", data=None, headers=None):
    if headers is None:
        headers = {}
    
    req_data = None
    if data:
        req_data = json.dumps(data).encode('utf-8')
        headers["Content-Type"] = "application/json"
        
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return res.status, json.loads(res.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        try:
            return e.code, json.loads(body)
        except:
            return e.code, body

def run_tests():
    print("[*] Starting backend validation test suite...")
    
    # 1. Start server process
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.join(base_dir, "backend")
    
    # Run uvicorn as a background process
    server_proc = subprocess.Popen([
        "py", "-m", "uvicorn", "main:app", 
        "--host", "127.0.0.1", 
        "--port", "8085", 
        "--app-dir", backend_dir
    ])
    
    time.sleep(2)  # Wait for server to spin up
    
    try:
        url_base = "http://127.0.0.1:8085/api"
        
        # Test Case 1: Login Admin
        print("\n--- Test Case 1: Login System Admin ---")
        status, res = make_request(f"{url_base}/auth/login", "POST", {
            "email": "sysadmin@uet.edu.pk",
            "password": "sys123"
        })
        print(f"Status: {status}, Response Role: {res.get('role')}")
        assert status == 200
        assert res.get('role') == 'System Admin'
        print("[+] System Admin Login: SUCCESS")
        
        # Test Case 2: Browse Catalog
        print("\n--- Test Case 2: Browse Catalog ---")
        status, books = make_request(f"{url_base}/catalog/books?search=Clean")
        print(f"Status: {status}, Books found: {len(books)}")
        assert status == 200
        assert len(books) > 0
        assert books[0]['title'] == 'Clean Code'
        print("[+] Browse Catalog: SUCCESS")
        
        # Test Case 3: Student Reserve Book
        print("\n--- Test Case 3: Student Reserve Book ---")
        # Let's reserve Bjarne's C++ book (ISBN: 978-0321563842) for student Hadi
        status, res = make_request(f"{url_base}/reservations/reserve?user_id=2025(s)-SE-5", "POST", {
            "isbn": "978-0321563842",
            "pickup_date": "2026-06-15"
        })
        print(f"Status: {status}, Reservation Status: {res.get('status')}")
        assert status == 200
        assert res.get('status') == 'Pending'
        reservation_id = res.get('id')
        print(f"[+] Reservation created successfully with ID: {reservation_id}")
        
        # Test Case 4: Librarian Approve Reservation
        print("\n--- Test Case 4: Librarian Approve Reservation ---")
        status, res = make_request(f"{url_base}/reservations/action/{reservation_id}?actor_id=LIB-201", "POST", {
            "action": "Approve"
        })
        print(f"Status: {status}, New Status: {res.get('status')}")
        assert status == 200
        assert res.get('status') == 'Approved'
        print("[+] Reservation Approved: SUCCESS")
        
        # Test Case 5: Librarian Issue Book
        print("\n--- Test Case 5: Librarian Issue Book ---")
        status, res = make_request(f"{url_base}/loans/issue?reservation_id={reservation_id}&actor_id=LIB-201", "POST")
        print(f"Status: {status}, Message: {res.get('message')}")
        assert status == 200
        print("[+] Book Issued: SUCCESS")
        
        # Test Case 6: Librarian Return Book
        print("\n--- Test Case 6: Librarian Return Book ---")
        status, res = make_request(f"{url_base}/loans/return?isbn=978-0321563842&user_id=2025(s)-SE-5&actor_id=LIB-201", "POST")
        print(f"Status: {status}, Message: {res.get('message')}, Fine Accrued: {res.get('fine_accrued')}")
        assert status == 200
        print("[+] Book Returned: SUCCESS")
        
        print("\n" + "="*40)
        print("   ALL BACKEND API TESTS COMPLETED: SUCCESS")
        print("="*40)
        
    finally:
        # Shutdown server
        print("\n[*] Terminating server process...")
        server_proc.terminate()
        server_proc.wait()

if __name__ == "__main__":
    run_tests()
