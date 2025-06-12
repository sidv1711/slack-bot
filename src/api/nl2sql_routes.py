"""API routes for Natural Language to SQL conversion using LLM."""
from fastapi import APIRouter, HTTPException, Depends
from loguru import logger

from ..models.test_history import (
    NL2SQLRequest, 
    NL2SQLResponse, 
    EnhancedNL2SQLResponse,
    QueryValidationRequest,
    QueryValidationResponse
)
from ..services.llm_nl2sql_service import LLMBasedNL2SQLService
from ..auth.propel import get_current_user

router = APIRouter(tags=["NL2SQL"])

# Initialize the LLM-based NL2SQL service
llm_nl2sql_service = LLMBasedNL2SQLService()

@router.post("/nl2sql", response_model=NL2SQLResponse)
async def convert_natural_language_to_sql(
    request: NL2SQLRequest,
    current_user=Depends(get_current_user)
) -> NL2SQLResponse:
    """
    Convert natural language query to SQL for test execution history using LLM.
    
    This endpoint takes a natural language query about test execution history
    and converts it to a safe SQL SELECT statement for the test_history table
    using a Large Language Model (OpenAI GPT).
    
    The LLM approach provides:
    - Better understanding of complex natural language
    - More flexible query patterns
    - Contextual understanding
    - Better handling of synonyms and variations
    
    Examples of supported queries:
    - "Show me the last 5 test runs for test ABC"
    - "List all failed test runs in the past week"
    - "What tests failed yesterday and took longer than 5 minutes?"
    - "Find all tests for project XYZ that passed in the last month"
    
    Args:
        request: Natural language query request
        current_user: Authenticated user (from auth dependency)
        
    Returns:
        SQL query response with explanation
        
    Raises:
        HTTPException: If query conversion fails or produces unsafe SQL
    """
    try:
        logger.info(f"User {current_user.user_id} requested LLM-powered NL2SQL conversion")
        
        # Convert natural language to SQL using LLM
        sql_query = await llm_nl2sql_service.convert_to_sql(request.query)
        
        # Get explanation from the LLM
        explanation = await llm_nl2sql_service.get_query_explanation(request.query, sql_query)
        
        logger.info(f"Successfully converted query to SQL: {sql_query}")
        
        return NL2SQLResponse(sql_query=sql_query, explanation=explanation)
        
    except Exception as e:
        logger.error(f"Error converting natural language to SQL: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert query: {str(e)}"
        )

@router.post("/nl2sql/enhanced", response_model=EnhancedNL2SQLResponse)
async def convert_natural_language_to_sql_enhanced(
    request: NL2SQLRequest,
    current_user=Depends(get_current_user)
) -> EnhancedNL2SQLResponse:
    """
    Enhanced natural language to SQL conversion with validation and insights.
    
    This endpoint provides the same conversion as the basic endpoint but includes:
    - Query validation results
    - Detailed explanations
    - Suggestions for improvement
    
    Args:
        request: Natural language query request
        current_user: Authenticated user (from auth dependency)
        
    Returns:
        Enhanced SQL query response with validation and insights
    """
    try:
        logger.info(f"User {current_user.user_id} requested enhanced LLM NL2SQL conversion")
        
        # Validate the natural language query first
        validation_result = await llm_nl2sql_service.validate_natural_query(request.query)
        
        if not validation_result.get("is_valid", True):
            logger.warning(f"Invalid query: {request.query}")
            # Still attempt conversion but include the warning
        
        # Convert natural language to SQL using LLM
        sql_query = await llm_nl2sql_service.convert_to_sql(request.query)
        
        # Get explanation from the LLM
        explanation = await llm_nl2sql_service.get_query_explanation(request.query, sql_query)
        
        logger.info(f"Successfully converted enhanced query to SQL: {sql_query}")
        
        return EnhancedNL2SQLResponse(
            sql_query=sql_query,
            explanation=explanation,
            query_validation=validation_result,
            natural_query=request.query
        )
        
    except Exception as e:
        logger.error(f"Error in enhanced NL2SQL conversion: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert query: {str(e)}"
        )

