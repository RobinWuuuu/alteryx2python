"""
sql_generator.py — SQL equivalents of prompt_helper and description_generator.

Functions for converting Alteryx workflow tools to SQL CTEs.
"""

import time
import pandas as pd
from langchain_core.prompts import PromptTemplate

from code.ToolContextDictionary import comprehensive_guide
from code.traverse_helper import get_input_name, get_output_name
from code.prompt_helper import _call_responses_api_from_prompt_template
from code.description_generator import create_tool_io_description


def generate_sql_for_tool(df_nodes, df_connections, progress_bar=None, message_placeholder=None,
                           model="gpt-4.1", temperature=0.0, extra_user_instructions=""):
    """
    Convert Alteryx tool configurations into SQL CTE snippets.

    Parameters:
        df_nodes (pd.DataFrame): DataFrame with 'tool_id', 'tool_type', 'text'.
        df_connections (pd.DataFrame): DataFrame with connection info.
        progress_bar: Optional SSE progress bar.
        message_placeholder: Optional SSE message placeholder.
        model (str): LLM model.
        temperature (float): Temperature (0.0–2.0).
        extra_user_instructions (str): Additional instructions.

    Returns:
        pd.DataFrame: Columns 'tool_id', 'tool_type', 'sql_code'.
    """
    template = """
    You are an expert SQL data engineer. Convert the following Alteryx tool configuration into an equivalent SQL CTE snippet.

    Tool type: {tool_type}
    Configuration details: {config_text}
    I/O details: {io_info}
    Additional instructions: {additional_instructions}
    User instructions: {extra_user_instructions}

    Rules:
    1. Return only a SQL CTE fragment in the form: cte_{tool_id} AS (SELECT ...)
    2. Use the input CTEs referenced in the I/O details as your FROM / JOIN sources.
    3. Do not include CREATE TABLE or INSERT statements — only the CTE expression.
    4. Do not wrap in markdown code fences.
    5. Use standard ANSI SQL that works in most databases (Snowflake, BigQuery, Postgres, etc.).
    6. Keep column names clean — no "Left_" or "Right_" prefixes; rename before joining if needed.
    """

    prompt_template = PromptTemplate(
        input_variables=["tool_type", "config_text", "io_info", "additional_instructions",
                         "extra_user_instructions", "tool_id"],
        template=template
    )

    results = []
    total_tools = len(df_nodes)
    progress_value = 0.05

    for index, row in df_nodes.iterrows():
        tool_name = row["tool_type"]
        tool_id = str(row["tool_id"])

        additional_instructions = (
            f'Refer to this additional information for "{tool_name}" tool - {comprehensive_guide[tool_name]}'
            if tool_name in comprehensive_guide else ""
        )

        # Build IO info for SQL: use CTE names instead of df_ variable names
        input_details = get_input_name(df_connections, row["tool_id"])
        output_details = get_output_name(df_connections, row["tool_id"])

        if input_details:
            input_ctes = [f"cte_{inp[0].replace('df_', '').split('_Output')[0]}" for inp in input_details]
            io_info = f"Input CTEs: {', '.join(input_ctes)}. Output CTE name: cte_{tool_id}."
        else:
            io_info = f"No inputs (this is a source/input tool). Output CTE name: cte_{tool_id}."

        config_text = str(row["text"])
        if len(config_text) > 3000:
            config_text = config_text[:3000] + "… [truncated]"

        if message_placeholder is not None:
            message_placeholder.write(f"Generating SQL for tool {tool_id} ({tool_name})…")

        generated_sql = _call_responses_api_from_prompt_template(
            prompt_template, model, temperature,
            tool_type=tool_name,
            config_text=config_text,
            io_info=io_info,
            additional_instructions=additional_instructions,
            extra_user_instructions=extra_user_instructions or "",
            tool_id=tool_id,
        )

        results.append({
            "tool_id": row["tool_id"],
            "tool_type": tool_name,
            "sql_code": generated_sql,
        })

        if progress_bar is not None:
            progress_value += (1 / total_tools) * 0.8
            progress_bar.progress(min(max(progress_value, 0.0), 1.0))

    return pd.DataFrame(results)


