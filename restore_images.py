import shutil
import os

brain_dir = r"C:\Users\supre\ .gemini\antigravity\brain\7f044edf-01c9-4cc2-9f9f-97690ed2faca"
# Note: I'll use the correct path without the space if possible, or just the absolute paths found in list_dir
target_dir = r"c:\Users\supre\civilkiss\frontend\assets\images"

# Mapping based on typical order
images = [
    ("media__1776865029833.jpg", "workers_site.jpg"),
    ("media__1776865030194.jpg", "building_structure.jpg"),
    ("media__1776865030306.jpg", "engineer_plans.jpg"),
    ("media__1776865030329.jpg", "construction_sign.jpg"),
    ("media__1776865030440.jpg", "crane.jpg")
]

if not os.path.exists(target_dir):
    os.makedirs(target_dir)

for src_name, dest_name in images:
    src_path = os.path.join(brain_dir.strip(), src_name)
    dest_path = os.path.join(target_dir, dest_name)
    try:
        shutil.copy(src_path, dest_path)
        print(f"Copied {src_name} to {dest_name}")
    except Exception as e:
        print(f"Error copying {src_name}: {e}")
