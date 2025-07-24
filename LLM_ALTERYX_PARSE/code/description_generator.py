import pandas as pd
import time
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from code.ToolContextDictionary import comprehensive_guide
from code.traverse_helper import get_input_name, get_output_name


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


def generate_tool_descriptions(df_nodes, df_connections, progress_bar=None, message_placeholder=None):
    """
    Convert Alteryx tool configurations into detailed technical descriptions for Python code generation.
    
    Parameters:
        df_nodes (pd.DataFrame): DataFrame containing columns 'tool_id', 'tool_type', and 'text'.
        df_connections (pd.DataFrame): DataFrame containing connection information.
        progress_bar (st.progress): Optional Streamlit progress bar to update during processing.
        message_placeholder: Optional Streamlit placeholder for status messages.
    
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
    1. Provide a detailed technical description that captures ALL parameters and logic needed for Python implementation
    2. Include specific column names, data types, filter values, join conditions, etc.
    3. Specify input and output dataframe names clearly
    4. For filters: include exact filter conditions, values, AND/OR logic, data types
    5. For joins: specify join type (inner, left, right, outer), join columns, and any additional conditions
    6. For transformations: include exact formulas, calculations, new column names
    7. For aggregations: specify group-by columns, aggregation functions, new column names
    8. For data types: mention any type conversions or casting operations
    9. For sorting: specify sort columns and order (ascending/descending)
    10. For unique operations: specify which columns determine uniqueness
    
    Format your response as:
    
    ## Tool {tool_id} ({tool_type})
    
    ### Tool Purpose
    [Brief business purpose in 1-2 sentences]
    
    ### Technical Details
    - **Input Dataframe(s)**: [exact dataframe names]
    - **Output Dataframe**: [exact output name]
    - **Operation Type**: [filter/join/transform/aggregate/etc.]
    
    ### Specific Parameters
    [List all specific parameters found in the configuration]
    - **Columns Used**: [exact column names]
    - **Filter Conditions**: [if applicable, include exact values and logic]
    - **Join Criteria**: [if applicable, include join type and columns]
    - **Transformations**: [if applicable, include exact formulas]
    - **Data Types**: [if applicable, include type conversions]
    - **Sort Order**: [if applicable, include columns and direction]
    - **Aggregation**: [if applicable, include functions and group-by columns]
    
    ### Python Implementation Notes
    [Any specific notes for Python implementation, such as pandas functions to use, parameter names, etc.]
    
    Example detailed descriptions:
    
    For a Filter tool:
    ## Tool 583 (Filter)
    
    ### Tool Purpose
    Filters customer data to include only high-value customers.
    
    ### Technical Details
    - **Input Dataframe(s)**: df_580_Output
    - **Output Dataframe**: df_583_Filter
    - **Operation Type**: filter
    
    ### Specific Parameters
    - **Columns Used**: ['Customer_ID', 'Total_Sales', 'Region']
    - **Filter Conditions**: 
      - Total_Sales > 10000 (numeric comparison)
      - Region IN ['North', 'South'] (string comparison with multiple values)
      - Logic: AND (both conditions must be true)
    - **Data Types**: Total_Sales is numeric, Region is string
    
    ### Python Implementation Notes
    Use pandas boolean indexing with & operator for AND logic. Filter on Total_Sales > 10000 AND Region.isin(['North', 'South']).
    
    For a Join tool:
    ## Tool 585 (Join)
    
    ### Tool Purpose
    Joins customer data with order data to create a comprehensive customer order view.
    
    ### Technical Details
    - **Input Dataframe(s)**: df_580_Output (left), df_582_Output (right)
    - **Output Dataframe**: df_585_Join
    - **Operation Type**: join
    
    ### Specific Parameters
    - **Join Type**: Left Join
    - **Join Columns**: Customer_ID (left) = Customer_ID (right)
    - **Additional Conditions**: None
    - **Columns Used**: All columns from both dataframes
    
    ### Python Implementation Notes
    Use pandas merge() with how='left', left_on='Customer_ID', right_on='Customer_ID'.
    
    Provide only the detailed description below:
    """

    prompt_template = PromptTemplate(
        input_variables=["tool_id", "tool_type", "config_text", "io_context", "additional_context"],
        template=template
    )

    llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
    chain = LLMChain(llm=llm, prompt=prompt_template)

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
            generated_description = chain.run(
                tool_id=row["tool_id"],
                tool_type=row["tool_type"],
                config_text=config_text,
                io_context=io_context,
                additional_context=additional_context
            ).strip()
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


