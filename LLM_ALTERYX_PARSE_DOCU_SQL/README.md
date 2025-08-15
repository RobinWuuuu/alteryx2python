# NPA Alteryx to SQL Converter

A Streamlit-based application that converts Alteryx workflows (.yxmd files) into production-ready SQL data pipelines.

## Overview

This tool transforms Alteryx workflow configurations into equivalent SQL code, enabling data engineers to migrate from Alteryx to SQL-based data processing. The application provides both direct conversion and advanced workflow generation with comprehensive documentation.

## Features

### 🚀 Direct Conversion
- Quick and simple conversion from Alteryx tools to SQL code
- Individual tool-to-SQL mapping
- Immediate code generation for rapid prototyping

### ⚙️ Advanced Conversion
- **Step 1: Concise Tool Descriptions** - Generate minimal but essential technical descriptions for SQL implementation
- **Step 2: SQL Code Structure Guide** - Create concise guides for SQL data pipeline organization using CTEs
- **Step 3: Final SQL Code** - Generate complete, production-ready SQL data pipelines

### 📊 Tool Connections Graph
- Visualize the connections and data flow between Alteryx tools
- Interactive graph with color-coded tool types
- Highlight selected tools for better focus
- Download graph as PNG image
- View tool type distribution and statistics

### 📚 Generation History
- View, manage, and download previous generation outputs
- Timestamped history with model information
- Export capabilities for all generated content

## Key Differences from Python Version

### 1. SQL-Focused Output
- Generates SQL code instead of Python code
- Uses CTEs (Common Table Expressions) for workflow organization
- Implements SQL-specific patterns and best practices

### 2. Concise Documentation
- **Step 1**: Super concise tool descriptions (under 100 words) with only essential information
- **Step 2**: Brief SQL structure guides (under 300 words) focusing on CTE organization
- Eliminates verbose explanations while maintaining completeness
- Skimmable bullet-point format for quick reading

### 3. SQL-Specific Tool Mappings
- Comprehensive SQL context dictionary for all Alteryx tools
- Database-agnostic SQL syntax (compatible with Snowflake, BigQuery, etc.)
- Focus on standard SQL features and functions

## Supported Alteryx Tools

The tool supports conversion of various Alteryx tools to SQL equivalents:

### Data Input/Output
- **Dbfileinput** → SQL table references and file loading operations
- **Output** → SQL result handling and table creation

### Data Manipulation
- **Alteryxselect** → SQL column selection and data type handling
- **Filter** → SQL WHERE clauses
- **Join** → SQL JOIN operations (INNER, LEFT, RIGHT, FULL)
- **Union** → SQL UNION/UNION ALL operations
- **Summarize** → SQL GROUP BY with aggregations

### Data Transformation
- **Formula** → SQL expressions and calculated columns
- **Sort** → SQL ORDER BY clauses
- **Unique** → SQL DISTINCT and GROUP BY for uniqueness
- **Sample** → SQL sampling functions

### Advanced Operations
- **DataCleaning** → SQL data quality functions
- **Aggregate** → SQL window functions and aggregations
- **Transform** → SQL pivot/unpivot operations
- **Lookup** → SQL JOIN and subquery operations
- **DateTime** → SQL date/time functions
- **String** → SQL string manipulation functions
- **Numeric** → SQL mathematical functions
- **Conditional** → SQL CASE statements

### Specialized Tools
- **Spatial** → SQL spatial data functions
- **Statistical** → SQL statistical functions
- **MachineLearning** → SQL ML features and data preparation
- **Reporting** → SQL reporting and analytics queries
- **DataQuality** → SQL data validation queries
- **ETL** → SQL data pipeline operations
- **Analytics** → SQL analytical functions
- **Integration** → SQL data integration patterns

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd LLM_ALTERYX_PARSE_DOCU_SQL
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your OpenAI API key (required for all operations)

## Usage

### Running the Application

```bash
streamlit run main.py
```

### Step-by-Step Process

1. **Upload Workflow File**: Select your Alteryx .yxmd file
2. **Enter API Key**: Provide your OpenAI API key
3. **Select Model**: Choose from available AI models (gpt-4o, o1, o3-mini-high, etc.)
4. **Enter Tool IDs**: Specify comma-separated tool IDs to convert
5. **Choose Conversion Type**:
   - **Direct Conversion**: Quick SQL code generation
   - **Advanced Conversion**: Complete workflow with documentation
   - **Tool Connections Graph**: Visualize workflow structure and connections