def combine_sql_of_tools(tool_ids, df_generated_sql, execution_sequence="",
                          extra_user_instructions="", model="gpt-5.1-codex", temperature=0.0):
    """
    Combine per-tool SQL CTEs into a single final SQL script with a SELECT statement.

    Returns:
        tuple: (final_sql, full_prompt)
    """
    cte_snippets = []
    for tool_id in tool_ids:
        subset = df_generated_sql.loc[df_generated_sql["tool_id"] == tool_id, "sql_code"]
        if not subset.empty:
            cte_snippets.append(subset.iloc[0])
        else:
            cte_snippets.append(f"-- No SQL generated for tool {tool_id}")

    all_ctes = "\n\n".join(
        f"-- Tool {tid}\n{snippet}" for tid, snippet in zip(tool_ids, cte_snippets)
    )

    if not extra_user_instructions:
        extra_user_instructions = ""

    template = """
    You are an expert SQL data engineer. Combine the following per-tool SQL CTE snippets into a single, clean SQL script.

    Per-tool CTEs:
    {all_ctes}

    Execution sequence (tool order): {execution_sequence}
    Extra user instructions: {extra_user_instructions}

    Requirements:
    1. Produce a WITH clause that assembles all CTEs in the correct order (respecting execution_sequence).
    2. Add a final SELECT * FROM <last_cte> (or the most appropriate final result CTE) at the end.
    3. Remove duplicate or conflicting CTE definitions.
    4. Add concise inline SQL comments to explain each CTE's business purpose.
    5. Do not wrap in markdown code fences — return only raw SQL.
    6. Use standard ANSI SQL.
    7. Keep column names clean (no "Left_" / "Right_" prefixes).

    Provide only the final combined SQL below:
    """

    prompt = PromptTemplate(
        input_variables=["all_ctes", "execution_sequence", "extra_user_instructions"],
        template=template
    )

    final_sql = _call_responses_api_from_prompt_template(
        prompt, model, temperature,
        all_ctes=all_ctes,
        execution_sequence=execution_sequence,
        extra_user_instructions=extra_user_instructions,
    )

    full_prompt = prompt.format(
        all_ctes=all_ctes,
        execution_sequence=execution_sequence,
        extra_user_instructions=extra_user_instructions,
    )

    return final_sql, full_prompt


