# Pipeline Conversion Engine — Electron Desktop App

Electron desktop app wrapping the Alteryx/Fabric to Python/SQL converter. React frontend + FastAPI backend, packaged for offline desktop use.

## Architecture

```
electron/          Electron shell (main process, preload bridge)
frontend/          React + TypeScript + Vite + Tailwind
code/              Python business logic (parsers, generators)
api.py             FastAPI backend (dynamic port)
build-*.bat        Build scripts (Windows)
build-*.sh         Build scripts (macOS)
```

- **Electron main process** spawns the Python backend, polls `/api/health`, then loads the React frontend.
- **Frontend** communicates with the backend via `http://127.0.0.1:9721` (Electron) or Vite proxy (dev).
- **Packaged app** bundles the Python backend as a PyInstaller exe and the frontend as static files.

## Development (3 terminals)

**Terminal 1 — Backend:**
```bash
cd LLM_ALTERYX_PARSE_REACT
pip install -r requirements.txt
uvicorn api:app --reload --port 9721
```

**Terminal 2 — Frontend:**
```bash
cd LLM_ALTERYX_PARSE_REACT/frontend
npm install
npm run dev
# → http://localhost:5200
```

**Terminal 3 — Electron (optional, for testing the desktop shell):**
```bash
cd LLM_ALTERYX_PARSE_REACT/electron
npm install
npx electron .
```

## Build & Package (Production)

### Windows

Run the full pipeline:
```bash
cd LLM_ALTERYX_PARSE_REACT
build-all.bat
```

Or build each layer individually:
```bash
build-frontend.bat    # → frontend/dist/
build-backend.bat     # → dist-backend/api/api.exe
build-electron.bat    # → dist-electron/win-unpacked/
```

### macOS

> **Important:** The macOS build must be run on a Mac. PyInstaller cannot cross-compile from Windows to macOS.

```bash
cd LLM_ALTERYX_PARSE_REACT

# Make scripts executable (first time only)
chmod +x build-all.sh build-backend.sh build-frontend.sh build-electron.sh

# Full build (frontend + backend + Electron)
./build-all.sh
```

Or build each layer individually:
```bash
./build-frontend.sh    # → frontend/dist/
./build-backend.sh     # → dist-backend/api/api (macOS binary)
./build-electron.sh    # → dist-electron/mac-arm64/ or dist-electron/mac/
```

### Prerequisites

- Node.js 18+
- Python 3.10+ with PyInstaller (`pip install pyinstaller`)
- All Python dependencies (`pip install -r requirements.txt`)

## Distribution

### Windows
Copy the entire `dist-electron/win-unpacked/` folder to a shared location (SharePoint, network drive, USB). Users launch `Pipeline Conversion Engine.exe` directly — no install required.

### macOS
Compress the `.app` bundle from `dist-electron/mac-arm64/` (Apple Silicon) or `dist-electron/mac/` (Intel) into a `.zip` file and share it. Users unzip and double-click `Pipeline Conversion Engine.app`.

If macOS shows "App can't be opened because it is from an unidentified developer", right-click the app and select **Open**, then confirm. Alternatively, run:
```bash
xattr -cr "Pipeline Conversion Engine.app"
```

### What must be inside the packaged app

PyInstaller **onedir** output must include **both**:

- **`api.exe`** (Windows) or **`api`** (macOS) — the launcher next to `_internal`
- **`_internal/`** — dependencies

Inside the built Electron app, that lives under:

- **Windows:** `win-unpacked/resources/backend/api/`
- **macOS:** `Something.app/Contents/Resources/backend/api/`

If recipients only see `_internal` and no launcher, the packager used a bad `extraResources` filter (older builds used `filter: ["**/*"]`, which skipped **root-level** files). **Rebuild with the current `electron/package.json`**, or run `node scripts/verify-dist-for-electron.js` before `electron-builder` — `build-electron.bat` / `build-electron.sh` run this automatically.

**Do not** share a loose `resources` folder as the app: on macOS use the full **`.app` bundle**; on Windows the full **`win-unpacked`** directory (including `resources`, `locales`, `Pipeline Conversion Engine.exe`, etc.).

## UI Features

| Feature | Description |
|---|---|
| File upload | Drag-and-drop with validation |
| Code output | VS Code dark theme, line numbers, copy + download |
| Structure guide | Rendered markdown with syntax-highlighted code blocks |
| LLM progress | Live SSE per-tool progress bar + elapsed timer |
| Advanced steps | Per-step controls, re-run any step independently |
| History | `localStorage` persisted — survives app restart |
| Downloads | Browser-native Blob downloads |
