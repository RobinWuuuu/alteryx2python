"""
fabric_generator.py — LLM-based description and code generation for Microsoft Fabric pipelines.

Three-step flow (mirrors description_generator.py):
  1. generate_activity_descriptions  → per-activity technical descriptions
  2. combine_fabric_descriptions     → Python/SQL structure guide
  3. generate_final_fabric_code      → complete Python implementation
"""

import time
import pandas as pd
from langchain_core.prompts import PromptTemplate

from code.prompt_helper import _call_responses_api_from_prompt_template
from code.fabric_parser import get_activity_config_text, get_activity_io_description


# ---------------------------------------------------------------------------
# Step 1 — Per-activity descriptions
# ---------------------------------------------------------------------------

def generate_activity_descriptions(
    activities,
    progress_bar=None,
    message_placeholder=None,
    model="gpt-4.1",
    temperature=0.0,
    extra_user_instructions="",
):
    """
    Generate concise technical descriptions for each Fabric pipeline activity.

    Parameters:
        activities (list): List of activity dicts from fabric_parser.load_fabric_pipeline().
        progress_bar: Optional SSE progress bar.
        message_placeholder: Optional SSE message placeholder.
        model (str): LLM model to use.
        temperature (float): Temperature (0.0–2.0).
        extra_user_instructions (str): Additional user context.

    Returns:
        pd.DataFrame: Columns ['activity_name', 'activity_type', 'description'].
    """
    template = """
    You are an expert data engineer analyzing a Microsoft Fabric Data Factory pipeline activity.
    Write a concise technical description (max 5 bullet points) for Python reimplementation.

    Activity Name: {activity_name}
    Activity Type: {activity_type}
    Configuration: {config_text}
    Data Flow:     {io_context}
    User context:  {extra_user_instructions}

    Required format (plain text, no markdown headers):
    - Purpose: [1 sentence — what this activity does in business terms]
    - Inputs: [upstream activity names or data sources]
    - Outputs: [what data/result this produces and where it goes]
    - Operation: [specific operation — copy, transform, notebook call, SQL script, loop, condition, etc. with key parameters]
    - Notes: [table names, notebook names, SQL snippets, retry policy — omit if none]

    Rules:
    - Be specific: include exact table names, notebook references, SQL queries, loop variables, conditions.
    - No Python code examples. No JSON/XML detail.

    Provide only the 5-bullet description:
    """

    prompt_template = PromptTemplate(
        input_variables=["activity_name", "activity_type", "config_text", "io_context", "extra_user_instructions"],
        template=template,
    )

    results = []
    total = len(activities)
    progress_value = 0.0

    for i, activity in enumerate(activities):
        name = activity.get("name", f"Activity_{i}")
        activity_type = activity.get("type", "Unknown")
        config_text = get_activity_config_text(activity)
        io_context = get_activity_io_description(activities, name)

        if message_placeholder:
            message_placeholder.write(f"Describing activity {i + 1}/{total}: {name} ({activity_type})…")

        try:
            description = _call_responses_api_from_prompt_template(
                prompt_template, model, temperature,
                activity_name=name,
                activity_type=activity_type,
                config_text=config_text,
                io_context=io_context,
                extra_user_instructions=extra_user_instructions or "",
            )
        except Exception as exc:
            description = f"Error generating description: {exc}"

        results.append({
            "activity_name": name,
            "activity_type": activity_type,
            "description": description,
        })

        if progress_bar is not None:
            progress_value += 1.0 / total
            progress_bar.progress(min(progress_value, 1.0))

        if i < total - 1:
            time.sleep(0.3)

    return pd.DataFrame(results)


# ---------------------------------------------------------------------------
# Step 2 — Python/SQL structure guide
# ---------------------------------------------------------------------------

