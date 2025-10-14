import os
import json
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime
import google.auth.transport.requests
import google.oauth2.credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GoogleDriveManager:
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/userinfo.email'
    ]
    
    BACKUP_FOLDER_NAME = 'K9 Database Backups'
    
    def __init__(self, client_secrets_file: Optional[str] = None):
        self.client_secrets_file = client_secrets_file or os.environ.get(
            'GOOGLE_OAUTH_CLIENT_SECRETS',
            'google_client_secrets.json'
        )
    
    def create_oauth_flow(self, redirect_uri: str, state: Optional[str] = None) -> Flow:
        try:
            flow = Flow.from_client_secrets_file(
                self.client_secrets_file,
                scopes=self.SCOPES,
                redirect_uri=redirect_uri
            )
            if state:
                flow.state = state
            return flow
        except FileNotFoundError:
            raise ValueError(
                f"Google OAuth client secrets file not found: {self.client_secrets_file}. "
                "Please configure Google Cloud OAuth credentials first."
            )
    
    def get_authorization_url(self, redirect_uri: str) -> Tuple[str, str]:
        flow = self.create_oauth_flow(redirect_uri)
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return authorization_url, state
    
    def exchange_code_for_credentials(
        self, 
        authorization_response: str, 
        redirect_uri: str, 
        state: str
    ) -> Dict:
        flow = self.create_oauth_flow(redirect_uri, state)
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials
        return self.credentials_to_dict(credentials)
    
    @staticmethod
    def credentials_to_dict(credentials) -> Dict:
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes,
            'expiry': credentials.expiry.isoformat() if credentials.expiry else None
        }
    
    @staticmethod
    def dict_to_credentials(credentials_dict: Dict):
        if 'expiry' in credentials_dict and credentials_dict['expiry']:
            credentials_dict = credentials_dict.copy()
            credentials_dict['expiry'] = datetime.fromisoformat(credentials_dict['expiry'])
        return google.oauth2.credentials.Credentials(**credentials_dict)
    
    def refresh_credentials(self, credentials_dict: Dict) -> Dict:
        credentials = self.dict_to_credentials(credentials_dict)
        
        if credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(google.auth.transport.requests.Request())
                logger.info("Google Drive credentials refreshed successfully")
                return self.credentials_to_dict(credentials)
            except Exception as e:
                logger.error(f"Failed to refresh Google Drive credentials: {e}")
                raise
        
        return credentials_dict
    
    def get_service(self, credentials_dict: Dict):
        credentials = self.dict_to_credentials(credentials_dict)
        
        if credentials.expired and credentials.refresh_token:
            credentials_dict = self.refresh_credentials(credentials_dict)
            credentials = self.dict_to_credentials(credentials_dict)
        
        return build('drive', 'v3', credentials=credentials)
    
    def get_user_info(self, credentials_dict: Dict) -> Optional[Dict]:
        try:
            credentials = self.dict_to_credentials(credentials_dict)
            
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(google.auth.transport.requests.Request())
            
            oauth2_service = build('oauth2', 'v2', credentials=credentials)
            user_info = oauth2_service.userinfo().get().execute()
            
            return {
                'email': user_info.get('email'),
                'name': user_info.get('name'),
                'picture': user_info.get('picture')
            }
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    def find_or_create_backup_folder(self, credentials_dict: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            service = self.get_service(credentials_dict)
            
            query = f"name='{self.BACKUP_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                folder_id = files[0]['id']
                logger.info(f"Found existing backup folder: {folder_id}")
                return True, folder_id, None
            
            folder_metadata = {
                'name': self.BACKUP_FOLDER_NAME,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            folder = service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"Created backup folder: {folder_id}")
            return True, folder_id, None
            
        except HttpError as e:
            error_msg = f"Google Drive API error: {e}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Failed to create backup folder: {e}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def upload_backup(
        self, 
        credentials_dict: Dict, 
        backup_file_path: str, 
        folder_id: str,
        description: str = ''
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        try:
            service = self.get_service(credentials_dict)
            
            file_name = os.path.basename(backup_file_path)
            
            file_metadata = {
                'name': file_name,
                'parents': [folder_id],
                'description': description or f'K9 Database Backup - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
            
            media = MediaFileUpload(
                backup_file_path,
                mimetype='application/x-sql',
                resumable=True
            )
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            
            file_id = file.get('id')
            web_link = file.get('webViewLink')
            
            logger.info(f"Backup uploaded to Google Drive: {file_id} ({file_name})")
            return True, file_id, None
            
        except HttpError as e:
            error_msg = f"Google Drive API error during upload: {e}"
            logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Failed to upload backup to Google Drive: {e}"
            logger.error(error_msg)
            return False, None, error_msg
    
    def revoke_credentials(self, credentials_dict: Dict) -> bool:
        try:
            credentials = self.dict_to_credentials(credentials_dict)
            import requests
            
            response = requests.post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': credentials.token},
                headers={'content-type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                logger.info("Google Drive credentials revoked successfully")
                return True
            else:
                logger.warning(f"Failed to revoke credentials: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error revoking credentials: {e}")
            return False
