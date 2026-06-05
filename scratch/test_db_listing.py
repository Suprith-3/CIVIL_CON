import sys
import os

# Add backend to path to import config
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from config import supabase
    import uuid

    user_id = "69052d3d-4bf9-4432-a13f-d8689fee0ff6" # User ID from logs

    test_item = {
        'shopkeeper_id': user_id,
        'name': "AGENT TEST PRODUCT",
        'description': "Created by AI to verify database persistence",
        'category': "Steel",
        'price': 999.00,
        'item_type': "buy",
        'stock': 1,
        'image_url': "https://placehold.co/400x300?text=Agent+Success",
        'is_active': True
    }

    print(f"Creating test item for user {user_id}...")
    res = supabase.table('items').insert(test_item).execute()

    if res.data:
        print("✅ SUCCESS: Item inserted into Supabase!")
        print(f"Item ID: {res.data[0]['id']}")
    else:
        print("❌ FAILED: Database accepted request but returned no data.")

except Exception as e:
    print(f"❌ CRITICAL ERROR: {str(e)}")
