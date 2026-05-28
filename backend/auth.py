import hashlib
import uuid

def hash_password(password: str) -> str:
    # Use SHA-256 with a fixed salt for simplicity and maximum reliability
    salt = "libreserve_secret_salt"
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return hashed

def verify_password(password: str, hashed_password: str) -> bool:
    return hash_password(password) == hashed_password

def generate_session_token() -> str:
    return str(uuid.uuid4())
