import os
import subprocess
import logging
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional, List, Dict, Tuple
import json

logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, backup_dir: str = 'backups'):
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
    def _parse_database_url(self) -> Dict[str, str]:
        database_url = os.environ.get('DATABASE_URL', '')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        parsed = urlparse(database_url)
        
        return {
            'host': parsed.hostname or 'localhost',
            'port': str(parsed.port or 5432),
            'database': parsed.path.lstrip('/'),
            'username': parsed.username or 'postgres',
            'password': parsed.password or ''
        }
    
    def create_backup(self, description: str = '') -> Tuple[bool, str, Optional[str]]:
        try:
            db_config = self._parse_database_url()
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"k9_backup_{timestamp}.sql"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']
            
            cmd = [
                'pg_dump',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['username'],
                '-d', db_config['database'],
                '-F', 'c',
                '-f', backup_path
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                metadata = {
                    'filename': backup_filename,
                    'timestamp': timestamp,
                    'description': description,
                    'size': os.path.getsize(backup_path),
                    'database': db_config['database']
                }
                
                metadata_path = backup_path + '.meta.json'
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                logger.info(f"Backup created successfully: {backup_filename}")
                return True, backup_filename, None
            else:
                error_msg = f"pg_dump failed: {result.stderr}"
                logger.error(error_msg)
                return False, '', error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Backup timeout after 5 minutes"
            logger.error(error_msg)
            return False, '', error_msg
        except Exception as e:
            error_msg = f"Backup failed: {str(e)}"
            logger.error(error_msg)
            return False, '', error_msg
    
    def restore_backup(self, backup_filename: str) -> Tuple[bool, Optional[str]]:
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return False, f"Backup file not found: {backup_filename}"
            
            db_config = self._parse_database_url()
            
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']
            
            cmd = [
                'pg_restore',
                '-h', db_config['host'],
                '-p', db_config['port'],
                '-U', db_config['username'],
                '-d', db_config['database'],
                '--clean',
                '--if-exists',
                '-F', 'c',
                backup_path
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode == 0:
                logger.info(f"Backup restored successfully: {backup_filename}")
                return True, None
            else:
                error_msg = f"pg_restore failed: {result.stderr}"
                logger.error(error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Restore timeout after 10 minutes"
            logger.error(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Restore failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def list_backups(self) -> List[Dict]:
        backups = []
        
        for filename in os.listdir(self.backup_dir):
            if filename.endswith('.sql'):
                backup_path = os.path.join(self.backup_dir, filename)
                metadata_path = backup_path + '.meta.json'
                
                metadata = {}
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                    except:
                        pass
                
                if not metadata:
                    metadata = {
                        'filename': filename,
                        'timestamp': datetime.fromtimestamp(os.path.getctime(backup_path)).strftime('%Y%m%d_%H%M%S'),
                        'description': '',
                        'size': os.path.getsize(backup_path),
                        'database': 'unknown'
                    }
                
                metadata['path'] = backup_path
                metadata['created_at'] = datetime.fromtimestamp(os.path.getctime(backup_path))
                backups.append(metadata)
        
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return backups
    
    def delete_backup(self, backup_filename: str) -> Tuple[bool, Optional[str]]:
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            metadata_path = backup_path + '.meta.json'
            
            if not os.path.exists(backup_path):
                return False, f"Backup file not found: {backup_filename}"
            
            os.remove(backup_path)
            
            if os.path.exists(metadata_path):
                os.remove(metadata_path)
            
            logger.info(f"Backup deleted successfully: {backup_filename}")
            return True, None
            
        except Exception as e:
            error_msg = f"Delete failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
    
    def cleanup_old_backups(self, retention_days: int = 30) -> int:
        count = 0
        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        
        for backup in self.list_backups():
            if backup['created_at'].timestamp() < cutoff_time:
                success, _ = self.delete_backup(backup['filename'])
                if success:
                    count += 1
        
        logger.info(f"Cleaned up {count} old backups (retention: {retention_days} days)")
        return count


class GoogleDriveBackupManager:
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path
        self.service = None
        
    def initialize(self) -> Tuple[bool, Optional[str]]:
        return False, "Google Drive integration not configured. Please provide service account credentials or OAuth token."
    
    def upload_backup(self, local_path: str, description: str = '') -> Tuple[bool, Optional[str], Optional[str]]:
        return False, None, "Google Drive integration not configured"
    
    def download_backup(self, file_id: str, local_path: str) -> Tuple[bool, Optional[str]]:
        return False, "Google Drive integration not configured"
    
    def list_backups(self) -> List[Dict]:
        return []
    
    def delete_backup(self, file_id: str) -> Tuple[bool, Optional[str]]:
        return False, "Google Drive integration not configured"
