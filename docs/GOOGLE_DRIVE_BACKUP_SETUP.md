# Google Drive Backup Integration Setup Guide

This guide explains how to configure Google Drive OAuth 2.0 authentication for the K9 Operations Management System backup feature.

## Overview

The Google Drive integration allows the system to automatically upload database backups to a dedicated folder in Google Drive. This provides an additional layer of backup redundancy in the cloud.

## Prerequisites

- Google account with access to Google Cloud Console
- Admin access to the K9 Operations Management System
- Basic understanding of OAuth 2.0 (helpful but not required)

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click "New Project"
4. Enter a project name (e.g., "K9 Backup System")
5. Click "Create"
6. Wait for the project to be created and select it

## Step 2: Enable Google Drive API

1. In the Google Cloud Console, navigate to "APIs & Services" > "Library"
2. Search for "Google Drive API"
3. Click on "Google Drive API"
4. Click "Enable"
5. Wait for the API to be enabled

## Step 3: Configure OAuth Consent Screen

1. Navigate to "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (or "Internal" if using Google Workspace)
3. Click "Create"
4. Fill in the required fields:
   - **App name**: K9 Backup System
   - **User support email**: Your email address
   - **Developer contact email**: Your email address
5. Click "Save and Continue"
6. On the "Scopes" page, click "Add or Remove Scopes"
7. Add the following scopes:
   - `https://www.googleapis.com/auth/drive.file` (Create, edit, and delete files)
   - `https://www.googleapis.com/auth/userinfo.email` (See your email address)
8. Click "Update" then "Save and Continue"
9. On the "Test users" page (for External apps):
   - Click "Add Users"
   - Add the email addresses of admin users who will use the backup feature
   - Click "Save and Continue"
10. Review the summary and click "Back to Dashboard"

## Step 4: Create OAuth 2.0 Credentials

1. Navigate to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. Select "Web application" as the application type
4. Enter a name (e.g., "K9 Backup OAuth Client")
5. Under "Authorized redirect URIs", add your callback URL:
   - For development: `http://localhost:5000/admin/google-drive/callback`
   - For production: `https://yourdomain.com/admin/google-drive/callback`
   - **Important**: Replace `yourdomain.com` with your actual domain
   - You can add multiple URIs for different environments
6. Click "Create"
7. A dialog will appear with your Client ID and Client Secret
8. Click "Download JSON" to download the credentials file
9. Click "OK" to close the dialog

## Step 5: Configure K9 System

### Option A: Using Environment Variable (Recommended for Production)

1. Rename the downloaded JSON file to `google_client_secrets.json`
2. Place it in a secure location accessible to your application
3. Set the environment variable:
   ```bash
   export GOOGLE_OAUTH_CLIENT_SECRETS=/path/to/google_client_secrets.json
   ```
4. Restart the application

### Option B: Using Default Location (Development)

1. Rename the downloaded JSON file to `google_client_secrets.json`
2. Place it in the root directory of the K9 application (same level as `app.py`)
3. Restart the application

## Step 6: Connect Google Drive in K9 System

1. Log in to the K9 system as an admin
2. Navigate to "Admin Panel" > "Backup Management"
3. In the "Google Drive" section, click "Connect to Google Drive"
4. You will be redirected to Google's OAuth consent screen
5. Select the Google account you want to use for backups
6. Review the permissions and click "Allow"
7. You will be redirected back to the Backup Management page
8. You should see a success message with your connected email

## Step 7: Verify Integration

1. Create a manual backup by clicking "Create New Backup"
2. Check the logs to confirm the backup was uploaded to Google Drive
3. Visit [Google Drive](https://drive.google.com)
4. Look for a folder named "K9 Database Backups"
5. Verify that your backup file is present

## Troubleshooting

### Error: "Client secrets file not found"

**Solution**: Ensure the `google_client_secrets.json` file is in the correct location and the path is properly configured.

### Error: "Access blocked: This app's request is invalid"

**Solution**: 
- Verify that all redirect URIs are correctly configured in Google Cloud Console
- Ensure the redirect URI in the OAuth consent screen matches exactly (including `http` vs `https`)
- Check that your domain is properly configured

### Error: "This app isn't verified"

**Solution**: 
- For development: Click "Advanced" > "Go to K9 Backup System (unsafe)"
- For production: Complete the Google verification process in the OAuth consent screen settings

### Error: "The user is not authorized to access this app"

**Solution**: 
- If using External user type, ensure the user is added to the "Test users" list in OAuth consent screen
- If using Internal user type, ensure the user is part of your Google Workspace organization

### Token Expired or Invalid

**Solution**: The system automatically refreshes tokens. If this fails:
1. Disconnect Google Drive in the Backup Management page
2. Reconnect by clicking "Connect to Google Drive"
3. Re-authorize the application

## Security Best Practices

1. **Protect Client Secrets**: Never commit `google_client_secrets.json` to version control
   - Add it to `.gitignore`
   - Use environment variables in production

2. **Limit Access**: Only grant admin users access to the backup management page

3. **Regular Audits**: Periodically review connected accounts in Google Cloud Console

4. **Least Privilege**: The system only requests the minimum required scopes:
   - `drive.file`: Access only to files created by the app
   - `userinfo.email`: Display user's email for verification

5. **Credential Storage Security**: 
   - **Important**: OAuth credentials (including refresh tokens) are currently stored as JSON in the database
   - **Production Recommendation**: Implement database encryption at rest for the `backup_settings` table
   - Consider using environment variable encryption or a secrets management service (e.g., HashiCorp Vault, AWS Secrets Manager)
   - Regularly rotate Google OAuth credentials if a database breach occurs
   - Limit database access to only necessary personnel

6. **Database Security**: 
   - Ensure PostgreSQL is not exposed to the public internet
   - Use strong passwords for database accounts
   - Enable SSL/TLS for database connections
   - Implement regular database backups (ironically, backup your backups!)

## Production Deployment Checklist

- [ ] OAuth consent screen configured with production domain
- [ ] Redirect URIs updated with production URL (`https://yourdomain.com/admin/google-drive/callback`)
- [ ] Client secrets file secured and not in version control
- [ ] Environment variable `GOOGLE_OAUTH_CLIENT_SECRETS` set correctly
- [ ] HTTPS enabled for production (required for OAuth)
- [ ] Test users added (for External apps) or organization verified (for Internal apps)
- [ ] Backup to Google Drive tested and verified
- [ ] Automated backup schedule configured

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Drive API Reference](https://developers.google.com/drive/api/v3/reference)
- [OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)

## Support

If you encounter issues not covered in this guide:
1. Check the application logs for detailed error messages
2. Review the Google Cloud Console audit logs
3. Verify all configuration steps were completed correctly
4. Contact your system administrator for assistance
