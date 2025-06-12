"""Adapter for NL2SQL service to conform to base AI service interface."""
from typing import Dict, Any, List, Optional
from .base_ai_service import BaseAIService
from .llm_nl2sql_service import LLMBasedNL2SQLService
from .database_service import DatabaseService

class NL2SQLAdapter(BaseAIService):
    """Adapter to make NL2SQL service conform to base AI service interface."""
    
    def __init__(self):
        """Initialize the NL2SQL adapter."""
        super().__init__(
            service_name="NL2SQL",
            service_description="converting natural language to SQL database queries and executing them"
        )
        self.nl2sql_service = LLMBasedNL2SQLService()
        self.db_service = DatabaseService()
    
    async def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a natural language database query request.
        
        Args:
            user_input: The user's natural language query
            context: Optional context information
            
        Returns:
            Dictionary with SQL query, results, and formatted table
        """
        try:
            # Step 1: Convert natural language to SQL
            sql_query = await self.nl2sql_service.convert_to_sql(user_input)
            
            # Step 2: Execute the SQL query
            db_result = await self.db_service.execute_query(sql_query)
            
            if not db_result["success"]:
                return {
                    "service": "nl2sql",
                    "success": False,
                    "error": f"Database error: {db_result['error']}",
                    "user_query": user_input,
                    "sql_query": sql_query,
                    "service_type": "database_query"
                }
            
            # Step 3: Format results as table
            formatted_table = self.db_service.format_results_as_table(
                db_result["data"], 
                max_rows=15
            )
            
            # Step 4: Get explanation
            explanation = await self.nl2sql_service.get_query_explanation(user_input, sql_query)
            
            return {
                "service": "nl2sql",
                "success": True,
                "sql_query": sql_query,
                "explanation": explanation,
                "results": db_result["data"],
                "formatted_table": formatted_table,
                "row_count": db_result["row_count"],
                "user_query": user_input,
                "service_type": "database_query"
            }
            
        except Exception as e:
            return {
                "service": "nl2sql",
                "success": False,
                "error": str(e),
                "user_query": user_input,
                "service_type": "database_query"
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return NL2SQL service capabilities."""
        return {
            "service": "NL2SQL",
            "description": "Convert natural language to SQL database queries and execute them",
            "database": "test_history table",
            "supported_operations": [
                "SELECT queries only (read-only)",
                "Filtering by test_uid, status, execution_time",
                "Ordering and limiting results",
                "Time-based queries (last week, yesterday, etc.)",
                "Status filtering (failed, passed, etc.)",
                "Query execution with formatted table results"
            ],
            "safety_features": [
                "SQL injection prevention",
                "Read-only operations",
                "Input validation",
                "Query explanation",
                "Results truncation for readability"
            ]
        }
    
    def get_examples(self) -> List[Dict[str, str]]:
        """Return example NL2SQL conversions."""
        return [
            {
                "input": "Show me the last 5 test runs for test ABC",
                "output": "Executes SQL and returns formatted table with test results"
            },
            {
                "input": "List all failed test runs in the past week",
                "output": "Returns table of failed tests from the last 7 days"
            },
            {
                "input": "Find tests that failed yesterday",
                "output": "Shows table of yesterday's failed test executions"
            },
            {
                "input": "Count how many tests passed today",
                "output": "Returns count and details of today's passed tests"
            }
        ]
    
    def validate_input(self, user_input: str) -> Dict[str, Any]:
        """Validate user input for NL2SQL conversion."""
        if not user_input or not user_input.strip():
            return {
                "is_valid": False,
                "reason": "Empty query cannot be converted to SQL",
                "suggestion": "Please provide a database query in natural language"
            }
        
        # Check for obviously non-database queries
        non_db_keywords = [
            "write code", "generate function", "create script", "program",
            "hello", "hi", "how are you", "weather", "joke"
        ]
        
        lower_input = user_input.lower()
        for keyword in non_db_keywords:
            if keyword in lower_input:
                return {
                    "is_valid": False,
                    "reason": f"Query appears to be about '{keyword}', not database operations",
                    "suggestion": "Please ask about test data, test results, or database queries"
                }
        
        return {
            "is_valid": True,
            "reason": "Query appears suitable for SQL conversion and execution"
        } 