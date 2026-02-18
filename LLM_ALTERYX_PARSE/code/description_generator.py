import pandas as pd
import time
from langchain.prompts import PromptTemplate
from code.ToolContextDictionary import comprehensive_guide
from code.traverse_helper import get_input_name, get_output_name
from code.prompt_helper import _call_responses_api_from_prompt_template


def create_tool_io_description(df_connections, tool_id):
    """
    For a given tool_id, create a human-readable description of its inputs and outputs.
    
    Example output:
    "This tool receives data from tools 580 and 582, and produces output that will be used by subsequent tools."
    """
    input_details = get_input_name(df_connections, tool_id)
    output_details = get_output_name(df_connections, tool_id)

    num_inputs = len(input_details)
    num_outputs = len(output_details)
    
    # Build input description
    if num_inputs == 0:
        input_desc = "This tool has no input data"
    elif num_inputs == 1:
        input_desc = f"This tool receives data from {input_details[0][0]}"
    else:
        input_sources = [inp[0] for inp in input_details]
        input_desc = f"This tool receives data from {', '.join(input_sources[:-1])} and {input_sources[-1]}"
    
    # Build output description
    if num_outputs == 0:
        output_desc = " and produces no output"
    elif num_outputs == 1:
        output_desc = f" and produces output named {output_details[0]}"
    else:
        output_names = [out for out in output_details]
        output_desc = f" and produces {num_outputs} outputs: {', '.join(output_names[:-1])} and {output_names[-1]}"
    
    return input_desc + output_desc


def generate_tool_descriptions(df_nodes, df_connections, progress_bar=None, message_placeholder=None, model="gpt-4o", temperature=0.0):
    """
    Convert Alteryx tool configurations into detailed technical descriptions for Python code generation.
    
    Parameters:
        df_nodes (pd.DataFrame): DataFrame containing columns 'tool_id', 'tool_type', and 'text'.
        df_connections (pd.DataFrame): DataFrame containing connection information.
        progress_bar (st.progress): Optional Streamlit progress bar to update during processing.
        message_placeholder: Optional Streamlit placeholder for status messages.
        model (str): The LLM model to use for code generation.
        temperature (float): Temperature parameter for LLM responses (0.0-2.0).
    
    Returns:
        pd.DataFrame: A DataFrame with columns 'tool_id', 'tool_type', and 'description'.
        Each description contains detailed technical information needed for Python implementation.
    """
    template = """
    You are an expert data engineer analyzing Alteryx tool configurations to generate working Python code.
    Analyze the following Alteryx tool configuration and provide a detailed, technical description that includes ALL information needed to implement the tool in Python.
    
    Tool ID: {tool_id}
    Tool type: {tool_type}
    Configuration details: {config_text}
    I/O context: {io_context}
    Additional context: {additional_context}
    
    Instructions:
    - Provide a concise, detailed technical description with all information necessary for Python implementation.
    - Clearly specify input and output dataframe names, operation type, and key parameters (columns, filters, joins, transformations, etc.).
    - For each operation, include only relevant configuration needed for generating Python code (e.g., filter logic, join keys/type, aggregation functions, sorting).
    - Mention data types, conversions, or unique constraints if applicable.
    - Use clear, non-redundant bullet points or short paragraphs.
    - Where helpful, provide brief Python snippets or patterns to illustrate translation to pandas code.
    - Exclude information not relevant to code generation or implementation details not used in Python.

    Example response:
    ## Tool {tool_id} ({tool_type})

    ### Purpose
    [Short business purpose, 1-2 sentences.]

    ### Key Details
    - Inputs: [dataframe names]
    - Outputs: [output name(s)]
    - Operation: [e.g., filter, join, transform, aggregate, etc.]
    - Parameters:
        - Columns Used: [...]
        - Filter/Join/Transform/Aggregation specifics: [exact conditions or formulas, if applicable]
        - Data Types/Conversions: [as needed]

    [Optional]
    - Python Example: [Concise code pattern, if instructive]

    Important:
    - Focus only on details necessary for Python code, omitting unused XML/config parameters.
    - Warn about ignoring Alteryx-specific quirks (e.g., "Right_" column names) if relevant.
    - Make sure the description is efficient, clear, and actionable for code generation.

    Provide only the final, non-redundant technical description below.
    """

    prompt_template = PromptTemplate(
        input_variables=["tool_id", "tool_type", "config_text", "io_context", "additional_context"],
        template=template
    )

    results = []
    total_tools = len(df_nodes)  # This is now the filtered dataframe length
    progress_value = 0.0
    
    print(f"Processing {total_tools} tools for descriptions: {list(df_nodes['tool_id'])}")
    
    for tool_index, (index, row) in enumerate(df_nodes.iterrows()):  # Use enumerate to get proper counter
        tool_name = row["tool_type"]
        
        # Truncate the configuration text to avoid token limits
        config_text = row["text"]
        if len(config_text) > 8000:  # Limit to ~8000 characters to stay within token limits
            config_text = config_text[:8000] + "... [truncated]"
        
        # Get additional context from the comprehensive guide
        additional_context = (
            f'This tool is a "{tool_name}" tool. {comprehensive_guide.get(tool_name, "")}'
        )
        
        # Create I/O context description
        io_context = create_tool_io_description(df_connections, row["tool_id"])

        try:
            generated_description = _call_responses_api_from_prompt_template(
                prompt_template, model, temperature,
                tool_id=row["tool_id"],
                tool_type=row["tool_type"],
                config_text=config_text,
                io_context=io_context,
                additional_context=additional_context,
            )
        except Exception as e:
            error_msg = str(e)
            print(f"Error processing tool {row['tool_id']}: {error_msg}")
            
            # Handle specific error types
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                generated_description = f"Rate limit exceeded for tool {row['tool_id']} ({row['tool_type']}). Please wait and try again."
            elif "token" in error_msg.lower():
                generated_description = f"Token limit exceeded for tool {row['tool_id']} ({row['tool_type']}). Configuration too large."
            else:
                generated_description = f"Error generating description for tool {row['tool_id']} ({row['tool_type']}): {error_msg}"

        results.append({
            "tool_id": row["tool_id"],
            "tool_type": row["tool_type"],
            "description": generated_description
        })

        # Update progress bar
        if progress_bar is not None:
            progress_value += (1 / total_tools)
            progress_bar.progress(min(max(progress_value, 0.0), 1.0))

        # Update message placeholder
        if message_placeholder is not None:
            remaining_tools = total_tools - tool_index - 1
            message_placeholder.write(
                f"**Generating descriptions for {remaining_tools} tool(s), it may take {remaining_tools * 3} seconds...**"
            )
        
        # Add a small delay to avoid rate limiting (only if not the last tool)
        if tool_index < total_tools - 1:
            time.sleep(0.5)  # 0.5 second delay between API calls

    return pd.DataFrame(results)


