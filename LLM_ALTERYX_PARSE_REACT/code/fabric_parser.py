"""
fabric_parser.py — Parse Microsoft Fabric Data Factory pipeline JSON files.

Supported formats:
  - Single pipeline JSON (exported from Fabric Data Factory)
  - ZIP archive containing pipeline JSON (Fabric workspace export)
"""

import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_fabric_pipeline(file_path: str) -> Tuple[List[Dict], Dict]:
    """
    Parse a Fabric pipeline JSON or ZIP export.

    Returns:
        (activities, metadata)
        - activities: list of activity dicts from the pipeline JSON
        - metadata: {name, description, parameters, variables}
    """
    path = Path(file_path)
    if path.suffix.lower() == ".zip":
        return _load_from_zip(file_path)
    return _load_from_json(file_path)


def get_execution_order(activities: List[Dict]) -> List[str]:
    """
    Topological sort of Fabric activities based on their dependsOn fields.
    Returns an ordered list of activity names.
    """
    deps: Dict[str, List[str]] = {}
    for act in activities:
        name = act.get("name", "")
        deps[name] = [d["activity"] for d in act.get("dependsOn", [])]

    in_degree = {n: len(d) for n, d in deps.items()}
    queue = [n for n, d in in_degree.items() if d == 0]
    order: List[str] = []
    remaining = dict(in_degree)

    while queue:
        node = queue.pop(0)
        order.append(node)
        for name, depends in deps.items():
            if node in depends:
                remaining[name] -= 1
                if remaining[name] == 0:
                    queue.append(name)

    # Append any remaining (cyclic or disconnected)
    for name in deps:
        if name not in order:
            order.append(name)

    return order


def get_activity_config_text(activity: Dict) -> str:
    """
    Extract a readable configuration summary from a Fabric activity dict.
    Truncated to ~4 000 characters to keep LLM prompts concise.
    """
    activity_type = activity.get("type", "Unknown")
    type_props = activity.get("typeProperties", {})
    policy = activity.get("policy", {})

    parts = [f"Type: {activity_type}"]

    if activity_type == "Copy":
        source = type_props.get("source", {})
        sink = type_props.get("sink", {})
        parts.append(f"Source type: {source.get('type', 'Unknown')}")
        parts.append(f"Sink type:   {sink.get('type', 'Unknown')}")
        if "sqlReaderQuery" in source:
            parts.append(f"SQL query: {str(source['sqlReaderQuery'])[:600]}")
        for key in ("tableName", "schema", "dataset"):
            if key in source:
                parts.append(f"Source {key}: {source[key]}")
            if key in sink:
                parts.append(f"Sink {key}: {sink[key]}")

    elif activity_type == "Notebook":
        nb = type_props.get("notebook", {})
        parts.append(f"Notebook: {nb.get('referenceName', 'Unknown')}")
        params = type_props.get("baseParameters", {})
        if params:
            parts.append(f"Parameters: {list(params.keys())}")

    elif activity_type == "Script":
        scripts = type_props.get("scripts", [])
        if scripts:
            parts.append(f"Script: {str(scripts[0].get('text', ''))[:800]}")

    elif activity_type == "ForEach":
        items = type_props.get("items", {})
        inner = type_props.get("activities", [])
        parts.append(f"Iterates over: {items.get('value', 'items')}")
        parts.append(f"Is Sequential: {type_props.get('isSequential', False)}")
        parts.append(f"Inner activities: {[a.get('name') for a in inner]}")

    elif activity_type == "IfCondition":
        expr = type_props.get("expression", {})
        parts.append(f"Condition: {expr.get('value', 'Unknown')}")
        true_acts = [a.get("name") for a in type_props.get("ifTrueActivities", [])]
        false_acts = [a.get("name") for a in type_props.get("ifFalseActivities", [])]
        if true_acts:
            parts.append(f"If True: {true_acts}")
        if false_acts:
            parts.append(f"If False: {false_acts}")

    elif activity_type in ("ExecutePipeline", "InvokePipeline"):
        pipeline = type_props.get("pipeline", {})
        parts.append(f"Calls pipeline: {pipeline.get('referenceName', 'Unknown')}")
        params = type_props.get("parameters", {})
        if params:
            parts.append(f"Parameters: {list(params.keys())}")

    elif activity_type == "Lookup":
        source = type_props.get("source", {})
        dataset = type_props.get("dataset", {})
        parts.append(f"Dataset: {dataset.get('referenceName', 'Unknown')}")
        if "sqlReaderQuery" in source:
            parts.append(f"Query: {str(source['sqlReaderQuery'])[:600]}")
        parts.append(f"First row only: {type_props.get('firstRowOnly', True)}")

    elif activity_type == "GetMetadata":
        dataset = type_props.get("dataset", {})
        field_list = type_props.get("fieldList", [])
        parts.append(f"Dataset: {dataset.get('referenceName', 'Unknown')}")
        parts.append(f"Fields: {field_list}")

    elif activity_type == "Web":
        parts.append(f"URL: {str(type_props.get('url', ''))[:300]}")
        parts.append(f"Method: {type_props.get('method', 'GET')}")

    else:
        # Generic fallback — dump first few type properties
        for k, v in list(type_props.items())[:6]:
            parts.append(f"{k}: {str(v)[:200]}")

    # Retry policy
    if policy.get("retry", 0):
        parts.append(f"Retry: {policy['retry']} times, interval {policy.get('retryIntervalInSeconds', 30)}s")

    # Upstream dependencies
    depends_on = [d["activity"] for d in activity.get("dependsOn", [])]
    if depends_on:
        parts.append(f"Depends on: {', '.join(depends_on)}")

    config_text = "\n".join(parts)
    if len(config_text) > 4000:
        config_text = config_text[:4000] + "… [truncated]"
    return config_text


