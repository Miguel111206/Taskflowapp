from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from passlib.context import CryptContext

SECRET_KEY = "taskflow-secret-key-change-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


class JWTHandler:
    """
    JWT token handler for creating and verifying tokens.
    """
    
    def __init__(
        self,
        secret_key: str = SECRET_KEY,
        algorithm: str = ALGORITHM
    ) -> None:
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create an access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a refresh token."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self._secret_key, algorithm=self._algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a token."""
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm]
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode token without verification."""
        try:
            return jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                options={"verify_signature": False}
            )
        except PyJWTError:
            return None