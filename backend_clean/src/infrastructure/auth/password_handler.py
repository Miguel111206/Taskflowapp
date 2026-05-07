from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PasswordHandler:
    """
    Password handler for hashing and verifying passwords.
    """
    
    def __init__(self) -> None:
        self._context = pwd_context
    
    def hash(self, password: str) -> str:
        """Hash a password."""
        return self._context.hash(password)
    
    def verify(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return self._context.verify(password, password_hash)