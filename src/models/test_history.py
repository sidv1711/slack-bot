"""Models for test execution history."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any
from uuid import UUID

class TestHistory(BaseModel):
    """Test execution history model."""
    id: UUID
    test_uid: str
    execution_time: datetime
    status: str
    metadata: Optional[dict[str, Any]] = None

class NL2SQLRequest(BaseModel):
    """Request model for natural language to SQL conversion."""
    query: str

class NL2SQLResponse(BaseModel):
    """Response model for natural language to SQL conversion."""
    sql_query: str
    explanation: Optional[str] = None

class EnhancedNL2SQLResponse(BaseModel):
    """Enhanced response model with additional LLM insights."""
    sql_query: str
    explanation: str
    query_validation: dict[str, Any]
    natural_query: str

class QueryValidationRequest(BaseModel):
    """Request model for validating natural language queries."""
    query: str

class QueryValidationResponse(BaseModel):
    """Response model for query validation."""
    is_valid: bool
    reason: str
    suggested_rephrase: Optional[str] = None 