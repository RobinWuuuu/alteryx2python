#!/usr/bin/env python
"""
example_usage.py

Example script demonstrating how to use the new description generation functionality
programmatically without the Streamlit interface.
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from code import alteryx_parser as parser
from code import description_generator
from code import traverse_helper


def main():
    """
    Example usage of the description generation functionality.
    """
    # Set your OpenAI API key
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"
    
    # Path to your Alteryx workflow file
    workflow_file = "path/to/your/workflow.yxmd"
    
    print("Loading Alteryx workflow...")
    
    # Load Alteryx data
    df_nodes, df_connections = parser.load_alteryx_data(workflow_file)
    
    # Filter out unwanted tool types
    df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
    
    print(f"Loaded {len(df_nodes)} tools from the workflow")
    
    # Generate individual tool descriptions
    print("\nGenerating tool descriptions...")
    df_descriptions = description_generator.generate_tool_descriptions(
        df_nodes, df_connections
    )
    
    # Display individual tool descriptions
    print("\n=== Individual Tool Descriptions ===")
    for _, row in df_descriptions.iterrows():
        print(f"\nTool {row['tool_id']} ({row['tool_type']}):")
        print(f"  {row['description']}")
    
    # Get execution sequence
    execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
    print(f"\nExecution sequence: {execution_sequence}")
    
    # Example: Generate workflow description for first 5 tools
    if len(df_descriptions) >= 5:
        example_tool_ids = [str(tid) for tid in execution_sequence[:5]]
        
        print(f"\n=== Workflow Description (Tools: {example_tool_ids}) ===")
        workflow_description, _ = description_generator.combine_tool_descriptions(
            example_tool_ids, 
            df_descriptions, 
            execution_sequence=", ".join(example_tool_ids),
            extra_user_instructions="This workflow processes customer data for analysis."
        )
        print(workflow_description)
        
        print(f"\n=== Data Steps Summary (Tools: {example_tool_ids}) ===")
        data_steps_summary, _ = description_generator.generate_data_steps_summary(
            example_tool_ids, 
            df_descriptions, 
            execution_sequence=", ".join(example_tool_ids),
            extra_user_instructions="This workflow processes customer data for analysis."
        )
        print(data_steps_summary)
    
    # Save descriptions to files
    print("\nSaving descriptions to files...")
    
    # Save individual descriptions
    with open("tool_descriptions.txt", "w") as f:
        for _, row in df_descriptions.iterrows():
            f.write(f"Tool {row['tool_id']} ({row['tool_type']}):\n{row['description']}\n\n")
    
    # Save workflow description if we have one
    if len(df_descriptions) >= 5:
        with open("workflow_description.md", "w") as f:
            f.write(workflow_description)
        
        with open("data_steps_summary.md", "w") as f:
            f.write(data_steps_summary)
    
    print("Files saved:")
    print("- tool_descriptions.txt: Individual tool descriptions")
    if len(df_descriptions) >= 5:
        print("- workflow_description.md: Combined workflow description")
        print("- data_steps_summary.md: Structured data steps summary")


def example_with_cursor_integration():
    """
    Example showing how to use the descriptions with Cursor or other AI assistants.
    """
    print("\n=== Example for Cursor Integration ===")
    print("""
    To use these descriptions with Cursor or other AI coding assistants:
    
    1. Generate the descriptions using this tool
    2. Provide the following to Cursor:
       - The Alteryx workflow file (.yxmd)
       - The generated descriptions (workflow_description.md)
       - The data steps summary (data_steps_summary.md)
    
    3. Ask Cursor to create a Python implementation like:
       "Create a Jupyter notebook that implements this data processing pipeline:
        [paste the workflow description here]
        
        The pipeline should follow these steps:
        [paste the data steps summary here]
        
        Use pandas and other standard data science libraries."
    
    4. Cursor will generate more accurate Python code based on the business logic
       described in the workflow descriptions.
    """)


if __name__ == "__main__":
    print("Alteryx Description Generator - Example Usage")
    print("=" * 50)
    
    # Check if we have a workflow file to process
    if len(sys.argv) > 1:
        workflow_file = sys.argv[1]
        if os.path.exists(workflow_file):
            main()
        else:
            print(f"Error: Workflow file '{workflow_file}' not found.")
    else:
        print("Usage: python example_usage.py <path_to_workflow.yxmd>")
        print("\nOr run without arguments to see the Cursor integration example:")
        example_with_cursor_integration() 