# Print working directory
import os
import sys
print(os.getcwd())

from code.traverse_helper import get_input_name, get_output_name
import pandas as pd
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from code.ToolContextDictionary import comprehensive_guide
import streamlit as st


def create_tool_io_template(df_connections, tool_id):
    """
    For a given tool_id, create a template string describing its inputs and outputs.
    The template will use get_input_name and get_output_name to obtain the names.

    Example output:
    "This tool (tool id 583) has 2 input(s): df_580_Output connects to the 'Left', df_582_Output connects to the 'Right'.
     And the 1st output is df_583_Join."
    """
    # Use the helper functions to get input and output names
    input_details = get_input_name(df_connections, tool_id)
    output_details = get_output_name(df_connections, tool_id)

    num_inputs = len(input_details)
    # Build input details string
    if num_inputs == 0:
        input_str = "No inputs"
    else:
        input_str_list = [f"{inp} connects to the '{typ}'" for inp, typ in input_details]
        input_str = ", ".join(input_str_list)

    # Build output details string with ordinal numbers
    num_outputs = len(output_details)
    if num_outputs == 0:
        output_str = "No outputs"
    else:
        output_str_list = []
        for i, out in enumerate(output_details):
            # Determine ordinal representation
            if i == 0:
                ordinal = "1st"
            elif i == 1:
                ordinal = "2nd"
            elif i == 2:
                ordinal = "3rd"
            else:
                ordinal = f"{ i +1}th"
            output_str_list.append(f"name the {ordinal} output as {out}")
        output_str = ", ".join(output_str_list)

    template_text = (f"This tool with id {tool_id} has {num_inputs} input(s), their variable name is {input_str}. Use {input_str} as the input for this tool "
                     f"And {output_str}.")
    return template_text


def generate_python_code_from_alteryx_df(df_nodes, df_connections, progress_bar=None, message_placeholder=None, model="gpt-4o"):
    """
    Convert Alteryx tool configurations in a DataFrame to equivalent Python code,
    incorporating I/O details so the LLM knows which dataframes are expected.

    Parameters:
        df_nodes (pd.DataFrame): DataFrame containing columns 'tool_id', 'tool_type', and 'text'.
        progress_bar (st.progress): Optional Streamlit progress bar to update during processing.

    Returns:
        pd.DataFrame: A DataFrame with columns 'tool_id', 'tool_type', and 'python_code'.
    """
    # Define a prompt template with an additional_instructions placeholder.
    template = """
    You are an expert data engineer. Convert the following Alteryx tool configuration into equivalent Python code using open-source libraries.
    Tool type: {tool_type}
    Configuration details: {config_text}
    I/O details: {io_info}
    Additional instructions: {additional_instructions} In the <DefaultAnnotationText> element, there is a text field that contains the high level description of the tool but it could be empty. You can keep it as comment in the code.
    
    Rules:
    1. Please return only the Python code that reproduces the functionality of this tool.
    2. Include import statements as a comments.
    3. Don't include any function definitions or docstrings.
    4. Don't include sample data, just the code.
    """

    prompt_template = PromptTemplate(
        input_variables=["tool_type", "config_text", "io_info", "additional_instructions"],
        template=template
    )

    # Initialize the ChatOpenAI LLM using your chosen model.
    llm = ChatOpenAI(temperature=0, model_name=model)

    # Create the LangChain LLMChain.
    chain = LLMChain(llm=llm, prompt=prompt_template)

    results = []
    total_tools = len(df_nodes)  # Total number of tools to process
    rest_tools = total_tools

    for index, row in df_nodes.iterrows():
        tool_id = row["tool_id"]
        tool_type = row["tool_type"]
        config_text = row["text"]

        # Truncate config_text if it's too long (to avoid token limits)
        if len(config_text) > 8000:
            config_text = config_text[:8000] + "... [truncated]"

        # Get I/O information for this tool
        io_info = create_tool_io_template(df_connections, tool_id)

        # Get additional instructions for this tool type
        additional_instructions = comprehensive_guide.get(tool_type, "")

        # Generate Python code using the LLM
        try:
            response = chain.run({
                "tool_type": tool_type,
                "config_text": config_text,
                "io_info": io_info,
                "additional_instructions": additional_instructions
            })

            results.append({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "python_code": response.strip()
            })

            # Update progress bar if provided
            if progress_bar is not None:
                progress = (total_tools - rest_tools + 1) / total_tools
                progress_bar.progress(progress)

            # Update message placeholder if provided
            if message_placeholder is not None:
                message_placeholder.write(f"Generated Python code for tool {tool_id} ({tool_type})")

            rest_tools -= 1

        except Exception as e:
            st.error(f"Error generating Python code for tool {tool_id}: {str(e)}")
            # Add a placeholder for failed generations
            results.append({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "python_code": f"# Error generating code for tool {tool_id}: {str(e)}"
            })

    return pd.DataFrame(results)


