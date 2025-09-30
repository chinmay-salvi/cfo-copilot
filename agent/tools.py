# tools.py

import json
from typing import Dict, Any
import pandas as pd


class ToolRegistry:
    def __init__(self, fixtures_path="fixtures", temp_path="temp"):
        self.fixtures_path = fixtures_path
        self.temp_path = temp_path

        self.tools = {
            "explore_csv": {
                "function": self.explore_csv,
                "description": "Explore the structure and content of a CSV file, including data types, unique values, and example data. Use this first to understand what data is available.",
                "parameters": {
                    "csv_name": "Name of the CSV file (e.g., 'actuals.csv', 'budget.csv', 'fx.csv', 'cash.csv')"
                }
            },
            "extract_csv_data": {
                "function": self.extract_csv_data,
                "description": "Extract rows from a CSV file based on specified filter conditions. Returns filtered data with a sample preview. The filters parameter must be a JSON string.",
                "parameters": {
                    "csv_name": "CSV file to load from (e.g., 'actuals.csv', 'budget.csv')",
                    "filters": "JSON string of column-value filters to apply. Example: '{\"month\": \"2023-01\", \"account_category\": \"Revenue\"}' or '{\"entity\": [\"Entity A\", \"Entity B\"]}' for multiple values"
                }
            },
            "create_chart": {
                "function": self.create_chart,
                "description": "Prepare chart configuration (bar, line, pie, area, or scatter) from data. Returns chart config for visualization.",
                "parameters": {
                    "data": "JSON string containing the dataframe data to visualize",
                    "chart_type": "Type of chart: 'bar', 'line', 'pie', 'area', or 'scatter'",
                    "x_column": "Column name of dataframe data to use for the X-axis or categories",
                    "y_column": "Column name of dataframe data to use for the Y-axis or values"
                }
            }
        }

    def explore_csv(self, csv_name: str, max_unique: int = 10) -> Dict[str, Any]:
        """
        Describe a CSV in a consistent schema for LLM usage.

        Parameters:
            csv_name (str): Name of CSV file to explore
            max_unique (int): Threshold to treat column as low-cardinality categorical.

        Returns:
            dict: Structured metadata about the CSV
        """
        try:
            # Load DataFrame
            df = pd.read_csv(f"{self.fixtures_path}/{csv_name}")

            summary = {
                "csv_name": csv_name,
                "num_rows": len(df),
                "num_columns": df.shape[1],
                "columns": {}
            }

            for col in df.columns:
                col_data = df[col].dropna()
                unique_vals = col_data.unique()
                col_summary = {
                    "type": None,
                    "stats": None,
                    "unique_values": None,
                    "top_values": None,
                    "example_values": col_data.sample(n=min(3, len(col_data)), random_state=1).tolist()
                }

                # Numeric
                if pd.api.types.is_numeric_dtype(col_data):
                    col_summary["type"] = "numeric"
                    col_summary["stats"] = {
                        "min": float(col_data.min()),
                        "max": float(col_data.max()),
                        "mean": float(col_data.mean()),
                        "std": float(col_data.std())
                    }

                # Datetime
                elif pd.api.types.is_datetime64_any_dtype(col_data):
                    col_summary["type"] = "datetime"
                    col_summary["stats"] = {
                        "earliest": str(col_data.min()),
                        "latest": str(col_data.max())
                    }

                # Object / Categorical
                else:
                    num_unique = len(unique_vals)
                    col_summary["type"] = "categorical" if num_unique <= max_unique else "object"

                    if num_unique <= max_unique:
                        col_summary["unique_values"] = unique_vals.tolist()
                    else:
                        col_summary["top_values"] = col_data.value_counts().head(5).to_dict()

                summary["columns"][col] = col_summary

            return summary

        except Exception as e:
            raise Exception(f"Error exploring CSV '{csv_name}': {str(e)}")

    def extract_csv_data(self, csv_name: str, filters: str) -> Dict[str, Any]:
        """
        Load CSV and apply filters

        Args:
            csv_name: Name of CSV file (e.g., 'actuals.csv')
            filters: JSON string of filters, e.g., '{"month": "2023-01", "account_category": "Revenue"}'

        Returns:
            Dictionary with extracted data and metadata
        """
        try:
            # Load CSV
            df = pd.read_csv(f"{self.fixtures_path}/{csv_name}")

            # Parse filters
            try:
                filters_dict = json.loads(filters) if isinstance(filters, str) else filters
            except json.JSONDecodeError:
                raise ValueError(f"Invalid JSON in filters parameter: {filters}")

            # Apply filters dynamically
            for column, value in filters_dict.items():
                if column not in df.columns:
                    raise ValueError(
                        f"Column '{column}' not found in {csv_name}. Available columns: {list(df.columns)}")

                if isinstance(value, list):
                    df = df[df[column].isin(value)]
                else:
                    df = df[df[column] == value]

            return {
                "csv_name": csv_name,
                "extracted_data": df.to_dict('records'),
                "row_count": len(df),
                "columns": list(df.columns)
            }

        except Exception as e:
            raise Exception(f"Error extracting data from '{csv_name}': {str(e)}")

    def create_chart(self, chart_type: str, x_column: str, y_column: str, data: str) -> Dict[str, Any]:
        """
        Prepare chart configuration for rendering

        Args:
            chart_type: 'bar', 'line', 'pie', 'area', 'scatter'
            x_column: Column for chart axis
            y_column: Column for chart axis
            data: JSON string of dataframe data

        Returns:
            Dict with chart configuration
        """
        try:
            # Parse data
            data_dict = json.loads(data) if isinstance(data, str) else data
            df = pd.DataFrame(data_dict)

            # Verify columns exist
            if x_column not in df.columns:
                raise ValueError(f"Column '{x_column}' not found. Available: {list(df.columns)}")
            if y_column not in df.columns:
                raise ValueError(f"Column '{y_column}' not found. Available: {list(df.columns)}")

            # Prepare data for charting
            chart_df = df[[x_column, y_column]].copy()

            # Convert to appropriate format based on chart type
            if chart_type in ['bar', 'line', 'area']:
                # Set index for native Streamlit charts
                chart_data = chart_df.set_index(x_column)[y_column].to_dict()
            elif chart_type == 'scatter':
                # Keep as records for scatter
                chart_data = chart_df.to_dict('records')
            elif chart_type == 'pie':
                # Format for pie chart
                chart_data = chart_df.to_dict('records')
            else:
                chart_data = chart_df.to_dict('records')

            return {
                "render_type": "chart",
                "chart_type": chart_type,
                "data": chart_data,
                "x_column": x_column,
                "y_column": y_column,
                "title": f"{y_column} by {x_column}",
                "data_points": len(df),
                "status": "success"
            }

        except Exception as e:
            raise Exception(f"Error creating chart: {str(e)}")

    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions for LLM"""
        descriptions = []
        for tool_name, tool_info in self.tools.items():
            desc = f"**{tool_name}**: {tool_info['description']}\n"
            desc += f"Parameters:\n"
            for param_name, param_desc in tool_info['parameters'].items():
                desc += f"  - {param_name}: {param_desc}\n"
            descriptions.append(desc)
        return "\n".join(descriptions)

    def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool with given parameters"""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found. Available tools: {list(self.tools.keys())}"
            }

        try:
            result = self.tools[tool_name]["function"](**parameters)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "parameters": parameters
            }