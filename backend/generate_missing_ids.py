import os
import random
from config import supabase

def generate_ids():
    print("--- CIVIL CONNECTION ID FIXER ---")
    try:
        # Fetch all approved workers who are missing a worker_code
        res = supabase.table('worker_registrations').select('id, name').eq('status', 'approved').is_('worker_code', 'null').execute()
        
        workers = res.data
        if not workers:
            print("✅ No missing IDs found! All approved workers have codes.")
            return

        print(f"Found {len(workers)} approved workers missing IDs. Generating now...")
        
        for w in workers:
            new_id = f"WRK-{random.randint(1000, 9999)}"
            supabase.table('worker_registrations').update({'worker_code': new_id}).eq('id', w['id']).execute()
            print(f"  - Generated {new_id} for {w['name']}")
            
        print("✅ SUCCESS! All workers now have unique IDs.")
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

if __name__ == "__main__":
    generate_ids()