@router.post("/nl2sql/validate", response_model=QueryValidationResponse)
async def validate_natural_language_query(
    request: QueryValidationRequest,
    current_user=Depends(get_current_user)
) -> QueryValidationResponse:
    """
    Validate a natural language query before conversion.
    
    This endpoint checks if a natural language query is appropriate
    for our test history database schema and provides suggestions
    for improvement if needed.
    
    Args:
        request: Query validation request
        current_user: Authenticated user
        
    Returns:
        Validation results with suggestions
    """
    try:
        logger.info(f"User {current_user.user_id} requested query validation")
        
        validation_result = await llm_nl2sql_service.validate_natural_query(request.query)
        
        return QueryValidationResponse(
            is_valid=validation_result.get("is_valid", True),
            reason=validation_result.get("reason", "Query appears valid"),
            suggested_rephrase=validation_result.get("suggested_rephrase")
        )
        
    except Exception as e:
        logger.error(f"Error validating natural language query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate query: {str(e)}"
        )

@router.post("/nl2sql/examples")
async def get_nl2sql_examples(
    current_user=Depends(get_current_user)
) -> dict:
    """
    Get example natural language queries and their corresponding SQL outputs.
    
    Now powered by LLM for more sophisticated examples.
    
    Returns:
        Dictionary with example queries and their SQL conversions
    """
    example_queries = [
        "Show me the last 5 test runs for test ABC",
        "List all failed test runs in the past week",
        "Show all test runs for test XYZ that passed",
        "What tests failed today?",
        "Find tests that ran yesterday but took longer than normal",
        "Show me all pending tests from this month",
        "Get successful test runs from the past 3 days for project DEMO"
    ]
    
    examples = []
    for query in example_queries:
        try:
            sql_query = await llm_nl2sql_service.convert_to_sql(query)
            explanation = await llm_nl2sql_service.get_query_explanation(query, sql_query)
            
            examples.append({
                "natural_query": query,
                "sql_query": sql_query,
                "explanation": explanation
            })
        except Exception as e:
            logger.error(f"Error generating example for '{query}': {str(e)}")
            # Skip failed examples
            continue
    
    return {"examples": examples, "powered_by": "OpenAI GPT"}

@router.get("/nl2sql/schema")
async def get_schema_info(
    current_user=Depends(get_current_user)
) -> dict:
    """
    Get information about the test_history table schema.
    
    Returns:
        Schema information for the test_history table
    """
    return {
        "table": "test_history",
        "columns": [
            {
                "name": "id",
                "type": "UUID",
                "description": "Unique identifier for each test run"
            },
            {
                "name": "test_uid",
                "type": "TEXT",
                "description": "Unique identifier for the test"
            },
            {
                "name": "execution_time",
                "type": "TIMESTAMP",
                "description": "When the test was run"
            },
            {
                "name": "status",
                "type": "TEXT",
                "description": "Status of the test run (e.g., passed, failed, running, pending, skipped)"
            },
            {
                "name": "metadata",
                "type": "JSONB",
                "description": "Additional test run information stored as JSON"
            }
        ],
        "supported_operations": [
            "SELECT queries only",
            "Filtering by test_uid, status, execution_time",
            "Complex time-based queries using PostgreSQL intervals",
            "JSON queries on metadata field",
            "Ordering by execution_time",
            "Limiting results with LIMIT clause",
            "Aggregations like COUNT, AVG, etc."
        ],
        "llm_capabilities": [
            "Natural language understanding",
            "Synonym recognition (e.g., 'successful' = 'passed')",
            "Complex time expressions",
            "Contextual query building",
            "Query validation and suggestions"
        ]
    }

@router.get("/nl2sql/capabilities")
async def get_llm_capabilities(
    current_user=Depends(get_current_user)
) -> dict:
    """
    Get information about the LLM-powered NL2SQL capabilities.
    
    Returns:
        Information about what the LLM can understand and do
    """
    return {
        "model": llm_nl2sql_service.settings.openai_model,
        "capabilities": {
            "natural_language_understanding": [
                "Complex sentence structures",
                "Synonyms and variations (failed/error, passed/successful)",
                "Time expressions (yesterday, last week, past 3 days)",
                "Numerical expressions (last 5, top 10, first 3)",
                "Contextual understanding"
            ],
            "query_types": [
                "Simple filters (test ABC, failed tests)",
                "Time-based queries (tests from yesterday)",
                "Limited results (last 5 tests)",
                "Complex combinations (failed tests for project X in the past week)",
                "Aggregations (count of failed tests)",
                "JSON metadata queries"
            ],
            "safety_features": [
                "SQL injection prevention",
                "Only SELECT statements allowed",
                "Table restriction enforcement",
                "Dangerous keyword blocking",
                "Query validation"
            ]
        },
        "advantages_over_regex": [
            "Better handling of complex language",
            "Understanding of context and intent",
            "Flexible query patterns",
            "Natural synonym recognition",
            "Improved error handling",
            "Query explanations"
        ]
    } 