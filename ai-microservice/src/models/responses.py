"""Response models for the AI Microservice."""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class AIProcessResponse(BaseModel):
    """Response model for the main AI processing endpoint."""
    
    success: bool = Field(..., description="Whether the request was successful")
    service: str = Field(..., description="Which AI service was used")
    confidence: float = Field(..., description="Confidence score for service routing")
    response_data: Dict[str, Any] = Field(..., description="The actual response data")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "service": "nl2sql",
                "confidence": 0.95,
                "response_data": {
                    "sql_query": "SELECT COUNT(*) FROM test_history WHERE success = false",
                    "results": [{"count": 15}],
                    "formatted_table": "📊 **Answer:** 15"
                },
                "error": None
            }
        }


class NL2SQLResponse(BaseModel):
    """Response model for NL2SQL conversion."""
    
    success: bool = Field(..., description="Whether the conversion was successful")
    sql_query: Optional[str] = Field(default=None, description="Generated SQL query")
    explanation: Optional[str] = Field(default=None, description="Explanation of the query")
    results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Query results if executed")
    row_count: int = Field(default=0, description="Number of rows returned")
    formatted_table: Optional[str] = Field(default=None, description="Formatted table for display")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "sql_query": "SELECT COUNT(*) FROM test_history WHERE success = false AND execution_time > NOW() - INTERVAL '24 hours'",
                "explanation": "Counts failed tests in the last 24 hours",
                "results": [{"count": 15}],
                "row_count": 1,
                "formatted_table": "📊 **Answer:** 15",
                "error": None
            }
        }


class CodeGenerationResponse(BaseModel):
    """Response model for code generation."""
    
    success: bool = Field(..., description="Whether code generation was successful")
    code: Optional[str] = Field(default=None, description="Generated code")
    language: Optional[str] = Field(default=None, description="Programming language used")
    explanation: Optional[str] = Field(default=None, description="Explanation of the code")
    usage_example: Optional[str] = Field(default=None, description="Example of how to use the code")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "code": "import re\n\ndef validate_email(email: str) -> bool:\n    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n    return re.match(pattern, email) is not None",
                "language": "python",
                "explanation": "This function validates email addresses using regex",
                "usage_example": "is_valid = validate_email('test@example.com')",
                "error": None
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat/conversation."""
    
    success: bool = Field(..., description="Whether the chat response was successful")
    response: Optional[str] = Field(default=None, description="AI's response message")
    follow_up_questions: List[str] = Field(default=[], description="Suggested follow-up questions")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "response": "Machine learning is a subset of artificial intelligence that enables computers to learn and improve from experience without being explicitly programmed.",
                "follow_up_questions": [
                    "What are the main types of machine learning?",
                    "How does machine learning differ from traditional programming?",
                    "Can you give me an example of machine learning in action?"
                ],
                "error": None
            }
        }


class HealthResponse(BaseModel):
    """Response model for health checks."""
    
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: Optional[str] = Field(default=None, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "service": "ai-microservice",
                "version": "1.0.0",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        } 