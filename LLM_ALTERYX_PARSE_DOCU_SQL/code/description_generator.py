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
    """

    prompt_template = PromptTemplate(
        input_variables=["tool_id", "tool_type", "config_text", "io_context", "additional_context"],
        template=template
    )

    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt_template)

    results = []
    total_tools = len(df_nodes)

    for index, row in df_nodes.iterrows():
        tool_id = row["tool_id"]
        tool_type = row["tool_type"]
        config_text = row["text"]

        # Truncate if too long
        if len(config_text) > 8000:
            config_text = config_text[:8000] + "... [truncated]"

        # Get I/O context
        io_context = create_tool_io_description(df_connections, tool_id)

        # Get additional context for this tool type
        additional_context = comprehensive_guide.get(tool_type, "")

        try:
            description = chain.run({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "config_text": config_text,
                "io_context": io_context,
                "additional_context": additional_context
            })

            results.append({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "description": description.strip()
            })

            # Update progress
            if progress_bar is not None:
                progress = (index + 1) / total_tools
                progress_bar.progress(progress)

            if message_placeholder is not None:
                message_placeholder.write(f"Generated description for tool {tool_id} ({tool_type})")

        except Exception as e:
            print(f"Error generating description for tool {tool_id}: {str(e)}")
            results.append({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "description": f"Error generating description: {str(e)}"
            })

    return pd.DataFrame(results)


def generate_concise_tool_descriptions(df_nodes, df_connections, progress_bar=None, message_placeholder=None, model="gpt-4o"):
    """
    Convert Alteryx tool configurations into super concise technical descriptions for SQL code generation.
    
    Parameters:
        df_nodes (pd.DataFrame): DataFrame containing columns 'tool_id', 'tool_type', and 'text'.
        df_connections (pd.DataFrame): DataFrame containing connection information.
        progress_bar (st.progress): Optional Streamlit progress bar to update during processing.
        message_placeholder: Optional Streamlit placeholder for status messages.
    
    Returns:
        pd.DataFrame: A DataFrame with columns 'tool_id', 'tool_type', and 'description'.
        Each description contains only essential information needed to rebuild the data pipeline.
    """
    template = """
    You are an expert SQL data engineer. Analyze this Alteryx tool configuration and provide a SUPER CONCISE description with only essential information needed to rebuild the data pipeline.
    
    Tool ID: {tool_id}
    Tool type: {tool_type}
    Configuration: {config_text}
    I/O: {io_context}
    
    Instructions:
    1. Keep description under 100 words - be extremely concise
    2. Focus ONLY on essential parameters needed to rebuild the pipeline
    3. Skip technical details like encoding, file paths, or internal configurations
    4. Include only: key columns, filter conditions, join criteria, formulas, aggregations
    5. Use bullet points for easy skimming
    6. Avoid redundant information - we know what the tool type is
    7. Focus on business logic and data transformations
    
    Format as:
    
    **Purpose**: [1-sentence business purpose]
    
    **Key Parameters**:
    • [essential parameter 1]
    • [essential parameter 2]
    • [essential parameter 3]
    
    **Output**: [what this step produces]
    """

    prompt_template = PromptTemplate(
        input_variables=["tool_id", "tool_type", "config_text", "io_context"],
        template=template
    )

    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt_template)

    results = []
    total_tools = len(df_nodes)

    for index, row in df_nodes.iterrows():
        tool_id = row["tool_id"]
        tool_type = row["tool_type"]
        config_text = row["text"]

        # Truncate if too long
        if len(config_text) > 8000:
            config_text = config_text[:8000] + "... [truncated]"

        # Get I/O context
        io_context = create_tool_io_description(df_connections, tool_id)

        try:
            description = chain.run({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "config_text": config_text,
                "io_context": io_context
            })

            results.append({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "description": description.strip()
            })

            # Update progress
            if progress_bar is not None:
                progress = (index + 1) / total_tools
                progress_bar.progress(progress)

            if message_placeholder is not None:
                message_placeholder.write(f"Generated concise description for tool {tool_id} ({tool_type})")

        except Exception as e:
            print(f"Error generating description for tool {tool_id}: {str(e)}")
            results.append({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "description": f"Error generating description: {str(e)}"
            })

    return pd.DataFrame(results)


def combine_tool_descriptions(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="", model="gpt-4o"):
    """
    Combine individual tool descriptions into a comprehensive Python code structure guide.
    
    Parameters:
        tool_ids (list): List of tool IDs to combine.
        df_descriptions (pd.DataFrame): DataFrame containing tool descriptions.
        execution_sequence (str): Optional execution sequence string.
        extra_user_instructions (str): Additional user instructions.
        model (str): Model to use for combination.
    
    Returns:
        tuple: (workflow_description, prompt_used)
    """
    # Filter descriptions for specified tool IDs
    filtered_df = df_descriptions[df_descriptions["tool_id"].isin(tool_ids)]
    
    # Create combined descriptions string
    combined_descriptions = ""
    for _, row in filtered_df.iterrows():
        combined_descriptions += f"\n{row['description']}\n"

    template = """
    You are an expert Python data engineer. Create a comprehensive Python code structure guide based on the following tool descriptions.
    
    Tool IDs: {tool_ids}
    Execution sequence: {execution_sequence}
    Extra user instructions: {extra_user_instructions}
    
    Tool descriptions:
    {combined_descriptions}
    
    Instructions:
    1. Create a detailed Python code structure guide that explains how to implement this workflow
    2. Include recommended imports, data structures, and function organization
    3. Explain the data flow between tools and how to handle dependencies
    4. Provide code structure recommendations and best practices
    5. Include error handling and validation considerations
    6. Suggest appropriate Python libraries and tools
    7. Explain how to handle the execution sequence properly
    8. Include performance optimization recommendations
    9. Provide testing and validation strategies
    10. Make the guide production-ready and comprehensive
    
    Format your response as a detailed markdown guide with clear sections and code examples.
    """
    
    prompt_template = PromptTemplate(
        input_variables=["tool_ids", "execution_sequence", "extra_user_instructions", "combined_descriptions"],
        template=template
    )
    
    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    try:
        workflow_description = chain.run({
            "tool_ids": ", ".join(map(str, tool_ids)),
            "execution_sequence": execution_sequence,
            "extra_user_instructions": extra_user_instructions,
            "combined_descriptions": combined_descriptions
        })
        
        return workflow_description.strip(), template.format(
            tool_ids=", ".join(map(str, tool_ids)),
            execution_sequence=execution_sequence,
            extra_user_instructions=extra_user_instructions,
            combined_descriptions=combined_descriptions
        )
        
    except Exception as e:
        print(f"Error combining tool descriptions: {str(e)}")
        return f"Error creating workflow description: {str(e)}", "Error occurred"


def combine_tool_descriptions_for_sql(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="", model="gpt-4o"):
    """
    Combine individual tool descriptions into a concise SQL code structure guide.
    
    Parameters:
        tool_ids (list): List of tool IDs to combine.
        df_descriptions (pd.DataFrame): DataFrame containing tool descriptions.
        execution_sequence (str): Optional execution sequence string.
        extra_user_instructions (str): Additional user instructions.
        model (str): Model to use for combination.
    
    Returns:
        tuple: (workflow_description, prompt_used)
    """
    # Filter descriptions for specified tool IDs
    filtered_df = df_descriptions[df_descriptions["tool_id"].isin(tool_ids)]
    
    # Create combined descriptions string
    combined_descriptions = ""
    for _, row in filtered_df.iterrows():
        combined_descriptions += f"\n{row['description']}\n"
    
    template = """
    You are an expert SQL data engineer. Create a SUPER CONCISE SQL structure guide based on these tool descriptions.
    
    Tool IDs: {tool_ids}
    Execution sequence: {execution_sequence}
    Extra instructions: {extra_user_instructions}
    
    Tool descriptions:
    {combined_descriptions}
    
    Instructions:
    1. Create a BRIEF SQL structure guide (under 300 words)
    2. Focus ONLY on CTE organization and logical flow
    3. Use bullet points for easy skimming
    4. Skip verbose explanations - be direct and actionable
    5. Include only essential naming conventions and structure tips
    6. Focus on what's needed to rebuild the pipeline quickly
    
    Format as:
    
    **Pipeline Overview**: [1-sentence summary]
    
    **CTE Structure**:
    • [CTE 1 name] - [brief purpose]
    • [CTE 2 name] - [brief purpose]
    • [CTE 3 name] - [brief purpose]
    
    **Key Considerations**:
    • [essential tip 1]
    • [essential tip 2]
    • [essential tip 3]
    """
    
    prompt_template = PromptTemplate(
        input_variables=["tool_ids", "execution_sequence", "extra_user_instructions", "combined_descriptions"],
        template=template
    )
    
    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    try:
        workflow_description = chain.run({
            "tool_ids": ", ".join(map(str, tool_ids)),
            "execution_sequence": execution_sequence,
            "extra_user_instructions": extra_user_instructions,
            "combined_descriptions": combined_descriptions
        })
        
        return workflow_description.strip(), template.format(
            tool_ids=", ".join(map(str, tool_ids)),
            execution_sequence=execution_sequence,
            extra_user_instructions=extra_user_instructions,
            combined_descriptions=combined_descriptions
        )
        
    except Exception as e:
        print(f"Error combining tool descriptions for SQL: {str(e)}")
        return f"Error creating SQL workflow description: {str(e)}", "Error occurred"


def generate_final_python_code(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="", workflow_description="", model="gpt-4o"):
    """
    Generate final Python code based on tool descriptions and workflow guide.
    
    Parameters:
        tool_ids (list): List of tool IDs to include.
        df_descriptions (pd.DataFrame): DataFrame containing tool descriptions.
        execution_sequence (str): Optional execution sequence string.
        extra_user_instructions (str): Additional user instructions.
        workflow_description (str): Workflow structure guide.
        model (str): Model to use for generation.
    
    Returns:
        tuple: (final_code, prompt_used)
    """
    # Filter descriptions for specified tool IDs
    filtered_df = df_descriptions[df_descriptions["tool_id"].isin(tool_ids)]
    
    # Create combined descriptions string
    combined_descriptions = ""
    for _, row in filtered_df.iterrows():
        combined_descriptions += f"\n{row['description']}\n"

    template = """
    You are an expert Python data engineer. Generate complete, production-ready Python code based on the following information.
    
    Tool IDs: {tool_ids}
    Execution sequence: {execution_sequence}
    Extra user instructions: {extra_user_instructions}
    Workflow description: {workflow_description}
    
    Tool descriptions:
    {combined_descriptions}
    
    Instructions:
    1. Generate complete, executable Python code that implements the entire workflow
    2. Follow the workflow description and structure guide provided
    3. Implement all tools in the correct execution sequence
    4. Include all necessary imports and dependencies
    5. Use proper variable naming and data flow between tools
    6. Add comprehensive error handling and validation
    7. Include comments to explain complex logic
    8. Make the code production-ready and maintainable
    9. Follow Python best practices and PEP 8 guidelines
    10. Ensure the code is complete and can be executed directly
    
    Return only the complete Python code without any additional explanations.
    """
    
    prompt_template = PromptTemplate(
        input_variables=["tool_ids", "execution_sequence", "extra_user_instructions", "workflow_description", "combined_descriptions"],
        template=template
    )
    
    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    try:
        final_code = chain.run({
            "tool_ids": ", ".join(map(str, tool_ids)),
            "execution_sequence": execution_sequence,
            "extra_user_instructions": extra_user_instructions,
            "workflow_description": workflow_description,
            "combined_descriptions": combined_descriptions
        })
        
        return final_code.strip(), template.format(
            tool_ids=", ".join(map(str, tool_ids)),
            execution_sequence=execution_sequence,
            extra_user_instructions=extra_user_instructions,
            workflow_description=workflow_description,
            combined_descriptions=combined_descriptions
        )
        
    except Exception as e:
        print(f"Error generating final Python code: {str(e)}")
        return f"# Error generating final Python code: {str(e)}", "Error occurred"


def generate_final_sql_code(tool_ids, df_descriptions, execution_sequence="", extra_user_instructions="", workflow_description="", model="gpt-4o"):
    """
    Generate final SQL code based on tool descriptions and workflow guide.
    
    Parameters:
        tool_ids (list): List of tool IDs to include.
        df_descriptions (pd.DataFrame): DataFrame containing tool descriptions.
        execution_sequence (str): Optional execution sequence string.
        extra_user_instructions (str): Additional user instructions.
        workflow_description (str): Workflow structure guide.
        model (str): Model to use for generation.
    
    Returns:
        tuple: (final_code, prompt_used)
    """
    # Filter descriptions for specified tool IDs
    filtered_df = df_descriptions[df_descriptions["tool_id"].isin(tool_ids)]
    
    # Create combined descriptions string
    combined_descriptions = ""
    for _, row in filtered_df.iterrows():
        combined_descriptions += f"\n{row['description']}\n"
    
    template = """
    You are an expert SQL data engineer. Generate complete, production-ready SQL code based on the following information.
    
    Tool IDs: {tool_ids}
    Execution sequence: {execution_sequence}
    Extra user instructions: {extra_user_instructions}
    Workflow description: {workflow_description}
    
    Tool descriptions:
    {combined_descriptions}
    
    Instructions:
    1. Generate complete, executable SQL code that implements the entire data pipeline
    2. Follow the workflow description and structure guide provided
    3. Implement all tools in the correct execution sequence using CTEs
    4. Use proper table naming and column references between steps
    5. Include comprehensive comments to explain each step
    6. Handle data dependencies and flow between tools properly
    7. Use standard SQL syntax compatible with most databases
    8. Include proper data type handling and conversions
    9. Make the SQL production-ready with error handling considerations
    10. Ensure the final query is complete and can be executed directly
    
    Return only the complete SQL code without any additional explanations.
    """
    
    prompt_template = PromptTemplate(
        input_variables=["tool_ids", "execution_sequence", "extra_user_instructions", "workflow_description", "combined_descriptions"],
        template=template
    )

    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    try:
        final_code = chain.run({
            "tool_ids": ", ".join(map(str, tool_ids)),
            "execution_sequence": execution_sequence,
            "extra_user_instructions": extra_user_instructions,
            "workflow_description": workflow_description,
            "combined_descriptions": combined_descriptions
        })
        
        return final_code.strip(), template.format(
            tool_ids=", ".join(map(str, tool_ids)),
        execution_sequence=execution_sequence,
        extra_user_instructions=extra_user_instructions,
            workflow_description=workflow_description,
            combined_descriptions=combined_descriptions
    )

    except Exception as e:
        print(f"Error generating final SQL code: {str(e)}")
        return f"-- Error generating final SQL code: {str(e)}", "Error occurred" 