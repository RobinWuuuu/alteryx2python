"""
api.py — FastAPI backend for Alteryx to Python Converter.

Run with:
    uvicorn api:app --reload --port 8000
"""

import asyncio
import json
import os
import sys
import tempfile
import threading
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure the project root is on sys.path so `code.*` imports work.
ROOT = Path(__file__).parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from code import alteryx_parser as parser
from code import description_generator
from code import prompt_helper
from code import traverse_helper
from code import sql_generator
from code import fabric_parser
from code import fabric_generator
from code.prompt_helper import _call_responses_api
from code.description_generator import create_tool_io_description

# ---------------------------------------------------------------------------
# Session store: session_id → {path, created_at}
# ---------------------------------------------------------------------------
_sessions: Dict[str, Dict[str, Any]] = {}
_SESSION_TTL = 2 * 60 * 60  # 2 hours in seconds


async def _cleanup_loop():
    """Background task: remove temp files older than TTL."""
    while True:
        await asyncio.sleep(30 * 60)  # check every 30 minutes
        now = time.time()
        expired = [sid for sid, info in _sessions.items() if now - info["created_at"] > _SESSION_TTL]
        for sid in expired:
            info = _sessions.pop(sid, None)
            if info and os.path.exists(info["path"]):
                try:
                    os.remove(info["path"])
                except OSError:
                    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_cleanup_loop())
    yield
    task.cancel()


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(title="Alteryx to Python API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Available models constant (shared with frontend via GET /api/models)
# ---------------------------------------------------------------------------
MODEL_OPTIONS = [
    "gpt-4.1",
    "gpt-4o",
    "gpt-4o-mini",
    "o1",
    "o3-mini-high",
    "gpt-5",
    "gpt-5.2",
    "gpt-5-mini",
    "gpt-5.1-codex",
    "gpt-5.1-codex-mini",
    "gpt-5.1-codex-max",
]

# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------

class SessionConfig(BaseModel):
    api_key: str
    code_generate_model: str = "gpt-4.1"
    reasoning_model: str = "gpt-4.1"
    code_combine_model: str = "gpt-5.1-codex"
    temperature: float = 0.0


class SequenceRequest(BaseModel):
    session_id: str


class ChildrenRequest(BaseModel):
    session_id: str
    container_tool_id: str


class DirectConvertRequest(BaseModel):
    session_id: str
    config: SessionConfig
    tool_ids: List[str]
    extra_instructions: str = ""


class AdvancedStep1Request(BaseModel):
    session_id: str
    config: SessionConfig
    tool_ids: List[str]
    extra_instructions: str = ""


class AdvancedStep2Request(BaseModel):
    session_id: str
    config: SessionConfig
    tool_ids: List[str]
    extra_instructions: str = ""
    tool_descriptions: List[Dict[str, str]]  # [{tool_id, tool_type, description}]
    execution_sequence: str


class AdvancedStep3Request(BaseModel):
    session_id: str
    config: SessionConfig
    tool_ids: List[str]
    extra_instructions: str = ""
    tool_descriptions: List[Dict[str, str]]
    execution_sequence: str
    workflow_description: str


# ---------------------------------------------------------------------------
# Helper: SSE adapter objects (mimic Streamlit progress_bar / st.empty)
# ---------------------------------------------------------------------------

class _SSEProgressBar:
    """Thread-safe adapter: forwards progress() calls as SSE events."""

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self._q = queue
        self._loop = loop

    def progress(self, value: float):
        asyncio.run_coroutine_threadsafe(
            self._q.put({"type": "progress", "value": float(min(max(value, 0.0), 1.0))}),
            self._loop,
        )


class _SSEMessagePlaceholder:
    """Thread-safe adapter: forwards write() calls as SSE message events."""

    def __init__(self, queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self._q = queue
        self._loop = loop

    def write(self, text: str):
        asyncio.run_coroutine_threadsafe(
            self._q.put({"type": "message", "text": str(text)}),
            self._loop,
        )


def _sse_bytes(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def _run_with_sse(blocking_fn, *args, **kwargs) -> StreamingResponse:
    """
    Runs a blocking function in a background thread.
    The function receives `progress_bar` and `message_placeholder` keyword args
    that forward events to an SSE stream.

    The final SSE event is {"type": "result", "data": <return value>}
    or {"type": "error", "message": <str>}.
    """
    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()
    SENTINEL = object()
    result_box: Dict[str, Any] = {}

    progress_bar = _SSEProgressBar(queue, loop)
    message_placeholder = _SSEMessagePlaceholder(queue, loop)

    def _thread():
        try:
            result = blocking_fn(
                *args,
                progress_bar=progress_bar,
                message_placeholder=message_placeholder,
                **kwargs,
            )
            result_box["ok"] = result
        except Exception as exc:
            result_box["error"] = str(exc)
        finally:
            asyncio.run_coroutine_threadsafe(queue.put(SENTINEL), loop)

    t = threading.Thread(target=_thread, daemon=True)
    t.start()

    async def _generate():
        while True:
            try:
                item = await asyncio.wait_for(queue.get(), timeout=5.0)
            except asyncio.TimeoutError:
                yield _sse_bytes({"type": "heartbeat"})
                continue

            if item is SENTINEL:
                break
            yield _sse_bytes(item)

        if "error" in result_box:
            yield _sse_bytes({"type": "error", "message": result_box["error"]})
        else:
            yield _sse_bytes({"type": "result", "data": result_box.get("ok")})

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Helper: load workflow from session
# ---------------------------------------------------------------------------

def _get_session_path(session_id: str) -> str:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found or expired. Please re-upload the file.")
    return _sessions[session_id]["path"]


def _parse_tool_ids(raw: List[str]) -> List[str]:
    """Accept a list of potentially messy tool ID strings and flatten/clean them."""
    result = []
    for item in raw:
        # Handle comma-separated within a single string element
        cleaned = item.replace('"', '').replace("'", '').replace("[", '').replace("]", '')
        for tid in cleaned.split(","):
            tid = tid.strip()
            if tid:
                result.append(tid)
    return result


def _set_api_key(api_key: str):
    os.environ["OPENAI_API_KEY"] = api_key


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/models")
def get_models():
    return {"models": MODEL_OPTIONS}


@app.post("/api/upload")
async def upload_workflow(file: UploadFile = File(...)):
    """Upload a .yxmd/.yxmc file and return a session_id."""
    if file.filename and not file.filename.lower().endswith((".yxmd", ".yxmc")):
        raise HTTPException(status_code=400, detail="Only .yxmd or .yxmc files are supported.")

    # Save to a temp file
    suffix = Path(file.filename).suffix if file.filename else ".yxmd"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    content = await file.read()
    tmp.write(content)
    tmp.close()

    # Parse immediately to validate and get stats
    try:
        df_nodes, df_connections = parser.load_alteryx_data(tmp.name)
    except Exception as exc:
        os.remove(tmp.name)
        raise HTTPException(status_code=422, detail=f"Failed to parse workflow: {exc}")

    if df_nodes.empty:
        os.remove(tmp.name)
        raise HTTPException(status_code=422, detail="No tools found in the uploaded workflow file.")

    session_id = str(uuid.uuid4())
    _sessions[session_id] = {"path": tmp.name, "created_at": time.time()}

    tool_types = sorted(df_nodes["tool_type"].dropna().unique().tolist())
    return {
        "session_id": session_id,
        "filename": file.filename,
        "node_count": len(df_nodes),
        "connection_count": len(df_connections),
        "tool_types": tool_types,
    }


@app.post("/api/sequence")
def get_sequence(req: SequenceRequest):
    path = _get_session_path(req.session_id)
    df_nodes, df_connections = parser.load_alteryx_data(path)
    execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
    sequence_str = ", ".join(str(tid) for tid in execution_sequence)
    return {"execution_sequence": [str(t) for t in execution_sequence], "sequence_str": sequence_str}


@app.post("/api/children")
def get_children(req: ChildrenRequest):
    path = _get_session_path(req.session_id)
    df_nodes, _ = parser.load_alteryx_data(path)

    df_containers = parser.extract_container_children(df_nodes)
    df_containers = parser.clean_container_children(df_containers, df_nodes)

    container_info = df_containers[df_containers["container_id"] == req.container_tool_id]
    if container_info.empty:
        return {"container_id": req.container_tool_id, "child_tool_ids": []}

    child_tool_ids = list(container_info["child_tools"].values[0])
    return {"container_id": req.container_tool_id, "child_tool_ids": child_tool_ids}


@app.post("/api/convert/direct")
async def convert_direct(req: DirectConvertRequest):
    """SSE endpoint: direct conversion (per-tool code gen + combine)."""
    path = _get_session_path(req.session_id)
    _set_api_key(req.config.api_key)

    tool_ids = _parse_tool_ids(req.tool_ids)
    if not tool_ids:
        raise HTTPException(status_code=400, detail="No tool IDs provided.")

    def _work(progress_bar, message_placeholder):
        df_nodes, df_connections = parser.load_alteryx_data(path)
        df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
        test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]

        if test_df.empty:
            raise ValueError(f"No tools found with IDs: {tool_ids}")

        # Execution order
        execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
        ordered_tool_ids = traverse_helper.adjust_order(tool_ids, execution_sequence)

        # Per-tool code generation (with SSE progress)
        df_generated = prompt_helper.generate_python_code_from_alteryx_df(
            test_df, df_connections,
            progress_bar=progress_bar,
            message_placeholder=message_placeholder,
            model=req.config.code_generate_model,
            temperature=req.config.temperature,
            extra_user_instructions=req.extra_instructions,
        )

        # Ensure tool_id column exists
        if "tool_id" not in df_generated.columns:
            df_generated.insert(0, "tool_id", test_df["tool_id"].values)

        message_placeholder.write("Combining code snippets into final script...")

        # Combine step (single LLM call)
        final_script, prompt_used = prompt_helper.combine_python_code_of_tools(
            tool_ids, df_generated,
            execution_sequence=", ".join(str(t) for t in ordered_tool_ids),
            extra_user_instructions=req.extra_instructions,
            model=req.config.code_combine_model,
            temperature=req.config.temperature,
        )

        progress_bar.progress(1.0)
        return {
            "final_script": final_script,
            "prompt_used": prompt_used,
            "model_info": {
                "code_generate_model": req.config.code_generate_model,
                "code_combine_model": req.config.code_combine_model,
                "temperature": req.config.temperature,
            },
            "tool_ids": tool_ids,
            "ordered_tool_ids": [str(t) for t in ordered_tool_ids],
        }

    return await _run_with_sse(_work)


@app.post("/api/convert/advanced/step1")
async def advanced_step1(req: AdvancedStep1Request):
    """SSE endpoint: generate tool descriptions (per-tool, streamed)."""
    path = _get_session_path(req.session_id)
    _set_api_key(req.config.api_key)

    tool_ids = _parse_tool_ids(req.tool_ids)
    if not tool_ids:
        raise HTTPException(status_code=400, detail="No tool IDs provided.")

    def _work(progress_bar, message_placeholder):
        df_nodes, df_connections = parser.load_alteryx_data(path)
        df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
        test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]

        if test_df.empty:
            raise ValueError(f"No tools found with IDs: {tool_ids}")

        execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
        ordered_tool_ids = traverse_helper.adjust_order(tool_ids, execution_sequence)

        df_descriptions = description_generator.generate_tool_descriptions(
            test_df, df_connections,
            progress_bar=progress_bar,
            message_placeholder=message_placeholder,
            model=req.config.code_generate_model,
            temperature=req.config.temperature,
            extra_user_instructions=req.extra_instructions,
        )

        progress_bar.progress(1.0)
        descriptions = df_descriptions.to_dict(orient="records")
        return {
            "descriptions": descriptions,
            "ordered_tool_ids": [str(t) for t in ordered_tool_ids],
            "execution_sequence": ", ".join(str(t) for t in ordered_tool_ids),
        }

    return await _run_with_sse(_work)


@app.post("/api/convert/advanced/step2")
async def advanced_step2(req: AdvancedStep2Request):
    """Generate the workflow structure guide (single LLM call, JSON response)."""
    path = _get_session_path(req.session_id)
    _set_api_key(req.config.api_key)

    tool_ids = _parse_tool_ids(req.tool_ids)
    import pandas as pd

    df_descriptions = pd.DataFrame(req.tool_descriptions)

    loop = asyncio.get_event_loop()

    def _work():
        workflow_description, workflow_prompt = description_generator.combine_tool_descriptions(
            tool_ids,
            df_descriptions,
            execution_sequence=req.execution_sequence,
            extra_user_instructions=req.extra_instructions,
            model=req.config.reasoning_model,
            temperature=req.config.temperature,
        )
        return workflow_description, workflow_prompt

    workflow_description, workflow_prompt = await loop.run_in_executor(None, _work)
    return {"workflow_description": workflow_description, "workflow_prompt": workflow_prompt}


@app.post("/api/convert/advanced/step3")
async def advanced_step3(req: AdvancedStep3Request):
    """Generate final Python code (single LLM call, JSON response)."""
    path = _get_session_path(req.session_id)
    _set_api_key(req.config.api_key)

    tool_ids = _parse_tool_ids(req.tool_ids)
    import pandas as pd

    df_descriptions = pd.DataFrame(req.tool_descriptions)

    loop = asyncio.get_event_loop()

    def _work():
        final_python_code, final_prompt = description_generator.generate_final_python_code(
            tool_ids,
            df_descriptions,
            execution_sequence=req.execution_sequence,
            extra_user_instructions=req.extra_instructions,
            workflow_description=req.workflow_description,
            model=req.config.code_combine_model,
            temperature=req.config.temperature,
        )
        return final_python_code, final_prompt

    final_python_code, final_prompt = await loop.run_in_executor(None, _work)
    return {"final_python_code": final_python_code, "final_prompt": final_prompt}


@app.get("/api/workflow/{session_id}")
def get_workflow(session_id: str):
    """Return nodes and connections for workflow graph visualization."""
    path = _get_session_path(session_id)
    df_nodes, df_connections = parser.load_alteryx_data(path)

    nodes = [
        {"tool_id": row["tool_id"], "tool_type": row["tool_type"]}
        for _, row in df_nodes.iterrows()
    ]

    connections = [
        {
            "origin_tool_id": str(row["origin_tool_id"]) if row["origin_tool_id"] else "",
            "origin_connection": str(row["origin_connection"]) if row["origin_connection"] else "",
            "destination_tool_id": str(row["destination_tool_id"]) if row["destination_tool_id"] else "",
            "destination_connection": str(row["destination_connection"]) if row["destination_connection"] else "",
        }
        for _, row in df_connections.iterrows()
        if row["origin_tool_id"] and row["destination_tool_id"]
    ]

    return {"nodes": nodes, "connections": connections}


class WorkflowDescribeRequest(BaseModel):
    session_id: str
    config: SessionConfig


@app.post("/api/workflow/describe")
async def describe_workflow_tools(req: WorkflowDescribeRequest):
    """SSE endpoint: generate short 1-sentence descriptions for every tool in the workflow."""
    path = _get_session_path(req.session_id)
    _set_api_key(req.config.api_key)

    def _work(progress_bar, message_placeholder):
        df_nodes, df_connections = parser.load_alteryx_data(path)
        # Exclude viewer/container tools that don't need description
        df_tools = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2"])]

        total = len(df_tools)
        descriptions: Dict[str, str] = {}

        for i, (_, row) in enumerate(df_tools.iterrows()):
            tool_id = str(row["tool_id"])
            tool_type = str(row["tool_type"])

            config_text = str(row.get("text", ""))
            if len(config_text) > 1500:
                config_text = config_text[:1500] + "…"

            io_context = create_tool_io_description(df_connections, row["tool_id"])

            prompt = (
                f"Describe this Alteryx {tool_type} tool in one sentence (max 20 words). "
                f"Focus on the specific data operation it performs.\n"
                f"Configuration: {config_text}\n"
                f"Data flow: {io_context}\n"
                f"Return only the sentence, no prefix."
            )

            message_placeholder.write(f"Describing tool {i + 1}/{total}: {tool_type} ({tool_id})")
            try:
                desc = _call_responses_api(
                    req.config.code_generate_model,
                    req.config.temperature,
                    prompt,
                )
            except Exception as exc:
                desc = f"{tool_type} tool."
                print(f"Error describing tool {tool_id}: {exc}")

            descriptions[tool_id] = desc
            progress_bar.progress((i + 1) / total)

        return {"descriptions": descriptions}

    return await _run_with_sse(_work)


# ---------------------------------------------------------------------------
# SQL conversion endpoints
# ---------------------------------------------------------------------------

class SqlDirectConvertRequest(BaseModel):
    session_id: str
    config: SessionConfig
    tool_ids: List[str]
    extra_instructions: str = ""


class SqlAdvancedStep2Request(BaseModel):
    session_id: str
    config: SessionConfig
    tool_ids: List[str]
    extra_instructions: str = ""
    tool_descriptions: List[Dict[str, str]]
    execution_sequence: str


class SqlAdvancedStep3Request(BaseModel):
    session_id: str
    config: SessionConfig
    tool_ids: List[str]
    extra_instructions: str = ""
    tool_descriptions: List[Dict[str, str]]
    execution_sequence: str
    sql_structure_guide: str


@app.post("/api/convert/sql/direct")
async def convert_sql_direct(req: SqlDirectConvertRequest):
    """SSE endpoint: direct SQL conversion (per-tool CTE gen + combine)."""
    path = _get_session_path(req.session_id)
    _set_api_key(req.config.api_key)

    tool_ids = _parse_tool_ids(req.tool_ids)
    if not tool_ids:
        raise HTTPException(status_code=400, detail="No tool IDs provided.")

    def _work(progress_bar, message_placeholder):
        df_nodes, df_connections = parser.load_alteryx_data(path)
        df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
        test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]

        if test_df.empty:
            raise ValueError(f"No tools found with IDs: {tool_ids}")

        execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
        ordered_tool_ids = traverse_helper.adjust_order(tool_ids, execution_sequence)

        df_generated = sql_generator.generate_sql_for_tool(
            test_df, df_connections,
            progress_bar=progress_bar,
            message_placeholder=message_placeholder,
            model=req.config.code_generate_model,
            temperature=req.config.temperature,
            extra_user_instructions=req.extra_instructions,
        )

        if "tool_id" not in df_generated.columns:
            df_generated.insert(0, "tool_id", test_df["tool_id"].values)

        message_placeholder.write("Combining SQL CTEs into final script…")

        final_sql, prompt_used = sql_generator.combine_sql_of_tools(
            tool_ids, df_generated,
            execution_sequence=", ".join(str(t) for t in ordered_tool_ids),
            extra_user_instructions=req.extra_instructions,
            model=req.config.code_combine_model,
            temperature=req.config.temperature,
        )

        progress_bar.progress(1.0)
        return {
            "final_sql": final_sql,
            "prompt_used": prompt_used,
            "tool_ids": tool_ids,
            "ordered_tool_ids": [str(t) for t in ordered_tool_ids],
        }

    return await _run_with_sse(_work)


