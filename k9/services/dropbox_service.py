"""
Dropbox Integration Service
Handles OAuth authentication and file operations with Dropbox
"""

import os
import secrets
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from urllib.parse import urlencode
from flask import current_app
import requests

from app import db
from k9.models.models import UserCloudIntegration, CloudProvider


class DropboxService:
    """Service for Dropbox integration"""
    
    def __init__(self, user_id: str):
        """Initialize Dropbox service for a specific user"""
        self.user_id = user_id
        self.integration = self._get_integration()
    
    def _get_integration(self) -> Optional[UserCloudIntegration]:
        """Get user's Dropbox integration from database"""
        return UserCloudIntegration.query.filter_by(
            user_id=self.user_id,
            provider=CloudProvider.DROPBOX
        ).first()
    
    def is_connected(self) -> bool:
        """Check if user has connected Dropbox"""
        return self.integration is not None and self.integration.access_token is not None
    
    def get_authorization_url(self, redirect_uri: str) -> Tuple[str, str]:
        """
        Get OAuth authorization URL with state parameter for CSRF protection
        
        Args:
            redirect_uri: OAuth callback URL
            
        Returns:
            Tuple of (authorization_url, state) for CSRF protection
        """
        try:
            app_key = self._get_app_key()
            
            # Generate cryptographically strong random state
            state = secrets.token_urlsafe(32)
            
            params = {
                'client_id': app_key,
                'redirect_uri': redirect_uri,
                'response_type': 'code',
                'token_access_type': 'offline',
                'state': state
            }
            
            auth_url = f"https://www.dropbox.com/oauth2/authorize?{urlencode(params)}"
            
            return auth_url, state
            
        except Exception as e:
            current_app.logger.error(f"Error generating Dropbox auth URL: {e}")
            raise
    
    def handle_oauth_callback(self, code: str, redirect_uri: str, state: str) -> bool:
        """
        Handle OAuth callback and store credentials with state validation
        
        Args:
            code: Authorization code from OAuth callback
            redirect_uri: OAuth callback URL
            state: State parameter for CSRF protection (validation done in route)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            app_key = self._get_app_key()
            app_secret = self._get_app_secret()
            
            # Exchange code for tokens
            response = requests.post(
                'https://api.dropboxapi.com/oauth2/token',
                data={
                    'code': code,
                    'grant_type': 'authorization_code',
                    'client_id': app_key,
                    'client_secret': app_secret,
                    'redirect_uri': redirect_uri
                }
            )
            
            if response.status_code != 200:
                current_app.logger.error(f"Dropbox OAuth error: {response.text}")
                return False
            
            data = response.json()
            access_token = data.get('access_token')
            refresh_token = data.get('refresh_token')
            
            # Get user info
            user_info = self._get_user_info(access_token)
            user_email = user_info.get('email') if user_info else None
            
            # Save or update integration
            if self.integration:
                # Preserve existing refresh_token if new one is None
                old_refresh_token = self.integration.refresh_token
                self.integration.access_token = access_token
                self.integration.refresh_token = refresh_token or old_refresh_token
                self.integration.user_email = user_email
                self.integration.updated_at = datetime.utcnow()
            else:
                self.integration = UserCloudIntegration(
                    user_id=self.user_id,
                    provider=CloudProvider.DROPBOX,
                    access_token=access_token,
                    refresh_token=refresh_token,
                    user_email=user_email
                )
                db.session.add(self.integration)
            
            db.session.commit()
            current_app.logger.info(f"Dropbox connected for user {self.user_id}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error handling Dropbox OAuth callback: {e}")
            db.session.rollback()
            return False
    
    def disconnect(self) -> bool:
        """Disconnect Dropbox integration"""
        try:
            if self.integration:
                # Revoke token
                self._revoke_token()
                
                db.session.delete(self.integration)
                db.session.commit()
                current_app.logger.info(f"Dropbox disconnected for user {self.user_id}")
                return True
            return False
        except Exception as e:
            current_app.logger.error(f"Error disconnecting Dropbox: {e}")
            db.session.rollback()
            return False
    
    def _get_app_key(self) -> str:
        """Get Dropbox app key from environment"""
        app_key = os.environ.get('DROPBOX_APP_KEY')
        if not app_key:
            raise ValueError("Dropbox credentials not configured. Set DROPBOX_APP_KEY environment variable.")
        return app_key
    
    def _get_app_secret(self) -> str:
        """Get Dropbox app secret from environment"""
        app_secret = os.environ.get('DROPBOX_APP_SECRET')
        if not app_secret:
            raise ValueError("Dropbox credentials not configured. Set DROPBOX_APP_SECRET environment variable.")
        return app_secret
    
    def _get_access_token(self) -> Optional[str]:
        """Get valid access token, refreshing if necessary"""
        if not self.integration or not self.integration.access_token:
            return None
        
        # Try to refresh if we have refresh token
        if self.integration.refresh_token:
            try:
                app_key = self._get_app_key()
                app_secret = self._get_app_secret()
                
                response = requests.post(
                    'https://api.dropboxapi.com/oauth2/token',
                    data={
                        'grant_type': 'refresh_token',
                        'refresh_token': self.integration.refresh_token,
                        'client_id': app_key,
                        'client_secret': app_secret
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    new_token = data.get('access_token')
                    
                    # Update database
                    self.integration.access_token = new_token
                    self.integration.updated_at = datetime.utcnow()
                    db.session.commit()
                    
                    return new_token
                    
            except Exception as e:
                current_app.logger.error(f"Error refreshing Dropbox token: {e}")
        
        return self.integration.access_token
    
    def _get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Dropbox"""
        try:
            response = requests.post(
                'https://api.dropboxapi.com/2/users/get_current_account',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error getting Dropbox user info: {e}")
            return None
    
    def _revoke_token(self):
        """Revoke access token"""
        try:
            if self.integration and self.integration.access_token:
                requests.post(
                    'https://api.dropboxapi.com/2/auth/token/revoke',
                    headers={'Authorization': f'Bearer {self.integration.access_token}'}
                )
        except Exception as e:
            current_app.logger.error(f"Error revoking Dropbox token: {e}")
    
    def upload_file(self, file_path: str, file_name: str, folder_path: str = "/K9_Backups") -> Optional[str]:
        """
        Upload a file to Dropbox
        
        Args:
            file_path: Local path to file
            file_name: Name for file on Dropbox
            folder_path: Folder path to store file
            
        Returns:
            File path if successful, None otherwise
        """
        try:
            access_token = self._get_access_token()
            if not access_token:
                current_app.logger.error("No valid access token for Dropbox upload")
                return None
            
            # Ensure folder path starts with /
            if not folder_path.startswith('/'):
                folder_path = '/' + folder_path
            
            # Combine folder and file name
            dropbox_path = f"{folder_path}/{file_name}"
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Upload file
            response = requests.post(
                'https://content.dropboxapi.com/2/files/upload',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Dropbox-API-Arg': f'{{"path": "{dropbox_path}", "mode": "add", "autorename": true}}',
                    'Content-Type': 'application/octet-stream'
                },
                data=file_data
            )
            
            if response.status_code == 200:
                result = response.json()
                current_app.logger.info(f"File uploaded to Dropbox: {result.get('name')} ({result.get('path_display')})")
                return result.get('path_display')
            else:
                current_app.logger.error(f"Dropbox upload error: {response.text}")
                return None
            
        except Exception as e:
            current_app.logger.error(f"Error uploading to Dropbox: {e}")
            return None
    
    def get_storage_quota(self) -> Optional[Dict[str, Any]]:
        """
        Get storage quota information
        
        Returns:
            Dict with 'used', 'total', 'allocated' in bytes
        """
        try:
            access_token = self._get_access_token()
            if not access_token:
                return None
            
            response = requests.post(
                'https://api.dropboxapi.com/2/users/get_space_usage',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code == 200:
                data = response.json()
                used = data.get('used', 0)
                allocation = data.get('allocation', {})
                
                # Get allocated space based on account type
                allocated = 0
                if 'allocated' in allocation:
                    allocated = allocation['allocated']
                elif allocation.get('.tag') == 'individual':
                    allocated = allocation.get('individual', {}).get('allocated', 0)
                elif allocation.get('.tag') == 'team':
                    allocated = allocation.get('team', {}).get('allocated', 0)
                
                return {
                    'used': int(used),
                    'total': int(allocated),
                    'allocated': int(allocated)
                }
            
            return None
            
        except Exception as e:
            current_app.logger.error(f"Error getting Dropbox quota: {e}")
            return None
    
    def list_backups(self, folder_path: str = "/K9_Backups") -> List[Dict[str, Any]]:
        """
        List backup files in Dropbox
        
        Returns:
            List of file dictionaries with name, path, size, modified
        """
        try:
            access_token = self._get_access_token()
            if not access_token:
                return []
            
            # Ensure folder path starts with /
            if not folder_path.startswith('/'):
                folder_path = '/' + folder_path
            
            response = requests.post(
                'https://api.dropboxapi.com/2/files/list_folder',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                json={
                    'path': folder_path,
                    'recursive': False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get('entries', [])
                
                files = []
                for entry in entries:
                    if entry.get('.tag') == 'file':
                        files.append({
                            'name': entry.get('name'),
                            'path': entry.get('path_display'),
                            'size': int(entry.get('size', 0)),
                            'modified': entry.get('server_modified')
                        })
                
                return files
            
            return []
            
        except Exception as e:
            current_app.logger.error(f"Error listing Dropbox backups: {e}")
            return []
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from Dropbox"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                return False
            
            response = requests.post(
                'https://api.dropboxapi.com/2/files/delete_v2',
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                },
                json={'path': file_path}
            )
            
            if response.status_code == 200:
                current_app.logger.info(f"File deleted from Dropbox: {file_path}")
                return True
            else:
                current_app.logger.error(f"Dropbox delete error: {response.text}")
                return False
            
        except Exception as e:
            current_app.logger.error(f"Error deleting file from Dropbox: {e}")
            return False
