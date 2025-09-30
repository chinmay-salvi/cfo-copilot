# app.py

import streamlit as st
import pandas as pd
from agent.tools import ToolRegistry
from agent.main_agent import MainAgent
from dotenv import load_dotenv

load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Financial Data Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# model = 'qwen/qwen3-32b'
model = 'openai/gpt-oss-20b'

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .execution-log {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .tool-call {
        background-color: #e8eaf6;
        padding: 0.75rem;
        border-radius: 0.3rem;
        margin: 0.5rem 0;
        border-left: 3px solid #3f51b5;
    }
    .success-badge {
        background-color: #4caf50;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.2rem;
        font-size: 0.8rem;
    }
    .error-badge {
        background-color: #f44336;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.2rem;
        font-size: 0.8rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
if 'result' not in st.session_state:
    st.session_state.result = None
if 'processing' not in st.session_state:
    st.session_state.processing = False

# Sidebar configuration
with st.sidebar:
    # Data source info
    st.subheader("📁 Available Data Sources")
    st.markdown("""
    - **actuals.csv** - Monthly financial results
    - **budget.csv** - Monthly budget projections  
    - **fx.csv** - Currency exchange rates
    - **cash.csv** - Cash balances by account
    """)

    st.divider()

    # Example queries
    st.subheader("💡 Example Queries")
    example_queries = [
        "What was June 2025 revenue vs budget in USD?",
        "Break down Opex by category for June.",
        "Show Gross Margin % trend for the last 3 months.",
        "What is our cash runway right now?"
    ]

    for i, query in enumerate(example_queries, 1):
        if st.button(query, key=f"example_{i}", use_container_width=True):
            st.session_state.selected_query = query

# Main content
st.title("📊 Financial Data Analyst Agent")
st.markdown("Ask questions about your financial data and get AI-powered insights with visualizations.")

# Initialize agent
if st.session_state.agent is None:
    with st.spinner("Initializing agent..."):
        tool_registry = ToolRegistry(fixtures_path="fixtures", temp_path="temp")
        st.session_state.agent = MainAgent(tool_registry=tool_registry, model=model)

# Query input
query = st.text_area(
    "Enter your question:",
    value=st.session_state.get('selected_query', ''),
    height=100,
    placeholder="e.g., What was the total revenue for Q2 2025?"
)

col1, col2, col3 = st.columns([1, 1, 4])
with col1:
    analyze_button = st.button("🔍 Analyze", type="primary", use_container_width=True)
with col2:
    clear_button = st.button("🗑️ Clear", use_container_width=True)

if clear_button:
    st.session_state.result = None
    st.session_state.selected_query = ""
    st.rerun()

# Process query
if analyze_button and query:
    st.session_state.processing = True

    with st.spinner("Processing your query..."):
        try:
            result = st.session_state.agent.process_query(query)
            st.session_state.result = result
            st.session_state.processing = False
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")
            st.session_state.processing = False

# Display results
if st.session_state.result:
    result = st.session_state.result

    # Answer section
    st.divider()
    st.subheader("💬 Answer")
    st.markdown(result['answer'])

    # Chart rendering
    if result.get('chart_data'):
        st.divider()
        st.subheader("📈 Visualization")

        chart_data = result['chart_data']
        chart_type = chart_data.get('chart_type')
        data = chart_data.get('data')
        x_col = chart_data.get('x_column')
        y_col = chart_data.get('y_column')

        try:
            if chart_type == 'bar':
                # Convert dict to DataFrame for bar chart
                if isinstance(data, dict):
                    df = pd.DataFrame(list(data.items()), columns=[x_col, y_col])
                else:
                    df = pd.DataFrame(data)
                st.bar_chart(df.set_index(x_col))

            elif chart_type == 'line':
                if isinstance(data, dict):
                    df = pd.DataFrame(list(data.items()), columns=[x_col, y_col])
                else:
                    df = pd.DataFrame(data)
                st.line_chart(df.set_index(x_col))

            elif chart_type == 'area':
                if isinstance(data, dict):
                    df = pd.DataFrame(list(data.items()), columns=[x_col, y_col])
                else:
                    df = pd.DataFrame(data)
                st.area_chart(df.set_index(x_col))

            elif chart_type == 'scatter':
                df = pd.DataFrame(data)
                st.scatter_chart(df, x=x_col, y=y_col)

            elif chart_type == 'pie':
                # For pie charts, use plotly or similar
                df = pd.DataFrame(data)
                st.write("Pie chart data:")
                st.dataframe(df)

        except Exception as e:
            st.error(f"Error rendering chart: {str(e)}")
            st.write("Chart data:", chart_data)