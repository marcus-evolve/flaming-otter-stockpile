#!/usr/bin/env python3
"""
Database setup script for Ricky application.
Creates tables and performs initial setup with progress tracking.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.config import config
from src.utils.logger import logger
from src.models import init_db, Base, get_db_session, Image


class DatabaseSetup:
    """Database setup with progress tracking."""
    
    def __init__(self):
        """Initialize database setup."""
        self.steps = [
            ("Initializing database connection", self._init_database),
            ("Creating tables", self._create_tables),
            ("Verifying database structure", self._verify_structure),
            ("Setting up indexes", self._setup_indexes),
        ]
        self.total_steps = len(self.steps)
    
    def _print_progress(self, step: int, message: str):
        """Print progress message."""
        progress = f"[{step}/{self.total_steps}]"
        print(f"{progress} {message}")
        logger.info(f"{progress} {message}")
    
    def _init_database(self):
        """Initialize database connection."""
        init_db()
        return True
    
    def _create_tables(self):
        """Create database tables."""
        # Tables are created in init_db, but we verify here
        with get_db_session() as session:
            # Try to query the table
            count = session.query(Image).count()
            logger.info(f"Images table exists with {count} records")
        return True
    
    def _verify_structure(self):
        """Verify database structure."""
        with get_db_session() as session:
            # Get table info
            inspector = session.bind.inspector
            
            # Check if images table exists
            if 'images' not in inspector.get_table_names():
                raise Exception("Images table not found")
            
            # Check columns
            columns = inspector.get_columns('images')
            required_columns = {
                'id', 'filename', 'file_hash', 'file_size', 'mime_type',
                'description', 'created_at', 'last_sent', 'send_count',
                'is_active', 'is_sent', 'upload_ip', 'notes'
            }
            
            actual_columns = {col['name'] for col in columns}
            missing_columns = required_columns - actual_columns
            
            if missing_columns:
                raise Exception(f"Missing columns: {missing_columns}")
            
            logger.info("Database structure verified successfully")
        return True
    
    def _setup_indexes(self):
        """Verify indexes are created."""
        with get_db_session() as session:
            # Get index info
            inspector = session.bind.inspector
            indexes = inspector.get_indexes('images')
            
            logger.info(f"Found {len(indexes)} indexes on images table")
            for idx in indexes:
                logger.info(f"  - {idx['name']}: {idx['column_names']}")
        
        return True
    
    def run(self):
        """Run database setup."""
        print("=== Ricky Database Setup ===")
        print(f"Database URL: {config.DATABASE_URL}")
        print()
        
        success = True
        for i, (description, func) in enumerate(self.steps, 1):
            self._print_progress(i, description)
            try:
                result = func()
                if result:
                    self._print_progress(i, f"✓ {description} - Complete")
                else:
                    self._print_progress(i, f"✗ {description} - Failed")
                    success = False
                    break
            except Exception as e:
                self._print_progress(i, f"✗ {description} - Error: {e}")
                logger.error(f"Setup error in step {i}: {e}", exc_info=True)
                success = False
                break
        
        print()
        if success:
            print("✓ Database setup completed successfully!")
            logger.info("Database setup completed successfully")
        else:
            print("✗ Database setup failed!")
            logger.error("Database setup failed")
            sys.exit(1)


def main():
    """Main entry point."""
    setup = DatabaseSetup()
    setup.run()


if __name__ == "__main__":
    main() 