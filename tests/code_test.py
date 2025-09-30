import pytest
from unittest.mock import Mock, MagicMock, patch
import json
from agent.main_agent import MainAgent


class TestMainAgent:
    """Test suite for MainAgent class"""

    @pytest.fixture
    def mock_tool_registry(self):
        """Create a mock tool registry with sample tools"""
        registry = Mock()
        registry.tools = {
            'explore_csv': {
                'description': 'Explore CSV file structure and content',
                'parameters': {
                    'csv_name': 'Name of the CSV file to explore',
                    'columns': 'Specific columns to analyze'
                }
            },
            'extract_csv_data': {
                'description': 'Extract filtered data from CSV',
                'parameters': {
                    'csv_name': 'Name of the CSV file',
                    'filters': 'Filters to apply as JSON object'
                }
            },
            'create_chart': {
                'description': 'Create a chart from data',
                'parameters': {
                    'data': 'Data to visualize as JSON',
                    'chart_type': 'Type of chart (bar, line, etc.)'
                }
            }
        }
        registry.execute_tool = Mock(return_value={
            'success': True,
            'result': {'row_count': 10, 'columns': ['month', 'revenue']}
        })
        return registry

    @pytest.fixture
    def agent(self, mock_tool_registry):
        """Create MainAgent instance with mocked dependencies"""
        with patch('agent.main_agent.Groq') as mock_groq:
            agent = MainAgent(
                model='llama-3.3-70b-versatile',
                tool_registry=mock_tool_registry
            )
            agent.client = mock_groq.return_value
            return agent

    def test_process_query_with_tool_calls(self, agent, mock_tool_registry):
        """Test query processing when model makes tool calls"""
        # Mock Groq API response with tool calls
        mock_tool_call = Mock()
        mock_tool_call.id = 'call_123'
        mock_tool_call.function.name = 'explore_csv'
        mock_tool_call.function.arguments = json.dumps({
            'csv_name': 'actuals.csv',
            'columns': 'revenue'
        })

        # First response: tool call
        mock_response_with_tools = Mock()
        mock_response_with_tools.choices = [Mock()]
        mock_response_with_tools.choices[0].message.tool_calls = [mock_tool_call]
        mock_response_with_tools.choices[0].message.content = None

        # Second response: final answer
        mock_final_response = Mock()
        mock_final_response.choices = [Mock()]
        mock_final_response.choices[0].message.tool_calls = None
        mock_final_response.choices[0].message.content = "The revenue for June 2025 was $500,000."

        # Configure mock to return different responses
        agent.client.chat.completions.create = Mock(
            side_effect=[mock_response_with_tools, mock_final_response]
        )

        # Mock tool execution
        mock_tool_registry.execute_tool.return_value = {
            'success': True,
            'result': {
                'row_count': 1,
                'columns': ['month', 'revenue'],
                'data': [{'month': '2025-06', 'revenue': 500000}]
            }
        }

        # Execute query
        result = agent.process_query("What was June 2025 revenue?")

        # Assertions
        assert result['success'] is True
        assert "revenue" in result['answer'].lower()
        assert result['iterations'] == 2
        assert len(result['execution_log']) == 1
        assert result['execution_log'][0]['tool'] == 'explore_csv'

        # Verify tool was executed
        mock_tool_registry.execute_tool.assert_called_once_with(
            'explore_csv',
            {'csv_name': 'actuals.csv', 'columns': 'revenue'}
        )

        # Verify API was called twice (once for tool call, once for final answer)
        assert agent.client.chat.completions.create.call_count == 2


    def test_process_query_handles_errors_gracefully(self, agent, mock_tool_registry):
        """Test that query processing handles API and tool errors gracefully"""
        # Test Case 1: API exception during first call
        agent.client.chat.completions.create = Mock(
            side_effect=Exception("API connection timeout")
        )

        result = agent.process_query("What was the revenue?")

        assert result['success'] is False
        assert "Error occurred during processing" in result['answer']
        assert "API connection timeout" in result['answer']
        assert result['iterations'] == 1

        # Test Case 2: Tool execution failure
        mock_tool_call = Mock()
        mock_tool_call.id = 'call_456'
        mock_tool_call.function.name = 'extract_csv_data'
        mock_tool_call.function.arguments = json.dumps({
            'csv_name': 'nonexistent.csv',
            'filters': '{}'
        })

        mock_response_with_tools = Mock()
        mock_response_with_tools.choices = [Mock()]
        mock_response_with_tools.choices[0].message.tool_calls = [mock_tool_call]
        mock_response_with_tools.choices[0].message.content = None

        mock_final_response = Mock()
        mock_final_response.choices = [Mock()]
        mock_final_response.choices[0].message.tool_calls = None
        mock_final_response.choices[0].message.content = "Unable to retrieve data due to file not found."

        agent.client.chat.completions.create = Mock(
            side_effect=[mock_response_with_tools, mock_final_response]
        )

        # Mock tool failure
        mock_tool_registry.execute_tool.return_value = {
            'success': False,
            'error': 'CSV file not found: nonexistent.csv'
        }

        result = agent.process_query("Get data from missing file")

        assert result['success'] is True  # Agent completes but reports tool failure
        assert len(result['execution_log']) == 1
        assert result['execution_log'][0]['result']['success'] is False
        assert 'CSV file not found' in result['execution_log'][0]['result']['error']

        # Test Case 3: Malformed tool arguments (invalid JSON)
        mock_tool_call_bad = Mock()
        mock_tool_call_bad.id = 'call_789'
        mock_tool_call_bad.function.name = 'explore_csv'
        mock_tool_call_bad.function.arguments = "not valid json {{"

        mock_response_bad_args = Mock()
        mock_response_bad_args.choices = [Mock()]
        mock_response_bad_args.choices[0].message.tool_calls = [mock_tool_call_bad]
        mock_response_bad_args.choices[0].message.content = None

        mock_recovery_response = Mock()
        mock_recovery_response.choices = [Mock()]
        mock_recovery_response.choices[0].message.tool_calls = None
        mock_recovery_response.choices[0].message.content = "I encountered an error parsing the tool arguments."

        agent.client.chat.completions.create = Mock(
            side_effect=[mock_response_bad_args, mock_recovery_response]
        )

        result = agent.process_query("Test malformed args")

        # Should still complete despite JSON parse error
        assert result['success'] is True
        assert result['iterations'] == 2