def generate_sql_code_from_alteryx_df(df_nodes, df_connections, progress_bar=None, message_placeholder=None, model="gpt-4o"):
    """
    Convert Alteryx tool configurations in a DataFrame to equivalent SQL code,
    incorporating I/O details so the LLM knows which tables are expected.

    Parameters:
        df_nodes (pd.DataFrame): DataFrame containing columns 'tool_id', 'tool_type', and 'text'.
        progress_bar (st.progress): Optional Streamlit progress bar to update during processing.

    Returns:
        pd.DataFrame: A DataFrame with columns 'tool_id', 'tool_type', and 'sql_code'.
    """
    # Define a prompt template for SQL generation
    template = """
    You are an expert SQL data engineer. Convert the following Alteryx tool configuration into equivalent SQL code.
    Tool type: {tool_type}
    Configuration details: {config_text}
    I/O details: {io_info}
    Additional instructions: {additional_instructions}
    
    Rules:
    1. Return only the SQL code that reproduces the functionality of this tool.
    2. Use standard SQL syntax compatible with most databases (Snowflake, BigQuery, etc.).
    3. Create CTEs (Common Table Expressions) for intermediate steps when needed.
    4. Use meaningful table aliases and column names.
    5. Include comments to explain complex logic.
    6. Handle data types appropriately (VARCHAR, INTEGER, DECIMAL, DATE, etc.).
    7. For joins, specify the join type clearly (INNER, LEFT, RIGHT, FULL).
    8. For aggregations, use proper GROUP BY clauses.
    9. For filters, use WHERE clauses with proper syntax.
    10. For transformations, use CASE statements or other SQL functions as appropriate.
    
    The SQL should be production-ready and follow best practices.
    """

    prompt_template = PromptTemplate(
        input_variables=["tool_type", "config_text", "io_info", "additional_instructions"],
        template=template
    )

    # Initialize the ChatOpenAI LLM using your chosen model.
    llm = ChatOpenAI(temperature=0, model_name=model)

    # Create the LangChain LLMChain.
    chain = LLMChain(llm=llm, prompt=prompt_template)

    results = []
    total_tools = len(df_nodes)  # Total number of tools to process
    rest_tools = total_tools

    for index, row in df_nodes.iterrows():
        tool_id = row["tool_id"]
        tool_type = row["tool_type"]
        config_text = row["text"]

        # Truncate config_text if it's too long (to avoid token limits)
        if len(config_text) > 8000:
            config_text = config_text[:8000] + "... [truncated]"

        # Get I/O information for this tool
        io_info = create_tool_io_template(df_connections, tool_id)

        # Get additional instructions for this tool type
        additional_instructions = comprehensive_guide.get(tool_type, "")

        # Generate SQL code using the LLM
        try:
            response = chain.run({
                "tool_type": tool_type,
                "config_text": config_text,
                "io_info": io_info,
                "additional_instructions": additional_instructions
            })

            results.append({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "sql_code": response.strip()
            })

            # Update progress bar if provided
            if progress_bar is not None:
                progress = (total_tools - rest_tools + 1) / total_tools
                progress_bar.progress(progress)

            # Update message placeholder if provided
            if message_placeholder is not None:
                message_placeholder.write(f"Generated SQL code for tool {tool_id} ({tool_type})")

            rest_tools -= 1

        except Exception as e:
            st.error(f"Error generating SQL code for tool {tool_id}: {str(e)}")
            # Add a placeholder for failed generations
            results.append({
                "tool_id": tool_id,
                "tool_type": tool_type,
                "sql_code": f"-- Error generating SQL code for tool {tool_id}: {str(e)}"
            })

    return pd.DataFrame(results)


