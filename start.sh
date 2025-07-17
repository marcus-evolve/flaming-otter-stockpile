#!/bin/bash
# Railway startup script

echo "Starting Ricky application..."

# Ensure data directories exist
mkdir -p data/images data/logs

# Initialize database with default admin user
echo "Initializing database and creating admin user..."
python src/scripts/init_railway_db.py

if [ $? -ne 0 ]; then
    echo "❌ Database initialization failed!"
    exit 1
fi

# Start the application
echo "Starting gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT wsgi:app 