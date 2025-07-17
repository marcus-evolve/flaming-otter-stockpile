# Railway Deployment Guide for Ricky

This guide will help you deploy the Ricky application to Railway with PostgreSQL database.

## Prerequisites

1. A Railway account (sign up at https://railway.app)
2. Railway CLI installed (optional but recommended): `npm install -g @railway/cli`
3. Your Twilio credentials ready

## Deployment Steps

### 1. Prepare Your Repository

Ensure all changes are committed to Git:
```bash
git add .
git commit -m "Prepare for Railway deployment with PostgreSQL"
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

### 3. Add PostgreSQL Database

**In your Railway project dashboard:**

1. Click the "+" button or "New Service"
2. Select "Database" → "PostgreSQL"
3. Railway will create a PostgreSQL instance and automatically set the `DATABASE_URL` environment variable

### 4. Configure Environment Variables

In your Railway project dashboard:

1. Go to your **web service** settings (not the database)
2. Click on "Variables"
3. Add all the environment variables from `railway-env-example.txt`
4. **Important**: Update these values:
   - `SECRET_KEY`: Generate a secure key (use `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `TWILIO_ACCOUNT_SID`: Your Twilio Account SID
   - `TWILIO_AUTH_TOKEN`: Your Twilio Auth Token
   - `TWILIO_PHONE_NUMBER`: Your Twilio phone number
   - `RECIPIENT_PHONE_NUMBER`: The phone number to receive messages
   - `BASE_URL`: Will be automatically set to your Railway app URL

**Note**: `DATABASE_URL` will be automatically provided by Railway when you add the PostgreSQL service. You don't need to set this manually.

### 5. Deploy

#### Using CLI:
```bash
railway up
```

#### Using GitHub:
Push to your main branch - Railway will automatically deploy.

### 6. Verify Database Setup

After deployment, check the logs to ensure PostgreSQL setup was successful:
- Look for "PostgreSQL database detected - running PostgreSQL setup..."
- Verify you see "✓ Database schema created"
- Confirm "✓ Default admin user created (admin/rickyAdmin123!)"

### 7. Get Your App URL

After deployment, Railway will provide you with a URL like:
`https://your-app-name.up.railway.app`

### 8. Update Environment Variables

1. Set the `BASE_URL` environment variable to your Railway app URL
2. Railway will automatically restart your service

### 9. Update Twilio Webhook

1. Go to your Twilio Console
2. Navigate to Phone Numbers > Manage > Active Numbers
3. Click on your phone number
4. Update the SMS webhook URL to: `https://your-app-name.up.railway.app/sms`

### 10. Test Your Deployment

1. Visit your Railway app URL
2. Log in with the default admin credentials (admin/rickyAdmin123!)
3. Upload an image
4. Send a test message

## PostgreSQL Advantages

Using PostgreSQL instead of SQLite provides:
- ✅ **Persistent storage** - Data survives deployments
- ✅ **Better performance** - Optimized for concurrent access
- ✅ **Reliability** - ACID compliance and crash recovery
- ✅ **Scalability** - Handles larger datasets efficiently
- ✅ **Backup and recovery** - Railway provides automated backups

## Troubleshooting

### Database Connection Issues
1. Ensure PostgreSQL service is running in Railway dashboard
2. Check that `DATABASE_URL` environment variable is set automatically
3. Verify both services are in the same Railway project

### Migration from SQLite
If you previously had SQLite data:
1. The new PostgreSQL database will start fresh
2. You'll need to re-upload any images
3. Default admin user will be recreated automatically

### Viewing Database
Railway provides a database client:
1. Go to your PostgreSQL service in Railway
2. Click "Connect" → "Railway CLI"
3. Run `railway connect postgresql`

### Viewing Logs
```bash
railway logs
```

## Important Notes

1. **Change the default admin password** immediately after first login
2. **PostgreSQL data persists** between deployments (unlike SQLite)
3. **Automatic backups** are provided by Railway
4. For production use, consider upgrading to Railway Pro for better performance

## Environment Variable Reference

| Variable | Description | Example | Auto-set by Railway |
|----------|-------------|---------|-------------------|
| SECRET_KEY | Flask secret key for sessions | (generate a secure random key) | No |
| DATABASE_URL | PostgreSQL connection string | postgresql://user:pass@host:port/db | **Yes** |
| BASE_URL | Your Railway app URL | https://your-app.up.railway.app | No (set manually) |
| TWILIO_ACCOUNT_SID | Twilio Account SID | ACxxxxxxxxxxxxx | No |
| TWILIO_AUTH_TOKEN | Twilio Auth Token | (your auth token) | No |
| TWILIO_PHONE_NUMBER | Your Twilio phone number | +15551234567 | No |
| RECIPIENT_PHONE_NUMBER | Number to receive messages | +15559876543 | No |

## Next Steps

After successful deployment:
1. Test the SMS functionality thoroughly
2. Monitor PostgreSQL usage in Railway dashboard
3. Set up monitoring/alerts
4. Configure any additional backup strategies if needed 