def combine_tool_descriptions(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="", model="gpt-4o", temperature=0.0):
    """
    Create a comprehensive Python code structure guide from individual tool descriptions.
    
    Parameters:
        tool_ids (list): A list of tool IDs to combine descriptions for.
        df_descriptions (pd.DataFrame): DataFrame containing 'tool_id' and 'description' columns.
        execution_sequence (str): The execution order of tools.
        extra_user_instructions (str): Additional instructions for the summary.
        model (str): The LLM model to use.
        temperature (float): Temperature parameter for LLM responses (0.0-2.0).
    
    Returns:
        tuple: (code_structure_guide, full_prompt)
    """
    # Gather descriptions for each tool
    descriptions = []
    for tool_id in tool_ids:
        subset = df_descriptions.loc[df_descriptions["tool_id"] == tool_id, "description"]
        if not subset.empty:
            descriptions.append(f"Tool {tool_id}: {subset.iloc[0]}")
        else:
            descriptions.append(f"Tool {tool_id}: No description available")

    all_descriptions = "\n\n".join(descriptions)
    
    if not extra_user_instructions:
        extra_user_instructions = ''

    template = """
    You are an expert Python data engineer creating a comprehensive code structure guide for converting Alteryx workflows to Python.
    Below are detailed technical descriptions of individual Alteryx tools that form a data processing pipeline.
    
    Individual tool descriptions:
    {all_descriptions}
    
    Additional context: {extra_user_instructions}
    Execution sequence: {execution_sequence}
    
    Your task is to create a detailed Python code structure guide that:
    1. Analyzes the workflow and suggests optimal Python code organization
    2. Recommends meaningful variable/function names instead of Alteryx-style names (e.g., 'customer_data_df' instead of 'df_155_Output')
    3. Identifies opportunities to use Pythonic patterns (loops, list comprehensions, functions)
    4. Suggests logical function groupings and code structure
    5. Handles Alteryx-specific patterns that need Python equivalents
    6. Provides clear guidance on data flow and variable management
    
    Structure your response as:
    
    ## Workflow Overview
    [Brief description of the overall data processing purpose in business language]
    
    ## Python Code Structure Recommendations
    
    ### Function Organization
    [Recommend how to group multiple tools that are related to each other into functions]
    [Suggest meaningful names for the output of functions (dataframes/variables), it could be reasonably long to help understand]
    
    ### Pythonic Optimizations
    [Identify and call out opportunities for which tools we might be able to combine into a single function, can be concise because we are using python, loops, list comprehensions, functions, etc., e.g., "For tool ID 13,14,15, Use a loop to process multiple files instead of separate tools"]
    
    ### Data Flow Management
    [Explain how to handle data flow between steps, e.g., "Chain operations using method chaining where possible"]
    
    ## Technical Specification: Python Code Structure for Alteryx Workflow Conversion

    ### Phase 1: Data Loading and Cleaning (Organized by Data Topic)

    For the first phase, identify each data topic in the workflow (e.g., customer data, sales data, product data, etc.). For each data topic, all loading, cleaning, and basic transformation steps should be grouped together (possibly within one or more functions per topic). This ensures all relevant preparation for each data source is handled locally and intuitively.

    For each data topic, provide:

    #### Data Topic: [Descriptive Name for Data Topic 1]
    - **Related Tools**: [List all tool IDs, e.g., 1, 2, 3]
    - **Description**: Clearly state what this dataset represents and how it is used in the workflow.
    - **Loading Function Name**: [e.g., `load_and_prepare_customer_data`]
    - **Input/Output Variable Names**: [e.g., `raw_customer_df`, `cleaned_customer_df`]
    - **Processing & Python Patterns**: Describe the steps (load data, drop nulls, standardize columns, type conversion, etc.) and mention best practices (e.g., method chaining, explicit type casting).
    - **Code Example**:
    ```python
    def load_and_prepare_customer_data(filepath):
        # Load dataset
        customer_df = pd.read_csv(filepath)
        # Clean and preprocess
        customer_df = (
            customer_df.dropna(subset=["customer_id"])
            .rename(columns=lambda x: x.lower().strip())
            .astype({{"customer_id": int}})
            .drop_duplicates()
        )
        return customer_df
    ```

    #### Data Topic: [Descriptive Name for Data Topic 2]
    - **Related Tools**: [e.g., 4, 5, 6]
    - **Description**: ...
    - **Loading Function Name**: ...
    - **Input/Output Variable Names**: ...
    - **Processing & Python Patterns**: ...
    - **Code Example**:
    ```python
    # Similar structure as above for each data topic
    ```

    [Continue for all major data topics identified in the workflow, grouping every tool that loads/cleans/massages each data source.]

    ### Phase 2: Data Processing (Combining and Transforming Data Topics)

    Organize the main data transformation and processing logic into "Processing Units." Each unit should focus on **combining, joining, or further transforming** one or more data topics; these units reflect the main business logic after raw data preparation.

    For each processing unit, provide:

    #### Processing Unit: [Descriptive Name, e.g., Merge Customers and Sales]
    - **Tools Included**: [e.g., 7, 8, 9]
    - **Purpose**: High-level description of the logic (e.g., "Join cleaned customer data with sales transactions and filter for 2022 sales.")
    - **Function Name**: [e.g., `combine_customer_sales`]
    - **Input/Output Variable Names**: Clearly indicate all inputs and what the output variable should be called (e.g., `cleaned_customer_df`, `sales_df` → `customer_sales_df`).
    - **Pythonic Patterns**: Recommend method chaining, use of `merge`, aggregation via `groupby.agg`, etc.
    - **Detailed Steps**: Outline substeps if necessary (e.g., drop/rename columns before/after join, filter criteria, handling left/right join outputs).
    - **Code Example**:
    ```python
    def combine_customer_sales(customers, sales):
        result = (
            customers.merge(sales, on="customer_id", how="left")
            .query("sales_date >= '2022-01-01'")
        )
        return result
    ```

    #### Processing Unit: [e.g., Aggregate Sales by Region]
    - **Tools Included**: ...
    - **Purpose**: ...
    - **Function Name**: ...
    - **Input/Output Variable Names**: ...
    - **Pythonic Patterns**: ...
    - **Detailed Steps**: ...
    - **Code Example**:
    ```python
    # Example here as above
    ```

    [Continue this format for each further major transformation step or business logic unit, referencing all included tool IDs.]

    ### Phase 3: Data Output

    For the output phase, specify all logic relating to exporting or saving final results. For each distinct output, provide:

    - **Tools Included**: [e.g., output tool IDs]
    - **Description**: What does the output represent? Where should it be saved?
    - **Output Function Name**: [e.g., `export_final_results`]
    - **Input Variable Name**: [e.g., `final_aggregated_df`]
    - **Python Patterns**: e.g., `df.to_csv`, `df.to_excel`, robust file naming, error handling.
    - **Code Example**:
    ```python
    def export_final_results(final_df, output_path):
        final_df.to_csv(output_path, index=False)
    ```

    [Repeat as necessary for all output steps.]

    ---
    **General Principles:**
    - All code sections above should include robust error handling and comments.
    - Avoid Alteryx-like variable names in function and variable naming; use intuitive business-driven names.
    - Do **not** introduce column prefixes like "Left_" or "Right_" during joins; instead, pre-rename columns if necessary before joining.
    - Group code so that data engineers can intuitively work with, extend, or refactor logic relating to each data topic and each core workflow unit.
    
    ## Alteryx to Python Conversions
    
    ### Key Differences to Handle
    - **Multiple Outputs**: Alteryx tools like joins, filters, etc. can have multiple outputs, Python will have less.
    - **Iterative Operations**: Use loops instead of multiple similar tools
    - **Variable Scope**: Plan variable names and scope carefully
    - **Error Handling**: Add appropriate try-catch blocks with clear error messages indicate which step is failing.
    
    ### Recommended Code Structure
    # High-Level Python Code Structure (Natural Language Guide)
    - **Data Loading Phase**: Begin by loading all required input datasets using dedicated functions. If multiple tools load data from similar sources, group them into a single function or logical block. Assign clear, descriptive variable names to each loaded DataFrame.
    - **Preprocessing & Cleaning**: Organize all data cleaning and preprocessing steps into one or more functions. If several tools perform similar cleaning operations (e.g., filtering, type conversion), consider combining them into a single function with parameters.
    - **Transformation & Processing**: For tools that transform or join data, group related operations together. If multiple tools operate on the same DataFrame or perform sequential transformations, chain these steps within a function. For complex workflows, break down processing into logical phases (e.g., "customer enrichment", "sales aggregation").
    - **Data Merging & Joins**: If the workflow includes multiple join or union tools, describe how to consolidate these into fewer, well-structured merge operations in Python. Remove unnecessary column prefixes (like "Right_") and handle multiple outputs by returning tuples or using clear variable names.
    - **Iterative or Repetitive Operations**: Where the workflow uses repeated tools for similar tasks (e.g., multiple filters or formulas), use Python loops or list comprehensions to generalize the logic.
    - **Output Phase**: Collect all output steps at the end of the workflow. Use dedicated functions for writing or exporting data, and ensure variable names reflect the output content.
    - **Workflow Orchestration**: Don't use `main()` function to orchestrate the overall workflow since we start with Jupyter Notebook, calling each phase in the correct order as determined by the execution sequence. Pass DataFrames between functions as needed, and document the data flow.
    - **Error Handling**: Add try-except blocks around major workflow phases to catch and report errors, indicating which step failed.
    - **Modularity & Reusability**: Structure the code so that each logical phase (loading, cleaning, processing, output) is encapsulated in a function. This makes the code easier to test and maintain.
    - **Example**:  
      - `def load_customer_data()`
      - `def clean_sales_data(sales_df)`
      - `def join_customer_sales(customer_df, sales_df)`
      - `def aggregate_sales_by_region(joined_df)`
      - `def export_results(final_df)`
    
    ## Implementation Notes
    [Specific notes about implementation details, potential challenges, and best practices]
    
    # Most important instructions (You should mention this when try to combine the code in Phase 2 above, and also include this in the final result.):
    Try your best to not use column names like "Right_" or "Left_" after join in the code structure guide, just use the column names as they are. When conduct join, if columns need to be dropped or renamed, please do before the join instead of introduce "Right_" or "Left_" columns. 
    Don't profiling/visualize the data, we only need the data to be processed.

    Provide only the detailed code structure guide below:
    """

    prompt = PromptTemplate(
        input_variables=["all_descriptions", "extra_user_instructions", "execution_sequence"],
        template=template
    )

    combined_description = _call_responses_api_from_prompt_template(
        prompt, model, temperature,
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence,
    )

    full_prompt = prompt.format(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence
    )

    return combined_description, full_prompt


