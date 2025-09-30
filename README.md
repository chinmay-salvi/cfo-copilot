# CFO Copilot - AI Financial Data Analyst

An intelligent AI agent that helps CFOs and finance teams analyze monthly financial data through natural language questions. Built with Groq LLMs and Streamlit.

## 🎯 What It Does

Ask questions like:
- "What was June 2025 revenue vs budget in USD?"
- "Show Gross Margin % trend for the last 3 months"
- "Break down Opex by category for June"
- "What is our cash runway right now?"

Get instant answers with charts and insights.

## 🚀 Quick Start

### Prerequisites
- Python 3.13
- Groq API key

### Installation

1. **Clone the repository**
```bash
git clone <repo-url>
cd cfo-copilot
```

2. **Create and activate virtual environment**

On macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

You should see (venv) in your terminal prompt.

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up your Groq API key**

Edit `.env` and replace the API key:
GROQ_API_KEY='YOUR_GROQ_API_KEY_HERE'

5. **Run the application**
```bash
streamlit run app.py
```

6. **Open your browser**
Navigate to `http://localhost:8501`

## 📁 Project Structure

```
cfo-copilot/
├── app.py                   # Streamlit web interface
├── agent/
│   ├── main_agent.py        # Main AI agent with Groq integration
│   ├── tools.py             # Data analysis tools
│   └── __init__.py
├── fixtures/
│   ├── actuals.csv          # Financial actuals
│   ├── budget.csv           # Budget data
│   ├── fx.csv               # FX rates
│   └── cash.csv             # Cash balances
├── tests/
│   └── code_test.py         # Pytest code file
├── requirements.txt
├── .env                     # Environment variables
└── README.md
```

## 📊 How It Works

1. **User asks a question** in natural language
2. **Agent explores data** using `explore_csv` tool to understand structure
3. **Agent extracts data** using `extract_csv_data` with intelligent filters
4. **Agent creates visualizations** using `create_chart` tool
5. **Agent returns answer** with numbers, insights, and charts

## 🔧 Configuration

### Change AI Model

In `app.py`, modify the model variable:
```python
MODEL = 'openai/gpt-oss-20b'  # or 'qwen/qwen3-32b' or any model which supports tool calling 
```

### Adjust Tool Behavior

Edit `agent/tools.py` to modify:
- Data extraction logic
- Chart types
- Filter capabilities

## 📈 Supported Metrics

- **Revenue**: Actual vs Budget (USD converted)
- **Gross Margin %**: (Revenue - COGS) / Revenue
- **EBITDA**: Revenue - COGS - Opex
- **Opex**: Broken down by category
- **Cash Runway**: Cash ÷ Avg Monthly Burn

## 🧪 Testing

Run tests/code.test.py for testing


## 🎨 Features

- ✅ Natural language query understanding
- ✅ Multi-step reasoning with tool use
- ✅ Automatic chart generation
- ✅ Multi-currency support with FX conversion
- ✅ Real-time execution logging
- ✅ Interactive Streamlit UI
