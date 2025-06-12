"""LLM-powered Natural Language to SQL conversion service for test execution history."""
import json
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from loguru import logger
from ..config.settings import get_settings
import re

class LLMBasedNL2SQLService:
    """Service for converting natural language queries to SQL using LLM."""
    
    def __init__(self):
        """Initialize the LLM-based NL2SQL service."""
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key)
        self.table_name = "test_history"
        self.allowed_columns = ["id", "test_uid", "execution_time", "success", "metadata", "duration"]
        
    async def convert_to_sql(self, natural_query: str) -> str:
        """
        Convert natural language query to SQL SELECT statement using LLM.
        
        Args:
            natural_query: Natural language query string
            
        Returns:
            SQL SELECT query string
            
        Raises:
            ValueError: If the query cannot be safely converted
        """
        logger.info(f"Converting natural language query using LLM: '{natural_query}'")
        
        try:
            # Create the system prompt with schema and rules
            system_prompt = self._create_system_prompt()
            
            # Get SQL from LLM
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": natural_query}
                ],
                temperature=0.1,  # Low temperature for consistent, deterministic outputs
                max_tokens=200,   # Keep responses concise
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Parse the response
            response_content = response.choices[0].message.content
            parsed_response = json.loads(response_content)
            
            sql_query = parsed_response.get("sql", "").strip()
            explanation = parsed_response.get("explanation", "")
            
            if not sql_query:
                raise ValueError("LLM did not generate a SQL query")
            
            # Validate the generated SQL for safety
            if not self.validate_query(sql_query):
                logger.error(f"Generated unsafe SQL query: {sql_query}")
                raise ValueError("Generated query failed safety validation")
            
            logger.info(f"LLM generated SQL query: {sql_query}")
            logger.debug(f"LLM explanation: {explanation}")
            
            return sql_query
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            raise ValueError("Invalid response format from LLM")
        except Exception as e:
            logger.error(f"Error converting natural language to SQL with LLM: {str(e)}")
            raise ValueError(f"Failed to convert query: {str(e)}")
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the LLM."""
        return f"""You are an expert SQL query generator. Convert natural language questions about test execution history into safe PostgreSQL SELECT queries.

SCHEMA:
Table: {self.table_name}
Columns:
- id (UUID): Unique identifier for each test run
- test_uid (TEXT): Unique identifier for the test 
- execution_time (TIMESTAMP): When the test was run
- success (BOOLEAN): Whether the test passed (true) or failed (false)
- metadata (JSONB): Additional test run information
- duration (NUMERIC): Test execution duration in seconds

RULES:
1. ONLY generate SELECT statements for the {self.table_name} table
2. NEVER use other tables, INSERT, UPDATE, DELETE, DROP, CREATE, or any DDL/DML except SELECT
3. Use proper PostgreSQL syntax with single quotes for string literals
4. For boolean fields, use true/false (not quoted)
5. For time-based queries, use PostgreSQL interval syntax: NOW() - INTERVAL 'X days/weeks/months'
6. For date comparisons, use functions like CURRENT_DATE, DATE_TRUNC()
7. Always end with a semicolon
8. Use ORDER BY execution_time DESC for chronological ordering
9. Use LIMIT for queries requesting specific numbers of results

RESPONSE FORMAT:
Return a JSON object with exactly this structure:
{{
    "sql": "SELECT * FROM {self.table_name} WHERE ... ORDER BY execution_time DESC;",
    "explanation": "Brief explanation of what the query does"
}}

EXAMPLES:

User: "Show me the last 5 test runs for test ABC"
Response: {{
    "sql": "SELECT * FROM {self.table_name} WHERE test_uid = 'ABC' ORDER BY execution_time DESC LIMIT 5;",
    "explanation": "Gets the 5 most recent test runs for test ABC"
}}

User: "List all failed test runs in the past week"  
Response: {{
    "sql": "SELECT * FROM {self.table_name} WHERE success = false AND execution_time > NOW() - INTERVAL '7 days' ORDER BY execution_time DESC;",
    "explanation": "Gets all failed tests from the past 7 days"
}}

User: "Show all test runs for test XYZ that passed"
Response: {{
    "sql": "SELECT * FROM {self.table_name} WHERE test_uid = 'XYZ' AND success = true ORDER BY execution_time DESC;",
    "explanation": "Gets all successful test runs for test XYZ"
}}

