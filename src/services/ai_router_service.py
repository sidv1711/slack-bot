"""Central AI router service that manages and routes requests to appropriate AI services."""
from typing import Dict, Any, List, Optional
from loguru import logger

from .base_ai_service import BaseAIService
from .intent_classification_service import IntentClassificationService
from .nl2sql_adapter_service import NL2SQLAdapter
from .code_generation_service import CodeGenerationService
from .general_chat_service import GeneralChatService

class AIRouterService:
    """Central service that routes user requests to appropriate AI services."""
    
    def __init__(self):
        """Initialize the AI router with all available services."""
        self.services: Dict[str, BaseAIService] = {}
        self._initialize_services()
        
        # Initialize intent classifier with available services
        service_descriptions = {
            name: service.service_description 
            for name, service in self.services.items()
        }
        self.intent_classifier = IntentClassificationService(service_descriptions)
        
        logger.info(f"AI Router initialized with services: {list(self.services.keys())}")
    
    def _initialize_services(self):
        """Initialize all available AI services."""
        try:
            # Database query service
            self.services["nl2sql"] = NL2SQLAdapter()
            logger.info("✓ NL2SQL service initialized")
            
            # Code generation service
            self.services["code_generation"] = CodeGenerationService()
            logger.info("✓ Code Generation service initialized")
            
            # General chat service (fallback)
            self.services["general_chat"] = GeneralChatService()
            logger.info("✓ General Chat service initialized")
            
            # You can easily add more services here:
            # self.services["bug_analysis"] = BugAnalysisService()
            # self.services["documentation"] = DocumentationService()
            # self.services["report_generation"] = ReportGenerationService()
            
        except Exception as e:
            logger.error(f"Error initializing AI services: {str(e)}")
            # Ensure we at least have general chat as fallback
            if "general_chat" not in self.services:
                self.services["general_chat"] = GeneralChatService()
    
    async def process_request(
        self, 
        user_input: str, 
        context: Optional[Dict[str, Any]] = None,
        force_service: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user request by routing it to the appropriate AI service.
        
        Args:
            user_input: The user's natural language input
            context: Optional context information (user info, conversation history, etc.)
            force_service: Optional service name to force routing to (bypasses intent classification)
            
        Returns:
            Dictionary with the service response and routing information
        """
        try:
            # Validate input
            if not user_input or not user_input.strip():
                return {
                    "success": False,
                    "error": "Empty input provided",
                    "suggestion": "Please provide a question or request"
                }
            
            # Determine which service to use
            if force_service:
                service_name = force_service
                routing_info = {
                    "service": service_name,
                    "confidence": 1.0,
                    "reasoning": "Service manually specified",
                    "method": "forced"
                }
            else:
                # Use intent classification
                intent_result = await self.intent_classifier.process_request(user_input, context)
                service_name = intent_result.get("service", "general_chat")
                routing_info = {
                    "service": service_name,
                    "confidence": intent_result.get("confidence", 0.5),
                    "reasoning": intent_result.get("reasoning", "AI classification"),
                    "method": "classified"
                }
            
            # Validate service exists
            if service_name not in self.services:
                logger.warning(f"Unknown service '{service_name}', falling back to general_chat")
                service_name = "general_chat"
                routing_info["fallback"] = True
            
            # Get the service
            service = self.services[service_name]
            
            # Validate input for the specific service
            validation = service.validate_input(user_input)
            if not validation["is_valid"]:
                # If validation fails, try general chat instead
                logger.info(f"Input validation failed for {service_name}, using general_chat")
                service = self.services["general_chat"]
                service_name = "general_chat"
                routing_info["fallback"] = True
                routing_info["validation_error"] = validation["reason"]
            
            # Process the request
            logger.info(f"Routing request to {service_name} service")
            result = await service.process_request(user_input, context)
            
            # Add routing information to the result
            result["routing"] = routing_info
            result["timestamp"] = context.get("timestamp") if context else None
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AI router: {str(e)}")
            return {
                "success": False,
                "error": f"AI routing error: {str(e)}",
                "service": "error",
                "routing": {
                    "method": "error_fallback",
                    "error": str(e)
                }
            }
    
    def get_available_services(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available services."""
        return {
            name: service.get_capabilities()
            for name, service in self.services.items()
        }
    
    def get_service_examples(self, service_name: Optional[str] = None) -> Dict[str, List[Dict[str, str]]]:
        """Get examples for services."""
        if service_name:
            if service_name in self.services:
                return {service_name: self.services[service_name].get_examples()}
            else:
                return {"error": f"Service '{service_name}' not found"}
        else:
            return {
                name: service.get_examples()
                for name, service in self.services.items()
            }
    
    async def validate_request_for_service(
        self, 
        user_input: str, 
        service_name: str
    ) -> Dict[str, Any]:
        """Validate if a request is appropriate for a specific service."""
        if service_name not in self.services:
            return {
                "is_valid": False,
                "reason": f"Service '{service_name}' does not exist",
                "available_services": list(self.services.keys())
            }
        
        service = self.services[service_name]
        return service.validate_input(user_input)
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get statistics about the AI router and services."""
        return {
            "total_services": len(self.services),
            "available_services": list(self.services.keys()),
            "router_status": "operational",
            "classification_service": "enabled",
            "features": [
                "Intent classification",
                "Service routing",
                "Input validation",
                "Fallback handling",
                "Error recovery"
            ]
        }
    
    def add_service(self, name: str, service: BaseAIService):
        """
        Dynamically add a new AI service.
        
        Args:
            name: Name of the service
            service: Service instance that implements BaseAIService
        """
        if not isinstance(service, BaseAIService):
            raise ValueError("Service must inherit from BaseAIService")
        
        self.services[name] = service
        
        # Update intent classifier with new service
        service_descriptions = {
            name: service.service_description 
            for name, service in self.services.items()
        }
        self.intent_classifier = IntentClassificationService(service_descriptions)
        
        logger.info(f"Added new AI service: {name}")
    
    def remove_service(self, name: str):
        """
        Remove an AI service.
        
        Args:
            name: Name of the service to remove
        """
        if name == "general_chat":
            raise ValueError("Cannot remove general_chat service (it's the fallback)")
        
        if name in self.services:
            del self.services[name]
            
            # Update intent classifier
            service_descriptions = {
                name: service.service_description 
                for name, service in self.services.items()
            }
            self.intent_classifier = IntentClassificationService(service_descriptions)
            
            logger.info(f"Removed AI service: {name}")
        else:
            logger.warning(f"Service '{name}' not found for removal") 