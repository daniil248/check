"""
Авторизация: JWT, логин/пароль.
"""
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

DB_PATH = Path(__file__).resolve().parent / "users.db"
SECRET_KEY = os.environ.get("SECRET_KEY", "northpak-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 дней

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)


def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            name TEXT,
            picture TEXT,
            google_id TEXT,
            reset_token TEXT,
            reset_token_expires TEXT
        )
    """)
    for col in ("name", "picture", "google_id", "reset_token", "reset_token_expires"):
        try:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        except sqlite3.OperationalError:
            pass
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query TEXT NOT NULL,
            country TEXT NOT NULL,
            results_count INTEGER,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()


def create_user(email: str, password: str) -> dict:
    conn = _db()
    try:
        conn.execute(
            "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
            (email.strip().lower(), pwd_context.hash(password[:72]), datetime.utcnow().isoformat()),
        )
        conn.commit()
        row = conn.execute("SELECT id, email, created_at FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
        return {"id": row["id"], "email": row["email"], "created_at": row["created_at"]}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже есть")
    finally:
        conn.close()


def create_or_get_user_google(email: str, name: str = "", picture: str = "", google_id: str = "") -> dict:
    email = email.strip().lower()
    if not email:
        raise HTTPException(status_code=400, detail="Email от Google не получен")
    conn = _db()
    try:
        row = conn.execute(
            "SELECT id, email, created_at, name, picture FROM users WHERE email = ?", (email,)
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE users SET name = ?, picture = ?, google_id = ? WHERE email = ?",
                (name or None, picture or None, google_id or None, email),
            )
            conn.commit()
            return {"id": row["id"], "email": row["email"], "created_at": row["created_at"], "name": name or row["name"], "picture": picture or row["picture"]}
        conn.execute(
            "INSERT INTO users (email, password_hash, created_at, name, picture, google_id) VALUES (?, ?, ?, ?, ?, ?)",
            (email, "", datetime.utcnow().isoformat(), name or None, picture or None, google_id or None),
        )
        conn.commit()
        row = conn.execute("SELECT id, email, created_at FROM users WHERE email = ?", (email,)).fetchone()
        return {"id": row["id"], "email": row["email"], "created_at": row["created_at"], "name": name, "picture": picture}
    finally:
        conn.close()


def get_user_by_email(email: str) -> sqlite3.Row | None:
    conn = _db()
    row = conn.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (email.strip().lower(),)).fetchone()
    conn.close()
    return row


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Неверный токен")
    email = payload["sub"]
    conn = _db()
    row = conn.execute("SELECT id, email, name, picture FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    return {"id": row["id"], "email": row["email"], "name": row["name"] if "name" in row.keys() else None, "picture": row["picture"] if "picture" in row.keys() else None}


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict | None:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if not payload or "sub" not in payload:
        return None
    conn = _db()
    row = conn.execute("SELECT id, email FROM users WHERE email = ?", (payload["sub"],)).fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row["id"], "email": row["email"]}