def combine_sql_descriptions(tool_ids, df_descriptions, execution_sequence="",
                              extra_user_instructions="", model="gpt-4.1", temperature=0.0):
    """
    Create a SQL structure guide from individual tool descriptions.
    Equivalent of description_generator.combine_tool_descriptions but SQL-focused.

    Returns:
        tuple: (sql_structure_guide, full_prompt)
    """
    descriptions = []
    for tool_id in tool_ids:
        subset = df_descriptions.loc[df_descriptions["tool_id"] == tool_id, "description"]
        if not subset.empty:
            descriptions.append(f"Tool {tool_id}: {subset.iloc[0]}")
        else:
            descriptions.append(f"Tool {tool_id}: No description available")

    all_descriptions = "\n\n".join(descriptions)

    if not extra_user_instructions:
        extra_user_instructions = ""

    template = """
    You are an expert SQL data engineer creating a comprehensive SQL structure guide for converting Alteryx workflows to SQL.
    Below are technical descriptions of individual Alteryx tools that form a data processing pipeline.

    Individual tool descriptions:
    {all_descriptions}

    Additional context: {extra_user_instructions}
    Execution sequence: {execution_sequence}

    Your task is to create a detailed SQL CTE structure guide that:
    1. Describes the overall workflow purpose in business terms.
    2. Plans the CTE chain: which tool maps to which CTE, and how CTEs feed into each other.
    3. Recommends meaningful CTE names (e.g., `cleaned_customers`, `sales_filtered`) instead of `cte_123`.
    4. Identifies opportunities to simplify or merge CTEs.
    5. Handles Alteryx-specific patterns (multiple outputs, joins, filters, formulas) as SQL equivalents.
    6. Notes any columns that need renaming before joins to avoid "Left_"/"Right_" prefixes.

    Structure your response as:

    ## Workflow Overview
    [Brief description of the overall data processing purpose in business language]

    ## CTE Chain Design

    ### Phase 1: Source CTEs (Data Loading)
    For each source/input tool, describe:
    - **Tool ID**: [e.g., 12]
    - **CTE Name**: [e.g., `raw_customers`]
    - **Description**: What data this CTE represents
    - **SQL Pattern**: SELECT from base table / read from input

    ### Phase 2: Transformation CTEs
    For each transformation tool (filter, formula, select, join, etc.):
    - **Tool ID**: [e.g., 15]
    - **CTE Name**: [e.g., `active_customers`]
    - **Depends On**: [e.g., `raw_customers`]
    - **SQL Pattern**: The SQL operation (WHERE, JOIN, GROUP BY, CASE WHEN, etc.)
    - **Column Handling**: Any renames needed before/after join

    ### Phase 3: Output CTEs
    - **Tool ID**: [e.g., 20]
    - **CTE Name**: [e.g., `final_report`]
    - **Description**: Final SELECT and output

    ## Key SQL Conventions
    - CTE naming convention
    - Column naming rules (avoid prefixes)
    - Join type recommendations
    - Aggregation patterns

    Provide only the detailed SQL structure guide below:
    """

    prompt = PromptTemplate(
        input_variables=["all_descriptions", "extra_user_instructions", "execution_sequence"],
        template=template
    )

    sql_structure_guide = _call_responses_api_from_prompt_template(
        prompt, model, temperature,
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence,
    )

    full_prompt = prompt.format(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence,
    )

    return sql_structure_guide, full_prompt


def generate_final_sql(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="",
                        sql_structure_guide="", model="gpt-5.1-codex", temperature=0.0):
    """
    Generate final SQL code following the structure guide.
    Equivalent of description_generator.generate_final_python_code but for SQL.

    Returns:
        tuple: (final_sql, full_prompt)
    """
    descriptions = []
    for tool_id in tool_ids:
        subset = df_descriptions.loc[df_descriptions["tool_id"] == tool_id, "description"]
        if not subset.empty:
            descriptions.append(f"Tool {tool_id}:\n{subset.iloc[0]}")
        else:
            descriptions.append(f"Tool {tool_id}: No description available")

    all_descriptions = "\n\n".join(descriptions)

    if not extra_user_instructions:
        extra_user_instructions = ""

    template = """
    You are an expert SQL data engineer generating a complete SQL script from Alteryx tool descriptions.

    Individual tool descriptions:
    {all_descriptions}

    Additional context: {extra_user_instructions}
    Execution sequence: {execution_sequence}

    IMPORTANT: Follow the SQL structure guide below. Use the recommended CTE names, column handling rules, and patterns described in the guide.
    {sql_structure_guide}

    Generate a complete SQL script that:
    1. Uses a WITH (CTE) clause assembling all transformations in the correct execution order.
    2. Follows the CTE names and structure from the guide above.
    3. Includes a final SELECT from the last/output CTE.
    4. Adds concise SQL comments explaining the business purpose of each CTE.
    5. Uses standard ANSI SQL compatible with Snowflake, BigQuery, and Postgres.
    6. Avoids "Left_"/"Right_" column prefixes — rename columns before joins if necessary.
    7. Does NOT wrap output in markdown code fences — return only raw SQL.

    Provide only the complete SQL script below:
    """

    prompt = PromptTemplate(
        input_variables=["all_descriptions", "extra_user_instructions", "execution_sequence", "sql_structure_guide"],
        template=template
    )

    final_sql = _call_responses_api_from_prompt_template(
        prompt, model, temperature,
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence,
        sql_structure_guide=sql_structure_guide,
    )

    full_prompt = prompt.format(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence,
        sql_structure_guide=sql_structure_guide,
    )

    return final_sql, full_prompt
