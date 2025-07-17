#!/usr/bin/env python3
"""
Manual fix for Railway deployment - run this once to create the admin user.
You can run this via Railway's console or as a one-time job.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path  
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def create_admin_user():
    """Create the admin user manually."""
    try:
        from src.models import get_db_session, User
        
        print("Checking for existing admin user...")
        
        with get_db_session() as session:
            # Check if admin user already exists
            admin_user = session.query(User).filter_by(username='admin').first()
            
            if admin_user:
                print("✓ Admin user already exists")
                print(f"Username: {admin_user.username}")
                print(f"Is Admin: {admin_user.is_admin}")
                print(f"Is Active: {admin_user.is_active}")
                return True
            
            # Create new admin user
            print("Creating admin user...")
            admin_user = User(
                username='admin',
                is_admin=True,
                is_active=True
            )
            admin_user.set_password('rickyAdmin123!')
            
            session.add(admin_user)
            session.commit()
            
            print("✓ Admin user created successfully!")
            print("Username: admin")
            print("Password: rickyAdmin123!")
            print("⚠️  Please change this password after first login!")
            
            return True
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("RAILWAY ADMIN USER CREATION")
    print("=" * 50)
    
    success = create_admin_user()
    
    if success:
        print("\n✅ Process completed successfully!")
        print("\nYou can now log in to your Railway app with:")
        print("Username: admin")
        print("Password: rickyAdmin123!")
    else:
        print("\n❌ Process failed!")
        sys.exit(1) 