#!/usr/bin/env python
"""
example_usage.py

Example usage of the NPA Alteryx to SQL Converter.

This file demonstrates how to use the SQL converter programmatically,
showing the key functions and their usage for converting Alteryx workflows to SQL.
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add the code directory to the path
sys.path.append(str(Path(__file__).parent / "code"))

from alteryx_parser import load_alteryx_data, extract_container_children, clean_container_children
from prompt_helper import generate_sql_code_from_alteryx_df, combine_sql_code_of_tools
from description_generator import generate_concise_tool_descriptions, combine_tool_descriptions_for_sql, generate_final_sql_code
from traverse_helper import get_execution_order, adjust_order


def example_direct_sql_conversion():
    """
    Example of direct SQL conversion from Alteryx tools.
    """
    print("=== Direct SQL Conversion Example ===\n")
    
    # Set up your OpenAI API key
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"
    
    # Load Alteryx workflow data
    workflow_file = "path/to/your/workflow.yxmd"
    df_nodes, df_connections = load_alteryx_data(workflow_file)
    
    # Filter out unwanted tool types
    df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
    
    # Specify tool IDs to convert
    tool_ids = ["644", "645", "646"]
    test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]
    
    print(f"Converting {len(test_df)} tools to SQL...")
    
    # Generate SQL code for individual tools
    df_generated_code = generate_sql_code_from_alteryx_df(
        test_df, 
        df_connections, 
        model="gpt-4o"
    )
    
    # Get execution sequence
    execution_sequence = get_execution_order(df_nodes, df_connections)
    ordered_tool_ids = adjust_order(tool_ids, execution_sequence)
    
    # Combine SQL code snippets
    final_sql, prompt = combine_sql_code_of_tools(
        tool_ids, 
        df_generated_code, 
        execution_sequence=ordered_tool_ids,
        extra_user_instructions="These tools help clean customer data.",
        model="gpt-4o"
    )
    
    print("Generated SQL Code:")
    print(final_sql)
    print("\n" + "="*50 + "\n")


def example_advanced_sql_conversion():
    """
    Example of advanced SQL conversion with concise descriptions and structure guide.
    """
    print("=== Advanced SQL Conversion Example ===\n")
    
    # Set up your OpenAI API key
    os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"
    
    # Load Alteryx workflow data
    workflow_file = "path/to/your/workflow.yxmd"
    df_nodes, df_connections = load_alteryx_data(workflow_file)
    
    # Filter out unwanted tool types
    df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
    
    # Specify tool IDs to convert
    tool_ids = ["644", "645", "646"]
    test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]
    
    print(f"Processing {len(test_df)} tools for advanced SQL conversion...")
    
    # Step 1: Generate concise tool descriptions
    print("Step 1: Generating concise tool descriptions...")
    df_descriptions = generate_concise_tool_descriptions(
        test_df, 
        df_connections, 
        model="gpt-4o"
    )
    
    print("Tool Descriptions Generated:")
    for _, row in df_descriptions.iterrows():
        print(f"Tool {row['tool_id']} ({row['tool_type']}):")
        print(row['description'])
        print("-" * 30)
    
    # Step 2: Generate SQL code structure guide
    print("\nStep 2: Generating SQL code structure guide...")
    execution_sequence = get_execution_order(df_nodes, df_connections)
    ordered_tool_ids = adjust_order(tool_ids, execution_sequence)
    
    workflow_description, workflow_prompt = combine_tool_descriptions_for_sql(
        tool_ids, 
        df_descriptions, 
        execution_sequence=", ".join(ordered_tool_ids),
        extra_user_instructions="These tools help clean customer data.",
        model="gpt-4o"
    )
    
    print("SQL Structure Guide:")
    print(workflow_description)
    print("\n" + "="*50)
    
    # Step 3: Generate final SQL code
    print("\nStep 3: Generating final SQL code...")
    final_sql_code, final_prompt = generate_final_sql_code(
        tool_ids, 
        df_descriptions, 
        execution_sequence=", ".join(ordered_tool_ids),
        extra_user_instructions="These tools help clean customer data.",
        workflow_description=workflow_description,
        model="gpt-4o"
    )
    
    print("Final SQL Code:")
    print(final_sql_code)
    print("\n" + "="*50 + "\n")


def example_container_analysis():
    """
    Example of analyzing container tools and their child tools.
    """
    print("=== Container Analysis Example ===\n")
    
    # Load Alteryx workflow data
    workflow_file = "path/to/your/workflow.yxmd"
    df_nodes, df_connections = load_alteryx_data(workflow_file)
    
    # Extract container information
    df_containers = extract_container_children(df_nodes)
    df_containers = clean_container_children(df_containers, df_nodes)
    
    print("Container Analysis:")
    for _, container in df_containers.iterrows():
        container_id = container["container_id"]
        child_tools = container["child_tools"]
        
        print(f"Container {container_id}:")
        print(f"  Child tools: {list(child_tools)}")
        print(f"  Number of child tools: {len(child_tools)}")
        print("-" * 30)
    
    print("\n" + "="*50 + "\n")


def example_execution_sequence():
    """
    Example of generating and analyzing execution sequences.
    """
    print("=== Execution Sequence Example ===\n")
    
    # Load Alteryx workflow data
    workflow_file = "path/to/your/workflow.yxmd"
    df_nodes, df_connections = load_alteryx_data(workflow_file)
    
    # Generate execution sequence
    execution_sequence = get_execution_order(df_nodes, df_connections)
    
    print(f"Total execution sequence length: {len(execution_sequence)}")
    print("Execution sequence:")
    for i, tool_id in enumerate(execution_sequence[:10], 1):  # Show first 10
        print(f"  {i}. Tool {tool_id}")
    
    if len(execution_sequence) > 10:
        print(f"  ... and {len(execution_sequence) - 10} more tools")
    
    # Example of adjusting tool order
    tool_ids = ["644", "645", "646"]
    ordered_tool_ids = adjust_order(tool_ids, execution_sequence)
    
    print(f"\nOriginal tool order: {tool_ids}")
    print(f"Adjusted tool order: {ordered_tool_ids}")
    
    print("\n" + "="*50 + "\n")


def example_sql_output_formats():
    """
    Example of different SQL output formats and structures.
    """
    print("=== SQL Output Formats Example ===\n")
    
    # Example SQL code structure
    example_sql = """
