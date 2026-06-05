import sys
import os

# Add backend to path to import config
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from config import supabase
    res = supabase.table('worker_bookings').select('*').limit(10).execute()
    print("--- RAW BOOKINGS DATA ---")
    for r in res.data:
        print(r)
    print("-------------------------")
except Exception as e:
    print(f"Error: {e}")
