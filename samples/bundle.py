#!/usr/bin/env uv run
# /// script
# requires-python = ">=3.11"
# ///
import os
import sys
import zipfile

def bundle_samples():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if user specified specific folders
    args = sys.argv[1:]
    
    # Iterate through all subdirectories in the samples folder
    for item in os.listdir(current_dir):
        item_path = os.path.join(current_dir, item)
        
        # We only want to bundle directories (excluding any hidden ones)
        if os.path.isdir(item_path) and not item.startswith('.'):
            # If args were provided and this item isn't in them, skip
            if args and item not in args:
                continue
                
            zip_name = f"{item}.zip"
            zip_path = os.path.join(current_dir, zip_name)
            
            print(f"Bundling {item} into {zip_name}...")
            
            # Create a new zipfile
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk the directory
                for root, _, files in os.walk(item_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # We want the paths in the zip to be relative to the item directory
                        # so that 'deck.md' is at the root of the zip
                        arcname = os.path.relpath(file_path, item_path)
                        zipf.write(file_path, arcname)
                        
            print(f"  Successfully created {zip_name}")

if __name__ == "__main__":
    bundle_samples()