-- Example SQL Data Pipeline Generated from Alteryx Workflow
-- Tools: 644 (Filter), 645 (Join), 646 (Summarize)

WITH 
-- Step 1: Load and filter customer data (Tool 644)
filtered_customers AS (
    SELECT 
        customer_id,
        customer_name,
        region,
        total_sales
    FROM customer_table
    WHERE total_sales > 10000
      AND region IN ('North', 'South')
),

-- Step 2: Join with order data (Tool 645)
customer_orders AS (
    SELECT 
        c.customer_id,
        c.customer_name,
        c.region,
        c.total_sales,
        o.order_id,
        o.order_date,
        o.order_amount
    FROM filtered_customers c
    LEFT JOIN order_table o ON c.customer_id = o.customer_id
),

-- Step 3: Summarize by region (Tool 646)
regional_summary AS (
    SELECT 
        region,
        COUNT(DISTINCT customer_id) as customer_count,
        SUM(order_amount) as total_order_amount,
        AVG(order_amount) as avg_order_amount
    FROM customer_orders
    GROUP BY region
)

-- Final result
SELECT 
    region,
    customer_count,
    total_order_amount,
    avg_order_amount,
    ROUND(avg_order_amount, 2) as formatted_avg
FROM regional_summary
ORDER BY total_order_amount DESC;
"""
    
    print("Example SQL Output Structure:")
    print(example_sql)
    
    print("\nKey Features of Generated SQL:")
    print("1. Uses CTEs (Common Table Expressions) for logical organization")
    print("2. Each tool becomes a named CTE with clear purpose")
    print("3. Includes comprehensive comments explaining each step")
    print("4. Uses meaningful table and column aliases")
    print("5. Implements proper SQL best practices")
    print("6. Compatible with most SQL databases (Snowflake, BigQuery, etc.)")
    
    print("\n" + "="*50 + "\n")


def main():
    """
    Main function to run all examples.
    """
    print("NPA Alteryx to SQL Converter - Example Usage")
    print("=" * 60)
    
    # Note: These examples require actual Alteryx workflow files and OpenAI API keys
    # Uncomment the functions you want to run after setting up your environment
    
    # example_direct_sql_conversion()
    # example_advanced_sql_conversion()
    # example_container_analysis()
    # example_execution_sequence()
    example_sql_output_formats()
    
    print("Example usage completed!")
    print("\nTo use these examples:")
    print("1. Set your OpenAI API key in the environment")
    print("2. Provide a valid path to your Alteryx workflow file")
    print("3. Uncomment the example functions you want to run")
    print("4. Run: python example_usage.py")


if __name__ == "__main__":
    main() 