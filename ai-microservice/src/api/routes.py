"""API routes for the AI Microservice."""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from ..services.ai_router_service import AIRouterService
from ..services.nl2sql_adapter_service import NL2SQLAdapter
from ..services.code_generation_service import CodeGenerationService
from ..services.general_chat_service import GeneralChatService
from ..models.requests import (
    AIProcessRequest, 
    NL2SQLRequest, 
    CodeGenerationRequest, 
    ChatRequest
)
from ..models.responses import (
    AIProcessResponse,
    NL2SQLResponse, 
    CodeGenerationResponse, 
    ChatResponse,
    HealthResponse
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Service instances (will be injected)
ai_router_service = None
nl2sql_service = None
code_gen_service = None
chat_service = None


async def get_ai_router() -> AIRouterService:
    """Dependency to get AI router service."""
    global ai_router_service
    if ai_router_service is None:
        ai_router_service = AIRouterService()
    return ai_router_service


async def get_nl2sql_service() -> NL2SQLAdapter:
    """Dependency to get NL2SQL service."""
    global nl2sql_service
    if nl2sql_service is None:
        nl2sql_service = NL2SQLAdapter()
    return nl2sql_service


async def get_code_gen_service() -> CodeGenerationService:
    """Dependency to get code generation service."""
    global code_gen_service
    if code_gen_service is None:
        code_gen_service = CodeGenerationService()
    return code_gen_service


async def get_chat_service() -> GeneralChatService:
    """Dependency to get chat service."""
    global chat_service
    if chat_service is None:
        chat_service = GeneralChatService()
    return chat_service


@router.post("/ai/process", response_model=AIProcessResponse)
async def process_ai_request(
    request: AIProcessRequest,
    ai_router: AIRouterService = Depends(get_ai_router)
) -> AIProcessResponse:
    """
    Main AI processing endpoint - routes requests to appropriate service.
    
    This is the primary endpoint that mimics the behavior of the original
    AIRouterService but as a REST API.
    """
    try:
        logger.info(f"Processing AI request: {request.user_input[:100]}...")
        
        # Convert request to internal format
        context = request.context or {}
        
        # Process through AI router
        result = await ai_router.process_request(
            user_input=request.user_input,
            context=context
        )
        
        return AIProcessResponse(
            success=result.get("success", True),
            service=result.get("routing", {}).get("service", "unknown"),
            confidence=result.get("routing", {}).get("confidence", 0.0),
            response_data=result,
            error=result.get("error") if not result.get("success", True) else None
        )
        
    except Exception as e:
        logger.error(f"Error processing AI request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nl2sql/convert", response_model=NL2SQLResponse)
async def convert_nl2sql(
    request: NL2SQLRequest,
    nl2sql_service: NL2SQLAdapter = Depends(get_nl2sql_service)
) -> NL2SQLResponse:
    """Convert natural language to SQL and optionally execute."""
    try:
        logger.info(f"Converting NL2SQL: {request.natural_query}")
        
        result = await nl2sql_service.process_request(
            user_input=request.natural_query,
            context=request.context or {}
        )
        
        return NL2SQLResponse(
            success=result.get("success", True),
            sql_query=result.get("sql_query"),
            explanation=result.get("explanation"),
            results=result.get("results"),
            row_count=result.get("row_count", 0),
            formatted_table=result.get("formatted_table"),
            error=result.get("error") if not result.get("success", True) else None
        )
        
    except Exception as e:
        logger.error(f"Error in NL2SQL conversion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/code/generate", response_model=CodeGenerationResponse)
async def generate_code(
    request: CodeGenerationRequest,
    code_service: CodeGenerationService = Depends(get_code_gen_service)
) -> CodeGenerationResponse:
    """Generate code from natural language description."""
    try:
        logger.info(f"Generating code: {request.description[:100]}...")
        
        context = request.context or {}
        if request.language:
            context["preferred_language"] = request.language
            
        result = await code_service.process_request(
            user_input=request.description,
            context=context
        )
        
        return CodeGenerationResponse(
            success=result.get("success", True),
            code=result.get("code"),
            language=result.get("language"),
            explanation=result.get("explanation"),
            usage_example=result.get("usage_example"),
            error=result.get("error") if not result.get("success", True) else None
        )
        
    except Exception as e:
        logger.error(f"Error in code generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/respond", response_model=ChatResponse)
async def chat_respond(
    request: ChatRequest,
    chat_service: GeneralChatService = Depends(get_chat_service)
) -> ChatResponse:
    """Generate conversational AI response."""
    try:
        logger.info(f"Processing chat: {request.message[:100]}...")
        
        result = await chat_service.process_request(
            user_input=request.message,
            context=request.context or {}
        )
        
        return ChatResponse(
            success=result.get("success", True),
            response=result.get("response"),
            follow_up_questions=result.get("follow_up_questions", []),
            error=result.get("error") if not result.get("success", True) else None
        )
        
    except Exception as e:
        logger.error(f"Error in chat response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/services/status", response_model=Dict[str, Any])
async def get_services_status() -> Dict[str, Any]:
    """Get status of all AI services."""
    try:
        return {
            "ai_router": "healthy",
            "nl2sql": "healthy", 
            "code_generation": "healthy",
            "general_chat": "healthy",
            "timestamp": "2024-01-01T00:00:00Z"  # Add actual timestamp
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics", response_model=Dict[str, Any])
async def get_metrics() -> Dict[str, Any]:
    """Get service metrics and performance data."""
    return {
        "requests_processed": 0,  # Implement actual metrics
        "average_response_time": 0.0,
        "success_rate": 1.0,
        "services": {
            "nl2sql": {"requests": 0, "avg_time": 0.0},
            "code_generation": {"requests": 0, "avg_time": 0.0},
            "general_chat": {"requests": 0, "avg_time": 0.0}
        }
    } 