@app.post("/api/convert/sql/advanced/step1")
async def sql_advanced_step1(req: AdvancedStep1Request):
    """SSE endpoint: generate tool descriptions for SQL workflow (reuses Python descriptions)."""
    # Same as Python step1 — descriptions are language-agnostic
    return await advanced_step1(req)


@app.post("/api/convert/sql/advanced/step2")
async def sql_advanced_step2(req: SqlAdvancedStep2Request):
    """Generate SQL structure guide (JSON response)."""
    _get_session_path(req.session_id)  # validate session exists
    _set_api_key(req.config.api_key)

    tool_ids = _parse_tool_ids(req.tool_ids)
    import pandas as pd
    df_descriptions = pd.DataFrame(req.tool_descriptions)

    loop = asyncio.get_event_loop()

    def _work():
        return sql_generator.combine_sql_descriptions(
            tool_ids, df_descriptions,
            execution_sequence=req.execution_sequence,
            extra_user_instructions=req.extra_instructions,
            model=req.config.reasoning_model,
            temperature=req.config.temperature,
        )

    sql_structure_guide, sql_structure_prompt = await loop.run_in_executor(None, _work)
    return {"sql_structure_guide": sql_structure_guide, "sql_structure_prompt": sql_structure_prompt}


@app.post("/api/convert/sql/advanced/step3")
async def sql_advanced_step3(req: SqlAdvancedStep3Request):
    """Generate final SQL code (JSON response)."""
    _get_session_path(req.session_id)  # validate session exists
    _set_api_key(req.config.api_key)

    tool_ids = _parse_tool_ids(req.tool_ids)
    import pandas as pd
    df_descriptions = pd.DataFrame(req.tool_descriptions)

    loop = asyncio.get_event_loop()

    def _work():
        return sql_generator.generate_final_sql(
            tool_ids, df_descriptions,
            execution_sequence=req.execution_sequence,
            extra_user_instructions=req.extra_instructions,
            sql_structure_guide=req.sql_structure_guide,
            model=req.config.code_combine_model,
            temperature=req.config.temperature,
        )

    final_sql, final_prompt = await loop.run_in_executor(None, _work)
    return {"final_sql": final_sql, "final_prompt": final_prompt}


