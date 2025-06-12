"""Request models for the AI Microservice."""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


class AIProcessRequest(BaseModel):
    """Request model for the main AI processing endpoint."""
    
    user_input: str = Field(..., description="The user's input/query")
    context: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional context for the request"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "user_input": "Show me failed tests from yesterday",
                "context": {
                    "user_id": "123",
                    "channel_id": "slack-channel",
                    "platform": "slack"
                }
            }
        }


class NL2SQLRequest(BaseModel):
    """Request model for natural language to SQL conversion."""
    
    natural_query: str = Field(..., description="Natural language query to convert to SQL")
    execute_query: bool = Field(
        default=True, 
        description="Whether to execute the query and return results"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for the query"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "natural_query": "How many tests failed in the last 24 hours?",
                "execute_query": True,
                "context": {"user_id": "123"}
            }
        }


class CodeGenerationRequest(BaseModel):
    """Request model for code generation."""
    
    description: str = Field(..., description="Description of the code to generate")
    language: Optional[str] = Field(
        default=None, 
        description="Preferred programming language"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for code generation"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "description": "Create a function that validates email addresses",
                "language": "python",
                "context": {"framework": "fastapi"}
            }
        }


class ChatRequest(BaseModel):
    """Request model for general chat/conversation."""
    
    message: str = Field(..., description="User's chat message")
    conversation_id: Optional[str] = Field(
        default=None,
        description="ID to maintain conversation context"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context for the conversation"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "message": "What is machine learning?",
                "conversation_id": "conv-123",
                "context": {"user_level": "beginner"}
            }
        } 