def get_activity_io_description(activities: List[Dict], activity_name: str) -> str:
    """
    Return a human-readable description of what feeds into and out of an activity.
    """
    target = next((a for a in activities if a.get("name") == activity_name), None)
    if not target:
        return ""

    depends_on = [d["activity"] for d in target.get("dependsOn", [])]
    outputs_to = [
        a["name"]
        for a in activities
        if any(d["activity"] == activity_name for d in a.get("dependsOn", []))
    ]

    parts: List[str] = []
    if depends_on:
        parts.append(f"Receives control/data from: {', '.join(depends_on)}")
    else:
        parts.append("Entry-point activity (no upstream dependencies)")

    if outputs_to:
        parts.append(f"Triggers downstream: {', '.join(outputs_to)}")
    else:
        parts.append("Terminal activity (nothing depends on it)")

    return "; ".join(parts)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_from_json(file_path: str) -> Tuple[List[Dict], Dict]:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _extract_pipeline(data)


def _load_from_zip(file_path: str) -> Tuple[List[Dict], Dict]:
    """Find and parse the pipeline JSON inside a Fabric workspace ZIP export."""
    with zipfile.ZipFile(file_path, "r") as z:
        json_files = [n for n in z.namelist() if n.endswith(".json")]
        # Prefer files with 'pipeline' in the name
        pipeline_files = [n for n in json_files if "pipeline" in n.lower()]
        target = pipeline_files[0] if pipeline_files else (json_files[0] if json_files else None)

        if not target:
            raise ValueError("No JSON files found in the uploaded ZIP.")

        with z.open(target) as f:
            data = json.load(f)

    return _extract_pipeline(data)


def _extract_pipeline(data: Dict) -> Tuple[List[Dict], Dict]:
    """Extract activities and metadata from any Fabric pipeline JSON structure."""
    # Fabric exports may wrap everything under 'properties'
    props = data.get("properties", data)

    activities = props.get("activities", [])
    metadata: Dict[str, Any] = {
        "name": data.get("name") or props.get("description") or "Unnamed Pipeline",
        "description": props.get("description", ""),
        "parameters": props.get("parameters", {}),
        "variables": props.get("variables", {}),
    }

    return activities, metadata
