# Architecture: Markdown Present

## Overview
Markdown Present is a web application that allows users to upload a zipped presentation (Markdown files + assets) and present it in real-time to an audience. The application has a FastAPI backend and a pure HTML/JS/Vanilla CSS frontend. It is designed to be stateless and deployed on Fly.io without external persistent storage.

## Backend (FastAPI)
The backend is responsible for:
1. **Handling Uploads**: Receiving the zip file from the presenter.
2. **Ephemeral Storage**: Extracting the zip file to a temporary directory on the server's ephemeral filesystem to serve the markdown and assets (e.g., images) as static files.
3. **State Management**: Managing the current state of active presentations in memory (e.g., a dictionary mapping a unique presentation ID to its current slide index and temporary directory path).
4. **Real-time Synchronization**: Using **WebSockets** to synchronize the current slide between the presenter and the connected audience members.
5. **Session Cleanup**: Providing an endpoint to "End Presentation" which deletes the temporary files and removes the presentation from the in-memory state.

*Note on Fly.io Deployment*: Since the app relies on in-memory state and ephemeral disk storage, it must be deployed as a single instance, or use sticky sessions (Fly-Replay) to route requests for a specific presentation to the correct instance. For the first version, we will rely on a single instance.

## Frontend (Pure HTML/JS/CSS)
The frontend uses vanilla web technologies without a heavy framework like React.

### Core Libraries
- **Reveal.js**: For parsing Markdown into beautifully rendered, interactive slides. It natively handles keyboard navigation, grid (overview) view, and provides a JavaScript API.
- **LocalForage / IndexedDB API**: To store the last 3 uploaded zip files in the browser. `localStorage` has a ~5MB limit which is easily exceeded by presentations with images, so `IndexedDB` is necessary to store the files locally.

### Views / Pages
1. **Home / Upload View (`/`)**:
   - UI to upload a `.zip` file.
   - UI to select from the last 3 presentations (loaded from IndexedDB).
   - Once a presentation is selected/uploaded, it is sent to the backend, which returns a unique presentation ID and presenter token. The user is redirected to the Presenter View.

2. **Presenter View (`/present/{id}?token={token}`)**:
   - Initializes Reveal.js with the fetched Markdown.
   - Reveal.js natively handles "Prev" and "Next" navigation and the 'Overview/Grid' mode.
   - A copyable URL for the Audience View.
   - Toggle for Dark/Light mode (using Reveal.js themes or custom CSS).
   - "End Presentation" button which notifies the server to tear down the session and redirects to Home.
   - Connects to the server via WebSocket as the "controller". Listens to `slidechanged` events from Reveal.js to broadcast the current slide index.

3. **Audience View (`/view/{id}`)**:
   - Initializes Reveal.js with the fetched Markdown (configurable to disable keyboard navigation and controls if desired).
   - Connects to the server via WebSocket as a "listener".
   - Receives the current slide index from the server and updates Reveal.js via its API (e.g., `Reveal.slide()`).
   - Toggle for Dark/Light mode (using Reveal.js themes).
   - Automatically updates when the presenter changes the slide or ends the presentation.

## Data Flow
1. **Upload**: User uploads `deck.zip` -> Client saves to IndexedDB -> Client posts `deck.zip` to `/api/upload` -> Server extracts to `/tmp/{uuid}` and returns `{ presentation_id, presenter_token }`.
2. **Present**: Presenter navigates to `/present/{id}?token={token}` -> Opens WebSocket to `/ws/present/{id}?token={token}` -> Sends `{"action": "change_slide", "slide": 2}`.
3. **View**: Audience navigates to `/view/{id}` -> Opens WebSocket to `/ws/view/{id}` -> Receives `{"action": "slide_changed", "slide": 2}` -> Client updates UI.
4. **End**: Presenter clicks End -> Sends request to `/api/end/{id}` -> Server deletes `/tmp/{uuid}`, broadcasts `{"action": "ended"}` to all WebSockets, and closes connections.

## Directory Structure
```
.
├── backend/
│   ├── main.py            # FastAPI application and WebSocket handlers
│   ├── models.py          # Data models
│   └── utils.py           # Zip extraction and cleanup helpers
├── frontend/
│   ├── index.html         # Upload/Home view
│   ├── presenter.html     # Presenter view
│   ├── audience.html      # Audience view
│   ├── css/
│   │   └── style.css      # Shared styles, custom Reveal.js overrides
│   └── js/
│       ├── upload.js      # Handles file upload and IndexedDB storage
│       ├── presenter.js   # Presenter logic, Reveal.js init, and WS controller
│       └── audience.js    # Audience logic, Reveal.js init, and WS listener
├── pyproject.toml         # Python dependencies (managed via uv)
└── fly.toml               # Fly.io configuration
```

## Local Development
To run this application locally during development:
1. Ensure `uv` is installed.
2. Install dependencies (e.g., `uv add fastapi uvicorn python-multipart`).
3. Run the development server using `uv run uvicorn backend.main:app --reload` (or `fastapi dev backend/main.py`).
4. The server will be available at `http://localhost:8000`.
