from fastapi.testclient import TestClient
import zipfile
import tempfile
import os

from backend.main import app, presentations, viewers, controllers

client = TestClient(app)

def teardown_module(module):
    # End all presentations to clean up tmp dirs
    for p in list(presentations.keys()):
        from backend.utils import cleanup_presentation_files
        cleanup_presentation_files(presentations[p].tmp_path)
    presentations.clear()
    viewers.clear()
    controllers.clear()

def create_test_zip_content():
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tf:
        with zipfile.ZipFile(tf.name, 'w') as zf:
            zf.writestr('deck.md', '# Slide 1')
            zf.writestr('image.png', 'fake image bytes')
        tf.flush()
        with open(tf.name, 'rb') as f:
            content = f.read()
    os.unlink(tf.name)
    return content

def test_static_routes():
    res = client.get("/")
    assert res.status_code == 200
    assert "Markdown Present" in res.text

    res = client.get("/present/123")
    assert res.status_code == 200
    assert "Presenter View" in res.text

    res = client.get("/view/123")
    assert res.status_code == 200
    assert "Audience View" in res.text

def test_upload_presentation():
    content = create_test_zip_content()
    res = client.post("/api/upload", files={"file": ("test.zip", content, "application/zip")})
    assert res.status_code == 200
    data = res.json()
    assert "presentation_id" in data
    assert "presenter_token" in data
    
    pres_id = data["presentation_id"]
    token = data["presenter_token"]
    
    assert pres_id in presentations
    assert presentations[pres_id].token == token
    assert presentations[pres_id].main_markdown_path == "deck.md"

def test_upload_invalid_file_extension():
    res = client.post("/api/upload", files={"file": ("test.txt", b"dummy", "text/plain")})
    assert res.status_code == 400

def test_presentation_info():
    content = create_test_zip_content()
    res = client.post("/api/upload", files={"file": ("test.zip", content, "application/zip")})
    pres_id = res.json()["presentation_id"]
    
    res_info = client.get(f"/api/presentations/{pres_id}/info")
    assert res_info.status_code == 200
    assert res_info.json()["main_markdown_path"] == "deck.md"
    assert "state" in res_info.json()
    
def test_static_files_serve():
    content = create_test_zip_content()
    res = client.post("/api/upload", files={"file": ("test.zip", content, "application/zip")})
    pres_id = res.json()["presentation_id"]
    
    res_file = client.get(f"/api/presentations/{pres_id}/files/deck.md")
    assert res_file.status_code == 200
    assert "# Slide 1" in res_file.text
    
def test_serve_missing_file():
    content = create_test_zip_content()
    res = client.post("/api/upload", files={"file": ("test.zip", content, "application/zip")})
    pres_id = res.json()["presentation_id"]
    
    res_file = client.get(f"/api/presentations/{pres_id}/files/missing.md")
    assert res_file.status_code == 404

def test_serve_path_traversal():
    content = create_test_zip_content()
    res = client.post("/api/upload", files={"file": ("test.zip", content, "application/zip")})
    pres_id = res.json()["presentation_id"]
    
    res_file = client.get(f"/api/presentations/{pres_id}/files/../../etc/passwd")
    assert res_file.status_code == 403
    
def test_websockets_and_end_presentation():
    content = create_test_zip_content()
    res = client.post("/api/upload", files={"file": ("test.zip", content, "application/zip")})
    data = res.json()
    pres_id = data["presentation_id"]
    token = data["presenter_token"]
    
    with client.websocket_connect(f"/ws/view/{pres_id}") as viewer_ws:
        msg = viewer_ws.receive_json()
        assert msg["action"] == "slide_changed"
        
        with client.websocket_connect(f"/ws/present/{pres_id}?token={token}") as controller_ws:
            controller_ws.send_json({"action": "change_slide", "state": {"indexh": 1, "indexv": 0, "indexf": 0}})
            
            msg = viewer_ws.receive_json()
            assert msg["action"] == "slide_changed"
            assert msg["state"]["indexh"] == 1
            
            # Test End
            end_res = client.post(f"/api/end/{pres_id}", json={"token": token})
            assert end_res.status_code == 200
            
            end_msg = viewer_ws.receive_json()
            assert end_msg["action"] == "ended"

            assert pres_id not in presentations
