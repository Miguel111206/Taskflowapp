import re
from typing import Optional


class Email:
    """
    Value object representing an email address.
    Provides validation and immutability.
    """
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def __init__(self, value: str) -> None:
        self._value = self._validate(value)
    
    def _validate(self, value: str) -> str:
        """Validate email format."""
        if not value or not self.EMAIL_PATTERN.match(value):
            raise ValueError(f"Invalid email format: {value}")
        return value.lower()
    
    @property
    def value(self) -> str:
        """Get the email value."""
        return self._value
    
    def __str__(self) -> str:
        return self._value
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Email):
            return False
        return self._value == other._value
    
    def __hash__(self) -> int:
        return hash(self._value)
    
    def __repr__(self) -> str:
        return f"Email('{self._value}')"