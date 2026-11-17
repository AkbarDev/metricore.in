import json
import os
import hashlib
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

DATA_DIR = Path(__file__).resolve().parent / "data"
USERS_FILE = DATA_DIR / "users.json"

def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    ).hex()
    return key, salt

def _load_users() -> List[Dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        # Initialize with Admin account (Akbar / unlock) with secure password hash
        admin_hash, admin_salt = _hash_password("unlock")
        initial_users = [
            {
                "username": "Akbar",
                "email": "akber96@hotmail.com",
                "password_hash": admin_hash,
                "salt": admin_salt,
                "role": "admin",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_users, f, indent=2)
        return initial_users

    with open(USERS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []

def _save_users(users: List[Dict[str, Any]]):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    users = _load_users()
    for u in users:
        if u["username"].strip().lower() == username.strip().lower():
            return u
    return None

def verify_credentials(username: str, password: str) -> Optional[Dict[str, Any]]:
    user = get_user_by_username(username)
    if not user:
        return None
    test_hash, _ = _hash_password(password, user["salt"])
    if test_hash == user["password_hash"]:
        return user
    return None

def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    clean_username = username.strip()
    clean_email = email.strip().lower()

    if len(clean_username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(password) < 4:
        return False, "Password must be at least 4 characters long."

    users = _load_users()

    # Check for existing username or email
    for u in users:
        if u["username"].lower() == clean_username.lower():
            return False, "Username is already registered. Please sign in or choose another."
        if u.get("email", "").lower() == clean_email:
            return False, "An account with this email already exists."

    pwd_hash, salt = _hash_password(password)
    new_user = {
        "username": clean_username,
        "email": clean_email,
        "password_hash": pwd_hash,
        "salt": salt,
        "role": "user",
        "created_at": datetime.utcnow().isoformat()
    }

    users.append(new_user)
    _save_users(users)
    return True, "Account created successfully!"