def combine_python_code_of_tools(tool_ids, df_generated_code, execution_sequence="",extra_user_instructions="", model="gpt-4o"):
    """
    Combine individual Python code snippets into a cohesive script.
    
    Parameters:
        tool_ids (list): List of tool IDs to combine.
        df_generated_code (pd.DataFrame): DataFrame containing generated Python code.
        execution_sequence (str): Optional execution sequence string.
        extra_user_instructions (str): Additional user instructions.
        model (str): Model to use for combination.
    
    Returns:
        tuple: (combined_script, prompt_used)
    """
    # Filter the DataFrame to only include the specified tool IDs
    filtered_df = df_generated_code[df_generated_code["tool_id"].isin(tool_ids)]
    
    # Create a combined code string
    combined_code = ""
    for _, row in filtered_df.iterrows():
        combined_code += f"\n# Tool {row['tool_id']} ({row['tool_type']})\n"
        combined_code += row["python_code"]
        combined_code += "\n\n"
    
    # Create a prompt for the LLM to combine and improve the code
    template = """
    You are an expert Python data engineer. Combine the following individual Python code snippets into a cohesive, production-ready script.
    
    Tool IDs to combine: {tool_ids}
    Execution sequence: {execution_sequence}
    Extra user instructions: {extra_user_instructions}
    
    Individual code snippets:
    {combined_code}
    
    Instructions:
    1. Combine all the code snippets into a single, coherent Python script.
    2. Ensure proper variable naming and data flow between tools.
    3. Add necessary import statements at the top.
    4. Add comments to explain the overall workflow.
    5. Handle any dependencies between tools based on the execution sequence.
    6. Make the code production-ready with proper error handling.
    7. Follow Python best practices and PEP 8 style guidelines.
    8. Ensure the code is executable and follows the user's extra instructions.
    
    Return only the final combined Python script.
    """
    
    prompt_template = PromptTemplate(
        input_variables=["tool_ids", "execution_sequence", "extra_user_instructions", "combined_code"],
        template=template
    )
    
    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    try:
        final_script = chain.run({
            "tool_ids": ", ".join(map(str, tool_ids)),
            "execution_sequence": execution_sequence,
            "extra_user_instructions": extra_user_instructions,
            "combined_code": combined_code
        })
        
        return final_script.strip(), template.format(
            tool_ids=", ".join(map(str, tool_ids)),
            execution_sequence=execution_sequence,
            extra_user_instructions=extra_user_instructions,
            combined_code=combined_code
        )
        
    except Exception as e:
        st.error(f"Error combining Python code: {str(e)}")
        return combined_code, "Error occurred during combination"


def combine_sql_code_of_tools(tool_ids, df_generated_code, execution_sequence="", extra_user_instructions="", model="gpt-4o"):
    """
    Combine individual SQL code snippets into a cohesive data pipeline.
    
    Parameters:
        tool_ids (list): List of tool IDs to combine.
        df_generated_code (pd.DataFrame): DataFrame containing generated SQL code.
        execution_sequence (str): Optional execution sequence string.
        extra_user_instructions (str): Additional user instructions.
        model (str): Model to use for combination.
    
    Returns:
        tuple: (combined_script, prompt_used)
    """
    # Filter the DataFrame to only include the specified tool IDs
    filtered_df = df_generated_code[df_generated_code["tool_id"].isin(tool_ids)]
    
    # Create a combined code string
    combined_code = ""
    for _, row in filtered_df.iterrows():
        combined_code += f"\n-- Tool {row['tool_id']} ({row['tool_type']})\n"
        combined_code += row["sql_code"]
        combined_code += "\n\n"
    
    # Create a prompt for the LLM to combine and improve the SQL
    template = """
    You are an expert SQL data engineer. Combine the following individual SQL code snippets into a cohesive, production-ready data pipeline.
    
    Tool IDs to combine: {tool_ids}
    Execution sequence: {execution_sequence}
    Extra user instructions: {extra_user_instructions}
    
    Individual SQL snippets:
    {combined_code}
    
    Instructions:
    1. Combine all the SQL snippets into a single, coherent data pipeline.
    2. Use CTEs (Common Table Expressions) to organize the workflow logically.
    3. Ensure proper table naming and column references between steps.
    4. Add comments to explain each step of the pipeline.
    5. Handle dependencies between tools based on the execution sequence.
    6. Make the SQL production-ready with proper error handling considerations.
    7. Follow SQL best practices and use standard syntax compatible with most databases.
    8. Ensure the final query is executable and follows the user's extra instructions.
    9. Use meaningful CTE names that reflect the business logic.
    10. Include proper data type handling and conversions where needed.
    
    Return only the final combined SQL pipeline.
    """
    
    prompt_template = PromptTemplate(
        input_variables=["tool_ids", "execution_sequence", "extra_user_instructions", "combined_code"],
        template=template
    )
    
    llm = ChatOpenAI(temperature=0, model_name=model)
    chain = LLMChain(llm=llm, prompt=prompt_template)
    
    try:
        final_script = chain.run({
            "tool_ids": ", ".join(map(str, tool_ids)),
            "execution_sequence": execution_sequence,
            "extra_user_instructions": extra_user_instructions,
            "combined_code": combined_code
        })
        
        return final_script.strip(), template.format(
            tool_ids=", ".join(map(str, tool_ids)),
            execution_sequence=execution_sequence,
            extra_user_instructions=extra_user_instructions,
            combined_code=combined_code
        )
        
    except Exception as e:
        st.error(f"Error combining SQL code: {str(e)}")
        return combined_code, "Error occurred during combination"
