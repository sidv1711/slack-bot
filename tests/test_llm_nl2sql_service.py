"""Tests for the LLM-powered NL2SQL service."""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.llm_nl2sql_service import LLMBasedNL2SQLService


class TestLLMBasedNL2SQLService:
    """Test cases for the LLM-based NL2SQL service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('src.services.llm_nl2sql_service.get_settings') as mock_settings:
            mock_settings.return_value.openai_api_key = "test-api-key"
            mock_settings.return_value.openai_model = "gpt-4o-mini"
            self.service = LLMBasedNL2SQLService()
    
    @pytest.mark.asyncio
    async def test_convert_to_sql_basic_query(self):
        """Test basic SQL conversion with mocked OpenAI response."""
        mock_response = {
            "sql": "SELECT * FROM test_history WHERE test_uid = 'ABC' ORDER BY execution_time DESC LIMIT 5;",
            "explanation": "Gets the 5 most recent test runs for test ABC"
        }
        
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                MagicMock(message=MagicMock(content=json.dumps(mock_response)))
            ]
            
            result = await self.service.convert_to_sql("Show me the last 5 test runs for test ABC")
            
            assert result == mock_response["sql"]
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_convert_to_sql_with_validation_failure(self):
        """Test that unsafe SQL queries are rejected."""
        unsafe_response = {
            "sql": "DROP TABLE test_history;",
            "explanation": "This would drop the table"
        }
        
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                MagicMock(message=MagicMock(content=json.dumps(unsafe_response)))
            ]
            
            with pytest.raises(ValueError, match="Generated query failed safety validation"):
                await self.service.convert_to_sql("Delete all data")
    
    @pytest.mark.asyncio
    async def test_convert_to_sql_json_parse_error(self):
        """Test handling of malformed JSON response from LLM."""
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                MagicMock(message=MagicMock(content="Invalid JSON response"))
            ]
            
            with pytest.raises(ValueError, match="Invalid response format from LLM"):
                await self.service.convert_to_sql("Show me tests")
    
    @pytest.mark.asyncio
    async def test_convert_to_sql_empty_response(self):
        """Test handling of empty SQL in LLM response."""
        empty_response = {
            "sql": "",
            "explanation": "No query generated"
        }
        
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                MagicMock(message=MagicMock(content=json.dumps(empty_response)))
            ]
            
            with pytest.raises(ValueError, match="LLM did not generate a SQL query"):
                await self.service.convert_to_sql("Show me tests")
    
    def test_validate_query_safe_queries(self):
        """Test validation of safe SQL queries."""
        safe_queries = [
            "SELECT * FROM test_history;",
            "SELECT * FROM test_history WHERE status = 'passed';",
            "SELECT * FROM test_history ORDER BY execution_time DESC LIMIT 5;",
            "SELECT test_uid, status FROM test_history WHERE execution_time > NOW() - INTERVAL '7 days';"
        ]
        
        for query in safe_queries:
            assert self.service.validate_query(query) is True
    
    def test_validate_query_unsafe_queries(self):
        """Test validation rejects unsafe SQL queries."""
        unsafe_queries = [
            "DROP TABLE test_history;",
            "DELETE FROM test_history;",
            "INSERT INTO test_history VALUES (...);",
            "UPDATE test_history SET status = 'hacked';",
            "SELECT * FROM users;",  # Wrong table
            "CREATE TABLE malicious (...);",
            "SELECT * FROM test_history; DROP TABLE test_history;",  # SQL injection attempt
            "SELECT * FROM test_history -- comment",  # SQL comment
            "SELECT * FROM test_history /* comment */;"  # SQL block comment
        ]
        
        for query in unsafe_queries:
            assert self.service.validate_query(query) is False
    
    def test_validate_query_wrong_table(self):
        """Test validation rejects queries for wrong tables."""
        wrong_table_queries = [
            "SELECT * FROM wrong_table;",
            "SELECT * FROM test_data;",
            "SELECT * FROM history;"
        ]
        
        for query in wrong_table_queries:
            assert self.service.validate_query(query) is False
    
    def test_validate_query_non_select(self):
        """Test validation rejects non-SELECT statements."""
        non_select_queries = [
            "TRUNCATE test_history;",
            "EXEC sp_test;",
            "MERGE test_history;",
            "WITH cte AS (...) DELETE FROM test_history;"
        ]
        
        for query in non_select_queries:
            assert self.service.validate_query(query) is False
    
    @pytest.mark.asyncio
    async def test_get_query_explanation(self):
        """Test getting explanations for SQL queries."""
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                MagicMock(message=MagicMock(content="This query finds the last 5 test runs for test ABC"))
            ]
            
            explanation = await self.service.get_query_explanation(
                "Show me the last 5 test runs for test ABC",
                "SELECT * FROM test_history WHERE test_uid = 'ABC' ORDER BY execution_time DESC LIMIT 5;"
            )
            
            assert explanation == "This query finds the last 5 test runs for test ABC"
            mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_query_explanation_error_handling(self):
        """Test error handling in query explanation."""
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            explanation = await self.service.get_query_explanation("test query", "SELECT * FROM test_history;")
            
            assert explanation == "No explanation available"
    
    @pytest.mark.asyncio
    async def test_validate_natural_query_valid(self):
        """Test validation of valid natural language queries."""
        mock_response = {
            "is_valid": True,
            "reason": "Query is asking for test execution data which matches our schema",
            "suggested_rephrase": None
        }
        
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                MagicMock(message=MagicMock(content=json.dumps(mock_response)))
            ]
            
            result = await self.service.validate_natural_query("Show me failed tests")
            
            assert result["is_valid"] is True
            assert "test execution data" in result["reason"]
            assert result["suggested_rephrase"] is None
    
    @pytest.mark.asyncio
    async def test_validate_natural_query_invalid(self):
        """Test validation of invalid natural language queries."""
        mock_response = {
            "is_valid": False,
            "reason": "Query is asking for user data which is not available in test history",
            "suggested_rephrase": "Ask about test execution history instead"
        }
        
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                MagicMock(message=MagicMock(content=json.dumps(mock_response)))
            ]
            
            result = await self.service.validate_natural_query("Show me user login data")
            
            assert result["is_valid"] is False
            assert "user data" in result["reason"]
            assert result["suggested_rephrase"] is not None
    
    @pytest.mark.asyncio
    async def test_validate_natural_query_error_handling(self):
        """Test error handling in natural query validation."""
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API Error")
            
            result = await self.service.validate_natural_query("test query")
            
            assert result["is_valid"] is True  # Default to valid on error
            assert result["reason"] == "Could not validate query"
            assert result["suggested_rephrase"] is None
    
    def test_create_system_prompt(self):
        """Test that system prompt is properly formatted."""
        prompt = self.service._create_system_prompt()
        
        # Check that key elements are in the prompt
        assert "test_history" in prompt
        assert "PostgreSQL" in prompt
        assert "SELECT" in prompt
        assert "NEVER use other tables" in prompt
        assert "JSON object" in prompt
        assert "test_uid" in prompt
        assert "execution_time" in prompt
        assert "status" in prompt
    
    @pytest.mark.asyncio
    async def test_openai_api_call_parameters(self):
        """Test that OpenAI API is called with correct parameters."""
        mock_response = {
            "sql": "SELECT * FROM test_history;",
            "explanation": "Gets all test history"
        }
        
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                MagicMock(message=MagicMock(content=json.dumps(mock_response)))
            ]
            
            await self.service.convert_to_sql("Show me all tests")
            
            # Verify the API call parameters
            call_args = mock_create.call_args
            assert call_args[1]["model"] == "gpt-4o-mini"
            assert call_args[1]["temperature"] == 0.1
            assert call_args[1]["max_tokens"] == 200
            assert call_args[1]["response_format"] == {"type": "json_object"}
            
            # Check messages structure
            messages = call_args[1]["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "system"
            assert messages[1]["role"] == "user"
            assert messages[1]["content"] == "Show me all tests"
    
    @pytest.mark.asyncio
    async def test_complex_query_handling(self):
        """Test handling of complex natural language queries."""
        complex_queries = [
            "Show me failed tests from yesterday that took longer than 5 minutes",
            "What are the most common test failures in the past month?",
            "Find all tests for project ABC that have been failing consistently",
            "Show me test performance trends over the last week"
        ]
        
        mock_response = {
            "sql": "SELECT * FROM test_history WHERE status = 'failed' ORDER BY execution_time DESC;",
            "explanation": "Complex query explanation"
        }
        
        with patch.object(self.service.client.chat.completions, 'create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value.choices = [
                MagicMock(message=MagicMock(content=json.dumps(mock_response)))
            ]
            
            for query in complex_queries:
                result = await self.service.convert_to_sql(query)
                assert result == mock_response["sql"]
                # Verify that each complex query gets processed
                assert mock_create.called 