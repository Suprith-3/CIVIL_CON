import os
from supabase import create_client, Client
from flask import current_app
import requests

class SupabaseService:
    def __init__(self, url: str, key: str):
        self.supabase: Client = create_client(url, key)

    def upload_file(self, bucket_name: str, file_path: str, file_body, content_type: str):
        """Uploads a file to Supabase Storage."""
        try:
            # Check if file exists to overwrite if needed or handle duplicates
            # For this requirement, we use the path documents/{user_id}/{filename}
            res = self.supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=file_body,
                file_options={"content-type": content_type, "upsert": "true"}
            )
            return res
        except Exception as e:
            current_app.logger.error(f"Supabase upload error: {str(e)}")
            raise e

    def get_signed_url(self, bucket_name: str, file_path: str, expires_in: int = 3600):
        """Generates a signed URL for a private file."""
        try:
            res = self.supabase.storage.from_(bucket_name).create_signed_url(file_path, expires_in)
            return res.get('signedURL')
        except Exception as e:
            current_app.logger.error(f"Supabase signed URL error: {str(e)}")
            raise e

    def insert_metadata(self, table_name: str, data: dict):
        """Inserts file metadata into the database."""
        try:
            res = self.supabase.table(table_name).insert(data).execute()
            return res.data
        except Exception as e:
            current_app.logger.error(f"Supabase database error: {str(e)}")
            raise e

    def update_metadata(self, table_name: str, record_id: str, data: dict):
        """Updates file metadata status/backup info."""
        try:
            res = self.supabase.table(table_name).update(data).eq('id', record_id).execute()
            return res.data
        except Exception as e:
            current_app.logger.error(f"Supabase update error: {str(e)}")
            raise e

    def get_all_documents(self, table_name: str):
        """Fetches all document records for admin."""
        try:
            res = self.supabase.table(table_name).select("*").order('uploaded_at', desc=True).execute()
            return res.data
        except Exception as e:
            current_app.logger.error(f"Supabase fetch error: {str(e)}")
            raise e

    def get_document_by_id(self, table_name: str, doc_id: str):
        """Fetches a single document record."""
        try:
            res = self.supabase.table(table_name).select("*").eq('id', doc_id).single().execute()
            return res.data
        except Exception as e:
            current_app.logger.error(f"Supabase fetch error: {str(e)}")
            raise e
