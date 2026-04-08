#!/bin/bash
set -e
echo "=== Building Backend with PyInstaller (macOS) ==="
cd "$(dirname "$0")"

export CSC_IDENTITY_AUTO_DISCOVERY=false

pyinstaller \
  --noconfirm \
  --distpath dist-backend \
  --name api \
  api.py \
  --hidden-import=uvicorn.logging \
  --hidden-import=uvicorn.lifespan \
  --hidden-import=uvicorn.lifespan.on \
  --hidden-import=uvicorn.lifespan.off \
  --hidden-import=uvicorn.protocols \
  --hidden-import=uvicorn.protocols.http \
  --hidden-import=uvicorn.protocols.http.auto \
  --hidden-import=uvicorn.protocols.http.h11_impl \
  --hidden-import=uvicorn.protocols.http.httptools_impl \
  --hidden-import=uvicorn.protocols.websockets \
  --hidden-import=uvicorn.protocols.websockets.auto \
  --hidden-import=uvicorn.protocols.websockets.wsproto_impl \
  --hidden-import=uvicorn.loops \
  --hidden-import=uvicorn.loops.auto \
  --hidden-import=uvicorn.loops.asyncio \
  --hidden-import=fastapi \
  --hidden-import=pydantic \
  --hidden-import=pydantic_settings \
  --hidden-import=starlette \
  --hidden-import=multipart \
  --hidden-import=openai \
  --hidden-import=certifi \
  --collect-all=certifi \
  --hidden-import=langchain \
  --hidden-import=langchain_openai \
  --hidden-import=pandas \
  --hidden-import=networkx \
  --hidden-import=dotenv \
  --hidden-import=code \
  --hidden-import=code.alteryx_parser \
  --hidden-import=code.description_generator \
  --hidden-import=code.prompt_helper \
  --hidden-import=code.traverse_helper \
  --hidden-import=code.sql_generator \
  --hidden-import=code.fabric_parser \
  --hidden-import=code.fabric_generator \
  --hidden-import=code.ToolContextDictionary \
  --collect-all=langchain \
  --collect-all=langchain_openai \
  --collect-all=langchain_core \
  --collect-all=langchain_text_splitters \
  --add-data "code:code"

echo "=== Backend build complete: dist-backend/api/ ==="
