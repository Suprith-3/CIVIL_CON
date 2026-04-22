import shutil
import os

# Source images from the brain directory
images = {
    r"C:\Users\supre\.gemini\antigravity\brain\a7cecc6e-617c-43bd-973e-a1bd559304f1\media__1776816240491.png": "hero-bg.png",
    r"C:\Users\supre\.gemini\antigravity\brain\a7cecc6e-617c-43bd-973e-a1bd559304f1\media__1776816753562.png": "workers.png",
    r"C:\Users\supre\.gemini\antigravity\brain\a7cecc6e-617c-43bd-973e-a1bd559304f1\media__1776816432271.png": "engineers.png",
    r"C:\Users\supre\.gemini\antigravity\brain\a7cecc6e-617c-43bd-973e-a1bd559304f1\media__1776816907868.jpg": "equipment.jpg"
}

destination_dir = r"c:\Users\supre\civilkiss\frontend\img"

print("--- CIVIL CONNECTION IMAGE FIXER ---")

if not os.path.exists(destination_dir):
    print(f"Creating folder: {destination_dir}")
    os.makedirs(destination_dir)

success_count = 0
for src, filename in images.items():
    dest = os.path.join(destination_dir, filename)
    try:
        if os.path.exists(src):
            shutil.copy(src, dest)
            print(f"✅ Copied: {filename}")
            success_count += 1
        else:
            print(f"❌ Source not found: {src}")
    except Exception as e:
        print(f"❌ Error copying {filename}: {e}")

if success_count == len(images):
    print("\n🎉 ALL IMAGES RESTORED!")
else:
    print(f"\n⚠️ {success_count}/{len(images)} images copied. Some might still be missing.")

print("\nPlease refresh your browser (F5) to see the changes.")
input("\nPress Enter to close...")
