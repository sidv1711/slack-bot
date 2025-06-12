"""Natural Language to SQL conversion service for test execution history."""
import re
from typing import Optional
from loguru import logger

class NL2SQLService:
    """Service for converting natural language queries to SQL for test_history table."""
    
    def __init__(self):
        """Initialize the NL2SQL service."""
        self.table_name = "test_history"
        self.allowed_columns = ["id", "test_uid", "execution_time", "status", "metadata"]
        
    def convert_to_sql(self, natural_query: str) -> str:
        """
        Convert natural language query to SQL SELECT statement.
        
        Args:
            natural_query: Natural language query string
            
        Returns:
            SQL SELECT query string
            
        Raises:
            ValueError: If the query cannot be safely converted
        """
        query = natural_query.lower().strip()
        logger.info(f"Converting natural language query: '{natural_query}'")
        
        # Start building the SQL query
        sql_parts = {
            "select": "*",
            "from": self.table_name,
            "where": [],
            "order_by": None,
            "limit": None
        }
        
        # Extract limit/number of results
        limit = self._extract_limit(query)
        if limit:
            sql_parts["limit"] = limit
            sql_parts["order_by"] = "execution_time DESC"
        
        # Extract test_uid filter (use original query to preserve case)
        test_uid = self._extract_test_uid(natural_query)
        if test_uid:
            sql_parts["where"].append(f"test_uid = '{test_uid}'")
        
        # Extract status filter
        status = self._extract_status(query)
        if status:
            sql_parts["where"].append(f"status = '{status}'")
        
        # Extract time frame filter
        time_filter = self._extract_time_frame(query)
        if time_filter:
            sql_parts["where"].append(time_filter)
        
        # If no explicit order by was set but we have filters, add default ordering
        if not sql_parts["order_by"] and (sql_parts["where"] or not limit):
            sql_parts["order_by"] = "execution_time DESC"
        
        # Build the final SQL query
        sql_query = self._build_sql_query(sql_parts)
        
        logger.info(f"Generated SQL query: {sql_query}")
        return sql_query
    
    def _extract_limit(self, query: str) -> Optional[int]:
        """Extract limit/number from natural language query."""
        # Look for patterns like "last 5", "top 3", "first 10", etc.
        patterns = [
            r"last\s+(\d+)",
            r"top\s+(\d+)",
            r"first\s+(\d+)",
            r"show\s+(\d+)",
            r"get\s+(\d+)",
            r"(\d+)\s+(?:test|result|record|run)s?"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return int(match.group(1))
        
        return None
    
    def _extract_test_uid(self, query: str) -> Optional[str]:
        """Extract test UID from natural language query."""
        # Look for patterns like "test ABC", "for test XYZ", "test_uid = 'value'"
        # Use more specific patterns to avoid false matches
        patterns = [
            r"(?:(?:for|of)\s+)?test\s+([a-zA-Z0-9_-]+)(?:\s+(?:that|which|where)|$|\s+[^a-zA-Z0-9_-])",
            r"test_uid\s*[=:]\s*['\"]?([a-zA-Z0-9_-]+)['\"]?",
            r"test\s+(?:id|uid|name)\s+([a-zA-Z0-9_-]+)",
            r"(?:^|\s)([a-zA-Z0-9_-]+)\s+test(?:\s|$)"  # ABC test pattern
        ]
        
        # Don't extract common words that might appear after "test"
        excluded_words = {
            'runs', 'run', 'results', 'result', 'data', 'history', 'records', 
            'record', 'execution', 'executions', 'logs', 'log', 'cases', 'case',
            'patterns', 'pattern', 'with', 'without', 'all', 'any', 'some',
            'the', 'a', 'an', 'and', 'or', 'but', 'from', 'to', 'in', 'on',
            'at', 'by', 'for', 'of', 'with', 'without'
        }
        
        query_lower = query.lower()
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                test_uid_lower = match.group(1).lower()
                
                # Skip excluded words
                if test_uid_lower in excluded_words:
                    continue
                
                # Get the actual case from the original query
                original_match = re.search(pattern, query, re.IGNORECASE)
                if original_match:
                    original_test_uid = original_match.group(1)
                    # Validate test_uid format (alphanumeric, underscore, hyphen)
                    if re.match(r"^[a-zA-Z0-9_-]+$", original_test_uid):
                        return original_test_uid
        
        return None
    
    def _extract_status(self, query: str) -> Optional[str]:
        """Extract status filter from natural language query."""
        # Look for status keywords
        status_keywords = {
            "passed": ["passed", "successful", "success", "green"],
            "failed": ["failed", "failure", "error", "red"],
            "running": ["running", "in progress", "executing"],
            "pending": ["pending", "waiting", "queued"],
            "skipped": ["skipped", "ignored"]
        }
        
        for status, keywords in status_keywords.items():
            for keyword in keywords:
                if keyword in query:
                    return status
        
        # Also check for direct status mentions
        if re.search(r"status\s*=\s*['\"]([^'\"]+)['\"]", query):
            match = re.search(r"status\s*=\s*['\"]([^'\"]+)['\"]", query)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_time_frame(self, query: str) -> Optional[str]:
        """Extract time frame filter from natural language query."""
        # Time frame patterns
        time_patterns = {
            r"(?:in\s+the\s+)?past\s+(\d+)\s+days?": lambda x: f"execution_time > NOW() - INTERVAL '{x} days'",
            r"(?:in\s+the\s+)?past\s+(\d+)\s+weeks?": lambda x: f"execution_time > NOW() - INTERVAL '{x} weeks'",
            r"(?:in\s+the\s+)?past\s+(\d+)\s+months?": lambda x: f"execution_time > NOW() - INTERVAL '{x} months'",
            r"(?:in\s+the\s+)?past\s+(\d+)\s+hours?": lambda x: f"execution_time > NOW() - INTERVAL '{x} hours'",
            r"(?:in\s+the\s+)?past\s+week": lambda x: "execution_time > NOW() - INTERVAL '7 days'",
            r"(?:in\s+the\s+)?past\s+month": lambda x: "execution_time > NOW() - INTERVAL '1 month'",
            r"today": lambda x: "execution_time >= CURRENT_DATE",
            r"yesterday": lambda x: "execution_time >= CURRENT_DATE - INTERVAL '1 day' AND execution_time < CURRENT_DATE",
            r"this\s+week": lambda x: "execution_time >= DATE_TRUNC('week', CURRENT_DATE)",
            r"this\s+month": lambda x: "execution_time >= DATE_TRUNC('month', CURRENT_DATE)",
            r"last\s+24\s+hours": lambda x: "execution_time > NOW() - INTERVAL '24 hours'"
        }
        
        for pattern, filter_func in time_patterns.items():
            match = re.search(pattern, query)
            if match:
                if match.groups():
                    return filter_func(match.group(1))
                else:
                    return filter_func(None)
        
        return None
    
    def _build_sql_query(self, sql_parts: dict) -> str:
        """Build the final SQL query from parts."""
        query = f"SELECT {sql_parts['select']} FROM {sql_parts['from']}"
        
        # Add WHERE clause
        if sql_parts["where"]:
            query += " WHERE " + " AND ".join(sql_parts["where"])
        
        # Add ORDER BY clause
        if sql_parts["order_by"]:
            query += f" ORDER BY {sql_parts['order_by']}"
        
        # Add LIMIT clause
        if sql_parts["limit"]:
            query += f" LIMIT {sql_parts['limit']}"
        
        query += ";"
        
        return query
    
    def validate_query(self, sql_query: str) -> bool:
        """
        Validate that the generated SQL query is safe.
        
        Args:
            sql_query: SQL query to validate
            
        Returns:
            True if query is safe, False otherwise
        """
        # Ensure it's a SELECT statement
        if not sql_query.strip().upper().startswith("SELECT"):
            return False
        
        # Ensure it only uses the allowed table
        if self.table_name not in sql_query:
            return False
        
        # Check for dangerous keywords (allow LIMIT, ORDER BY, etc.)
        dangerous_keywords = [
            "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE",
            "TRUNCATE", "EXEC", "EXECUTE", "MERGE", "UNION", ";"
        ]
        
        # Remove the trailing semicolon for validation
        query_to_check = sql_query.rstrip(';').upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_to_check:
                return False
        
        return True 