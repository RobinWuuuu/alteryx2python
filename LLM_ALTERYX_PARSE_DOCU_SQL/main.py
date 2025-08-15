#!/usr/bin/env python
"""
main.py

A simple Streamlit-based UI to convert an Alteryx workflow (.yxmd) to SQL code.

Features:
  - Browse for an Alteryx workflow file.
  - Enter an OpenAI API key.
  - (Optional) Fetch child tool IDs by specifying a container tool ID.
  - Input a comma-separated list of tool IDs you want to convert.
  - Run conversion to generate SQL code.
  - Display the final SQL script.
  - Debug logging to trace execution.

Usage:
    streamlit run main.py
"""

import os
import sys
import time
import streamlit as st
import logging
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import io
import base64

# Set page config with BCG branding
st.set_page_config(
    page_title="NPA Alteryx to SQL Converter",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark-mode compatible styling
st.markdown("""
<style>
    /* Dark-mode compatible styling */
    
    /* Main header styling */
    .main-header {
        background: linear-gradient(135deg, #1f77b4, #ff7f0e);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin: 0.5rem 0 0 0;
    }
    
    /* Card styling - dark mode compatible */
    .card {
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #1f77b4;
    }
    
    /* Button hover effects */
    .stButton > button {
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div > div {
        border-radius: 10px;
    }
    
    /* Enhanced Tab styling - dark mode compatible */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        padding: 0 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 12px 12px 0 0;
        font-weight: 600;
        font-size: 1rem;
        padding: 12px 20px;
        margin: 0 2px;
        transition: all 0.3s ease;
        border: 2px solid transparent;
        background: rgba(0, 0, 0, 0.05);
        color: rgba(0, 0, 0, 0.7);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1f77b4, #ff7f0e);
        color: white;
        border: 2px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 12px rgba(31, 119, 180, 0.3);
        transform: translateY(-2px);
    }
    
    /* Dark mode adjustments for tabs */
    @media (prefers-color-scheme: dark) {
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.05);
            color: rgba(255, 255, 255, 0.7);
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            background: rgba(255, 255, 255, 0.1);
        }
    }
    
    /* Code block styling - dark mode compatible */
    .stCodeBlock {
        border-radius: 8px;
        border: 2px solid rgba(0, 0, 0, 0.1);
    }
    
    /* Download button hover effects */
    .stDownloadButton > button {
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
    }
    
    /* File uploader styling - dark mode compatible */
    .stFileUploader > div {
        border-radius: 8px;
    }
    
    /* Text input styling - dark mode compatible */
    .stTextInput > div > div > input {
        border-radius: 6px;
        transition: border-color 0.3s ease;
    }
    
    /* Expander styling - dark mode compatible */
    .streamlit-expanderHeader {
        border-radius: 6px;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        border-radius: 0 0 6px 6px;
    }
</style>
""", unsafe_allow_html=True)

# Configure debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)


def create_tool_connection_graph(df_nodes, df_connections, selected_tool_ids=None):
    """
    Create a visual graph showing tool connections.
    
    Parameters:
        df_nodes (pd.DataFrame): DataFrame containing tool information
        df_connections (pd.DataFrame): DataFrame containing connection information
        selected_tool_ids (list): Optional list of tool IDs to highlight
    
    Returns:
        str: Base64 encoded image of the graph
    """
    # Create a directed graph
    G = nx.DiGraph()
    
    # Add nodes
    for _, row in df_nodes.iterrows():
        tool_id = str(row['tool_id'])
        tool_type = row['tool_type']
        G.add_node(tool_id, tool_type=tool_type)
    
    # Add edges based on connections
    for _, row in df_connections.iterrows():
        source = str(row['origin_tool_id'])
        target = str(row['destination_tool_id'])
        if source in G.nodes and target in G.nodes:
            G.add_edge(source, target)
    
    # Create the plot
    plt.figure(figsize=(20, 14))
    
    # Calculate hierarchical levels using topological sort
    try:
        # Create a proper hierarchical layout based on graph structure
        pos = {}
        
        # Find source nodes (nodes with no incoming edges)
        source_nodes = [node for node in G.nodes() if G.in_degree(node) == 0]
        
        if not source_nodes:
            # If no source nodes found, use any node as starting point
            source_nodes = [list(G.nodes())[0]]
        
        # Use breadth-first search to determine levels
        levels = {}
        visited = set()
        queue = [(node, 0) for node in source_nodes]  # (node, level)
        
        while queue:
            node, level = queue.pop(0)
            if node in visited:
                continue
                
            visited.add(node)
            
            if level not in levels:
                levels[level] = []
            levels[level].append(node)
            
            # Add neighbors to queue with next level
            for neighbor in G.successors(node):
                if neighbor not in visited:
                    queue.append((neighbor, level + 1))
        
        # Handle any remaining unvisited nodes (disconnected components)
        remaining_nodes = [node for node in G.nodes() if node not in visited]
        if remaining_nodes:
            max_level = max(levels.keys()) if levels else 0
            levels[max_level + 1] = remaining_nodes
        
        # Calculate positions
        max_level = max(levels.keys()) if levels else 0
        level_width = 0.8 / (max_level + 1) if max_level > 0 else 0.8
        
        for level, tools in levels.items():
            x = 0.1 + level * level_width  # X position based on level
            tools_in_level = len(tools)
            level_height = 0.8 / max(tools_in_level, 1)
            
            for j, tool_id in enumerate(tools):
                y = 0.1 + j * level_height + level_height / 2
                pos[tool_id] = (x, y)
            
    except Exception as e:
        # Fallback to hierarchical layout if execution order fails
        pos = nx.kamada_kawai_layout(G)
        # Adjust to make it more horizontal
        for node in pos:
            pos[node] = (pos[node][0] * 2, pos[node][1])
    
    # Define colors for different tool types
    tool_colors = {
        'Dbfileinput': '#FF6B6B',      # Red for input
        'Output': '#4ECDC4',           # Teal for output
        'Filter': '#45B7D1',           # Blue for filter
        'Join': '#96CEB4',             # Green for join
        'Union': '#FFEAA7',            # Yellow for union
        'Summarize': '#DDA0DD',        # Plum for summarize
        'Formula': '#98D8C8',          # Mint for formula
        'Sort': '#F7DC6F',             # Gold for sort
        'Unique': '#BB8FCE',           # Purple for unique
        'Sample': '#85C1E9',           # Light blue for sample
        'TextInput': '#F8C471',        # Orange for text input
        'DataCleaning': '#A9DFBF',     # Light green for cleaning
        'Aggregate': '#D7BDE2',        # Light purple for aggregate
        'Transform': '#FAD7A0',        # Light orange for transform
        'Lookup': '#AED6F1',           # Light blue for lookup
        'DateTime': '#F9E79F',         # Light yellow for datetime
        'String': '#D5A6BD',           # Pink for string
        'Numeric': '#A2D9CE',          # Turquoise for numeric
        'Conditional': '#F5B7B1',      # Salmon for conditional
        'Spatial': '#D2B4DE',          # Lavender for spatial
        'Statistical': '#A9CCE3',      # Sky blue for statistical
        'MachineLearning': '#F7DC6F',  # Gold for ML
        'Reporting': '#D7BDE2',        # Light purple for reporting
        'DataQuality': '#A9DFBF',      # Light green for quality
        'ETL': '#FAD7A0',              # Light orange for ETL
        'Analytics': '#AED6F1',        # Light blue for analytics
        'Integration': '#F9E79F',      # Light yellow for integration
        'Automation': '#D5A6BD',       # Pink for automation
        'Optimization': '#A2D9CE',     # Turquoise for optimization
        'Security': '#F5B7B1',         # Salmon for security
        'Compliance': '#D2B4DE',       # Lavender for compliance
        'Scalability': '#A9CCE3',      # Sky blue for scalability
        'Monitoring': '#F7DC6F',       # Gold for monitoring
        'Testing': '#D7BDE2',          # Light purple for testing
        'Documentation': '#A9DFBF',    # Light green for documentation
        'Deployment': '#FAD7A0',       # Light orange for deployment
        'Maintenance': '#AED6F1',      # Light blue for maintenance
        'Troubleshooting': '#F9E79F',  # Light yellow for troubleshooting
        'Innovation': '#D5A6BD',       # Pink for innovation
        'Future': '#A2D9CE'            # Turquoise for future
    }
    
    # Default color for unknown tool types
    default_color = '#E8E8E8'
    
    # Draw nodes with colors based on tool type
    node_colors = []
    node_sizes = []
    node_labels = {}
    
    for node in G.nodes():
        tool_type = G.nodes[node]['tool_type']
        color = tool_colors.get(tool_type, default_color)
        node_colors.append(color)
        
        # Make selected tools larger and more prominent
        if selected_tool_ids and node in selected_tool_ids:
            node_sizes.append(4000)
            node_labels[node] = f"{node}\n({tool_type})"
        else:
            node_sizes.append(2000)
            node_labels[node] = node
    
    # Draw the graph
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, 
                          alpha=0.8, edgecolors='black', linewidths=2)
    
    # Draw edges with arrows - make them curved for better visibility
    nx.draw_networkx_edges(G, pos, edge_color='#666666', arrows=True, arrowsize=25, 
                          arrowstyle='->', width=2.5, alpha=0.7, 
                          connectionstyle='arc3,rad=0.1')
    
    # Draw labels with better positioning
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=10, font_weight='bold',
                           font_color='black', bbox=dict(boxstyle="round,pad=0.3", 
                           facecolor='white', edgecolor='gray', alpha=0.8))
    
    # Create legend
    legend_elements = []
    unique_tool_types = set(G.nodes[node]['tool_type'] for node in G.nodes())
    
    for tool_type in sorted(unique_tool_types):
        color = tool_colors.get(tool_type, default_color)
        legend_elements.append(mpatches.Patch(color=color, label=tool_type))
    
    plt.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1, 1), 
              fontsize=10, title='Tool Types')
    
    plt.title('Alteryx Workflow Tool Connections\n(Left to Right: Execution Order)', 
              fontsize=18, fontweight='bold', pad=30)
    plt.axis('off')
    plt.tight_layout(pad=2.0)
    
    # Convert plot to base64 string
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    img_buffer.seek(0)
    img_str = base64.b64encode(img_buffer.getvalue()).decode()
    plt.close()
    
    return img_str