6. **Generate Output**: Review and download your SQL code

### Helper Tools

- **Execution Sequence Generator**: Automatically determine tool execution order
- **Container Child ID Fetcher**: Extract child tool IDs from container tools

## Output Formats

### Direct Conversion
- Individual SQL code snippets for each tool
- Combined SQL pipeline with proper CTE organization
- Copy-ready SQL code with syntax highlighting

### Advanced Conversion
- **Tool Descriptions**: Super concise technical descriptions for each tool
- **SQL Structure Guide**: Brief guide for organizing the SQL pipeline
- **Final SQL Code**: Complete, production-ready SQL data pipeline
- **Download Options**: Individual files or combined documentation

### Tool Connections Graph
- **Interactive Visualization**: Color-coded nodes representing different tool types
- **Data Flow Arrows**: Clear directional arrows showing data movement
- **Tool Highlighting**: Selected tools appear larger for better focus
- **Statistics Dashboard**: Tool counts, connection counts, and type distribution
- **Download Options**: Save graph as PNG or download summary statistics
- **Connection Details**: Expandable view of all tool-to-tool connections

## Example Output Formats

### Super Concise Tool Descriptions
```
Tool 644 (Filter):
**Purpose**: Filter customer data to include only high-value customers

**Key Parameters**:
• Filter: total_sales > 10000
• Filter: region IN ('North', 'South')
• Logic: AND (both conditions)

**Output**: Filtered customer dataset with high-value customers only

Tool 645 (Join):
**Purpose**: Join customer data with order information

**Key Parameters**:
• Join type: LEFT JOIN
• Join key: customer_id
• Tables: customers, orders

**Output**: Enriched customer dataset with order details
```

### Concise SQL Structure Guide
```
**Pipeline Overview**: Customer data filtering and enrichment pipeline

**CTE Structure**:
• filtered_customers - Apply sales and region filters
• customer_orders - Join with order data
• final_summary - Aggregate results by region

**Key Considerations**:
• Use meaningful CTE names reflecting business logic
• Handle NULL values in LEFT JOIN
• Consider performance for large datasets
```

## SQL Code Structure

The generated SQL follows these principles:

### CTE Organization
```sql
WITH 
-- Step 1: Data loading
input_data AS (
    SELECT * FROM source_table
),

-- Step 2: Data cleaning
cleaned_data AS (
    SELECT * FROM input_data 
    WHERE condition = 'valid'
),

-- Step 3: Data transformation
transformed_data AS (
    SELECT 
        column1,
        CASE WHEN condition THEN value1 ELSE value2 END as new_column
    FROM cleaned_data
)

-- Final result
SELECT * FROM transformed_data
```

### Best Practices
- Use meaningful CTE names that reflect business logic
- Include comprehensive comments for each step
- Handle data types and conversions appropriately
- Use standard SQL syntax compatible with most databases
- Implement proper error handling considerations

## Model Selection

Choose from available AI models based on your needs:

- **gpt-4o**: Balanced performance and cost
- **gpt-4o-mini**: Faster, more cost-effective
- **o1**: Advanced reasoning capabilities
- **o3-mini-high**: High-quality output with good performance

## File Structure

```
LLM_ALTERYX_PARSE_DOCU_SQL/
├── main.py                          # Main Streamlit application
├── code/
│   ├── alteryx_parser.py           # Alteryx file parsing
│   ├── description_generator.py    # SQL description generation
│   ├── prompt_helper.py            # SQL prompt management
│   ├── ToolContextDictionary.py    # SQL tool mappings
│   └── traverse_helper.py          # Workflow traversal
├── requirements.txt                 # Python dependencies
└── README.md                       # This file
```

## Requirements

- Python 3.8+
- OpenAI API key
- Streamlit
- LangChain
- Pandas
- Other dependencies listed in requirements.txt

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please:
1. Check existing issues
2. Create a new issue with detailed information
3. Include your Alteryx workflow file (if possible)
4. Specify the tool IDs you're trying to convert

## Roadmap

- [ ] Support for more Alteryx tools
- [ ] Database-specific SQL dialects
- [ ] Performance optimization features
- [ ] Batch processing capabilities
- [ ] Integration with data catalogs
- [ ] Advanced error handling and validation 