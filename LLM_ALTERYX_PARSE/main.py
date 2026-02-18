#!/usr/bin/env python
"""
main.py

A simple Streamlit-based UI to convert an Alteryx workflow (.yxmd) to Python code.

Features:
  - Browse for an Alteryx workflow file.
  - Enter an OpenAI API key.
  - (Optional) Fetch child tool IDs by specifying a container tool ID.
  - Input a comma-separated list of tool IDs you want to convert.
  - Run conversion to generate Python code.
  - Display the final Python script.
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

# Set page config with BCG branding
st.set_page_config(
    page_title="NPA Alteryx to Python Converter",
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
    <h3 style="margin: 0; color: white;"> NPA Alteryx to Python</h3>
    <p style="margin: 0.5rem 0 0 0; font-size: 0.9rem; opacity: 0.9;">Workflow Converter</p>
</div>
""", unsafe_allow_html=True)

st.sidebar.header("📁 Step 1 - Upload Workflow File")
# File uploader: user browses for a .yxmd file.
uploaded_file = st.sidebar.file_uploader("Select Alteryx Workflow File", type=["yxmd", "yxmc"])
st.sidebar.header("🔑 Step 2 - Upload OpenAI API Key")

# Input for the OpenAI API key.
api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# Model selection - three models for different stages
MODEL_OPTIONS = [
    "gpt-4.1", "gpt-4o", "gpt-4o-mini", "o1", "o3-mini-high",
    "gpt-5", "gpt-5.2", "gpt-5-mini",
    "gpt-5.1-codex", "gpt-5.1-codex-mini", "gpt-5.1-codex-max",
]
st.sidebar.header("🤖 Step 3 - Select Models")
code_generate_model = st.sidebar.selectbox(
    "Code Generate Model (fast, per-tool)",
    options=MODEL_OPTIONS,
    index=0,
    key="code_generate_model",
    help="Used for generating Python code from each Alteryx tool. Choose a fast model (e.g. gpt-4o-mini, gpt-5.1-codex-mini).",
)
reasoning_model = st.sidebar.selectbox(
    "Reasoning Model (descriptions & structure)",
    options=MODEL_OPTIONS,
    index=0,
    key="reasoning_model",
    help="Used for tool descriptions, code structure guide, and final code in the Complete Python Workflow. Choose a capable model (e.g. gpt-4o, o1, gpt-5).",
)
code_combine_model = st.sidebar.selectbox(
    "Code Combine Model (high quality)",
    options=MODEL_OPTIONS,
    index=0,
    key="code_combine_model",
    help="Used for combining code snippets into the final script. Choose a high-quality model (e.g. gpt-4o, o1, gpt-5).",
)

# Temperature selection
temperature = st.sidebar.slider(
    "Temperature",
    min_value=0.0,
    max_value=2.0,
    value=0.0,
    step=0.1,
    help="Controls randomness in the AI responses. Lower values (0.0-0.3) make responses more focused and deterministic. Higher values (0.7-1.0) make responses more creative and varied."
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
    <h1>NPA Alteryx to Python Converter</h1>
    <p>Transform your Alteryx workflows into production-ready Python code</p>
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
                <li><strong>🚀 Direct Conversion</strong>: Quick and simple conversion from Alteryx tools to Python code</li>
                <li><strong>⚙️ Advanced Conversion</strong>: Comprehensive workflow with detailed descriptions, structure guide, and production-ready Python code</li>
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
    help="You can provide additional instructions for the code generation."
)

# Create tabs for different functionalities
tab1, tab2, tab3 = st.tabs(["🚀 Direct Conversion", "⚙️ Advanced Conversion", "📚 Generation History"])

