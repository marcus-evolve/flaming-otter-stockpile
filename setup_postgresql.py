#!/usr/bin/env python3
"""
Database migration script for Railway PostgreSQL.
Handles migration from SQLite to PostgreSQL if needed.
"""

import sys
import os
from pathlib import Path

# For Railway deployment, ensure we're in the right directory
if '/app' in os.getcwd():
    # We're on Railway, set up paths correctly
    project_root = Path('/app')
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))
else:
    # Local development
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    sys.path.insert(0, str(project_root))

def setup_postgresql():
    """Set up PostgreSQL database with initial data."""
    try:
        from src.models import init_db, get_db_session, User
        from src.utils.config import config
        
        print("Setting up PostgreSQL database...")
        print(f"Database URL: {config.DATABASE_URL[:50]}...")
        
        # Initialize database schema
        print("Creating database schema...")
        init_db()
        print("✓ Database schema created")
        
        # Create default admin user
        with get_db_session() as session:
            admin_user = session.query(User).filter_by(username='admin').first()
            
            if not admin_user:
                print("Creating default admin user...")
                admin_user = User(
                    username='admin',
                    is_admin=True,
                    is_active=True
                )
                admin_user.set_password('rickyAdmin123!')
                session.add(admin_user)
                session.commit()
                print("✓ Default admin user created (admin/rickyAdmin123!)")
            else:
                print("✓ Admin user already exists")
        
        print("PostgreSQL setup completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error setting up PostgreSQL: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_database_type():
    """Check what type of database we're using."""
    try:
        from src.utils.config import config
        db_url = config.DATABASE_URL.lower()
        
        if db_url.startswith('postgresql://') or db_url.startswith('postgres://'):
            return 'postgresql'
        elif db_url.startswith('sqlite:'):
            return 'sqlite'
        else:
            return 'unknown'
    except Exception as e:
        print(f"Error checking database type: {e}")
        return 'unknown'

if __name__ == "__main__":
    print("=" * 60)
    print("RAILWAY DATABASE SETUP")
    print("=" * 60)
    
    db_type = check_database_type()
    print(f"Database type detected: {db_type}")
    
    if db_type == 'postgresql':
        print("Setting up PostgreSQL database...")
        success = setup_postgresql()
    elif db_type == 'sqlite':
        print("SQLite detected - no migration needed for local development")
        success = setup_postgresql()  # Still run setup for consistency
    else:
        print(f"Unknown database type: {db_type}")
        success = False
    
    if success:
        print("\n✅ Database setup completed successfully!")
    else:
        print("\n❌ Database setup failed!")
        sys.exit(1) 