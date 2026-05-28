import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def main():
    print("=" * 60)
    print("       UET LibReserve - Library Book Reservation System       ")
    print("=" * 60)
    
    # Define directories
    base_dir = Path(__file__).resolve().parent
    db_file = base_dir / "libreserve.db"
    backend_dir = base_dir / "backend"
    
    # 1. Check if DB is initialized. If not, seed it.
    if not db_file.exists():
        print("[*] Database file 'libreserve.db' not found. Initializing database...")
        # Add backend folder to path so seed.py can import database/models/auth
        sys.path.append(str(backend_dir))
        try:
            import seed
            seed.seed_data()
            print("[+] Database initialized and seeded successfully!")
        except Exception as e:
            print(f"[-] Database initialization failed: {e}")
            sys.exit(1)
    else:
        print("[+] Existing database 'libreserve.db' detected.")

    # 2. Open browser automatically after a short delay
    print("[*] Launching system default web browser...")
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:8000/")

    # 3. Launch FastAPI server via Uvicorn
    print("[*] Starting FastAPI Uvicorn Server at http://127.0.0.1:8000 ...")
    print("[*] Press Ctrl+C to terminate the application.")
    print("-" * 60)
    
    try:
        # Run uvicorn process
        # We specify --app-dir to find the 'backend' folder module
        subprocess.run([
            sys.executable, "-m", "uvicorn", "main:app", 
            "--host", "127.0.0.1", 
            "--port", "8000", 
            "--app-dir", str(backend_dir)
        ], check=True)
    except KeyboardInterrupt:
        print("\n[-] Server shutting down. Goodbye!")
    except subprocess.CalledProcessError as e:
        print(f"\n[-] Uvicorn server stopped with error: {e}")
    except FileNotFoundError:
        print("\n[-] Python executable or uvicorn not found in PATH.")

if __name__ == "__main__":
    main()
