# Email Setup Instructions for Test Management System

## Quick Setup

1. **Create `.env` file** in the project root directory
2. **Copy the configuration** from `env_template.txt`
3. **Replace with your actual email credentials**

## Gmail Setup (Recommended)

### Step 1: Enable 2-Factor Authentication
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication if not already enabled

### Step 2: Generate App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Click on "2-Step Verification"
3. Scroll down to "App passwords"
4. Click "App passwords"
5. Select "Mail" and your device
6. Copy the generated 16-character password

### Step 3: Configure .env file
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-16-character-app-password
```

## Outlook/Hotmail Setup

### Step 1: Enable Less Secure Apps (if needed)
1. Go to [Microsoft Account Security](https://account.microsoft.com/security)
2. Enable "Less secure app access" or use App Password

### Step 2: Configure .env file
```env
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SENDER_EMAIL=your-email@outlook.com
SENDER_PASSWORD=your-password
```

## Custom SMTP Setup

If you have your own email server:
```env
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
SENDER_EMAIL=your-email@yourdomain.com
SENDER_PASSWORD=your-password
```

## Testing Email Configuration

After setting up the `.env` file:

1. **Restart the backend server**:
   ```bash
   cd agents/shortlisting
   python start_server.py
   ```

2. **Test by creating a test and sending invitations**

## Troubleshooting

### Common Issues:

1. **"Authentication failed"**
   - Check if 2FA is enabled and you're using App Password
   - Verify email and password are correct

2. **"Connection refused"**
   - Check SMTP server and port
   - Ensure firewall allows outbound connections on port 587

3. **"Less secure app access"**
   - Enable 2FA and use App Password instead
   - Or enable "Less secure app access" in Gmail settings

### Security Notes:

- Never commit `.env` file to version control
- Use App Passwords instead of your main password
- The `.env` file is already in `.gitignore`

## Example .env file:

```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=hr@yourcompany.com
SENDER_PASSWORD=abcd efgh ijkl mnop
```

Replace the values with your actual email credentials.
