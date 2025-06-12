"""Base class for all AI-powered services."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from openai import AsyncOpenAI
from loguru import logger
from ..config.settings import get_settings

class BaseAIService(ABC):
    """Base class for all AI-powered services."""
    
    def __init__(self, service_name: str, service_description: str):
        """Initialize the base AI service."""
        self.service_name = service_name
        self.service_description = service_description
        self.settings = get_settings()
        self.client = AsyncOpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None
        
        if not self.client:
            logger.warning(f"{service_name} service initialized without OpenAI client")
    
    @abstractmethod
    async def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process a user request and return a structured response.
        
        Args:
            user_input: The user's natural language input
            context: Optional context information (user info, conversation history, etc.)
            
        Returns:
            Structured response containing the service output
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Return information about what this service can do.
        
        Returns:
            Dictionary describing service capabilities
        """
        pass
    
    @abstractmethod
    def get_examples(self) -> List[Dict[str, str]]:
        """
        Return example inputs and outputs for this service.
        
        Returns:
            List of example dictionaries with 'input' and 'output' keys
        """
        pass
    
    @abstractmethod
    def validate_input(self, user_input: str) -> Dict[str, Any]:
        """
        Validate if the input is appropriate for this service.
        
        Args:
            user_input: The user's input to validate
            
        Returns:
            Dictionary with 'is_valid', 'reason', and optional 'suggestion' keys
        """
        pass
    
    async def call_openai(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1,
        max_tokens: int = 500,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Common method to call OpenAI API.
        
        Args:
            messages: List of message dictionaries for the conversation
            temperature: Creativity level (0.0 to 1.0)
            max_tokens: Maximum response length
            response_format: Optional response format specification
            
        Returns:
            The AI's response content
            
        Raises:
            ValueError: If OpenAI client is not available
        """
        if not self.client:
            raise ValueError(f"{self.service_name} requires OpenAI API key to be configured")
        
        try:
            kwargs = {
                "model": self.settings.openai_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            if response_format:
                kwargs["response_format"] = response_format
            
            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error calling OpenAI for {self.service_name}: {str(e)}")
            raise ValueError(f"Failed to get AI response: {str(e)}")
    
    def create_system_prompt(self, specific_instructions: str) -> str:
        """
        Create a system prompt with common structure.
        
        Args:
            specific_instructions: Service-specific instructions
            
        Returns:
            Complete system prompt
        """
        return f"""You are an expert AI assistant specializing in {self.service_description}.

{specific_instructions}

Always provide helpful, accurate, and safe responses. If you're unsure about something, say so rather than guessing.
""" 