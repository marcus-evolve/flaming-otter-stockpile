# Ricky - Random Image Texter

A Python application that sends random images with descriptions via SMS/MMS using Twilio at random intervals.

## Architecture Overview

### Technology Stack
- **Language**: Python 3.8+
- **Database**: SQLite (development) / PostgreSQL (production)
- **SMS/MMS Service**: Twilio
- **Scheduler**: APScheduler
- **ORM**: SQLAlchemy
- **Configuration**: python-dotenv

### Project Structure
```
Ricky/
├── src/
│   ├── __init__.py
│   ├── models/           # Database models
│   │   ├── __init__.py
│   │   └── image.py
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   ├── scheduler.py  # Random interval scheduling
│   │   └── twilio_service.py  # SMS/MMS sending
│   ├── utils/            # Utility functions
│   │   ├── __init__.py
│   │   └── config.py     # Configuration management
│   └── main.py           # Application entry point
├── scripts/              # Management scripts
│   ├── add_image.py      # Add images to database
│   └── setup_db.py       # Database initialization
├── data/                 # Local data storage
│   └── images/           # Image file storage
├── tests/                # Unit tests
├── config/               # Configuration files
│   └── config.example.json
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore
└── README.md

```

### Core Components

#### 1. Database Schema
- **Images Table**:
  - `id`: Primary key
  - `filename`: Path to image file
  - `description`: Text description
  - `created_at`: Timestamp
  - `last_sent`: Last time this image was sent
  - `send_count`: Number of times sent

#### 2. Scheduler Service
- Uses APScheduler for random interval scheduling
- Configurable min/max interval range
- Persistent job storage to survive restarts

#### 3. Twilio Integration
- Sends MMS with image and description
- Error handling and retry logic
- Delivery status tracking

#### 4. Configuration Management
- Environment variables for sensitive data (Twilio credentials)
- JSON config for non-sensitive settings
- Support for multiple environments

### Key Features
1. **Random Selection**: Images are selected randomly from the database
2. **Send History**: Tracks when each image was last sent
3. **Configurable Intervals**: Set min/max time between messages
4. **Error Handling**: Robust error handling with logging
5. **Admin Scripts**: Easy image management via CLI
6. **Web Interface**: Modern web UI for complete control without terminal
7. **Authentication**: Secure login system with account lockout protection
8. **Real-time Monitoring**: Live dashboard with statistics and countdown

### Security Considerations
- Twilio credentials stored in environment variables
- Images stored locally (not in database)
- Input validation for phone numbers
- Rate limiting to prevent abuse

## Setup Instructions

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and add your Twilio credentials
6. Initialize database: `python scripts/setup_db.py`
7. Add images: `python scripts/add_image.py`
8. Run application: `python src/main.py` 