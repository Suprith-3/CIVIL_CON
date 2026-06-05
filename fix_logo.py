import shutil
import os

# Paths
source_image = r"C:\Users\supre\.gemini\antigravity\brain\e10cc6a1-8da8-4ee7-8b91-90cce1160247\media__1776704015074.jpg"
destination_dir = r"c:\Users\supre\civilkiss\frontend\img"
destination_file = os.path.join(destination_dir, "logo.jpg")

print("--- CIVIL CONNECTION LOGO FIXER ---")

if not os.path.exists(destination_dir):
    print(f"Creating folder: {destination_dir}")
    os.makedirs(destination_dir)

try:
    shutil.copy(source_image, destination_file)
    print("\n✅ SUCCESS! The logo has been placed in the project.")
    print("Please refresh your browser (F5) to see the change.")
except Exception as e:
    print(f"\n❌ ERROR: Could not copy the file. Details: {e}")
    print("\nPlease try to manually save your logo as: c:\\Users\\supre\\civilkiss\\frontend\\img\\logo.jpg")

input("\nPress Enter to close...")
