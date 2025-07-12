# Ricky Quick Setup Guide

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Twilio account with SMS/MMS capabilities
- macOS (for python-magic) or Linux

## Setup Steps

### 1. Clone and Navigate
```bash
cd /path/to/Ricky
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

**Note for macOS users**: If you encounter issues with python-magic:
```bash
brew install libmagic
```

### 4. Configure Environment
```bash
cp env.example .env
```

Edit `.env` and add your Twilio credentials:
- `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
- `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
- `TWILIO_PHONE_NUMBER`: Your Twilio phone number (with country code)
- `RECIPIENT_PHONE_NUMBER`: Recipient's phone number (with country code)

### 5. Initialize Database
```bash
python scripts/setup_db.py
```

### 6. Add Images

**Single image:**
```bash
python scripts/add_image.py -i /path/to/image.jpg -d "Description of the image"
```

**Batch from directory:**
```bash
python scripts/add_image.py -D /path/to/images/directory
```

**Interactive mode:**
```bash
python scripts/add_image.py
```

### 7. Verify Setup
```bash
# Check Twilio configuration
python scripts/manage.py verify-twilio

# List images in database
python scripts/manage.py list-images

# Send a test message (replace 1 with actual image ID)
python scripts/manage.py send-test 1
```

### 8. Run the Application

**Option 1: Command Line Interface**
```bash
python src/main.py
```

**Option 2: Web Interface (Recommended)**
```bash
python src/web_app.py
```

Then open your browser and navigate to: http://127.0.0.1:5000

Default admin credentials:
- Username: admin
- Password: rickyAdmin123!

**Important:** Change the admin password immediately after first login!

The application will run continuously, sending random images at unpredictable intervals between 24-90 hours.

## Management Commands

```bash
# View all management commands
python scripts/manage.py --help

# Common commands:
python scripts/manage.py list-images     # List all images
python scripts/manage.py stats           # Show statistics
python scripts/manage.py reset-sent-status  # Reset all images to unsent
python scripts/manage.py toggle-image 1 --deactivate  # Deactivate an image
```

## Security Notes

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Keep images directory secure** - Files are stored with restrictive permissions
3. **Monitor logs** - Check `logs/ricky.log` for any security events
4. **Use strong Twilio credentials** - Enable 2FA on your Twilio account

## Troubleshooting

### Image Not Sending
1. Check Twilio credentials: `python scripts/manage.py verify-twilio`
2. Verify image exists: `python scripts/manage.py list-images`
3. Check logs: `tail -f logs/ricky.log`

### Database Issues
1. Ensure database file has correct permissions
2. Try reinitializing: `python scripts/setup_db.py`

### Scheduling Issues
1. Check if scheduler is running in logs
2. Verify interval configuration in `.env`

## Production Deployment

For production deployment:
1. Use PostgreSQL instead of SQLite
2. Set up proper media hosting (AWS S3, Cloudinary, etc.)
3. Use a process manager (systemd, supervisor)
4. Set up log rotation
5. Configure firewall rules
6. Use environment-specific configs 