@app.delete("/api/session/{session_id}")
def delete_session(session_id: str):
    info = _sessions.pop(session_id, None)
    if info and os.path.exists(info["path"]):
        try:
            os.remove(info["path"])
        except OSError:
            pass
    return {"deleted": True}



# ---------------------------------------------------------------------------
# Fabric pipeline endpoints
# ---------------------------------------------------------------------------

class FabricStep1Request(BaseModel):
    session_id: str
    config: SessionConfig
    extra_instructions: str = ''


class FabricStep2Request(BaseModel):
    session_id: str
    config: SessionConfig
    extra_instructions: str = ''
    activity_descriptions: List[Dict[str, str]]  # [{activity_name, activity_type, description}]
    execution_sequence: str
    activity_names: List[str]


class FabricStep3Request(BaseModel):
    session_id: str
    config: SessionConfig
    extra_instructions: str = ''
    activity_descriptions: List[Dict[str, str]]
    execution_sequence: str
    activity_names: List[str]
    structure_guide: str


# Separate session store for Fabric files
_fabric_sessions: Dict[str, Dict[str, Any]] = {}


def _get_fabric_session(session_id: str) -> Dict[str, Any]:
    if session_id not in _fabric_sessions:
        raise HTTPException(status_code=404, detail="Fabric session not found. Please re-upload the file.")
    return _fabric_sessions[session_id]