with tab1:
    st.header("🚀 Direct Conversion")
    st.markdown("**Quick and simple conversion from Alteryx tools to Python code**")
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

                # Generate Python code for the specified tool IDs.
                test_df = df_nodes.loc[df_nodes["tool_id"].isin(tool_ids)]
                message_placeholder.write(f"**Generating code for {len(test_df)} tool(s), it may take {len(test_df)*4} seconds...**")
                logging.debug(f"Generating code for {len(test_df)} tool(s) with tool IDs: {tool_ids}")

                # Generate execution sequence.
                execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
                logging.debug(f"Execution sequence generated with {len(execution_sequence)} steps.")
                message_placeholder.write(f"Execution sequence generated with {len(execution_sequence)} steps.")

                # Adjust the order of tool IDs based on the execution sequence.
                ordered_tool_ids = traverse_helper.adjust_order(tool_ids, execution_sequence)
                st.write(f"Tool IDs ordered has been adjusted based on execution sequence.")
                progress_bar.progress(0.1)

                df_generated_code = prompt_helper.generate_python_code_from_alteryx_df(test_df, df_connections, progress_bar, message_placeholder, model=code_generate_model, temperature=temperature)

                # If "tool_id" is missing in df_generated_code, insert it
                if "tool_id" not in df_generated_code.columns:
                    logging.debug("Adding missing 'tool_id' column to generated code DataFrame.")
                    df_generated_code.insert(0, "tool_id", test_df["tool_id"].values)

                message_placeholder.write("**Working on combining code snippets...**")

                # Combine code snippets for the specified tools.
                final_script, prompt = prompt_helper.combine_python_code_of_tools(tool_ids, df_generated_code, execution_sequence=ordered_tool_ids, extra_user_instructions=extra_user_instructions, model=code_combine_model, temperature=temperature)
                message_placeholder.write("**Finished generating code!**")
                progress_bar.progress(1.0)
                st.success("Conversion succeeded! Scroll down to see your Python code.")
                st.code(final_script, language="python")
                st.header("Following a prompt was used to generate the code:")
                st.write(f"Code generation: **{code_generate_model}**. Code combine: **{code_combine_model}**. For better results, try o1 or o3-mini-high for the combine step.")
                st.code(prompt, language="python")
                
                # Save to history
                if "generation_history" not in st.session_state:
                    st.session_state.generation_history = []
                
                history_item = {
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'type': 'Python Code Generation',
                    'model_used': f"Code Gen: {code_generate_model}, Combine: {code_combine_model}",
                    'temperature': temperature,
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
    st.markdown("**Comprehensive workflow with detailed descriptions, structure guide, and production-ready Python code**")
    
    if st.button("Generate Complete Python Workflow", key="complete_workflow_btn"):
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
                    
                    # Step 1: Generate Tool Descriptions
                    st.subheader("Step 1: Generating Tool Descriptions")
                    st.write(f"Generating detailed technical descriptions for {len(test_df)} tool(s)...")
                    
                    # Create progress bar for description generation
                    progress_bar = st.progress(0)
                    message_placeholder = st.empty()
                    
                    # Generate descriptions for only the specified tools
                    df_descriptions = description_generator.generate_tool_descriptions(
                        test_df, df_connections, progress_bar, message_placeholder, model=reasoning_model, temperature=temperature
                    )
                    
                    st.success("✅ Tool descriptions generated successfully!")
                    
                    # Display the descriptions
                    with st.expander("View Generated Tool Descriptions"):
                        for _, row in df_descriptions.iterrows():
                            st.markdown(f"**Tool {row['tool_id']} ({row['tool_type']}):**")
                            st.write(row['description'])
                            st.markdown("---")
                    
                    # Step 2: Generate Python Code Structure Guide
                    st.subheader("Step 2: Generating Python Code Structure Guide")
                    st.write("Creating comprehensive guide for Python code organization...")
                    
                    # Get execution sequence
                    execution_sequence = traverse_helper.get_execution_order(df_nodes, df_connections)
                    ordered_tool_ids = traverse_helper.adjust_order(tool_ids, execution_sequence)
                    
                    with st.spinner("Generating Python code structure guide..."):
                        workflow_description, workflow_prompt = description_generator.combine_tool_descriptions(
                            tool_ids, 
                            df_descriptions, 
                            execution_sequence=", ".join(ordered_tool_ids),
                            extra_user_instructions=extra_user_instructions,
                            model=reasoning_model,
                            temperature=temperature
                        )
                    
                    st.success("✅ Python code structure guide generated successfully!")
                    
                    # Display the structure guide
                    with st.expander("View Python Code Structure Guide"):
                        st.markdown(workflow_description)
                    
                    # Step 3: Generate Final Python Code
                    st.subheader("Step 3: Generating Final Python Code")
                    st.write("Creating complete, working Python code...")
                    
                    with st.spinner("Generating final Python code..."):
                        final_python_code, final_prompt = description_generator.generate_final_python_code(
                            tool_ids, 
                            df_descriptions, 
                            execution_sequence=", ".join(ordered_tool_ids),
                            extra_user_instructions=extra_user_instructions,
                            workflow_description=workflow_description,
                            model=reasoning_model,
                            temperature=temperature
                        )
                    
                    st.success("✅ Final Python code generated successfully!")
                    
                    # Display the final code with copy functionality
                    st.subheader("Final Python Code")
                    
                    # Display the code
                    st.code(final_python_code, language="python")
                    
                    # Copy functionality with instructions
                    col_copy1, col_copy2 = st.columns([1, 3])
                    with col_copy1:
                        if st.button("📋 Copy Code", key="copy_code_btn"):
                            st.success("Code copied! Use Ctrl+V to paste.")
                            # Store in session state for easy access
                            st.session_state.copied_code = final_python_code
                    
                    with col_copy2:
                        st.info("💡 Tip: You can also select the code above and copy it directly (Ctrl+A, Ctrl+C)")
                    
                    # Hidden text area for easy copying
                    st.text_area(
                        "Quick copy area (select all and copy):",
                        value=final_python_code,
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
                            file_name="python_code_structure_guide.md",
                            mime="text/markdown"
                        )
                    
                    with col3:
                        # Download final Python code
                        st.download_button(
                            label="Download Python Code",
                            data=final_python_code,
                            file_name="final_python_code.py",
                            mime="text/plain"
                        )
                    
                    with col4:
                        # Download all outputs combined
                        combined_content = f"""# Complete Python Workflow Generation Output

Generated by Alteryx to Python Converter
Date: {time.strftime("%Y-%m-%d %H:%M:%S")}
Reasoning Model: {reasoning_model}
Temperature: {temperature}
Tool IDs: {', '.join(tool_ids)}

## 📋 Tool Descriptions

{descriptions_text}

---

## 🏗️ Python Code Structure Guide

{workflow_description}

---

## 🐍 Final Python Code

```python
{final_python_code}
```

---

## 📝 Prompts Used

### Tool Descriptions Prompt
(Tool descriptions were generated using the detailed technical prompt)

### Code Structure Guide Prompt
{workflow_prompt}

### Final Python Code Prompt
{final_prompt}

---
*This file contains all outputs from the complete Python workflow generation process.*
"""
                        
                        st.download_button(
                            label="📥 Download All Outputs",
                            data=combined_content,
                            file_name=f"complete_python_workflow_output_{time.strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown"
                        )
                    
                    # Show the prompts used
                    with st.expander("View Prompts Used for Code Generation"):
                        st.subheader("Tool Descriptions Prompt")
                        st.code("(Tool descriptions were generated using the detailed technical prompt)", language="text")
                        
                        st.subheader("Code Structure Guide Prompt")
                        st.code(workflow_prompt, language="text")
                        
                        st.subheader("Final Python Code Prompt")
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
                    'type': 'Complete Python Workflow',
                    'model_used': f"Reasoning: {reasoning_model}",
                    'temperature': temperature,
                    'tool_ids': ', '.join(tool_ids),
                    'extra_instructions': extra_user_instructions,
                    'tool_descriptions': descriptions_text,
                    'structure_guide': workflow_description,
                    'final_code': final_python_code,
                    'structure_prompt': workflow_prompt,
                    'final_prompt': final_prompt
                }
                st.session_state.generation_history.append(history_item)
                
            except Exception as e:
                st.error("Error in complete Python workflow generation:")
                st.exception(e)