def combine_fabric_descriptions(
    activity_names,
    df_descriptions,
    execution_sequence="",
    extra_user_instructions="",
    model="gpt-4.1",
    temperature=0.0,
):
    """
    Create a Python/SQL code structure guide from individual activity descriptions.

    Returns:
        tuple: (structure_guide, full_prompt)
    """
    descriptions = []
    for name in activity_names:
        subset = df_descriptions.loc[df_descriptions["activity_name"] == name, "description"]
        if not subset.empty:
            descriptions.append(f"Activity '{name}': {subset.iloc[0]}")
        else:
            descriptions.append(f"Activity '{name}': No description available")

    all_descriptions = "\n\n".join(descriptions)
    extra_user_instructions = extra_user_instructions or ""

    template = """
    You are an expert data engineer converting a Microsoft Fabric Data Factory pipeline to Python/PySpark code.
    Below are detailed descriptions of the pipeline activities.

    Activity descriptions:
    {all_descriptions}

    Execution sequence: {execution_sequence}
    Additional context: {extra_user_instructions}

    Create a comprehensive Python code structure guide that:
    1. Maps each Fabric activity to its Python/PySpark equivalent.
    2. Recommends a clean function/module structure with meaningful names.
    3. Identifies reusable patterns (loops for ForEach, conditionals for IfCondition, etc.).
    4. Plans how to handle Fabric-specific constructs:
       - CopyActivity     → pandas/PySpark read + write (or sqlalchemy for SQL endpoints)
       - NotebookActivity → Python function or subprocess / papermill call
       - ScriptActivity   → SQL execution via sqlalchemy / pyodbc
       - ForEachActivity  → Python for-loop
       - IfConditionActivity → Python if/else
       - LookupActivity   → SQL query returning a scalar or single row
       - ExecutePipelineActivity → function call to sub-pipeline function
       - GetMetadata      → os.stat / list files
       - WebActivity      → requests.get / requests.post
    5. Recommends connection management (env vars for credentials, connection pooling).
    6. Notes parallel vs sequential execution (from ForEach isSequential flag).

    Structure your response as:

    ## Pipeline Overview
    [Brief description of the overall pipeline purpose in business terms]

    ## Activity-to-Python Mapping

    For each activity provide:
    ### {activity_name} ({activity_type})
    - **Python Equivalent**: [pattern to use]
    - **Function Name**: [e.g., `copy_sales_to_lakehouse`]
    - **Input/Output Variables**: [what goes in and comes out]
    - **Code Sketch**:
    ```python
    def function_name(...):
        # brief outline
    ```

    ## Code Structure

    ### Phase 1: Setup & Connections
    [Connection objects, env var loading, logging setup]

    ### Phase 2: Data Ingestion
    [Activities that read/copy data in]

    ### Phase 3: Transformation & Processing
    [Notebook/Script/ForEach/IfCondition activities]

    ### Phase 4: Output & Export
    [Activities that write or publish results]

    ## Orchestration
    [How to chain function calls in the correct order; note parallel opportunities where dependsOn allows]

    ## Key Technical Notes
    [Credentials, retry logic, error handling recommendations]

    Provide only the detailed structure guide below:
    """

    prompt = PromptTemplate(
        input_variables=["all_descriptions", "execution_sequence", "extra_user_instructions"],
        template=template,
    )

    structure_guide = _call_responses_api_from_prompt_template(
        prompt, model, temperature,
        all_descriptions=all_descriptions,
        execution_sequence=execution_sequence,
        extra_user_instructions=extra_user_instructions,
    )

    full_prompt = prompt.format(
        all_descriptions=all_descriptions,
        execution_sequence=execution_sequence,
        extra_user_instructions=extra_user_instructions,
    )

    return structure_guide, full_prompt


# ---------------------------------------------------------------------------
# Step 3 — Final Python code
# ---------------------------------------------------------------------------

def generate_final_fabric_code(
    activity_names,
    df_descriptions,
    execution_sequence="",
    extra_user_instructions="",
    structure_guide="",
    model="gpt-5.1-codex",
    temperature=0.0,
):
    """
    Generate the final Python script for the Fabric pipeline.

    Returns:
        tuple: (final_code, full_prompt)
    """
    descriptions = []
    for name in activity_names:
        subset = df_descriptions.loc[df_descriptions["activity_name"] == name, "description"]
        if not subset.empty:
            descriptions.append(f"Activity '{name}':\n{subset.iloc[0]}")
        else:
            descriptions.append(f"Activity '{name}': No description available")

    all_descriptions = "\n\n".join(descriptions)
    extra_user_instructions = extra_user_instructions or ""

    template = """
    You are an expert data engineer generating Python code to reproduce a Microsoft Fabric Data Factory pipeline.

    Activity descriptions:
    {all_descriptions}

    Execution sequence: {execution_sequence}
    Additional context: {extra_user_instructions}

    IMPORTANT: Follow the structure guide below precisely — use its function names, variable names, and phase organization.
    {structure_guide}

    Generate complete, runnable Python code that:
    1. Reproduces all pipeline activities as Python functions.
    2. Maps Fabric activities to Python:
       - CopyActivity     → pandas read_csv/read_sql + to_parquet/to_sql, or PySpark equivalents
       - NotebookActivity → function call (stub with comment for actual notebook invocation)
       - ScriptActivity   → sqlalchemy text() execution
       - ForEachActivity  → Python for-loop calling the inner activity function
       - IfConditionActivity → Python if/else
       - LookupActivity   → SQL query returning scalar, stored in a variable
       - ExecutePipelineActivity → function call to the referenced pipeline function
       - WebActivity      → requests.get / requests.post
    3. Uses environment variables for all credentials:
       SERVER = os.environ.get("DB_SERVER", "your-server.database.windows.net")
       DATABASE = os.environ.get("DB_NAME", "your-db")
       ...
    4. Includes connection setup via sqlalchemy / pyodbc / delta-sharing as appropriate.
    5. Adds try/except around major steps with descriptive error messages.
    6. Is structured for Jupyter Notebook (cells separated by logical phase, no single main() wrapper).
    7. Includes clear inline comments explaining business logic.
    8. Respects execution order from the execution sequence.

    Requirements:
    - Include all necessary import statements at the top.
    - Placeholder credentials via os.environ.get().
    - Clear cell-level comments for Jupyter compatibility.

    Provide only the Python code below (no markdown fences, pure Python):
    """

    prompt = PromptTemplate(
        input_variables=["all_descriptions", "execution_sequence", "extra_user_instructions", "structure_guide"],
        template=template,
    )

    final_code = _call_responses_api_from_prompt_template(
        prompt, model, temperature,
        all_descriptions=all_descriptions,
        execution_sequence=execution_sequence,
        extra_user_instructions=extra_user_instructions,
        structure_guide=structure_guide,
    )

    full_prompt = prompt.format(
        all_descriptions=all_descriptions,
        execution_sequence=execution_sequence,
        extra_user_instructions=extra_user_instructions,
        structure_guide=structure_guide,
    )

    return final_code, full_prompt