@app.post("/api/fabric/upload")
async def upload_fabric(file: UploadFile = File(...)):
    """Upload a Fabric pipeline JSON or ZIP file."""
    fname = file.filename or "pipeline.json"
    if not any(fname.lower().endswith(ext) for ext in (".json", ".zip")):
        raise HTTPException(status_code=400, detail="Only .json or .zip files are supported.")

    suffix = Path(fname).suffix or ".json"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    content = await file.read()
    tmp.write(content)
    tmp.close()

    try:
        activities, metadata = fabric_parser.load_fabric_pipeline(tmp.name)
    except Exception as exc:
        os.remove(tmp.name)
        raise HTTPException(status_code=422, detail=f"Failed to parse Fabric pipeline: {exc}")

    if not activities:
        os.remove(tmp.name)
        raise HTTPException(status_code=422, detail="No activities found in the pipeline file.")

    session_id = str(uuid.uuid4())
    _fabric_sessions[session_id] = {
        "path": tmp.name,
        "activities": activities,
        "metadata": metadata,
        "created_at": time.time(),
    }

    activity_types = sorted(set(a.get("type", "Unknown") for a in activities))
    return {
        "session_id": session_id,
        "filename": fname,
        "pipeline_name": metadata.get("name", "Unnamed Pipeline"),
        "activity_count": len(activities),
        "activity_types": activity_types,
        "activity_names": [a.get("name", f"Activity_{i}") for i, a in enumerate(activities)],
    }


