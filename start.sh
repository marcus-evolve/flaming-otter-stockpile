#!/bin/bash
# Railway startup script

echo "Starting Ricky application..."

# Ensure data directories exist
mkdir -p data/images data/logs

# Initialize database if it doesn't exist
if [ ! -f "data/ricky.db" ]; then
    echo "Initializing database..."
    python -c "
from src.models import init_db
init_db()
print('Database initialized successfully!')
"
fi

# Start the application
echo "Starting gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT wsgi:app 