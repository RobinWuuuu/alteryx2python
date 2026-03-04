# Alteryx to Python Converter — React App

Modern React + FastAPI version of the LLM_ALTERYX_PARSE project.

## Development

**Terminal 1 — Backend:**
```bash
cd LLM_ALTERYX_PARSE_REACT
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd LLM_ALTERYX_PARSE_REACT/frontend
npm run dev
# → http://localhost:5173
```

## Production (single server)

```bash
cd LLM_ALTERYX_PARSE_REACT/frontend
npm run build
cd ..
uvicorn api:app --port 8000
# → http://localhost:8000
```

## Bug Fixes vs Original

- **Removed stray `import streamlit as st`** from `code/prompt_helper.py` (line 45) — this caused `ImportError` when importing the module outside of Streamlit.

## UI Improvements

| Feature | Streamlit | React |
|---|---|---|
| File upload | Basic picker | Drag-and-drop with validation |
| Code output | `st.code()` | VS Code dark theme, line numbers, copy + download |
| Structure guide | `st.markdown()` | Properly rendered markdown with syntax-highlighted code blocks |
| LLM progress | Static spinner | Live SSE per-tool progress bar + elapsed timer |
| Advanced steps | All 3 in one button | Per-step controls, re-run any step independently |
| History | Session-only | `localStorage` persisted — survives browser refresh |
| Downloads | Server round-trip | Browser-native Blob downloads |
| Errors | `st.error()` flash | Inline error messages with context |