@app.post("/api/fabric/advanced/step1")
async def fabric_step1(req: FabricStep1Request):
    """SSE endpoint: generate descriptions for all Fabric pipeline activities."""
    session = _get_fabric_session(req.session_id)
    _set_api_key(req.config.api_key)
    activities = session["activities"]

    def _work(progress_bar, message_placeholder):
        df = fabric_generator.generate_activity_descriptions(
            activities,
            progress_bar=progress_bar,
            message_placeholder=message_placeholder,
            model=req.config.code_generate_model,
            temperature=req.config.temperature,
            extra_user_instructions=req.extra_instructions,
        )
        execution_order = fabric_parser.get_execution_order(activities)
        progress_bar.progress(1.0)
        return {
            "descriptions": df.to_dict(orient="records"),
            "activity_names": [a.get("name") for a in activities],
            "execution_sequence": ", ".join(execution_order),
            "pipeline_name": session["metadata"].get("name", "Pipeline"),
        }

    return await _run_with_sse(_work)


@app.post("/api/fabric/advanced/step2")
async def fabric_step2(req: FabricStep2Request):
    """Generate Python/SQL structure guide for the Fabric pipeline (JSON response)."""
    _get_fabric_session(req.session_id)  # validate session
    _set_api_key(req.config.api_key)

    import pandas as pd
    df_descriptions = pd.DataFrame(req.activity_descriptions)
    loop = asyncio.get_event_loop()

    def _work():
        return fabric_generator.combine_fabric_descriptions(
            req.activity_names,
            df_descriptions,
            execution_sequence=req.execution_sequence,
            extra_user_instructions=req.extra_instructions,
            model=req.config.reasoning_model,
            temperature=req.config.temperature,
        )

    structure_guide, structure_prompt = await loop.run_in_executor(None, _work)
    return {"structure_guide": structure_guide, "structure_prompt": structure_prompt}


@app.post("/api/fabric/advanced/step3")
async def fabric_step3(req: FabricStep3Request):
    """Generate final Python code for the Fabric pipeline (JSON response)."""
    _get_fabric_session(req.session_id)  # validate session
    _set_api_key(req.config.api_key)

    import pandas as pd
    df_descriptions = pd.DataFrame(req.activity_descriptions)
    loop = asyncio.get_event_loop()

    def _work():
        return fabric_generator.generate_final_fabric_code(
            req.activity_names,
            df_descriptions,
            execution_sequence=req.execution_sequence,
            extra_user_instructions=req.extra_instructions,
            structure_guide=req.structure_guide,
            model=req.config.code_combine_model,
            temperature=req.config.temperature,
        )

    final_code, final_prompt = await loop.run_in_executor(None, _work)
    return {"final_code": final_code, "final_prompt": final_prompt}

# ---------------------------------------------------------------------------
# Serve React build in production (must be last)
# ---------------------------------------------------------------------------
FRONTEND_DIST = ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="static")