def combine_tool_descriptions(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="", model="gpt-4o"):
    """
    Create a comprehensive Python code structure guide from individual tool descriptions.
    
    Parameters:
        tool_ids (list): A list of tool IDs to combine descriptions for.
        df_descriptions (pd.DataFrame): DataFrame containing 'tool_id' and 'description' columns.
        execution_sequence (str): The execution order of tools.
        extra_user_instructions (str): Additional instructions for the summary.
        model (str): The LLM model to use.
    
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
    [Brief description of the overall data processing purpose]
    
    ## Python Code Structure Recommendations
    
    ### Function Organization
    [Recommend how to group tools into functions, e.g., "Create separate functions for data loading, cleaning, and transformation"]
    
    ### Variable Naming Strategy
    [Suggest meaningful names for dataframes and variables, e.g., "Use descriptive names like 'customer_data_df', 'sales_data_df', 'merged_data_df'"]
    
    ### Pythonic Optimizations
    [Identify opportunities for loops, list comprehensions, functions, etc., e.g., "Use a loop to process multiple files instead of separate tools"]
    
    ### Data Flow Management
    [Explain how to handle data flow between steps, e.g., "Chain operations using method chaining where possible"]
    
    ## Detailed Implementation Guide
    
    ### Phase 1: Data Loading
    [Specific guidance for data loading tools]
    - **Function Name**: [suggested function name]
    - **Variable Names**: [suggested variable names]
    - **Python Patterns**: [specific Python patterns to use]
    
    ### Phase 2: Data Processing
    [Specific guidance for processing tools]
    - **Function Name**: [suggested function name]
    - **Variable Names**: [suggested variable names]
    - **Python Patterns**: [specific Python patterns to use]
    
    ### Phase 3: Data Output
    [Specific guidance for output tools]
    - **Function Name**: [suggested function name]
    - **Variable Names**: [suggested variable names]
    - **Python Patterns**: [specific Python patterns to use]
    
    ## Alteryx to Python Conversions
    
    ### Key Differences to Handle
    - **Multiple Outputs**: Alteryx joins can have multiple outputs, Python merges have one
    - **Iterative Operations**: Use loops instead of multiple similar tools
    - **Variable Scope**: Plan variable names and scope carefully
    - **Error Handling**: Add appropriate try-catch blocks
    
    ### Recommended Code Structure
    ```python
    # Example structure
    def load_data():
        # Data loading logic
        pass
    
    def process_data(data_df):
        # Data processing logic
        pass
    
    def main():
        # Main workflow
        pass
    ```
    
    ## Implementation Notes
    [Specific notes about implementation details, potential challenges, and best practices]
    
    Provide only the detailed code structure guide below:
    """

    prompt = PromptTemplate(
        input_variables=["all_descriptions", "extra_user_instructions", "execution_sequence"],
        template=template
    )

    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt)

    combined_description = chain.run(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence
    ).strip()

    full_prompt = prompt.format(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence
    )

    return combined_description, full_prompt


def generate_final_python_code(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="", model="gpt-4o"):
    """
    Generate working Python code by combining detailed tool descriptions and code structure guidance.
    
    Parameters:
        tool_ids (list): A list of tool IDs to generate code for.
        df_descriptions (pd.DataFrame): DataFrame containing 'tool_id' and 'description' columns.
        execution_sequence (str): The execution order of tools.
        extra_user_instructions (str): Additional instructions for the code generation.
        model (str): The LLM model to use.
    
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
    
    Your task is to generate complete, working Python code that:
    1. Implements all the described tools in the correct execution order
    2. Uses meaningful variable and function names (not Alteryx-style names like df_155_Output)
    3. Follows Python best practices and pandas conventions
    4. Includes proper error handling and logging
    5. Uses Pythonic patterns like method chaining, list comprehensions, and loops where appropriate
    6. Handles Alteryx-specific patterns that need Python equivalents
    7. Produces a complete, runnable Python script
    
    Requirements:
    - Use descriptive variable names (e.g., 'customer_data_df', 'sales_data_df', 'merged_data_df')
    - Organize code into logical functions
    - Include all necessary import statements
    - Add appropriate comments explaining the logic
    - Handle data types and conversions properly
    - Implement proper error handling
    - Use pandas method chaining where beneficial
    - Follow PEP 8 style guidelines
    
    Generate a complete Python script that includes:
    1. Import statements
    2. Function definitions for different phases
    3. Main execution logic
    4. Proper variable management
    5. Error handling
    6. Comments explaining the business logic
    
    Provide only the complete Python code below (no markdown formatting, just pure Python code):
    """

    prompt = PromptTemplate(
        input_variables=["all_descriptions", "extra_user_instructions", "execution_sequence"],
        template=template
    )

    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt)

    final_python_code = chain.run(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence
    ).strip()

    full_prompt = prompt.format(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence
    )

    return final_python_code, full_prompt 