# Markdown Present

A lightweight, real-time presentation tool that turns standard Markdown into synchronized HTML slides. Perfect for presenters who want to write presentations fast and share them without the hassle of PDFs, screensharing lag, or clunky external websites.

## Features

- **Upload & Play**: Package your `.md` file alongside any assets (like images) in a `.zip` file—and drag and drop it directly onto the site!
- **Real-Time Sync**: Presenter slide navigation (next/prev) broadcasts via WebSockets directly to anyone with the audience link with barely any latency.
- **Presenter Controls**: Access a beautiful presentation view utilizing Reveal.js. Hit 'G' or click the controls button to toggle the visual Overview Mode. 
- **Standalone and Ephemeral**: Uses LocalForage / IndexedDB caching to keep presentation history entirely within the user's browser securely, while the server runs fully statelessly.
- **Dark/Light Mode**: Smooth, customizable dark/light theme switching.

---

## Getting Started

### Prerequisites

We use `uv` for python dependency mapping and testing. Download `uv` if you haven't already.

### Installation

Clone the repository and install all packages:
```bash
uv add fastapi uvicorn python-multipart websockets
```

### Running Locally

Fire up the local live server via Uvicorn:
```bash
uv run uvicorn backend.main:app --reload
```

Then visit `http://localhost:8000` in your web browser!

---

## Testing out the App: Bundling Presentations

Markdown Present accepts `.zip` files containing your slides markdown and assets. There is a convenient helper script provided to bundle sample presentations locally.

```bash
# To zip up all samples:
./samples/bundle.py

# Or to bundle a specific folder inside the /samples dir:
./samples/bundle.py with_images
```

This will create a `.zip` artifact inside the `samples/` directory which you can upload into the app's home screen.

---

## Development & Testing

Tests are written using `pytest`. They cover API endpoint logic, Zip handling, File Extractions, and WebSocket syncing.
To run the coverage suite:

```bash
uv add --dev pytest pytest-cov httpx
uv run pytest --cov=backend
```

### Architecture

All tech stack choices, file definitions, and server constraints are available extensively inside [`architecture.md`](./architecture.md).
