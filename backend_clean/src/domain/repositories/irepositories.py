from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.user import User


class IUserRepository(ABC):
    """
    Abstract repository interface for User entity.
    Defines the contract for user persistence operations.
    """
    
    @abstractmethod
    def create(self, user: User) -> User:
        """
        Create a new user.
        
        Args:
            user: User entity to create
            
        Returns:
            Created user with generated ID
        """
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to search
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: Email to search
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """
        Update an existing user.
        
        Args:
            user: User entity to update
            
        Returns:
            Updated user
        """
        pass
    
    @abstractmethod
    def delete(self, user_id: str) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if deleted, False otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[User]:
        """
        List all users.
        
        Returns:
            List of all users
        """
        pass