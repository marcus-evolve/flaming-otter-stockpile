"""
Database model for images with security and tracking features.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, 
    Boolean, Index, CheckConstraint, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from ..utils.config import config
from ..utils.logger import logger

# Create declarative base
Base = declarative_base()


class Image(Base):
    """
    Image model with comprehensive tracking and security features.
    """
    __tablename__ = 'images'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # File information
    filename = Column(String(255), nullable=False, unique=True)
    file_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(50), nullable=False)
    
    # Description with length constraint
    description = Column(Text, nullable=False)
    
    # Tracking information
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_sent = Column(DateTime, nullable=True)
    send_count = Column(Integer, nullable=False, default=0)
    
    # Status flags
    is_active = Column(Boolean, nullable=False, default=True)
    is_sent = Column(Boolean, nullable=False, default=False)
    
    # Metadata
    upload_ip = Column(String(45), nullable=True)  # IPv6 max length
    notes = Column(Text, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_active_not_sent', 'is_active', 'is_sent'),
        Index('idx_last_sent', 'last_sent'),
        Index('idx_created_at', 'created_at'),
        CheckConstraint('file_size > 0', name='check_file_size_positive'),
        CheckConstraint("mime_type IN ('image/jpeg', 'image/png', 'image/gif', 'image/webp')", 
                       name='check_mime_type'),
    )
    
    def __repr__(self):
        """String representation of Image object."""
        return f"<Image(id={self.id}, filename='{self.filename}', sent={self.is_sent})>"
    
    def mark_as_sent(self):
        """Mark image as sent and update tracking fields."""
        self.is_sent = True
        self.last_sent = datetime.utcnow()
        self.send_count += 1
    
    def reset_sent_status(self):
        """Reset sent status (useful for cycling through images)."""
        self.is_sent = False
    
    @classmethod
    def get_random_unsent(cls, session: Session) -> Optional['Image']:
        """
        Get a random unsent image using secure randomization.
        
        Args:
            session: Database session
        
        Returns:
            Random unsent Image or None if all images are sent
        """
        # Use database-level random for true randomness
        return session.query(cls).filter(
            cls.is_active == True,
            cls.is_sent == False
        ).order_by(func.random()).first()
    
    @classmethod
    def get_all_unsent_count(cls, session: Session) -> int:
        """Get count of unsent images."""
        return session.query(cls).filter(
            cls.is_active == True,
            cls.is_sent == False
        ).count()
    
    @classmethod
    def reset_all_sent_status(cls, session: Session) -> int:
        """
        Reset sent status for all images when all have been sent.
        
        Returns:
            Number of images reset
        """
        updated = session.query(cls).filter(
            cls.is_sent == True
        ).update({cls.is_sent: False})
        session.commit()
        return updated
    
    def to_dict(self) -> dict:
        """Convert to dictionary (excluding sensitive information)."""
        return {
            'id': self.id,
            'filename': self.filename,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_sent': self.last_sent.isoformat() if self.last_sent else None,
            'send_count': self.send_count,
            'is_active': self.is_active,
            'is_sent': self.is_sent
        }


# Database engine and session setup
engine = None
SessionLocal = None


def init_db():
    """Initialize database connection and create tables."""
    global engine, SessionLocal
    
    # Create engine with connection pooling
    engine = create_engine(
        config.DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,  # Verify connections before using
        echo=config.is_development()  # Log SQL in development
    )
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database initialized successfully")


@contextmanager
def get_db_session():
    """
    Provide a transactional scope for database operations.
    
    Yields:
        Database session
    """
    if SessionLocal is None:
        init_db()
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close() 