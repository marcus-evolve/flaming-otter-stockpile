#!/usr/bin/env python3
"""
Initialize database for Railway deployment.
Creates the default admin user if it doesn't exist.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def init_railway_db():
    """Initialize database for Railway deployment."""
    try:
        from src.models import init_db, get_db_session, User
        
        print("Initializing database...")
        init_db()
        print("✓ Database schema created")
        
        # Check if admin user exists
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
        
        print("Database initialization completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_railway_db()
    sys.exit(0 if success else 1) 