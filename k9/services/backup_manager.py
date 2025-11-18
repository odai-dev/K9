"""
Unified Backup Manager
Coordinates backups across multiple cloud providers (local, Google Drive, Dropbox)
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from flask import current_app

from k9.utils.backup_utils import LocalBackupManager
from k9.services.google_drive_service import GoogleDriveService
from k9.services.dropbox_service import DropboxService
from k9.models.models import BackupSettings, CloudProvider


class BackupManager:
    """Unified manager for multi-cloud backup operations"""
    
    def __init__(self, user_id: str):
        """
        Initialize backup manager
        
        Args:
            user_id: User ID for cloud integrations
        """
        self.user_id = user_id
        self.google_drive = GoogleDriveService(user_id)
        self.dropbox = DropboxService(user_id)
    
    def create_and_distribute_backup(self, include_local: bool = True, 
                                    include_google_drive: bool = True,
                                    include_dropbox: bool = True) -> Dict[str, Any]:
        """
        Create backup and distribute to selected providers
        
        Args:
            include_local: Save to local storage
            include_google_drive: Upload to Google Drive
            include_dropbox: Upload to Dropbox
            
        Returns:
            Dictionary with results for each provider
        """
        results = {
            'success': False,
            'backup_file': None,
            'local': {'enabled': include_local, 'success': False, 'path': None},
            'google_drive': {'enabled': include_google_drive, 'success': False, 'file_id': None},
            'dropbox': {'enabled': include_dropbox, 'success': False, 'path': None},
            'errors': []
        }
        
        try:
            # Create backup file using local backup manager
            current_app.logger.info("Creating backup file...")
            local_backup = LocalBackupManager()
            success, filename, error = local_backup.create_backup(description='', upload_to_drive=False)
            
            if not success:
                results['errors'].append(error or "Failed to create backup file")
                return results
            
            backup_file_path = os.path.join(local_backup.backup_dir, filename)
            results['backup_file'] = backup_file_path
            backup_file_name = filename
            
            # Local storage
            if include_local:
                results['local']['success'] = True
                results['local']['path'] = backup_file_path
                current_app.logger.info(f"Backup saved locally: {backup_file_path}")
            
            # Google Drive upload
            if include_google_drive and self.google_drive.is_connected():
                try:
                    file_id = self.google_drive.upload_file(
                        backup_file_path,
                        backup_file_name,
                        folder_name="K9_Backups"
                    )
                    
                    if file_id:
                        results['google_drive']['success'] = True
                        results['google_drive']['file_id'] = file_id
                        current_app.logger.info(f"Backup uploaded to Google Drive: {file_id}")
                    else:
                        results['errors'].append("Google Drive upload failed")
                        
                except Exception as e:
                    error_msg = f"Google Drive error: {str(e)}"
                    results['errors'].append(error_msg)
                    current_app.logger.error(error_msg)
            elif include_google_drive:
                results['google_drive']['enabled'] = False
                results['errors'].append("Google Drive not connected")
            
            # Dropbox upload
            if include_dropbox and self.dropbox.is_connected():
                try:
                    file_path = self.dropbox.upload_file(
                        backup_file_path,
                        backup_file_name,
                        folder_path="/K9_Backups"
                    )
                    
                    if file_path:
                        results['dropbox']['success'] = True
                        results['dropbox']['path'] = file_path
                        current_app.logger.info(f"Backup uploaded to Dropbox: {file_path}")
                    else:
                        results['errors'].append("Dropbox upload failed")
                        
                except Exception as e:
                    error_msg = f"Dropbox error: {str(e)}"
                    results['errors'].append(error_msg)
                    current_app.logger.error(error_msg)
            elif include_dropbox:
                results['dropbox']['enabled'] = False
                results['errors'].append("Dropbox not connected")
            
            # Overall success if at least one provider succeeded
            results['success'] = (
                results['local']['success'] or 
                results['google_drive']['success'] or 
                results['dropbox']['success']
            )
            
            return results
            
        except Exception as e:
            error_msg = f"Backup creation error: {str(e)}"
            results['errors'].append(error_msg)
            current_app.logger.error(error_msg)
            return results
    
    def get_storage_status(self) -> Dict[str, Any]:
        """
        Get storage quota status for all connected providers
        
        Returns:
            Dictionary with storage info for each provider
        """
        status = {
            'google_drive': {
                'connected': self.google_drive.is_connected(),
                'quota': None
            },
            'dropbox': {
                'connected': self.dropbox.is_connected(),
                'quota': None
            }
        }
        
        # Get Google Drive quota
        if status['google_drive']['connected']:
            try:
                quota = self.google_drive.get_storage_quota()
                if quota:
                    status['google_drive']['quota'] = quota
                    status['google_drive']['quota']['percentage'] = (
                        (quota['used'] / quota['total'] * 100) if quota['total'] > 0 else 0
                    )
            except Exception as e:
                current_app.logger.error(f"Error getting Google Drive quota: {e}")
        
        # Get Dropbox quota
        if status['dropbox']['connected']:
            try:
                quota = self.dropbox.get_storage_quota()
                if quota:
                    status['dropbox']['quota'] = quota
                    status['dropbox']['quota']['percentage'] = (
                        (quota['used'] / quota['allocated'] * 100) if quota['allocated'] > 0 else 0
                    )
            except Exception as e:
                current_app.logger.error(f"Error getting Dropbox quota: {e}")
        
        return status
    
    def list_all_backups(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        List backups from all connected providers
        
        Returns:
            Dictionary with backup lists for each provider
        """
        backups = {
            'local': [],
            'google_drive': [],
            'dropbox': []
        }
        
        # Local backups
        try:
            backup_dir = current_app.config.get('BACKUP_DIR', 'backups')
            if os.path.exists(backup_dir):
                for filename in os.listdir(backup_dir):
                    if filename.endswith('.sql'):
                        file_path = os.path.join(backup_dir, filename)
                        backups['local'].append({
                            'name': filename,
                            'path': file_path,
                            'size': os.path.getsize(file_path),
                            'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                        })
        except Exception as e:
            current_app.logger.error(f"Error listing local backups: {e}")
        
        # Google Drive backups
        if self.google_drive.is_connected():
            try:
                backups['google_drive'] = self.google_drive.list_backups()
            except Exception as e:
                current_app.logger.error(f"Error listing Google Drive backups: {e}")
        
        # Dropbox backups
        if self.dropbox.is_connected():
            try:
                backups['dropbox'] = self.dropbox.list_backups()
            except Exception as e:
                current_app.logger.error(f"Error listing Dropbox backups: {e}")
        
        return backups
    
    def get_connection_status(self) -> Dict[str, bool]:
        """
        Get connection status for all cloud providers
        
        Returns:
            Dictionary with connection status for each provider
        """
        return {
            'google_drive': self.google_drive.is_connected(),
            'dropbox': self.dropbox.is_connected()
        }
    
    def disconnect_provider(self, provider: str) -> bool:
        """
        Disconnect a cloud provider
        
        Args:
            provider: 'google_drive' or 'dropbox'
            
        Returns:
            True if successful
        """
        try:
            if provider == 'google_drive':
                return self.google_drive.disconnect()
            elif provider == 'dropbox':
                return self.dropbox.disconnect()
            else:
                return False
        except Exception as e:
            current_app.logger.error(f"Error disconnecting {provider}: {e}")
            return False
    
    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes to human readable string"""
        size = float(bytes_value)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"
