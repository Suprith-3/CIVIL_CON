from config import supabase
import os

def create_table():
    sql = """
    CREATE TABLE IF NOT EXISTS renter_registrations (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id),
        name TEXT,
        phone TEXT,
        email TEXT,
        status TEXT DEFAULT 'pending',
        verification_doc_url TEXT,
        location JSONB,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    try:
        # Note: Supabase doesn't allow direct SQL execution via the client library 
        # unless an RPC function is created. 
        # But I can try to insert a dummy record to see if table exists or just proceed.
        print("Table creation script ready.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_table()
