import pytest
import os
import zipfile
import tempfile
from backend.utils import extract_uploaded_zip, find_main_markdown, cleanup_presentation_files

def test_extract_uploaded_zip():
    # Create an in-memory zip
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
        with zipfile.ZipFile(tf.name, 'w') as zf:
            zf.writestr('test.md', '# Hello')
            zf.writestr('img.png', 'fake image bytes')
        tf.flush()
        with open(tf.name, 'rb') as f:
            content = f.read()
    
    os.unlink(tf.name)
    
    tmp_dir = extract_uploaded_zip(content)
    assert os.path.exists(tmp_dir)
    assert os.path.exists(os.path.join(tmp_dir, 'test.md'))
    assert os.path.exists(os.path.join(tmp_dir, 'img.png'))
    cleanup_presentation_files(tmp_dir)
    
def test_invalid_zip():
    with pytest.raises(ValueError, match="Invalid zip file"):
        extract_uploaded_zip(b"not a zip file content")

def test_find_main_markdown():
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test.md")
        with open(test_file, 'w') as f:
            f.write("test")
            
        md_path = find_main_markdown(tmpdir)
        assert md_path == "test.md"

def test_find_main_markdown_nested():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.join(tmpdir, 'nested'))
        test_file = os.path.join(tmpdir, "nested", "test.md")
        with open(test_file, 'w') as f:
            f.write("test")
            
        md_path = find_main_markdown(tmpdir)
        assert md_path in ["nested/test.md", "nested\\test.md"]
        
def test_find_main_markdown_missing():
    with tempfile.TemporaryDirectory() as tmpdir:
        with pytest.raises(FileNotFoundError):
            find_main_markdown(tmpdir)

def test_cleanup_presentation_files():
    tmp_dir = tempfile.mkdtemp()
    assert os.path.exists(tmp_dir)
    cleanup_presentation_files(tmp_dir)
    assert not os.path.exists(tmp_dir)