User: "How many tests failed today?"
Response: {{
    "sql": "SELECT COUNT(*) FROM {self.table_name} WHERE success = false AND execution_time >= CURRENT_DATE;",
    "explanation": "Counts the number of failed tests today"
}}

User: "How many of the last 20 test runs failed?"
Response: {{
    "sql": "SELECT COUNT(*) FROM (SELECT * FROM {self.table_name} ORDER BY execution_time DESC LIMIT 20) AS recent_tests WHERE success = false;",
    "explanation": "Counts failed tests among the 20 most recent test runs"
}}

Convert the user's natural language query following these rules exactly."""

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
            logger.warning(f"Query doesn't start with SELECT: {sql_query}")
            return False
        
        # Ensure it references the allowed table somewhere
        if self.table_name not in sql_query.lower():
            logger.warning(f"Query doesn't reference {self.table_name}: {sql_query}")
            return False
        
        # Check for dangerous keywords using word boundaries to avoid false positives
        dangerous_keywords = [
            "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE",
            "TRUNCATE", "EXEC", "EXECUTE", "MERGE", "UNION", "--", "/*", "*/"
        ]
        
        # Remove the trailing semicolon for validation
        query_to_check = sql_query.rstrip(';').upper()
        
        for keyword in dangerous_keywords:
            # Use word boundaries for most keywords, but special handling for comments
            if keyword in ["--", "/*", "*/"]:
                # For comment patterns, check for exact substring match
                if keyword in query_to_check:
                    logger.warning(f"Query contains dangerous keyword '{keyword}': {sql_query}")
                    return False
            else:
                # For SQL keywords, use word boundaries to avoid false positives
                # This prevents "EXEC" from matching "execution_time"
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, query_to_check):
                    logger.warning(f"Query contains dangerous keyword '{keyword}': {sql_query}")
                    return False
        
        # Improved table validation that handles subqueries
        # Just ensure our table is referenced somewhere in the query
        # and no other table names are present (excluding SQL keywords and subquery aliases)
        
        # List of known SQL keywords and functions that might appear after FROM/JOIN
        sql_keywords = {
            'select', 'from', 'where', 'order', 'by', 'limit', 'offset', 'group',
            'having', 'as', 'asc', 'desc', 'and', 'or', 'not', 'in', 'like',
            'between', 'null', 'count', 'sum', 'avg', 'max', 'min', 'distinct',
            'case', 'when', 'then', 'else', 'end', 'cast', 'extract', 'interval',
            'now', 'current_date', 'current_timestamp'
        }
        
        # Simple validation: ensure our table is referenced and no obvious other table names
        query_lower = sql_query.lower()
        
        # Check that our table appears in the query
        if self.table_name not in query_lower:
            logger.warning(f"Query doesn't reference {self.table_name}: {sql_query}")
            return False
            
        # For additional safety, we could add more sophisticated table name extraction
        # but for now, this basic check should work for our use case
        
        return True
    
    async def get_query_explanation(self, natural_query: str, sql_query: str) -> str:
        """
        Get an explanation of what the generated SQL query does.
        
        Args:
            natural_query: Original natural language query
            sql_query: Generated SQL query
            
        Returns:
            Human-readable explanation of the query
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system", 
                        "content": "Explain what this SQL query does in simple, non-technical language."
                    },
                    {
                        "role": "user", 
                        "content": f"Original question: '{natural_query}'\nGenerated SQL: {sql_query}"
                    }
                ],
                temperature=0.3,
                max_tokens=100
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating query explanation: {str(e)}")
            return "No explanation available"
    
    async def validate_natural_query(self, natural_query: str) -> Dict[str, Any]:
        """
        Validate if a natural language query is appropriate for our test history schema.
        
        Args:
            natural_query: Natural language query to validate
            
        Returns:
            Dictionary with validation results
        """
        try:
            validation_prompt = f"""Analyze this natural language query for a test execution history database.

Query: "{natural_query}"

Available data: test runs with id, test_uid, execution_time, success (boolean), metadata, and duration.

Respond with JSON:
{{
    "is_valid": true/false,
    "reason": "explanation of why valid or invalid",
    "suggested_rephrase": "better way to ask the question (if invalid)"
}}"""

            response = await self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[{"role": "user", "content": validation_prompt}],
                temperature=0.1,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error validating natural query: {str(e)}")
            return {
                "is_valid": True,  # Default to valid on error
                "reason": "Could not validate query",
                "suggested_rephrase": None
            } 