def set_project_root(marker: str = "README.md"):
    """
    Walk up parent directories until the marker file is found.
    Once found, set that directory as the working directory and add it to sys.path.
    """
    current_dir = Path().resolve()
    logging.debug(f"Starting search for project root from: {current_dir}")
    for parent in [current_dir, *current_dir.parents]:
        if (parent / marker).exists():
            os.chdir(parent)
            if str(parent) not in sys.path:
                sys.path.insert(0, str(parent))
            st.write(f"Working directory set to: {os.getcwd()}")
            return
    raise FileNotFoundError(f"Marker '{marker}' not found in any parent directory of {current_dir}")


# Uncomment below if you want to set the project root automatically.
# set_project_root()

# -- Import project modules (adjust paths as needed) --
try:
    from code import alteryx_parser as parser
    from code import prompt_helper
    from code import traverse_helper
    from code import description_generator

    logging.debug("Project modules imported successfully.")
except Exception as e:
    st.error("Error importing project modules.")
    st.exception(e)
    logging.exception("Error importing project modules.")
    st.stop()

# --------------------- Sidebar ---------------------------
# --------------------- Sidebar ---------------------------
# --------------------- Sidebar ---------------------------

# Sidebar header
st.sidebar.markdown("""
<div style="background: linear-gradient(135deg, #1f77b4, #ff7f0e); color: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center;">
    <h3 style="margin: 0; color: white;"> NPA Alteryx to SQL</h3>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">Data Pipeline Converter</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 Step 1 - Upload Workflow File")
# File uploader: user browses for a .yxmd file.
uploaded_file = st.sidebar.file_uploader("Select Alteryx Workflow File", type=["yxmd", "yxmc"])
st.sidebar.header("🔑 Step 2 - Upload OpenAI API Key")

# Input for the OpenAI API key.
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Model selection
st.sidebar.header("🤖 Step 3 - Select Model")
model_selection = st.sidebar.selectbox(
    "Choose AI Model",
    options=["gpt-4.1","gpt-4o", "gpt-4o-mini", "o1", "o3-mini-high"],
    index=0,
    help="Select the AI model to use for SQL generation. o1 and o3-mini-high are more advanced models that may provide better results."
)

st.sidebar.markdown("---")
st.sidebar.header("Helpers")

st.sidebar.header("🔄 Helper 1 - Get Execution Sequence")
# Sidebar: Button to generate the execution sequence

# Initialize session state for sequence generation if not already set
if "sequence_generated" not in st.session_state:
    st.session_state.sequence_generated = False
if "sequence_str" not in st.session_state:
    st.session_state.sequence_str = ""

if st.sidebar.button("Generate Sequence"):
    if not uploaded_file:
        st.sidebar.warning("Please upload a .yxmd file before generating the execution sequence.")
    else:
        # Save the uploaded file to a temporary path
        temp_file_path = "uploaded_workflow.yxmd"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logging.debug(f"File saved to {temp_file_path} for generating execution sequence.")

        # Load Alteryx data
        df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)

        # Generate execution sequence (list of tool IDs)
        execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
        st.session_state.sequence_str = ", ".join(str(tid) for tid in execution_sequence)

        # Mark sequence as generated in session state
        st.session_state.sequence_generated = True

# If a sequence was generated, display the persistent message and download button
if st.session_state.sequence_generated:
    st.sidebar.write("Execution sequence of current file has been generated.")
    st.sidebar.download_button(
        label="Download Sequence as TXT",
        data=st.session_state.sequence_str,
        file_name="execution_sequence.txt",
        mime="text/plain"
    )




# Input for the container tool ID
st.sidebar.header("📦 Helper 2 - Get Child Tool IDs of Container")

container_tool_id = st.sidebar.text_input("Enter Container Tool ID")
# Container instructions
st.sidebar.markdown("Fetch all child tool IDs of a container.")

# Button to fetch child tool IDs
if st.sidebar.button("Fetch Child Tool IDs"):
    if not uploaded_file:
        st.sidebar.warning("Please upload a .yxmd file before fetching child IDs.")
    else:
        # Save the uploaded file to a temporary path.
        temp_file_path = "uploaded_workflow.yxmd"
        with open(temp_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        logging.debug(f"File saved to {temp_file_path} for container child ID lookup.")

        # Load Alteryx data
        df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)

        # If the user provided a container tool ID
        if container_tool_id:
            df_containers = parser.extract_container_children(df_nodes)
            df_containers = parser.clean_container_children(df_containers, df_nodes)

            # Find the specific container
            container_info = df_containers[df_containers["container_id"] == container_tool_id]
            if not container_info.empty:
                child_tool_ids = list(container_info["child_tools"].values[0])
                child_tool_ids_string = f"[{', '.join(map(str, child_tool_ids))}]"
                st.sidebar.write("**Child Tool IDs:**", child_tool_ids_string)
            else:
                st.sidebar.write("No child tools found for this Container Tool ID.")




# --------------------- Main Content ---------------------------
# --------------------- Main Content ---------------------------

# BCG-styled header
st.markdown("""
<div class="main-header">
    <h1>NPA Alteryx to SQL Converter</h1>
    <p>Transform your Alteryx workflows into production-ready SQL data pipelines</p>
</div>
""", unsafe_allow_html=True)

# Short instructions for the user
st.markdown("""
<div class="card">
    <h3 style="color: #1f77b4; margin-bottom: 1rem;">📋 How to Use this App</h3>
    <ol style="margin: 0; padding-left: 1.5rem;">
        <li><strong>Upload a .yxmd file</strong> in the sidebar.</li>
        <li><strong>Enter your OpenAI API Key</strong> (required for all operations).</li>
        <li><strong>Select your preferred AI model</strong> (gpt-4o, gpt-4o-mini, o1, or o3-mini-high).</li>
        <li><strong>(Optional) Enter a Container Tool ID</strong> and click "Fetch Child Tool IDs" to get child tools for that container.</li>
        <li><strong>Provide your Tool IDs</strong> in the main text box (comma-separated).</li>
        <li><strong>Choose your desired output</strong> using the tabs above:
            <ul style="margin: 0.5rem 0;">
                <li><strong>🚀 Direct Conversion</strong>: Quick and simple conversion from Alteryx tools to SQL code</li>
                <li><strong>⚙️ Advanced Conversion</strong>: Comprehensive workflow with detailed descriptions, structure guide, and production-ready SQL code</li>
                <li><strong>📚 Generation History</strong>: View, manage, and download your previous generation outputs with timestamps</li>
            </ul>
        </li>
    </ol>
</div>
""", unsafe_allow_html=True)
# Input for the tool IDs (comma separated).
tool_ids_input = st.text_input(
    "Tool IDs (comma separated)",
    placeholder="e.g., 644, 645, 646",
    help=("Enter one or more tool IDs separated by commas. For example: '644, 645, 646'. "
          "Only the specified tools will be processed to avoid API limits. "
          "It's recommended to group tools that are logically connected together. "
          "Note: Each tool takes about 3-4 seconds to generate, so parsing 10 tools may take around 30-40 seconds.")
)

extra_user_instructions = st.text_input(
    "Extra User Instruction (optional)",
    placeholder="e.g., These tools help clean the CD data.",
    help="You can provide additional instructions for the SQL generation."
)

# Create tabs for different functionalities
tab1, tab2, tab3, tab4 = st.tabs(["🚀 Direct Conversion", "⚙️ Advanced Conversion", "📊 Tool Connections Graph", "📚 Generation History"])

with tab1:
    st.header("🚀 Direct Conversion")
    st.markdown("**Quick and simple conversion from Alteryx tools to SQL code**")
    # Button to run the conversion
    if st.button("Run Conversion", key="convert_btn"):
        # Basic input validation
        if not uploaded_file or not api_key or not tool_ids_input:
            st.error("Please upload a .yxmd file, provide an API key, and enter tool IDs.")
            logging.error("Missing one or more required inputs.")
        else:
            # Save the uploaded file to a temporary path.
            temp_file_path = "uploaded_workflow.yxmd"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            logging.debug(f"File saved to {temp_file_path} for conversion.")

            # Clean up tool IDs input: remove double quotes/brackets and split by comma.
            tool_ids_clean = tool_ids_input.replace('"', '').replace("'", '').replace("[", '').replace("]", '')
            tool_ids = [tid.strip() for tid in tool_ids_clean.split(",") if tid.strip()]
            logging.debug(f"Parsed tool IDs: {tool_ids}")


            # Set the OpenAI API key as an environment variable.
            os.environ["OPENAI_API_KEY"] = api_key
            logging.debug("OPENAI_API_KEY set in environment.")


            try:
                # Display a message placeholder and a progress bar.
                message_placeholder = st.empty()
                progress_bar = st.progress(0)

                # Load Alteryx nodes and connections from the selected file.
                message_placeholder.write("Parse alteryx file...")
                df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)
                st.write(f"Loaded {len(df_nodes)} nodes and {len(df_connections)} connections.")
                progress_bar.progress(0.05)


                # Filter out unwanted tool types.
                df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
                message_placeholder.write(f"After filtering, {len(df_nodes)} nodes remain.")
                st.write(f"After filtering browser and container, {len(df_nodes)} nodes remain.")

                # Generate SQL code for the specified tool IDs.
                test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]
                message_placeholder.write(f"**Generating SQL code for {len(test_df)} tool(s), it may take {len(test_df)*4} seconds...**")
                logging.debug(f"Generating SQL code for {len(test_df)} tool(s) with tool IDs: {tool_ids}")

                # Generate execution sequence.
                execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
                logging.debug(f"Execution sequence generated with {len(execution_sequence)} steps.")
                message_placeholder.write(f"Execution sequence generated with {len(execution_sequence)} steps.")

                # Adjust the order of tool IDs based on the execution sequence.
                ordered_tool_ids = traverse_helper.adjust_order(tool_ids, execution_sequence)
                st.write(f"Tool IDs ordered has been adjusted based on execution sequence.")
                progress_bar.progress(0.1)

                df_generated_code = prompt_helper.generate_sql_code_from_alteryx_df(test_df, df_connections, progress_bar, message_placeholder, model=model_selection)

                # If "tool_id" is missing in df_generated_code, insert it
                if "tool_id" not in df_generated_code.columns:
                    logging.debug("Adding missing 'tool_id' column to generated code DataFrame.")
                    df_generated_code.insert(0, "tool_id", test_df["tool_id"].values)

                message_placeholder.write("**Working on combining SQL snippets...**")

                # Combine code snippets for the specified tools.
                final_script, prompt = prompt_helper.combine_sql_code_of_tools(tool_ids, df_generated_code, execution_sequence=ordered_tool_ids, extra_user_instructions=extra_user_instructions, model=model_selection)
                message_placeholder.write("**Finished generating SQL code!**")
                progress_bar.progress(1.0)
                st.success("Conversion succeeded! Scroll down to see your SQL code.")
                st.code(final_script, language="sql")
                st.header("Following a prompt was used to generate the SQL code:")
                st.write(f"This app is using {model_selection}, if you want better results, you can try using o1 or o3-mini-high models.")
                st.code(prompt, language="sql")
                
                # Save to history
                if "generation_history" not in st.session_state:
                    st.session_state.generation_history = []
                
                history_item = {
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'type': 'SQL Code Generation',
                    'model_used': model_selection,
                    'tool_ids': ', '.join(tool_ids),
                    'extra_instructions': extra_user_instructions,
                    'output': final_script,
                    'prompt': prompt
                }
                st.session_state.generation_history.append(history_item)

            except Exception as e:
                st.error("Conversion Error:")
                st.exception(e)
                logging.exception("Error during conversion process.")

with tab2:
    st.header("⚙️ Advanced Conversion Generation")
    st.markdown("**Comprehensive workflow with detailed descriptions, structure guide, and production-ready SQL code**")
    
    if st.button("Generate Complete SQL Workflow", key="complete_workflow_btn"):
        if not uploaded_file or not api_key or not tool_ids_input:
            st.error("Please upload a .yxmd file, provide an API key, and enter tool IDs.")
        else:
            # Clean up tool IDs input
            tool_ids_clean = tool_ids_input.replace('"', '').replace("'", '').replace("[", '').replace("]", '')
            tool_ids = [tid.strip() for tid in tool_ids_clean.split(",") if tid.strip()]
            
            # Set the OpenAI API key
            os.environ["OPENAI_API_KEY"] = api_key
            
            try:
                # Save the uploaded file to a temporary path
                temp_file_path = "uploaded_workflow.yxmd"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Load Alteryx data
                df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)
                
                # Filter out unwanted tool types
                df_nodes = df_nodes[~df_nodes["tool_type"].isin(["BrowseV2", "Toolcontainer"])]
                
                # Filter to only the specified tool IDs
                test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]
                
                if test_df.empty:
                    st.error(f"No tools found with the specified IDs: {tool_ids}")
                else:
                    st.write(f"Found {len(test_df)} tool(s) to process: {list(test_df['tool_id'])}")
                    
                    # Check if too many tools are being processed
                    if len(test_df) > 30:
                        st.warning(f"Processing {len(test_df)} tools may take a while and could hit API limits. Consider processing fewer tools at once.")
                    
                    # Check for large tool configurations
                    large_configs = []
                    for _, row in test_df.iterrows():
                        if len(row['text']) > 8000:
                            large_configs.append(f"Tool {row['tool_id']} ({row['tool_type']}) - {len(row['text'])} chars")
                    
                    if large_configs:
                        st.warning(f"Some tools have large configurations that will be truncated: {', '.join(large_configs)}")
                    
                    # Step 1: Generate Tool Descriptions (Concise)
                    st.subheader("Step 1: Generating Tool Descriptions")
                    st.write(f"Generating concise technical descriptions for {len(test_df)} tool(s)...")
                    
                    # Create progress bar for description generation
                    progress_bar = st.progress(0)
                    message_placeholder = st.empty()
                    
                    # Generate descriptions for only the specified tools
                    df_descriptions = description_generator.generate_concise_tool_descriptions(
                        test_df, df_connections, progress_bar, message_placeholder, model=model_selection
                    )
                    
                    st.success("✅ Tool descriptions generated successfully!")
                    
                    # Display the descriptions
                    with st.expander("View Generated Tool Descriptions"):
                        for _, row in df_descriptions.iterrows():
                            st.markdown(f"**Tool {row['tool_id']} ({row['tool_type']}):**")
                            st.write(row['description'])
                            st.markdown("---")
                    
                    # Step 2: Generate SQL Code Structure Guide (Concise)
                    st.subheader("Step 2: Generating SQL Code Structure Guide")
                    st.write("Creating concise guide for SQL code organization...")
                    
                    # Get execution sequence
                    execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
                    ordered_tool_ids = traverse_helper.adjust_order(tool_ids, execution_sequence)
                    
                    with st.spinner("Generating SQL code structure guide..."):
                        workflow_description, workflow_prompt = description_generator.combine_tool_descriptions_for_sql(
                            tool_ids, 
                            df_descriptions, 
                            execution_sequence=", ".join(ordered_tool_ids),
                            extra_user_instructions=extra_user_instructions,
                            model=model_selection
                        )
                    
                    st.success("✅ SQL code structure guide generated successfully!")
                    
                    # Display the structure guide
                    with st.expander("View SQL Code Structure Guide"):
                        st.markdown(workflow_description)
                    
                    # Step 3: Generate Final SQL Code
                    st.subheader("Step 3: Generating Final SQL Code")
                    st.write("Creating complete, working SQL code...")
                    
                    with st.spinner("Generating final SQL code..."):
                        final_sql_code, final_prompt = description_generator.generate_final_sql_code(
                            tool_ids, 
                            df_descriptions, 
                            execution_sequence=", ".join(ordered_tool_ids),
                            extra_user_instructions=extra_user_instructions,
                            workflow_description=workflow_description,
                            model=model_selection
                        )
                    
                    st.success("✅ Final SQL code generated successfully!")
                    
                    # Display the final code with copy functionality
                    st.subheader("Final SQL Code")
                    
                    # Display the code
                    st.code(final_sql_code, language="sql")
                    
                    # Copy functionality with instructions
                    col_copy1, col_copy2 = st.columns([1, 3])
                    with col_copy1:
                        if st.button("📋 Copy Code", key="copy_code_btn"):
                            st.success("Code copied! Use Ctrl+V to paste.")
                            # Store in session state for easy access
                            st.session_state.copied_code = final_sql_code
                    
                    with col_copy2:
                        st.info("💡 Tip: You can also select the code above and copy it directly (Ctrl+A, Ctrl+C)")
                    
                    # Hidden text area for easy copying
                    st.text_area(
                        "Quick copy area (select all and copy):",
                        value=final_sql_code,
                        height=100,
                        key="code_copy_area",
                        help="Select all text and copy (Ctrl+A, Ctrl+C)"
                    )
                    
                    # Download options
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        # Download tool descriptions
                        descriptions_text = ""
                        for _, row in df_descriptions.iterrows():
                            descriptions_text += f"Tool {row['tool_id']} ({row['tool_type']}):\n{row['description']}\n\n"
                        
                        st.download_button(
                            label="Download Tool Descriptions",
                            data=descriptions_text,
                            file_name="tool_descriptions.txt",
                            mime="text/plain"
                        )
                    
                    with col2:
                        # Download structure guide
                        st.download_button(
                            label="Download Code Structure Guide",
                            data=workflow_description,
                            file_name="sql_code_structure_guide.md",
                            mime="text/markdown"
                        )
                    
                    with col3:
                        # Download final SQL code
                        st.download_button(
                            label="Download SQL Code",
                            data=final_sql_code,
                            file_name="final_sql_code.sql",
                            mime="text/plain"
                        )
                    
                    with col4:
                        # Download all outputs combined
                        combined_content = f"""# Complete SQL Workflow Generation Output

Generated by Alteryx to SQL Converter
Date: {time.strftime("%Y-%m-%d %H:%M:%S")}
Model Used: {model_selection}
Tool IDs: {', '.join(tool_ids)}

## 📋 Tool Descriptions

{descriptions_text}

---

## 🏗️ SQL Code Structure Guide

{workflow_description}

---

## 🗄️ Final SQL Code

```sql
{final_sql_code}
```

---

## 📝 Prompts Used

### Tool Descriptions Prompt
(Tool descriptions were generated using the concise technical prompt)

### Code Structure Guide Prompt
{workflow_prompt}

### Final SQL Code Prompt
{final_prompt}

---
*This file contains all outputs from the complete SQL workflow generation process.*
"""
                        
                        st.download_button(
                            label="📥 Download All Outputs",
                            data=combined_content,
                            file_name=f"complete_sql_workflow_output_{time.strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown"
                        )
                    
                    # Show the prompts used
                    with st.expander("View Prompts Used for Code Generation"):
                        st.subheader("Tool Descriptions Prompt")
                        st.code("(Tool descriptions were generated using the concise technical prompt)", language="text")
                        
                        st.subheader("Code Structure Guide Prompt")
                        st.code(workflow_prompt, language="text")
                        
                        st.subheader("Final SQL Code Prompt")
                        st.code(final_prompt, language="text")
                
                # Save to history
                if "generation_history" not in st.session_state:
                    st.session_state.generation_history = []
                
                # Prepare tool descriptions text for history
                descriptions_text = ""
                for _, row in df_descriptions.iterrows():
                    descriptions_text += f"Tool {row['tool_id']} ({row['tool_type']}):\n{row['description']}\n\n"
                
                history_item = {
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'type': 'Complete SQL Workflow',
                    'model_used': model_selection,
                    'tool_ids': ', '.join(tool_ids),
                    'extra_instructions': extra_user_instructions,
                    'tool_descriptions': descriptions_text,
                    'structure_guide': workflow_description,
                    'final_code': final_sql_code,
                    'structure_prompt': workflow_prompt,
                    'final_prompt': final_prompt
                }
                st.session_state.generation_history.append(history_item)
                
            except Exception as e:
                st.error("Error in complete SQL workflow generation:")
                st.exception(e)

with tab3:
    st.header("📊 Tool Connections Graph")
    st.markdown("**Visualize the connections and data flow between selected Alteryx tools**")
    
    if not uploaded_file:
        st.info("Please upload a .yxmd file to generate the tool connections graph.")
    elif not tool_ids_input:
        st.info("Please provide Tool IDs in the main input field to generate a focused graph.")
    else:
        # Parse tool IDs
        tool_ids_clean = tool_ids_input.replace('"', '').replace("'", '').replace("[", '').replace("]", '')
        selected_tool_ids = [tid.strip() for tid in tool_ids_clean.split(",") if tid.strip()]
        
        st.write(f"**Selected Tools:** {', '.join(selected_tool_ids)}")
        
        # Button to generate the graph
        if st.button("🔄 Generate Tool Connections Graph", key="generate_graph_btn"):
            try:
                # Save the uploaded file to a temporary path
                temp_file_path = "uploaded_workflow.yxmd"
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Load Alteryx data
                df_nodes, df_connections = parser.load_alteryx_data(temp_file_path)
                
                # Filter to only the selected tools
                df_nodes_filtered = df_nodes[df_nodes["tool_id"].isin(selected_tool_ids)]
                
                if df_nodes_filtered.empty:
                    st.error(f"No tools found with the specified IDs: {selected_tool_ids}")
                else:
                    st.write(f"Found {len(df_nodes_filtered)} tools to visualize.")
                    
                    # Filter connections to only include selected tools
                    df_connections_filtered = df_connections[
                        (df_connections['origin_tool_id'].isin(selected_tool_ids)) & 
                        (df_connections['destination_tool_id'].isin(selected_tool_ids))
                    ]
                    
                    st.write(f"Found {len(df_connections_filtered)} connections between selected tools.")
                    
                    # Generate the graph
                    with st.spinner("Generating focused tool connections graph..."):
                        graph_img = create_tool_connection_graph(df_nodes_filtered, df_connections_filtered, selected_tool_ids)
                    
                    # Display the graph
                    st.markdown("### Workflow Visualization")
                    st.markdown("""
                    **Graph Legend:**
                    - **Nodes**: Each circle represents a tool, colored by tool type
                    - **Arrows**: Show data flow direction between tools
                    - **Larger nodes**: Highlighted tools (selected tools)
                    - **Colors**: Different colors represent different tool types
                    """)
                    
                    # Display the image
                    st.image(f"data:image/png;base64,{graph_img}", use_column_width=True)
                    
                    # Graph statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Selected Tools", len(df_nodes_filtered))
                    with col2:
                        st.metric("Connections", len(df_connections_filtered))
                    with col3:
                        unique_tool_types = df_nodes_filtered['tool_type'].nunique()
                        st.metric("Tool Types", unique_tool_types)
                    
                    # Tool type breakdown
                    st.subheader("Tool Type Distribution")
                    tool_type_counts = df_nodes_filtered['tool_type'].value_counts()
                    st.bar_chart(tool_type_counts)
                    
                    # Download options
                    col1, col2 = st.columns(2)
                    with col1:
                        # Download graph as PNG
                        st.download_button(
                            label="📥 Download Graph (PNG)",
                            data=base64.b64decode(graph_img),
                            file_name="tool_connections_graph.png",
                            mime="image/png"
                        )
                    
                    with col2:
                        # Download tool summary
                        tool_summary = f"""Focused Tool Connections Summary
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}

