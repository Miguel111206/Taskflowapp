import re
from typing import Optional


class Password:
    """
    Value object representing a password.
    Provides validation and encapsulation.
    """
    
    MIN_LENGTH = 8
    
    def __init__(self, value: Optional[str] = None, hashed: str = None) -> None:
        if hashed is not None:
            self._value = hashed
            self._is_hashed = True
        elif value is not None:
            self._validate(value)
            self._value = value
            self._is_hashed = False
        else:
            raise ValueError("Password must have either value or hashed")
    
    def _validate(self, value: str) -> None:
        """Validate password requirements."""
        if len(value) < self.MIN_LENGTH:
            raise ValueError(f"Password must be at least {self.MIN_LENGTH} characters")
        if not re.search(r'[A-Za-z]', value):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r'[0-9]', value):
            raise ValueError("Password must contain at least one digit")
    
    @property
    def value(self) -> str:
        """Get the password value."""
        return self._value
    
    @property
    def is_hashed(self) -> bool:
        """Check if password is hashed."""
        return self._is_hashed
    
    def __str__(self) -> str:
        return "***"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Password):
            return False
        return self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)
    
    def __repr__(self) -> str:
        return "Password('***')"