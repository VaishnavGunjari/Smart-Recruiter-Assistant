import os
import tempfile
from werkzeug.utils import secure_filename
from flask import request
import logging
from typing import Optional
from db_driver import DatabaseDriver

logger = logging.getLogger(__name__)

class FileUploadHandler:
    """Handles file uploads for resume processing with Supabase Storage integration"""
    
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    
    def __init__(self, db_driver: Optional[DatabaseDriver] = None):
        # Use service role for storage operations
        self.db_driver = db_driver or DatabaseDriver(use_service_role=True)
    
    def allowed_file(self, filename: str) -> bool:
        """Check if file type is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def get_file_type(self, filename: str) -> str:
        """Get file extension"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def save_uploaded_file(self, file, candidate_id: str) -> tuple[str, str]:
        """
        Save uploaded file to Supabase Storage and return storage path and type
        Returns: (storage_path, file_type)
        """
        if not file or file.filename == '':
            raise ValueError("No file selected")
        
        if not self.allowed_file(file.filename):
            raise ValueError(f"File type not allowed. Supported types: {', '.join(self.ALLOWED_EXTENSIONS)}")
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset to beginning
        
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {self.MAX_FILE_SIZE // (1024*1024)}MB")
        
        # Secure filename and add timestamp to avoid conflicts
        filename = secure_filename(file.filename)
        file_type = self.get_file_type(filename)
        
        # Read file data
        file_data = file.read()
        
        try:
            # Upload to Supabase Storage
            storage_path = self.db_driver.upload_resume(candidate_id, file_data, filename)
            logger.info(f"File uploaded to Supabase Storage: {storage_path}")
            return storage_path, file_type
            
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {e}")
            raise ValueError(f"Failed to upload file: {str(e)}")
    
    def download_resume_for_processing(self, storage_path: str) -> str:
        """
        Download resume from Supabase Storage to temporary file for processing
        Returns: temporary file path
        """
        try:
            temp_file_path = self.db_driver.download_resume_to_temp(storage_path)
            logger.info(f"Resume downloaded for processing: {temp_file_path}")
            return temp_file_path
            
        except Exception as e:
            logger.error(f"Error downloading resume for processing: {e}")
            raise ValueError(f"Failed to download resume: {str(e)}")
    
    def cleanup_temp_file(self, file_path: str):
        """Clean up temporary file after processing"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Temporary file cleaned up: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up temporary file: {e}")
    
    def delete_resume_from_storage(self, storage_path: str) -> bool:
        """Delete resume from Supabase Storage"""
        try:
            result = self.db_driver.delete_resume(storage_path)
            if result:
                logger.info(f"Resume deleted from storage: {storage_path}")
            return result
        except Exception as e:
            logger.error(f"Error deleting resume from storage: {e}")
            return False