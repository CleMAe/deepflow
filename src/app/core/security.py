"""Password hashing utilities (bcrypt via passlib)."""

from passlib.context import CryptContext

_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _context.verify(plain_password, hashed_password)
