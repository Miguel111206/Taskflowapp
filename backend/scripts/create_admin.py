"""
Usage: python scripts/create_admin.py <username> <password> [email]

This script creates an admin user directly in the database. Run it inside the backend container:
  docker-compose exec backend python scripts/create_admin.py admin mypass admin@example.com

It uses the same hashing scheme as the app (pbkdf2_sha256) and sets is_admin=True.
"""
import sys
import os
from sqlmodel import Session, select
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db import engine
from app.models import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def main():
    if len(sys.argv) < 3:
        print("Usage: python scripts/create_admin.py <username> <password> [email]")
        sys.exit(1)
    username = sys.argv[1]
    password = sys.argv[2]
    email = sys.argv[3] if len(sys.argv) >= 4 else None

    with Session(engine) as session:
        existing = session.exec(select(User).where(User.username == username)).first()
        if existing:
            print(f"User '{username}' already exists (id={existing.id}).")
            return
        user = User(username=username, password_hash=hash_password(password), is_admin=True, role="admin", email=email)
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"Created admin user: id={user.id}, username={user.username}")

if __name__ == '__main__':
    main()