def generate_final_python_code(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="", workflow_description="", model="gpt-4o", temperature=0.0):
    """
    Generate working Python code by combining detailed tool descriptions and code structure guidance.
    
    Parameters:
        tool_ids (list): A list of tool IDs to generate code for.
        df_descriptions (pd.DataFrame): DataFrame containing 'tool_id' and 'description' columns.
        execution_sequence (str): The execution order of tools.
        extra_user_instructions (str): Additional instructions for the code generation.
        workflow_description (str): The workflow structure guide generated in step 2.
        model (str): The LLM model to use.
        temperature (float): Temperature parameter for LLM responses (0.0-2.0).
    
    Returns:
        tuple: (final_python_code, full_prompt)
    """
    # Gather descriptions for each tool
    descriptions = []
    for tool_id in tool_ids:
        subset = df_descriptions.loc[df_descriptions["tool_id"] == tool_id, "description"]
        if not subset.empty:
            descriptions.append(f"Tool {tool_id}:\n{subset.iloc[0]}")
        else:
            descriptions.append(f"Tool {tool_id}: No description available")

    all_descriptions = "\n\n".join(descriptions)
    
    if not extra_user_instructions:
        extra_user_instructions = ''

    template = """
    You are an expert Python data engineer tasked with generating working Python code from detailed Alteryx tool descriptions.
    
    Below are detailed technical descriptions of individual Alteryx tools that form a data processing pipeline:
    
    {all_descriptions}
    
    Additional context: {extra_user_instructions}
    Execution sequence: {execution_sequence}
    
    IMPORTANT: You have access to a detailed workflow structure guide that was generated in step 2. 
    This guide contains specific recommendations for code organization, variable naming, and Pythonic patterns.
    You MUST follow and implement the guidance provided in this structure guide:
    {workflow_description}
    
    Your task is to generate complete, working Python code that:
    1. Implements all the described tools in the correct execution order
    2. Follows the specific code structure and organization recommendations from the workflow guide
    3. Uses the suggested variable and function names from the workflow guide
    4. Implements the Pythonic patterns and optimizations suggested in the workflow guide
    5. Follows Python best practices and pandas conventions
    6. Includes proper error handling and logging
    7. Handles Alteryx-specific patterns that need Python equivalents
    8. Produces a complete, runnable Python script
    
    Requirements:
    - Strictly follow the workflow structure guide recommendations
    - Use the suggested variable names and function organization from the guide
    - Implement the Pythonic patterns and optimizations outlined in the guide
    - Include all necessary import statements
    - Add appropriate comments explaining the logic
    - Handle data types and conversions properly
    - Implement proper error handling
    - Use pandas method chaining where beneficial
    - Follow PEP 8 style guidelines
    
    Generate a complete Python script that includes:
    1. Import statements
    2. Function definitions following the workflow guide structure
    3. Main execution logic
    4. Proper variable management using suggested names
    5. Comments explaining the business logic
    Important instructions: Don't generate the code assume it's final. Make sure it's easy to debug and extend. For example, don't run all the functions in a final main function, instead, format the code that we can run it in jupyter notebook, where we can run step by step.
    Provide only the complete Python code below (no markdown formatting, just pure Python code):
    """

    prompt = PromptTemplate(
        input_variables=["all_descriptions", "extra_user_instructions", "execution_sequence", "workflow_description"],
        template=template
    )

    final_python_code = _call_responses_api_from_prompt_template(
        prompt, model, temperature,
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence,
        workflow_description=workflow_description,
    )

    full_prompt = prompt.format(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence,
        workflow_description=workflow_description
    )

    return final_python_code, full_prompt 