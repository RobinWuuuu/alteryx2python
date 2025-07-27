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


def generate_tool_descriptions(df_nodes, df_connections, progress_bar=None, message_placeholder=None, model="gpt-4o"):
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
    
    Important instructions:
    - Don't explicitly include all parameters of the method, only mention the parameters that are used.
    - Warning about ignoring alteryx habit like using "Right_" / '*Unknown' (ignored as per instructions; not a real column) is welcome.
    - Python code snippets are welcome.
    - Keep all the details for human and model to understand the tool and be able to generate the code, but don't include details don't contributes to the code generation.
    
    Provide only the detailed description below:
    """

    prompt_template = PromptTemplate(
        input_variables=["tool_id", "tool_type", "config_text", "io_context", "additional_context"],
        template=template
    )

    llm = ChatOpenAI(temperature=0, model_name=model)
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
    [Brief description of the overall data processing purpose in business language]
    
    ## Python Code Structure Recommendations
    
    ### Function Organization
    [Recommend how to group multiple tools into functions]
    
    ### Variable Naming Strategy
    [Suggest meaningful names for dataframes and variables, it could be reasonably long to help understand]
    
    ### Pythonic Optimizations
    [Identify and call out opportunities for which tools we might be able to combine into a single function, can be concise because we are using python, loops, list comprehensions, functions, etc., e.g., "For tool ID 13,14,15, Use a loop to process multiple files instead of separate tools"]
    
    ### Data Flow Management
    [Explain how to handle data flow between steps, e.g., "Chain operations using method chaining where possible"]
    
    ## Detailed Implementation Guide
    
    ### Phase 1: Data Loading
    [Specific guidance for data loading tools]
    - **Function Name**: [suggested function name]
    - **Variable Names**: [suggested variable names]
    - **Python Patterns**: [specific Python patterns to use]
    
    ### Phase 2: Data Processing
    [Organize the data processing phase by grouping related tools into logical units, referencing their tool IDs, and suggesting how to combine them into Pythonic functions. For each logic unit, provide the recommended function name, the tool IDs it covers, a brief description, and the actual combined Python code that would implement this logic.]

    Here is an example of how you might structure this section:

    ### Logic Unit 1: Data Cleaning and Preprocessing
    - **Tools Included**: [e.g., Tool IDs 3, 5, 7, 8]
    - **Purpose**: These tools perform sequential cleaning steps on the `raw_customer_data` DataFrame, such as removing nulls, standardizing column names, and filtering invalid records. In Python, these can be combined into a single function for clarity and efficiency.
    - **Suggested Function Name**: `clean_customer_data`
    - **Combined Code Example**:
    ```python
    def clean_customer_data(raw_customer_data):
        # Remove rows with missing customer_id
        cleaned = raw_customer_data.dropna(subset=["customer_id"])
        # Standardize column names
        cleaned.columns = [col.lower().strip() for col in cleaned.columns]
        # Filter out inactive customers
        cleaned = cleaned[cleaned["status"] == "active"]
        # Remove duplicate records
        cleaned = cleaned.drop_duplicates()
        return cleaned
    ```

    ### Logic Unit 2: Data Joining and Enrichment
    - **Tools Included**: [e.g., Tool IDs 14, 15, 16]
    - **Purpose**: These tools join the cleaned customer data with sales and region data. In Python, this can be handled in a single function using `pd.merge` for each join.
    - **Suggested Function Name**: `enrich_customer_data`
    - **Combined Code Example**:
    ```python
    def enrich_customer_data(cleaned_customers, sales_data, region_data):
        # Join customer with sales
        customer_sales = cleaned_customers.merge(sales_data, on="customer_id", how="left")
        # Join with region info
        enriched = customer_sales.merge(region_data, on="region_id", how="left")
        return enriched
    ```

    ### Logic Unit 3: Aggregation and Feature Engineering
    - **Tools Included**: [e.g., Tool IDs 21, 22]
    - **Purpose**: These tools aggregate sales by region and compute summary statistics. Combine these into a single aggregation function.
    - **Suggested Function Name**: `aggregate_sales_by_region`
    - **Combined Code Example**:
    ```python
    def aggregate_sales_by_region(enriched_data):
        # Aggregate total sales and customer count by region
        summary = (
            enriched_data.groupby("region_name")
            .agg(total_sales=("sales_amount", "sum"), customer_count=("customer_id", "nunique"))
            .reset_index()
        )
        return summary
    ```

    ### Logic Unit 4: Additional Transformations (if any)
    - **Tools Included**: [e.g., Tool IDs 25, 26]
    - **Purpose**: Apply any additional formulas or transformations, such as calculating sales per customer.
    - **Suggested Function Name**: `calculate_sales_per_customer`
    - **Combined Code Example**:
    ```python
    def calculate_sales_per_customer(summary_df):
        summary_df["sales_per_customer"] = summary_df["total_sales"] / summary_df["customer_count"]
        return summary_df
    ```

    [Continue grouping and describing each logic unit in the workflow, referencing the actual tool IDs and showing the combined Python code for each section. This approach results in a modular, readable, and maintainable Python codebase that mirrors the logical structure of the Alteryx workflow.]
    
    ### Phase 3: Data Output
    [Specific guidance for output tools]
    - **Function Name**: [suggested function name]
    - **Variable Names**: [suggested variable names]
    - **Python Patterns**: [specific Python patterns to use]
    
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


def generate_final_python_code(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="", workflow_description="", model="gpt-4o"):
    """
    Generate working Python code by combining detailed tool descriptions and code structure guidance.
    
    Parameters:
        tool_ids (list): A list of tool IDs to generate code for.
        df_descriptions (pd.DataFrame): DataFrame containing 'tool_id' and 'description' columns.
        execution_sequence (str): The execution order of tools.
        extra_user_instructions (str): Additional instructions for the code generation.
        workflow_description (str): The workflow structure guide generated in step 2.
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
    
    Provide only the complete Python code below (no markdown formatting, just pure Python code):
    """

    prompt = PromptTemplate(
        input_variables=["all_descriptions", "extra_user_instructions", "execution_sequence", "workflow_description"],
        template=template
    )

    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt)

    final_python_code = chain.run(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence,
        workflow_description=workflow_description
    ).strip()

    full_prompt = prompt.format(
        all_descriptions=all_descriptions,
        extra_user_instructions=extra_user_instructions,
        execution_sequence=execution_sequence,
        workflow_description=workflow_description
    )

    return final_python_code, full_prompt 