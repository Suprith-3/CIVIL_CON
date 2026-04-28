import os
import uuid
from config import supabase, Config
from werkzeug.utils import secure_filename

def upload_file_to_supabase(file, bucket_name="documents"):
    """
    Uploads a file to Supabase Storage and returns the public URL.
    Ensures safe, lifelong storage on cloud rather than ephemeral local disk.
    
    Common buckets:
    - 'documents': For Aadhar, GST, Certifications, etc.
    - 'media': For portfolio images, item photos, profile pics.
    """
    if not file or not file.filename:
        return None
        
    try:
        # 1. Ensure bucket exists
        # In Supabase, if it fails because it exists, we just move on.
        try:
            # Simple check if bucket is accessible
            supabase.storage.get_bucket(bucket_name)
        except:
            try:
                # Attempt to create if it doesn't exist
                supabase.storage.create_bucket(bucket_name, options={'public': True})
            except:
                pass 

        # 2. Generate a unique filename
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # 3. Read file content
        file.seek(0)
        file_content = file.read()
        
        # 4. Upload to Supabase
        # We use unique_filename to ensure no collisions and data integrity over time.
        supabase.storage.from_(bucket_name).upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": file.mimetype or "application/octet-stream"}
        )
        
        # 5. Get public URL
        # The public URL follows a standard format in Supabase
        public_url = f"{Config.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{unique_filename}"
        
        print(f"SUCCESS: Document safely stored in cloud: {public_url}")
        return public_url
    except Exception as e:
        print(f"CRITICAL STORAGE ERROR: {str(e)}")
        return None
