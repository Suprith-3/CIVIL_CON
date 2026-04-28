import os
import uuid
from datetime import datetime
from config import supabase
from werkzeug.utils import secure_filename

class SupabaseStorageManager:
    def __init__(self):
        self.client = supabase
        # Default buckets
        self.DOCS_BUCKET = 'documents'
        self.MEDIA_BUCKET = 'media'

    def upload_file(self, file_obj, bucket='media', folder=None):
        """
        Uploads a file to Supabase Storage and returns the public URL.
        :param file_obj: Werkzeug FileStorage object
        :param bucket: 'documents' (secure) or 'media' (public)
        :param folder: Optional subfolder path
        """
        if not self.client or not file_obj:
            return None

        try:
            filename = secure_filename(file_obj.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'bin'
            unique_name = f"{uuid.uuid4().hex}.{ext}"
            
            # Construct path
            timestamp = datetime.now().strftime("%Y/%m")
            path = f"{folder}/{timestamp}/{unique_name}" if folder else f"{timestamp}/{unique_name}"

            # Read file content
            file_content = file_obj.read()
            
            # Reset pointer for potential reuse
            file_obj.seek(0)

            # Upload to bucket
            res = self.client.storage.from_(bucket).upload(
                path=path,
                file=file_content,
                file_options={"content-type": file_obj.content_type}
            )

            # Generate Public URL
            url_res = self.client.storage.from_(bucket).get_public_url(path)
            
            # Handle potential Supabase URL structure (ensure it's absolute)
            if hasattr(url_res, 'public_url'):
                return url_res.public_url
            return str(url_res)

        except Exception as e:
            print(f"Cloud Storage Upload Error: {str(e)}")
            return None

    def list_files(self, bucket, folder=None):
        """List files in a bucket/folder"""
        try:
            return self.client.storage.from_(bucket).list(folder)
        except:
            return []

    def delete_file(self, bucket, path):
        """Delete a file from storage"""
        try:
            self.client.storage.from_(bucket).remove([path])
            return True
        except:
            return False

# Global instance for easy import
storage_manager = SupabaseStorageManager()

# Legacy function wrapper for backward compatibility with existing routes
def upload_file_to_supabase(file_obj, bucket='media'):
    return storage_manager.upload_file(file_obj, bucket)
