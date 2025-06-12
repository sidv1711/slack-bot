"""
AI Client Service - HTTP client for communicating with the AI Microservice.

This service replaces direct AI service calls with HTTP requests to the
standalone AI microservice, enabling modular architecture.
"""
import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class AIClientService:
    """HTTP client for the AI Microservice."""
    
    def __init__(self):
        """Initialize the AI client service."""
        self.settings = get_settings()
        self.ai_service_url = self.settings.ai_service_url or "http://localhost:8001"
        self.timeout = aiohttp.ClientTimeout(total=30)
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info(f"AI Client initialized for service at: {self.ai_service_url}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self.session
    
    async def close(self):
        """Close the HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process an AI request through the microservice.
        
        This is the main method that replaces AIRouterService.process_request().
        """
        try:
            session = await self._get_session()
            
            payload = {
                "user_input": user_input,
                "context": context or {}
            }
            
            async with session.post(
                f"{self.ai_service_url}/api/v1/ai/process",
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Convert microservice response to expected format
                    return {
                        "success": result.get("success", True),
                        "routing": {
                            "service": result.get("service", "unknown"),
                            "confidence": result.get("confidence", 0.0),
                            "reasoning": f"Routed to {result.get('service', 'unknown')} service"
                        },
                        **result.get("response_data", {})
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"AI service error {response.status}: {error_text}")
                    return {
                        "success": False,
                        "error": f"AI service error: {error_text}",
                        "routing": {"service": "error", "confidence": 0.0}
                    }
                    
        except asyncio.TimeoutError:
            logger.error("AI service request timeout")
            return {
                "success": False,
                "error": "AI service timeout",
                "routing": {"service": "error", "confidence": 0.0}
            }
        except Exception as e:
            logger.error(f"Error calling AI service: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to connect to AI service: {str(e)}",
                "routing": {"service": "error", "confidence": 0.0}
            }
    
    async def convert_nl2sql(self, natural_query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Convert natural language to SQL via microservice."""
        try:
            session = await self._get_session()
            
            payload = {
                "natural_query": natural_query,
                "execute_query": True,
                "context": context or {}
            }
            
            async with session.post(
                f"{self.ai_service_url}/api/v1/nl2sql/convert",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"success": False, "error": error_text}
                    
        except Exception as e:
            logger.error(f"Error in NL2SQL conversion: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def generate_code(self, description: str, language: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate code via microservice."""
        try:
            session = await self._get_session()
            
            payload = {
                "description": description,
                "language": language,
                "context": context or {}
            }
            
            async with session.post(
                f"{self.ai_service_url}/api/v1/code/generate",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"success": False, "error": error_text}
                    
        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def chat_respond(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get chat response via microservice."""
        try:
            session = await self._get_session()
            
            payload = {
                "message": message,
                "context": context or {}
            }
            
            async with session.post(
                f"{self.ai_service_url}/api/v1/chat/respond",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    return {"success": False, "error": error_text}
                    
        except Exception as e:
            logger.error(f"Error in chat response: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of AI microservice."""
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.ai_service_url}/health") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"status": "unhealthy", "error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"AI service health check failed: {str(e)}")
            return {"status": "unreachable", "error": str(e)}
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get metrics from AI microservice."""
        try:
            session = await self._get_session()
            
            async with session.get(f"{self.ai_service_url}/api/v1/metrics") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"HTTP {response.status}"}
                    
        except Exception as e:
            logger.error(f"Error getting AI service metrics: {str(e)}")
            return {"error": str(e)} 