Selected Tools: {', '.join(selected_tool_ids)}
Total Selected Tools: {len(df_nodes_filtered)}
Total Connections: {len(df_connections_filtered)}
Tool Types: {unique_tool_types}

Tool Type Breakdown:
{tool_type_counts.to_string()}

Tool Details:
"""
                        for _, row in df_nodes_filtered.iterrows():
                            tool_summary += f"- Tool {row['tool_id']}: {row['tool_type']}\n"
                        
                        st.download_button(
                            label="📥 Download Summary (TXT)",
                            data=tool_summary,
                            file_name="tool_connections_summary.txt",
                            mime="text/plain"
                        )
                    
                    # Connection details
                    if st.checkbox("Show detailed connection information"):
                        st.subheader("Connection Details")
                        connection_details = []
                        for _, conn in df_connections_filtered.iterrows():
                            source_tool = df_nodes_filtered[df_nodes_filtered['tool_id'] == conn['origin_tool_id']]
                            target_tool = df_nodes_filtered[df_nodes_filtered['tool_id'] == conn['destination_tool_id']]
                            
                            if not source_tool.empty and not target_tool.empty:
                                connection_details.append({
                                    'From Tool': f"{conn['origin_tool_id']} ({source_tool.iloc[0]['tool_type']})",
                                    'To Tool': f"{conn['destination_tool_id']} ({target_tool.iloc[0]['tool_type']})",
                                    'Connection Type': 'Data Flow'
                                })
                        
                        if connection_details:
                            st.dataframe(connection_details, use_container_width=True)
                        else:
                            st.info("No connections found between the selected tools.")
            
            except Exception as e:
                st.error("Error generating tool connections graph:")
                st.exception(e)

with tab4:
    st.header("📚 Generation History")
    st.markdown("**View, manage, and download your previous generation outputs with timestamps**")
    
    # Initialize history in session state if not exists
    if "generation_history" not in st.session_state:
        st.session_state.generation_history = []
    
    # Display history
    if not st.session_state.generation_history:
        st.info("No generation history yet. Generate some outputs to see them here!")
    else:
        st.write(f"Found {len(st.session_state.generation_history)} previous generation(s)")
        
        # Sort history by timestamp (newest first)
        sorted_history = sorted(st.session_state.generation_history, key=lambda x: x['timestamp'], reverse=True)
        
        for i, history_item in enumerate(sorted_history):
            model_info = f" - Model: {history_item.get('model_used', 'N/A')}" if 'model_used' in history_item else ""
            with st.expander(f"📅 {history_item['timestamp']} - {history_item['type']}{model_info} - Tools: {history_item['tool_ids']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Type:** {history_item['type']}")
                    st.markdown(f"**Tool IDs:** {history_item['tool_ids']}")
                    if history_item.get('model_used'):
                        st.markdown(f"**Model Used:** {history_item['model_used']}")
                    if history_item.get('extra_instructions'):
                        st.markdown(f"**Extra Instructions:** {history_item['extra_instructions']}")
                
                with col2:
                    # Download button for this history item
                    if history_item['type'] == 'Complete SQL Workflow':
                        combined_content = f"""# Complete SQL Workflow Generation Output

