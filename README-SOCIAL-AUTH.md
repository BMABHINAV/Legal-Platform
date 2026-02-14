# Social Authentication & Email Notifications Setup

This document explains how to configure Google and GitHub OAuth authentication, and email notifications for the Legal Platform.

## Social Authentication (Google & GitHub OAuth)

### Requirements
```bash
pip install django-allauth PyJWT
```

### Configuration

#### 1. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing one
3. Enable "Google+ API" or "Google People API"
4. Go to "Credentials" → "Create Credentials" → "OAuth client ID"
5. Select "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `http://127.0.0.1:8000/accounts/google/login/callback/`
   - `https://yourdomain.com/accounts/google/login/callback/` (for production)
7. Copy the Client ID and Client Secret

#### 2. GitHub OAuth Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in details:
   - **Application name**: Legal Platform
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/accounts/github/login/callback/`
4. Register the application
5. Copy the Client ID and generate a Client Secret

#### 3. Environment Variables

Add the following to your `.env` file:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### Testing Social Auth

1. Start the development server: `python manage.py runserver`
2. Go to `http://localhost:8000/login/`
3. Click "Google" or "GitHub" button
4. You should be redirected to the provider's login page
5. After authentication, you'll be redirected back and logged in

---

## Email Notifications Setup

The platform sends email notifications for:
- **Welcome email** - When a new user signs up
- **Login notification** - When a user logs in (security alert)
- **Password changed** - When password is changed
- **Booking confirmation** - When a booking is created
- **Payment receipt** - When payment is successful
- **Provider verification** - When a provider is verified by admin
- **Emergency alerts** - For panic button feature

### Gmail SMTP Configuration

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to [Google App Passwords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and your device
   - Copy the 16-character password

3. Add to your `.env` file:

```env
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=Legal Platform <your-email@gmail.com>
```

### Other SMTP Providers

#### SendGrid
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

#### Mailgun
```env
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@your-domain.mailgun.org
EMAIL_HOST_PASSWORD=your-mailgun-smtp-password
```

### Development Mode

If no email credentials are configured, emails are printed to the console:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

### Testing Email

```python
# In Django shell (python manage.py shell)
from django.core.mail import send_mail
send_mail(
    'Test Subject',
    'Test message body',
    'from@example.com',
    ['to@example.com'],
)
```

---

## Complete .env Example

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

# Database (optional - defaults to SQLite)
DATABASE_URL=postgres://user:pass@localhost:5432/dbname

# AI APIs
GROQ_API_KEY=your-groq-api-key
GEMINI_API_KEY=your-gemini-api-key

# Payment Gateway
RAZORPAY_KEY_ID=your-razorpay-key-id
RAZORPAY_KEY_SECRET=your-razorpay-key-secret

# Social Auth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Legal Platform <your-email@gmail.com>

# SMS (optional)
SMS_API_KEY=your-fast2sms-api-key
```

---

## Troubleshooting

### Social Auth Issues

1. **"Error: redirect_uri_mismatch"**
   - Ensure callback URLs in provider settings match exactly
   - Check for trailing slashes

2. **"Access blocked: This app's request is invalid"**
   - Add test users in Google Cloud Console OAuth consent screen
   - Or publish your app for production

### Email Issues

1. **"SMTPAuthenticationError"**
   - For Gmail: Use App Password, not regular password
   - Enable "Less secure app access" (not recommended)

2. **Emails not sending**
   - Check console output for development mode
   - Verify SMTP credentials
   - Check firewall/network for port 587

3. **Emails going to spam**
   - Set up SPF, DKIM, and DMARC records
   - Use a reputable email service for production
