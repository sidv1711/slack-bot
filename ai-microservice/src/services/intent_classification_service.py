"""Intent classification service to route user requests to appropriate AI services."""
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from .base_ai_service import BaseAIService

class IntentClassificationService(BaseAIService):
    """Service for classifying user intents and routing to appropriate AI services."""
    
    def __init__(self, available_services: Dict[str, str]):
        """
        Initialize the intent classification service.
        
        Args:
            available_services: Dictionary mapping service names to descriptions
        """
        super().__init__(
            service_name="Intent Classification",
            service_description="routing user queries to appropriate AI services"
        )
        self.available_services = available_services
    
    async def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Classify the user's intent and determine which service should handle it.
        
        Args:
            user_input: The user's natural language input
            context: Optional context information
            
        Returns:
            Dictionary with classified intent and confidence
        """
        try:
            system_prompt = self._create_classification_prompt()
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            response = await self.call_openai(
                messages=messages,
                temperature=0.1,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            # Validate the response
            if "service" not in result or result["service"] not in self.available_services:
                return {
                    "service": "general_chat",
                    "confidence": 0.5,
                    "reasoning": "Could not determine specific service",
                    "fallback": True
                }
            
            return {
                "service": result["service"],
                "confidence": result.get("confidence", 0.8),
                "reasoning": result.get("reasoning", "AI classification"),
                "fallback": False
            }
            
        except Exception as e:
            logger.error(f"Error in intent classification: {str(e)}")
            return {
                "service": "general_chat",
                "confidence": 0.3,
                "reasoning": f"Classification error: {str(e)}",
                "fallback": True
            }
    
    def _create_classification_prompt(self) -> str:
        """Create the classification prompt with available services."""
        services_description = "\n".join([
            f"- {name}: {description}" 
            for name, description in self.available_services.items()
        ])
        
        return self.create_system_prompt(f"""
You are an intent classification system. Analyze user queries and determine which service should handle them.

AVAILABLE SERVICES:
{services_description}

CLASSIFICATION RULES:
1. Analyze the user's query carefully
2. Determine which service is most appropriate
3. Provide a confidence score (0.0 to 1.0)
4. Explain your reasoning

RESPONSE FORMAT:
Return a JSON object with this exact structure:
{{
    "service": "service_name",
    "confidence": 0.85,
    "reasoning": "Brief explanation of why this service was chosen"
}}

EXAMPLES:

User: "Show me failed tests from yesterday"
Response: {{
    "service": "nl2sql",
    "confidence": 0.95,
    "reasoning": "User is asking for database query about test execution history"
}}

User: "Write a Python function to calculate fibonacci"
Response: {{
    "service": "code_generation",
    "confidence": 0.90,
    "reasoning": "User is requesting code generation for a specific algorithm"
}}

User: "What does this error mean?"
Response: {{
    "service": "bug_analysis",
    "confidence": 0.80,
    "reasoning": "User is asking for help understanding an error or bug"
}}

User: "Hello, how are you?"
Response: {{
    "service": "general_chat",
    "confidence": 0.85,
    "reasoning": "User is engaging in general conversation"
}}
""")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return intent classification capabilities."""
        return {
            "service": "Intent Classification",
            "description": "Routes user queries to appropriate AI services",
            "available_services": list(self.available_services.keys()),
            "features": [
                "Natural language intent detection",
                "Confidence scoring",
                "Fallback handling",
                "Multi-service routing"
            ]
        }
    
    def get_examples(self) -> List[Dict[str, str]]:
        """Return example classifications."""
        return [
            {
                "input": "Show me failed tests from yesterday",
                "output": "Routes to: nl2sql (Database queries)"
            },
            {
                "input": "Write a function to sort an array",
                "output": "Routes to: code_generation (Code creation)"
            },
            {
                "input": "Explain this error message",
                "output": "Routes to: bug_analysis (Error analysis)"
            },
            {
                "input": "Generate a test report",
                "output": "Routes to: report_generation (Document creation)"
            }
        ]
    
    def validate_input(self, user_input: str) -> Dict[str, Any]:
        """Validate user input for intent classification."""
        if not user_input or not user_input.strip():
            return {
                "is_valid": False,
                "reason": "Empty input cannot be classified",
                "suggestion": "Please provide a clear question or request"
            }
        
        if len(user_input.strip()) < 3:
            return {
                "is_valid": False,
                "reason": "Input too short for reliable classification",
                "suggestion": "Please provide a more detailed request"
            }
        
        return {
            "is_valid": True,
            "reason": "Input is suitable for intent classification"
        } 