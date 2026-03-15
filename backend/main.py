from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Set
from pydantic import BaseModel
import uuid
import os
import json

from backend.models import Presentation
from backend.utils import extract_uploaded_zip, find_main_markdown, cleanup_presentation_files

app = FastAPI(title="Markdown Present")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State
presentations: Dict[str, Presentation] = {}
viewers: Dict[str, Set[WebSocket]] = {}
controllers: Dict[str, WebSocket] = {}

# Static mount (for js, css inside frontend)
# We don't mount the root so we can serve index.html explicitly
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")


@app.get("/", response_class=FileResponse)
def index():
    return FileResponse("frontend/index.html")

@app.get("/present/{id}", response_class=FileResponse)
def presenter_view(id: str):
    return FileResponse("frontend/presenter.html")

@app.get("/view/{id}", response_class=FileResponse)
def audience_view(id: str):
    return FileResponse("frontend/audience.html")

@app.post("/api/upload")
async def upload_presentation(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are allowed")

    content = await file.read()
    try:
        tmp_dir = extract_uploaded_zip(content)
        main_md = find_main_markdown(tmp_dir)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    pres_id = str(uuid.uuid4())
    token = str(uuid.uuid4())

    pres = Presentation(
        id=pres_id,
        token=token,
        tmp_path=tmp_dir,
        main_markdown_path=main_md
    )
    presentations[pres_id] = pres
    viewers[pres_id] = set()

    return {"presentation_id": pres_id, "presenter_token": token}

@app.get("/api/presentations/{id}/info")
def get_presentation_info(id: str):
    if id not in presentations:
        raise HTTPException(status_code=404, detail="Presentation not found or ended")
    pres = presentations[id]
    return {
        "id": pres.id,
        "main_markdown_path": pres.main_markdown_path,
        "state": pres.state
    }

@app.get("/api/presentations/{id}/files/{file_path:path}")
def serve_presentation_file(id: str, file_path: str):
    if id not in presentations:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    pres = presentations[id]
    full_path = os.path.normpath(os.path.join(pres.tmp_path, file_path))
    # Prevent path traversal
    if not full_path.startswith(pres.tmp_path):
        raise HTTPException(status_code=403, detail="Forbidden")
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(full_path)

class EndPresentationRequest(BaseModel):
    token: str

@app.post("/api/end/{id}")
async def end_presentation(id: str, req: EndPresentationRequest):
    if id not in presentations:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    pres = presentations[id]
    if pres.token != req.token:
        raise HTTPException(status_code=403, detail="Invalid token")
        
    # Broadcast end to all viewers
    if id in viewers:
        for ws in viewers[id]:
            try:
                await ws.send_text(json.dumps({"action": "ended"}))
            except Exception:
                pass
                
    if id in controllers:
        ws = controllers[id]
        try:
            await ws.send_text(json.dumps({"action": "ended"}))
        except Exception:
            pass

    # Cleanup
    cleanup_presentation_files(pres.tmp_path)
    del presentations[id]
    if id in viewers:
        del viewers[id]
    if id in controllers:
        del controllers[id]
        
    return {"status": "ok"}

@app.websocket("/ws/present/{id}")
async def ws_controller(websocket: WebSocket, id: str, token: str):
    await websocket.accept()
    if id not in presentations:
        await websocket.send_text(json.dumps({"error": "Presentation not found"}))
        await websocket.close()
        return

    pres = presentations[id]
    if pres.token != token:
        await websocket.send_text(json.dumps({"error": "Invalid token"}))
        await websocket.close()
        return

    controllers[id] = websocket
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("action") == "change_slide":
                # msg format: {"action": "change_slide", "state": {"indexh": 0, "indexv": 0, "indexf": 0}, "sequence": 1}
                state = msg.get("state", pres.state)
                sequence = msg.get("sequence", pres.sequence)
                pres.state = state
                pres.sequence = sequence
                
                # broadcast to viewers
                if id in viewers:
                    for ws in viewers[id]:
                        try:
                            await ws.send_text(json.dumps({
                                "action": "slide_changed", 
                                "state": state,
                                "sequence": sequence
                            }))
                        except Exception:
                            pass
    except WebSocketDisconnect:
        if id in controllers and controllers[id] == websocket:
            del controllers[id]

@app.websocket("/ws/view/{id}")
async def ws_viewer(websocket: WebSocket, id: str):
    await websocket.accept()
    if id not in presentations:
        await websocket.send_text(json.dumps({"error": "Presentation not found"}))
        await websocket.close()
        return

    if id not in viewers:
        viewers[id] = set()
    viewers[id].add(websocket)
    
    # Send current state
    pres = presentations[id]
    await websocket.send_text(json.dumps({
        "action": "slide_changed", 
        "state": pres.state,
        "sequence": pres.sequence
    }))

    try:
        while True:
            # We don't expect messages from the viewer, just keep it open
            await websocket.receive_text()
    except WebSocketDisconnect:
        if id in viewers and websocket in viewers[id]:
            viewers[id].remove(websocket)
