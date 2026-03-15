import os
import shutil
import tempfile
import zipfile

def extract_uploaded_zip(file_content: bytes) -> str:
    """Extracts uploaded zip file content to a temporary directory and returns the path."""
    tmp_dir = tempfile.mkdtemp(prefix="mdp_")
    
    zip_path = os.path.join(tmp_dir, "upload.zip")
    with open(zip_path, "wb") as f:
        f.write(file_content)
        
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)
    except zipfile.BadZipFile:
        shutil.rmtree(tmp_dir)
        raise ValueError("Invalid zip file")
        
    os.remove(zip_path) # remove the zip itself
    return tmp_dir

def find_main_markdown(tmp_dir: str) -> str:
    """Finds the first markdown file in the extracted directory and returns its relative path."""
    for root, dirs, files in os.walk(tmp_dir):
        for f in files:
            if f.lower().endswith('.md'):
                rel_path = os.path.relpath(os.path.join(root, f), tmp_dir)
                # Convert windows separators to posix for URLs
                return rel_path.replace("\\", "/")
    raise FileNotFoundError("No markdown file found in the uploaded zip.")

def cleanup_presentation_files(tmp_path: str):
    """Deletes temporary files associated with a presentation."""
    if tmp_path and os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