with tab3:
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
            temp_info = f" - Temp: {history_item.get('temperature', 'N/A')}" if 'temperature' in history_item else ""
            with st.expander(f"📅 {history_item['timestamp']} - {history_item['type']}{model_info}{temp_info} - Tools: {history_item['tool_ids']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**Type:** {history_item['type']}")
                    st.markdown(f"**Tool IDs:** {history_item['tool_ids']}")
                    if history_item.get('model_used'):
                        st.markdown(f"**Model Used:** {history_item['model_used']}")
                    if history_item.get('temperature'):
                        st.markdown(f"**Temperature:** {history_item['temperature']}")
                    if history_item.get('extra_instructions'):
                        st.markdown(f"**Extra Instructions:** {history_item['extra_instructions']}")
                
                with col2:
                    # Download button for this history item
                    if history_item['type'] == 'Complete Python Workflow':
                        combined_content = f"""# Complete Python Workflow Generation Output

Generated by Alteryx to Python Converter
Date: {history_item['timestamp']}
Model Used: {history_item.get('model_used', 'N/A')}
Temperature: {history_item.get('temperature', 'N/A')}
Tool IDs: {history_item['tool_ids']}

## 📋 Tool Descriptions

{history_item['tool_descriptions']}

---

## 🏗️ Python Code Structure Guide

{history_item['structure_guide']}

---

## 🐍 Final Python Code

```python
{history_item['final_code']}
```

---

## 📝 Prompts Used

### Tool Descriptions Prompt
(Tool descriptions were generated using the detailed technical prompt)

### Code Structure Guide Prompt
{history_item['structure_prompt']}

### Final Python Code Prompt
{history_item['final_prompt']}

---
*This file contains all outputs from the complete Python workflow generation process.*
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
                            file_name=f"history_{history_item['timestamp'].replace(':', '-').replace(' ', '_')}.py",
                            mime="text/plain"
                        )
                
                # Display the main output
                if history_item['type'] == 'Complete Python Workflow':
                    st.subheader("Tool Descriptions")
                    st.write(history_item['tool_descriptions'])
                    
                    st.subheader("Python Code Structure Guide")
                    st.markdown(history_item['structure_guide'])
                    
                    st.subheader("Final Python Code")
                    st.code(history_item['final_code'], language="python")
                else:
                    st.subheader("Generated Python Code")
                    st.code(history_item['output'], language="python")
                
                # Delete button
                if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                    st.session_state.generation_history.pop(i)
                    st.rerun()
        
        # Clear all history button
        if st.button("🗑️ Clear All History", key="clear_all_history"):
            st.session_state.generation_history = []
            st.rerun()
