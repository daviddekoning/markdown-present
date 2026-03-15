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
    """Finds the main markdown file in the extracted directory and returns its relative path.
    
    Prefers well-known names (slides.md, deck.md, presentation.md, index.md, main.md)
    at the shallowest level. Falls back to the shallowest, alphabetically first .md file.
    """
    PREFERRED_NAMES = {"slides.md", "deck.md", "presentation.md", "index.md", "main.md"}
    
    all_md = []
    for root, dirs, files in os.walk(tmp_dir):
        dirs.sort()  # Ensure deterministic walk order
        for f in sorted(files):
            if f.lower().endswith('.md'):
                rel_path = os.path.relpath(os.path.join(root, f), tmp_dir)
                # Convert windows separators to posix for URLs
                rel_path = rel_path.replace("\\", "/")
                depth = rel_path.count("/")
                is_preferred = f.lower() in PREFERRED_NAMES
                all_md.append((not is_preferred, depth, rel_path))
    
    if not all_md:
        raise FileNotFoundError("No markdown file found in the uploaded zip.")
    
    all_md.sort()
    return all_md[0][2]

def cleanup_presentation_files(tmp_path: str):
    """Deletes temporary files associated with a presentation."""
    if tmp_path and os.path.exists(tmp_path):
        shutil.rmtree(tmp_path)
