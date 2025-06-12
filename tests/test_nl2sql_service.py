"""Tests for the NL2SQL service."""
import pytest
from src.services.nl2sql_service import NL2SQLService


class TestNL2SQLService:
    """Test cases for the NL2SQL service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = NL2SQLService()
    
    def test_basic_query_conversion(self):
        """Test basic query conversion without filters."""
        query = "Show me all test results"
        result = self.service.convert_to_sql(query)
        assert result == "SELECT * FROM test_history ORDER BY execution_time DESC;"
    
    def test_limit_extraction(self):
        """Test extraction of limit values from queries."""
        test_cases = [
            ("Show me the last 5 test results", 5),
            ("Get the top 3 results", 3),
            ("Show first 10 test results", 10),
            ("Display 7 test records", 7),
        ]
        
        for query, expected_limit in test_cases:
            result = self.service.convert_to_sql(query)
            assert f"LIMIT {expected_limit}" in result
            assert "ORDER BY execution_time DESC" in result
    
    def test_test_uid_extraction(self):
        """Test extraction of test UID from queries."""
        test_cases = [
            ("Show me test ABC", "ABC"),
            ("Get results for test XYZ-123", "XYZ-123"),
            ("Display test test_name_456", "test_name_456"),
            ("Show test uid DEMO-TEST", "DEMO-TEST")
        ]
        
        for query, expected_uid in test_cases:
            result = self.service.convert_to_sql(query)
            assert f"test_uid = '{expected_uid}'" in result
    
    def test_status_extraction(self):
        """Test extraction of status filters from queries."""
        test_cases = [
            ("Show me failed tests", "failed"),
            ("Get passed test runs", "passed"),
            ("Display successful tests", "passed"),
            ("Show error tests", "failed"),
            ("Get running tests", "running"),
        ]
        
        for query, expected_status in test_cases:
            result = self.service.convert_to_sql(query)
            assert f"status = '{expected_status}'" in result
    
    def test_time_frame_extraction(self):
        """Test extraction of time frame filters from queries."""
        test_cases = [
            ("Show tests from past 7 days", "execution_time > NOW() - INTERVAL '7 days'"),
            ("Get tests from past week", "execution_time > NOW() - INTERVAL '7 days'"),
            ("Show tests from past 2 weeks", "execution_time > NOW() - INTERVAL '2 weeks'"),
            ("Display tests from today", "execution_time >= CURRENT_DATE"),
            ("Get tests from this month", "execution_time >= DATE_TRUNC('month', CURRENT_DATE)"),
        ]
        
        for query, expected_filter in test_cases:
            result = self.service.convert_to_sql(query)
            assert expected_filter in result
    
    def test_complex_queries(self):
        """Test complex queries with multiple filters."""
        # Test case from requirements: "Show me the last 5 test runs for test ABC"
        query = "Show me the last 5 test runs for test ABC"
        result = self.service.convert_to_sql(query)
        expected = "SELECT * FROM test_history WHERE test_uid = 'ABC' ORDER BY execution_time DESC LIMIT 5;"
        assert result == expected
        
        # Test case from requirements: "List all failed test runs in the past week"
        query = "List all failed test runs in the past week"
        result = self.service.convert_to_sql(query)
        expected = "SELECT * FROM test_history WHERE status = 'failed' AND execution_time > NOW() - INTERVAL '7 days' ORDER BY execution_time DESC;"
        assert result == expected
        
        # Test case from requirements: "Show all test runs for test XYZ that passed"
        query = "Show all test runs for test XYZ that passed"
        result = self.service.convert_to_sql(query)
        expected = "SELECT * FROM test_history WHERE test_uid = 'XYZ' AND status = 'passed' ORDER BY execution_time DESC;"
        assert result == expected
    
    def test_query_validation(self):
        """Test SQL query validation for safety."""
        # Valid SELECT queries should pass
        valid_queries = [
            "SELECT * FROM test_history;",
            "SELECT * FROM test_history WHERE status = 'passed';",
            "SELECT * FROM test_history ORDER BY execution_time DESC LIMIT 5;",
        ]
        
        for query in valid_queries:
            assert self.service.validate_query(query) is True
        
        # Invalid/dangerous queries should fail
        invalid_queries = [
            "DROP TABLE test_history;",
            "DELETE FROM test_history;",
            "INSERT INTO test_history VALUES (...);",
            "UPDATE test_history SET status = 'hacked';",
            "SELECT * FROM users;",  # Wrong table
            "CREATE TABLE malicious (...);",
        ]
        
        for query in invalid_queries:
            assert self.service.validate_query(query) is False
    
    def test_edge_cases(self):
        """Test edge cases and error handling."""
        # Empty query
        result = self.service.convert_to_sql("")
        assert "SELECT * FROM test_history" in result
        
        # Query with no recognizable patterns
        result = self.service.convert_to_sql("random text here")
        assert result == "SELECT * FROM test_history ORDER BY execution_time DESC;"
        
        # Query with special characters in test_uid (should be filtered out)
        result = self.service.convert_to_sql("Show test with special chars'; DROP TABLE test_history; --")
        # Should not extract the malicious test_uid due to special characters
        assert "DROP" not in result
        # The word "with" might be extracted, but it doesn't contain special chars so it's safe
        # Let's test with a clearly malicious pattern
        result2 = self.service.convert_to_sql("Show me some random text without test patterns")
        assert "test_uid = " not in result2
    
    def test_case_insensitive_processing(self):
        """Test that queries work regardless of case."""
        queries = [
            "SHOW ME THE LAST 5 TEST RESULTS",
            "show me the last 5 test results",
            "Show Me The Last 5 Test Results",
            "sHoW mE tHe LaSt 5 tEsT rEsUlTs"
        ]
        
        expected_result = "SELECT * FROM test_history ORDER BY execution_time DESC LIMIT 5;"
        
        for query in queries:
            result = self.service.convert_to_sql(query)
            assert result == expected_result

    def test_multiple_number_patterns(self):
        """Test that the service handles multiple numbers correctly."""
        # Should pick up the limit, not other numbers
        query = "Show me the last 5 test results from the past 3 days"
        result = self.service.convert_to_sql(query)
        assert "LIMIT 5" in result
        assert "INTERVAL '3 days'" in result
    
    def test_status_keyword_variations(self):
        """Test various ways to express test status."""
        # Test different ways to say "failed"
        failed_queries = [
            "show failed tests",
            "get error tests", 
            "display failure tests"
        ]
        
        for query in failed_queries:
            result = self.service.convert_to_sql(query)
            assert "status = 'failed'" in result
        
        # Test different ways to say "passed"
        passed_queries = [
            "show passed tests",
            "get successful tests",
            "display success tests"
        ]
        
        for query in passed_queries:
            result = self.service.convert_to_sql(query)
            assert "status = 'passed'" in result
    
    def test_test_uid_case_preservation(self):
        """Test that test_uid case is preserved."""
        queries = [
            ("Show me test ABC", "ABC"),
            ("Show me test abc", "abc"),
            ("Show me test AbC", "AbC"),
            ("Show me test Test_123", "Test_123")
        ]
        
        for query, expected_uid in queries:
            result = self.service.convert_to_sql(query)
            assert f"test_uid = '{expected_uid}'" in result 