"""
User model for web authentication.
Implements secure password hashing and user management.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .image import Base


class User(Base, UserMixin):
    """
    User model for authentication with secure password storage.
    """
    __tablename__ = 'users'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Authentication fields
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # User status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Tracking
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # Security
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    def set_password(self, password: str):
        """
        Set password with secure hashing.
        
        Args:
            password: Plain text password
        """
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password: str) -> bool:
        """
        Check if provided password matches the hash.
        
        Args:
            password: Plain text password to check
            
        Returns:
            True if password matches
        """
        return check_password_hash(self.password_hash, password)
    
    def record_login(self):
        """Record successful login."""
        self.last_login = datetime.utcnow()
        self.login_count += 1
        self.failed_login_attempts = 0
        self.locked_until = None
    
    def record_failed_login(self):
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        
        # Lock account after 5 failed attempts
        if self.failed_login_attempts >= 5:
            from datetime import timedelta
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def is_locked(self) -> bool:
        """Check if account is locked."""
        if self.locked_until:
            if datetime.utcnow() < self.locked_until:
                return True
            else:
                # Unlock if time has passed
                self.locked_until = None
                self.failed_login_attempts = 0
        return False
    
    def __repr__(self):
        """String representation."""
        return f"<User(id={self.id}, username='{self.username}', admin={self.is_admin})>" 