import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path so we can import config
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

# Load environment variables from the .env file in the backend directory
load_dotenv(os.path.join(backend_dir, '.env'))

from config import supabase

def create_supabase_buckets():
    if not supabase:
        print("❌ Supabase client not initialized. Check your SUPABASE_URL and SUPABASE_KEY.")
        return

    buckets = [
        {'name': 'media', 'public': True},
        {'name': 'documents', 'public': True} # Change to False if you want private docs
    ]

    for bucket in buckets:
        name = bucket['name']
        is_public = bucket['public']
        
        try:
            # Check if bucket exists
            try:
                supabase.storage.get_bucket(name)
                print(f"✅ Bucket '{name}' already exists.")
            except Exception:
                # Create bucket if it doesn't exist
                print(f"⌛ Creating bucket '{name}'...")
                supabase.storage.create_bucket(name, options={'public': is_public})
                print(f"🎉 Bucket '{name}' created successfully (Public: {is_public}).")
                
        except Exception as e:
            print(f"❌ Error with bucket '{name}': {str(e)}")

if __name__ == "__main__":
    create_supabase_buckets()
