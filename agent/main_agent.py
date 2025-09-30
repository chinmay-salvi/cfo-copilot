# main_agent.py

import datetime
from groq import Groq
import json
from typing import Dict, Any, List
import os



class MainAgent:
    def __init__(self, model, tool_registry=None):
        self.model = model
        self.tool_registry = tool_registry
        self.conversation_history = []
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def get_groq_tools(self) -> List[Dict]:
        """Convert tool registry to Groq tool format"""
        groq_tools = []

        for tool_name, tool_info in self.tool_registry.tools.items():
            # Convert parameters to JSON Schema format
            properties = {}
            required = []

            for param_name, param_desc in tool_info['parameters'].items():
                # Determine type based on parameter name and description
                param_type = "string"
                param_schema = {
                    "type": param_type,
                    "description": param_desc
                }

                # Special handling for known structured parameters
                if param_name == "filters":
                    param_schema = {
                        "type": "string",
                        "description": param_desc + " Provide as JSON string."
                    }
                elif param_name in ["group_by", "columns", "on_columns"]:
                    param_schema = {
                        "type": "string",
                        "description": param_desc + " Provide as JSON array string."
                    }
                elif param_name == "data":
                    param_schema = {
                        "type": "string",
                        "description": param_desc + " Provide as JSON string."
                    }

                properties[param_name] = param_schema
                required.append(param_name)

            groq_tool = {
                'type': 'function',
                'function': {
                    'name': tool_name,
                    'description': tool_info['description'],
                    'parameters': {
                        'type': 'object',
                        'properties': properties,
                        'required': required
                    }
                }
            }
            groq_tools.append(groq_tool)

        return groq_tools

    def process_query(self, user_query: str) -> Dict[str, Any]:
        """Main agent processing with Groq tool calling"""

        system_prompt = f"""You are an expert financial data analyst assistant. 
Your role is to provide detailed and accurate insights into business performance using structured CSV datasets. 
Always follow the Required Workflow For Answering Questions and use tools to answer questions.

Date and Time Now:
{datetime.datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")}

Available Data Sources:
1. `actuals.csv` — Monthly financial results.
2. `budget.csv` — Monthly budget projections.
3. `fx.csv` — Monthly Currency exchange rates for conversion between local currencies and USD.
4. `cash.csv` — Cash balances by account.

Required Workflow For Answering Questions:
1. Use `explore_csv` to gather relevant CSV details like column headers, unique values, statistics, etc.
2. Use `extract_csv_data` to get filtered subset of CSV data. Provide filters as JSON string.
3. Use `merge_datasets` strictly for cross-dataset comparisons when required.
4. Use `create_chart` to generate relevant chart for visualization.
5. Provide clear numeric text answers highlight key calculations. 

IMPORTANT NOTES:
- For `extract_csv_data`, the `filters` parameter must be a JSON string, e.g., '{{"month": "2023-01", "account_category": "Revenue"}}'
- For `create_chart`, the `data` parameter must be a JSON string of the extracted data
- When you receive tool results, analyze them carefully before deciding next steps
- Always provide a final answer summarizing your findings with specific numbers and insights in text format.
- Never provide code in final answer text."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]

        # Get available tools in Groq format
        tools = self.get_groq_tools()

        max_iterations = 15
        iteration = 0
        execution_log = []

        while iteration < max_iterations:
            iteration += 1
            print(f"\n{'=' * 60}")
            print(f"Iteration: {iteration}")
            print(f"{'=' * 60}")

            try:
                # Make API call with tools
                chat_completion = self.client.chat.completions.create(
                    messages=messages,
                    model=self.model,
                    tools=tools,
                    tool_choice="auto",  # Let model decide when to use tools
                    temperature=0.7,
                    max_tokens=4096
                )

                response_message = chat_completion.choices[0].message

                # Add assistant's response to messages
                messages.append(response_message)

                # Check if model wants to use tools
                if response_message.tool_calls:
                    print(f"Tool calls count: {len(response_message.tool_calls)}")

                    # Execute each tool call
                    for index, tool_call in enumerate(response_message.tool_calls):
                        tool_name = tool_call.function.name
                        tool_args_str = tool_call.function.arguments

                        print(f"\n--- Tool Call {index + 1} ---")
                        print(f"Tool name: {tool_name}")
                        print(f"Arguments: {tool_args_str}")

                        # Parse arguments
                        try:
                            tool_args = json.loads(tool_args_str)
                        except json.JSONDecodeError as e:
                            tool_args = {}
                            print(f"Warning: Could not parse tool arguments for {tool_name}: {e}")

                        # Execute tool
                        tool_result = self.tool_registry.execute_tool(tool_name, tool_args)

                        print(f"Tool result success: {tool_result.get('success', False)}")
                        if not tool_result.get('success', False):
                            print(f"Tool error: {tool_result.get('error', 'Unknown error')}")
                        else:
                            # Print summary of result
                            result_data = tool_result.get('result', {})
                            if isinstance(result_data, dict):
                                if 'row_count' in result_data:
                                    print(f"Rows returned: {result_data['row_count']}")
                                if 'columns' in result_data:
                                    print(f"Columns: {result_data['columns']}")

                        execution_log.append({
                            "tool": tool_name,
                            "arguments": tool_args,
                            "result": tool_result
                        })

                        # Add tool result to messages in the format Groq expects
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": json.dumps(tool_result)
                        })

                else:
                    # Model provided final answer
                    final_answer = response_message.content

                    # Try to extract chart data from execution log
                    chart_data = None
                    for log_entry in execution_log:
                        if log_entry['tool'] == 'create_chart' and log_entry['result'].get('success'):
                            chart_data = log_entry['result'].get('result', {})

                    print(f"\n{'=' * 60}")
                    print(f"FINAL ANSWER:")
                    print(f"{'=' * 60}")
                    print(final_answer)
                    print(f"{'=' * 60}\n")

                    return {
                        "answer": final_answer,
                        "chart_data": chart_data,
                        "execution_log": execution_log,
                        "success": True,
                        "iterations": iteration
                    }

            except Exception as e:
                print(f"Error in iteration {iteration}: {str(e)}")
                return {
                    "answer": f"Error occurred during processing: {str(e)}",
                    "execution_log": execution_log,
                    "success": False,
                    "iterations": iteration
                }

        return {
            "answer": "Could not complete analysis within iteration limit",
            "execution_log": execution_log,
            "success": False,
            "iterations": max_iterations
        }