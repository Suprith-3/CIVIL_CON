import os
import io
import logging
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Use standard logging to avoid "Working outside of application context" error
logger = logging.getLogger(__name__)

class GoogleDriveService:
    def __init__(self, credentials_path: str):
        if not credentials_path or not os.path.exists(credentials_path):
            logger.warning(f"Google credentials file not found at {credentials_path}. Drive backup will be disabled.")
            self.service = None
            return

        try:
            self.credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            self.service = build('drive', 'v3', credentials=self.credentials)
            logger.info("Google Drive service initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {str(e)}")
            self.service = None

    def get_or_create_folder(self, folder_name: str, parent_id: str = None):
        """Finds or creates a folder by name."""
        if not self.service:
            return None

        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        try:
            results = self.service.files().list(q=query, fields="files(id, name)").execute()
            items = results.get('files', [])

            if items:
                return items[0]['id']
            
            # Create folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            return folder.get('id')
        except Exception as e:
            logger.error(f"Google Drive folder error: {str(e)}")
            return None

    def upload_file(self, file_content: bytes, filename: str, mime_type: str, user_id: str):
        """Uploads a file to a user-specific folder in Google Drive."""
        if not self.service:
            raise Exception("Google Drive service not initialized")

        try:
            root_folder_id = self.get_or_create_folder("Documents")
            if not root_folder_id:
                raise Exception("Could not create root Documents folder")

            user_folder_id = self.get_or_create_folder(user_id, root_folder_id)
            if not user_folder_id:
                raise Exception(f"Could not create user folder for {user_id}")

            file_metadata = {
                'name': filename,
                'parents': [user_folder_id]
            }
            media = MediaIoBaseUpload(io.BytesIO(file_content), mimetype=mime_type, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            return file.get('id')
        except Exception as e:
            logger.error(f"Google Drive upload failure: {str(e)}")
            raise e
