#!/bin/bash
# Railway startup script

echo "Starting Ricky application..."

# Set working directory to app root
cd /app

# Ensure data directories exist (for local file storage)
mkdir -p data/images data/logs

# Set Python path to include the app directory
export PYTHONPATH="/app:$PYTHONPATH"

# Check if we're using PostgreSQL and run appropriate setup
if [[ $DATABASE_URL == postgresql://* ]] || [[ $DATABASE_URL == postgres://* ]]; then
    echo "PostgreSQL database detected - running PostgreSQL setup..."
    python setup_postgresql.py
    
    if [ $? -ne 0 ]; then
        echo "❌ PostgreSQL setup failed!"
        exit 1
    fi
else
    echo "Non-PostgreSQL database detected - running standard initialization..."
    
    # Initialize database with default admin user
    echo "Initializing database and creating admin user..."
    python src/scripts/init_railway_db.py

    if [ $? -ne 0 ]; then
        echo "❌ Database initialization failed!"
        echo "Trying alternative initialization method..."
        
        # Fallback: run initialization directly with proper Python path
        cd /app && python -c "
import sys
sys.path.insert(0, '/app')
from src.models import init_db, get_db_session, User

print('Initializing database...')
init_db()
print('✓ Database schema created')

with get_db_session() as session:
    admin_user = session.query(User).filter_by(username='admin').first()
    if not admin_user:
        print('Creating default admin user...')
        admin_user = User(username='admin', is_admin=True, is_active=True)
        admin_user.set_password('rickyAdmin123!')
        session.add(admin_user)
        session.commit()
        print('✓ Default admin user created (admin/rickyAdmin123!)')
    else:
        print('✓ Admin user already exists')

print('Database initialization completed successfully!')
"
        
        if [ $? -ne 0 ]; then
            echo "❌ All database initialization methods failed!"
            exit 1
        fi
    fi
fi

# Start the application
echo "Starting gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT wsgi:app 