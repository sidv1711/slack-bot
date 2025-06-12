"""API routes for the multi-service AI bot system."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime

from ..models.test_history import (
    NL2SQLRequest, 
    QueryValidationRequest, 
    QueryValidationResponse
)
from ..services.ai_router_service import AIRouterService
from ..auth.propel import get_current_user

router = APIRouter()

# Global AI router instance
ai_router = AIRouterService()

# ============================================================================= 
# Core AI Bot Endpoints
# =============================================================================

@router.post("/ai/chat")
async def chat_with_ai_bot(
    request: Dict[str, Any],
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Main chat endpoint for the AI bot. Automatically routes requests to appropriate services.
    
    Request body should contain:
    - message: The user's message/question
    - context: Optional context information
    - force_service: Optional service name to force routing to
    """
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Build context with user information
        context = request.get("context", {})
        context.update({
            "user_id": current_user.user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process the request through AI router
        result = await ai_router.process_request(
            user_input=message,
            context=context,
            force_service=request.get("force_service")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in AI chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"AI chat error: {str(e)}")

@router.post("/ai/services/{service_name}/process")
async def process_with_specific_service(
    service_name: str,
    request: Dict[str, Any],
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Process a request with a specific AI service.
    
    Args:
        service_name: Name of the service to use
        request: Request body with message and optional context
    """
    try:
        message = request.get("message", "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Validate service exists
        available_services = ai_router.get_available_services()
        if service_name not in available_services:
            raise HTTPException(
                status_code=404, 
                detail=f"Service '{service_name}' not found. Available: {list(available_services.keys())}"
            )
        
        # Build context
        context = request.get("context", {})
        context.update({
            "user_id": current_user.user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Process with specific service
        result = await ai_router.process_request(
            user_input=message,
            context=context,
            force_service=service_name
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing with service {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service processing error: {str(e)}")

@router.post("/ai/validate")
async def validate_request_for_service(
    request: QueryValidationRequest,
    current_user=Depends(get_current_user)
) -> QueryValidationResponse:
    """
    Validate if a request is appropriate for a specific service.
    
    Args:
        request: Request with query and service_name
    """
    try:
        validation = await ai_router.validate_request_for_service(
            user_input=request.query,
            service_name=request.service_name
        )
        
        return QueryValidationResponse(
            is_valid=validation["is_valid"],
            reason=validation["reason"],
            suggested_rephrase=validation.get("suggestion")
        )
        
    except Exception as e:
        logger.error(f"Error in validation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Validation error: {str(e)}")

# =============================================================================
# Service Discovery and Information Endpoints  
# =============================================================================

@router.get("/ai/services")
async def get_available_services(current_user=Depends(get_current_user)) -> Dict[str, Dict[str, Any]]:
    """Get information about all available AI services."""
    try:
        return ai_router.get_available_services()
    except Exception as e:
        logger.error(f"Error getting services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving services: {str(e)}")

@router.get("/ai/services/{service_name}/capabilities")
async def get_service_capabilities(
    service_name: str,
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """Get detailed capabilities of a specific service."""
    try:
        services = ai_router.get_available_services()
        if service_name not in services:
            raise HTTPException(
                status_code=404, 
                detail=f"Service '{service_name}' not found"
            )
        
        return services[service_name]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting service capabilities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving capabilities: {str(e)}")

@router.get("/ai/services/{service_name}/examples")
async def get_service_examples(
    service_name: str,
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """Get example inputs and outputs for a specific service."""
    try:
        examples = ai_router.get_service_examples(service_name)
        if "error" in examples:
            raise HTTPException(status_code=404, detail=examples["error"])
        
        return examples
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting examples: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving examples: {str(e)}")

@router.get("/ai/examples")
async def get_all_service_examples(current_user=Depends(get_current_user)) -> Dict[str, Any]:
    """Get examples for all services."""
    try:
        return ai_router.get_service_examples()
    except Exception as e:
        logger.error(f"Error getting all examples: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving examples: {str(e)}")

@router.get("/ai/stats")
async def get_ai_bot_stats(current_user=Depends(get_current_user)) -> Dict[str, Any]:
    """Get statistics about the AI bot system."""
    try:
        return ai_router.get_service_stats()
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")

# =============================================================================
# Backwards Compatibility with Existing NL2SQL Endpoints
# =============================================================================

@router.post("/ai/nl2sql")
async def convert_nl_to_sql_compat(
    request: NL2SQLRequest,
    current_user=Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Legacy endpoint for NL2SQL conversion (backwards compatibility).
    Routes to the NL2SQL service through the AI router.
    """
    try:
        context = {
            "user_id": current_user.user_id,
            "timestamp": datetime.now().isoformat()
        }
        
        result = await ai_router.process_request(
            user_input=request.natural_query,
            context=context,
            force_service="nl2sql"
        )
        
        if result.get("success"):
            return {
                "sql_query": result.get("sql_query"),
                "explanation": result.get("explanation"),
                "natural_query": request.natural_query
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "NL2SQL conversion failed"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in legacy NL2SQL endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=f"NL2SQL error: {str(e)}")

# =============================================================================
# Health and Status Endpoints
# =============================================================================

@router.get("/ai/health")
async def ai_bot_health() -> Dict[str, Any]:
    """Health check for the AI bot system."""
    try:
        stats = ai_router.get_service_stats()
        return {
            "status": "healthy",
            "services_count": stats["total_services"],
            "available_services": stats["available_services"],
            "router_status": stats["router_status"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        } 