Generated by Alteryx to SQL Converter
Date: {history_item['timestamp']}
Model Used: {history_item.get('model_used', 'N/A')}
Tool IDs: {history_item['tool_ids']}

## 📋 Tool Descriptions

{history_item['tool_descriptions']}

---

## 🏗️ SQL Code Structure Guide

{history_item['structure_guide']}

---

## 🗄️ Final SQL Code

```sql
{history_item['final_code']}
```

---

## 📝 Prompts Used

### Tool Descriptions Prompt
(Tool descriptions were generated using the concise technical prompt)

### Code Structure Guide Prompt
{history_item['structure_prompt']}

### Final SQL Code Prompt
{history_item['final_prompt']}

---
*This file contains all outputs from the complete SQL workflow generation process.*
"""
                        
                        st.download_button(
                            label="📥 Download",
                            data=combined_content,
                            file_name=f"history_{history_item['timestamp'].replace(':', '-').replace(' ', '_')}.md",
                            mime="text/markdown"
                        )
                    else:
                        st.download_button(
                            label="📥 Download",
                            data=history_item['output'],
                            file_name=f"history_{history_item['timestamp'].replace(':', '-').replace(' ', '_')}.sql",
                            mime="text/plain"
                        )
                
                # Display the main output
                if history_item['type'] == 'Complete SQL Workflow':
                    st.subheader("Tool Descriptions")
                    st.write(history_item['tool_descriptions'])
                    
                    st.subheader("SQL Code Structure Guide")
                    st.markdown(history_item['structure_guide'])
                    
                    st.subheader("Final SQL Code")
                    st.code(history_item['final_code'], language="sql")
                else:
                    st.subheader("Generated SQL Code")
                    st.code(history_item['output'], language="sql")
                
                # Delete button
                if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                    st.session_state.generation_history.pop(i)
                    st.rerun()
        
        # Clear all history button
        if st.button("🗑️ Clear All History", key="clear_all_history"):
            st.session_state.generation_history = []
            st.rerun()
