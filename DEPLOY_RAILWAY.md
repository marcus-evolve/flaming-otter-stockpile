# Railway Deployment Guide for Ricky

This guide will help you deploy the Ricky application to Railway.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. Railway CLI installed (optional but recommended): `npm install -g @railway/cli`
3. Your Twilio credentials ready

## Deployment Steps

### 1. Prepare Your Repository

Ensure all changes are committed to Git:
```bash
git add .
git commit -m "Prepare for Railway deployment"
```

### 2. Create a New Railway Project

#### Option A: Using Railway CLI
```bash
railway login
railway init
railway link
```

#### Option B: Using Railway Dashboard
1. Go to https://railway.app/new
2. Choose "Deploy from GitHub repo"
3. Connect your GitHub account and select your repository

### 3. Configure Environment Variables

In your Railway project dashboard:

1. Go to your service settings
2. Click on "Variables"
3. Add all the environment variables from `railway-env-example.txt`
4. **Important**: Update these values:
   - `SECRET_KEY`: Generate a secure key (use `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
   - `TWILIO_PHONE_NUMBER`: Your Twilio phone number
   - `RECIPIENT_PHONE_NUMBER`: The phone number to receive messages
   - `BASE_URL`: Will be automatically set to your Railway app URL

### 4. Deploy

#### Using CLI:
```bash
railway up
```

#### Using GitHub:
Push to your main branch - Railway will automatically deploy.

### 5. Get Your App URL

After deployment, Railway will provide you with a URL like:
`https://your-app-name.up.railway.app`

### 6. Update Twilio Webhook

1. Go to your Twilio Console
2. Navigate to Phone Numbers > Manage > Active Numbers
3. Click on your phone number
4. Update the SMS webhook URL to: `https://your-app-name.up.railway.app/sms`

### 7. Initialize the Database

Visit your app URL and use the setup process, or run:
```bash
railway run python src/scripts/setup_db.py
```

### 8. Test Your Deployment

1. Visit your Railway app URL
2. Log in with the default admin credentials (admin/rickyAdmin123!)
3. Upload an image
4. Send a test message

## Troubleshooting

### Database Issues
Railway provides ephemeral storage. For production, consider using Railway's PostgreSQL service:
1. Add PostgreSQL to your Railway project
2. Update `DATABASE_URL` to use the provided PostgreSQL URL

### Image Storage
For persistent image storage in production, consider:
1. Using Railway's volume mounts
2. Integrating with a cloud storage service (S3, Cloudinary, etc.)

### Viewing Logs
```bash
railway logs
```

## Important Notes

1. **Change the default admin password** immediately after first login
2. Railway's free tier has limitations - check current limits at railway.app/pricing
3. For production use, implement proper image storage (not local filesystem)
4. Consider using PostgreSQL instead of SQLite for production

## Environment Variable Reference

| Variable | Description | Example |
|----------|-------------|---------|
| SECRET_KEY | Flask secret key for sessions | (generate a secure random key) |
| DATABASE_URL | Database connection string | sqlite:///data/ricky.db |
| BASE_URL | Your Railway app URL | https://your-app.up.railway.app |
| TWILIO_ACCOUNT_SID | Twilio Account SID | ACxxxxxxxxxxxxx |
| TWILIO_AUTH_TOKEN | Twilio Auth Token | (your auth token) |
| TWILIO_PHONE_NUMBER | Your Twilio phone number | +15551234567 |
| RECIPIENT_PHONE_NUMBER | Number to receive messages | +15559876543 |

## Next Steps

After successful deployment:
1. Test the SMS functionality thoroughly
2. Set up monitoring/alerts
3. Configure backups for your database
4. Implement proper logging and error tracking 