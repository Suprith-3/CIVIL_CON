import logging
from config import supabase

# Use standard logging to avoid "Working outside of application context" error
logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        self.client = supabase

    def upload_document(self, file_path: str, file_content: bytes, mime_type: str):
        """Uploads a file to Supabase Storage."""
        try:
            res = self.client.storage.from_('documents').upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": mime_type, "upsert": "true"}
            )
            return res
        except Exception as e:
            logger.error(f"Supabase Storage upload error: {str(e)}")
            raise e

    def save_metadata(self, data: dict):
        """Saves document metadata to the database."""
        try:
            res = self.client.table('user_documents').insert(data).execute()
            return res.data
        except Exception as e:
            logger.error(f"Supabase Database insert error: {str(e)}")
            raise e

    def get_user_documents(self, user_id: str):
        """Retrieves documents for a specific user."""
        try:
            res = self.client.table('user_documents').select("*").eq('user_id', user_id).execute()
            return res.data
        except Exception as e:
            logger.error(f"Supabase Database query error: {str(e)}")
            return []

    def get_all_documents(self):
        """Admin: Retrieves all uploaded documents."""
        try:
            res = self.client.table('user_documents').select("*").execute()
            return res.data
        except Exception as e:
            logger.error(f"Supabase Admin query error: {str(e)}")
            return []

    def update_status(self, doc_id: int, status: str):
        """Admin: Updates document approval status."""
        try:
            res = self.client.table('user_documents').update({'status': status}).eq('id', doc_id).execute()
            return res.data
        except Exception as e:
            logger.error(f"Supabase update error: {str(e)}")
            raise e

    def create_signed_url(self, file_path: str, expires_in: int = 3600):
        """Generates a secure signed URL for temporary access."""
        try:
            res = self.client.storage.from_('documents').create_signed_url(file_path, expires_in)
            return res.get('signedURL')
        except Exception as e:
            logger.error(f"Supabase Signed URL error: {str(e)}")
            return None
