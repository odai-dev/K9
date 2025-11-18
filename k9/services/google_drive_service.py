"""
Google Drive Integration Service
Handles OAuth authentication and file operations with Google Drive
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from flask import url_for, current_app
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from app import db
from k9.models.models import UserCloudIntegration, CloudProvider


class GoogleDriveService:
    """Service for Google Drive integration"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.appdata'
    ]
    
    def __init__(self, user_id: str):
        """Initialize Google Drive service for a specific user"""
        self.user_id = user_id
        self.integration = self._get_integration()
    
    def _get_integration(self) -> Optional[UserCloudIntegration]:
        """Get user's Google Drive integration from database"""
        return UserCloudIntegration.query.filter_by(
            user_id=self.user_id,
            provider=CloudProvider.GOOGLE_DRIVE
        ).first()
    
    def is_connected(self) -> bool:
        """Check if user has connected Google Drive"""
        return self.integration is not None and self.integration.access_token is not None
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """
        Get OAuth authorization URL
        
        Args:
            redirect_uri: OAuth callback URL
            
        Returns:
            Authorization URL for user to visit
        """
        try:
            # Get client config from environment
            client_config = self._get_client_config()
            
            flow = Flow.from_client_config(
                client_config,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return authorization_url
            
        except Exception as e:
            current_app.logger.error(f"Error generating Google Drive auth URL: {e}")
            raise
    
    def handle_oauth_callback(self, code: str, redirect_uri: str) -> bool:
        """
        Handle OAuth callback and store credentials
        
        Args:
            code: Authorization code from OAuth callback
            redirect_uri: OAuth callback URL
            
        Returns:
            True if successful, False otherwise
        """
        try:
            client_config = self._get_client_config()
            
            flow = Flow.from_client_config(
                client_config,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            
            flow.fetch_token(code=code)
            credentials = flow.credentials
            
            # Calculate token expiry
            expires_at = None
            if credentials.expiry:
                expires_at = credentials.expiry
            
            # Save or update integration
            if self.integration:
                self.integration.access_token = credentials.token
                self.integration.refresh_token = credentials.refresh_token
                self.integration.expires_at = expires_at
                self.integration.updated_at = datetime.utcnow()
            else:
                self.integration = UserCloudIntegration(
                    user_id=self.user_id,
                    provider=CloudProvider.GOOGLE_DRIVE,
                    access_token=credentials.token,
                    refresh_token=credentials.refresh_token,
                    expires_at=expires_at
                )
                db.session.add(self.integration)
            
            db.session.commit()
            current_app.logger.info(f"Google Drive connected for user {self.user_id}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error handling Google Drive OAuth callback: {e}")
            db.session.rollback()
            return False
    
    def disconnect(self) -> bool:
        """Disconnect Google Drive integration"""
        try:
            if self.integration:
                db.session.delete(self.integration)
                db.session.commit()
                current_app.logger.info(f"Google Drive disconnected for user {self.user_id}")
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Error disconnecting Google Drive: {e}")
            db.session.rollback()
            return False
    
    def _get_credentials(self) -> Optional[Credentials]:
        """Get valid credentials, refreshing if necessary"""
        if not self.integration or not self.integration.access_token:
            return None
        
        credentials = Credentials(
            token=self.integration.access_token,
            refresh_token=self.integration.refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=os.environ.get('GOOGLE_CLIENT_ID'),
            client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
            scopes=self.SCOPES
        )
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            try:
                from google.auth.transport.requests import Request
                credentials.refresh(Request())
                
                # Update database
                self.integration.access_token = credentials.token
                self.integration.expires_at = credentials.expiry
                self.integration.updated_at = datetime.utcnow()
                db.session.commit()
                
            except Exception as e:
                current_app.logger.error(f"Error refreshing Google Drive token: {e}")
                return None
        
        return credentials
    
    def _get_client_config(self) -> Dict[str, Any]:
        """Get OAuth client configuration from environment"""
        client_id = os.environ.get('GOOGLE_CLIENT_ID')
        client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError("Google Drive credentials not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.")
        
        return {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        }
    
    def upload_file(self, file_path: str, file_name: str, folder_name: str = "K9_Backups") -> Optional[str]:
        """
        Upload a file to Google Drive
        
        Args:
            file_path: Local path to file
            file_name: Name for file on Drive
            folder_name: Folder name to store file
            
        Returns:
            File ID if successful, None otherwise
        """
        try:
            credentials = self._get_credentials()
            if not credentials:
                current_app.logger.error("No valid credentials for Google Drive upload")
                return None
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Find or create folder
            folder_id = self._find_or_create_folder(service, folder_name)
            
            # Upload file
            file_metadata = {
                'name': file_name,
                'parents': [folder_id] if folder_id else []
            }
            
            media = MediaFileUpload(file_path, resumable=True)
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, size, createdTime'
            ).execute()
            
            current_app.logger.info(f"File uploaded to Google Drive: {file.get('name')} ({file.get('id')})")
            return file.get('id')
            
        except HttpError as e:
            current_app.logger.error(f"Google Drive API error: {e}")
            return None
        except Exception as e:
            current_app.logger.error(f"Error uploading to Google Drive: {e}")
            return None
    
    def _find_or_create_folder(self, service, folder_name: str) -> Optional[str]:
        """Find existing folder or create new one"""
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                return folders[0]['id']
            
            # Create folder if not found
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            return folder.get('id')
            
        except Exception as e:
            current_app.logger.error(f"Error finding/creating folder: {e}")
            return None
    
    def get_storage_quota(self) -> Optional[Dict[str, Any]]:
        """
        Get storage quota information
        
        Returns:
            Dict with 'used', 'total', 'limit' in bytes
        """
        try:
            credentials = self._get_credentials()
            if not credentials:
                return None
            
            service = build('drive', 'v3', credentials=credentials)
            
            about = service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            
            return {
                'used': int(quota.get('usage', 0)),
                'total': int(quota.get('limit', 0)),
                'limit': int(quota.get('limit', 0))
            }
            
        except Exception as e:
            current_app.logger.error(f"Error getting Google Drive quota: {e}")
            return None
    
    def list_backups(self, folder_name: str = "K9_Backups") -> List[Dict[str, Any]]:
        """
        List backup files in Drive
        
        Returns:
            List of file dictionaries with name, id, size, created_time
        """
        try:
            credentials = self._get_credentials()
            if not credentials:
                return []
            
            service = build('drive', 'v3', credentials=credentials)
            
            # Find folder
            folder_id = self._find_or_create_folder(service, folder_name)
            if not folder_id:
                return []
            
            # List files in folder
            query = f"'{folder_id}' in parents and trashed=false"
            results = service.files().list(
                q=query,
                fields='files(id, name, size, createdTime)',
                orderBy='createdTime desc'
            ).execute()
            
            files = results.get('files', [])
            
            return [{
                'id': f['id'],
                'name': f['name'],
                'size': int(f.get('size', 0)),
                'created_time': f.get('createdTime')
            } for f in files]
            
        except Exception as e:
            current_app.logger.error(f"Error listing Google Drive backups: {e}")
            return []
    
    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive"""
        try:
            credentials = self._get_credentials()
            if not credentials:
                return False
            
            service = build('drive', 'v3', credentials=credentials)
            service.files().delete(fileId=file_id).execute()
            
            current_app.logger.info(f"File deleted from Google Drive: {file_id}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error deleting file from Google Drive: {e}")
            return False
