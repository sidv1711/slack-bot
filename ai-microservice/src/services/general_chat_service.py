"""General chat AI service for casual conversation."""
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from .base_ai_service import BaseAIService

class GeneralChatService(BaseAIService):
    """AI service for general conversation and non-specialized queries."""
    
    def __init__(self):
        """Initialize the general chat service."""
        super().__init__(
            service_name="General Chat",
            service_description="general conversation and information queries"
        )
    
    async def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle general conversation and information queries.
        
        Args:
            user_input: The user's message or question
            context: Optional context (conversation history, user preferences, etc.)
            
        Returns:
            Dictionary with conversational response
        """
        try:
            system_prompt = self._create_chat_prompt(context)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Add conversation history if available
            if context and "conversation_history" in context:
                history = context["conversation_history"]
                # Insert history before the current user message
                messages = [messages[0]] + history + [messages[1]]
            
            response = await self.call_openai(
                messages=messages,
                temperature=0.7,  # Higher temperature for more conversational responses
                max_tokens=600
            )
            
            return {
                "service": "general_chat",
                "success": True,
                "response": response,
                "user_message": user_input,
                "service_type": "conversation",
                "tone": self._analyze_tone(response)
            }
            
        except Exception as e:
            logger.error(f"Error in general chat: {str(e)}")
            return {
                "service": "general_chat",
                "success": False,
                "error": str(e),
                "response": "I apologize, but I'm having trouble responding right now. Please try again.",
                "user_message": user_input,
                "service_type": "conversation"
            }
    
    def _create_chat_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Create chat prompt with context."""
        user_info = ""
        if context:
            if "user_name" in context:
                user_info += f"The user's name is {context['user_name']}. "
            if "user_role" in context:
                user_info += f"They work as a {context['user_role']}. "
        
        return self.create_system_prompt(f"""
You are a helpful, friendly, and knowledgeable AI assistant. You can engage in natural conversation while being informative and supportive.

{user_info}

CONVERSATION GUIDELINES:
1. Be conversational and friendly
2. Provide helpful and accurate information
3. Ask clarifying questions when needed
4. Acknowledge when you don't know something
5. Keep responses concise but informative
6. Show empathy and understanding
7. Offer suggestions or next steps when appropriate

TOPICS YOU CAN HELP WITH:
- General questions and information
- Explanations of concepts
- Advice and recommendations
- Problem-solving discussions
- Creative brainstorming
- Learning and education
- Technology questions (non-coding)

IMPORTANT: If the user asks about specialized tasks like:
- Database queries or SQL
- Code generation or programming
- Technical analysis or debugging
- Document generation

Politely suggest they might want to use specific tools for those tasks, but still try to provide general help if possible.
""")
    
    def _analyze_tone(self, response: str) -> str:
        """Analyze the tone of the response."""
        if not response:
            return "neutral"
        
        response_lower = response.lower()
        
        if any(word in response_lower for word in ["sorry", "apologize", "unfortunately"]):
            return "apologetic"
        elif any(word in response_lower for word in ["great", "excellent", "wonderful", "amazing"]):
            return "enthusiastic"
        elif any(word in response_lower for word in ["help", "assist", "support", "guide"]):
            return "helpful"
        elif "?" in response:
            return "inquisitive"
        else:
            return "informative"
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return general chat capabilities."""
        return {
            "service": "General Chat",
            "description": "Engage in natural conversation and provide general information",
            "conversation_features": [
                "Natural dialogue",
                "Question answering",
                "Explanations and definitions",
                "Advice and recommendations",
                "Creative brainstorming",
                "Problem discussion"
            ],
            "knowledge_areas": [
                "General knowledge",
                "Science and technology",
                "History and culture",
                "Learning and education",
                "Business and productivity",
                "Health and wellness (general info only)"
            ],
            "interaction_style": [
                "Friendly and approachable",
                "Informative and accurate",
                "Empathetic and understanding",
                "Concise but thorough"
            ]
        }
    
    def get_examples(self) -> List[Dict[str, str]]:
        """Return example chat interactions."""
        return [
            {
                "input": "Hi! How are you doing today?",
                "output": "Friendly greeting and offer to help"
            },
            {
                "input": "Can you explain what machine learning is?",
                "output": "Clear explanation of machine learning concepts"
            },
            {
                "input": "I'm feeling stressed about a project deadline",
                "output": "Empathetic response with stress management suggestions"
            },
            {
                "input": "What's the best way to learn a new programming language?",
                "output": "Structured advice on learning approaches and resources"
            },
            {
                "input": "Tell me something interesting about space",
                "output": "Engaging space facts or recent discoveries"
            }
        ]
    
    def validate_input(self, user_input: str) -> Dict[str, Any]:
        """Validate user input for general chat."""
        if not user_input or not user_input.strip():
            return {
                "is_valid": False,
                "reason": "Empty message cannot be processed",
                "suggestion": "Please type a message or question"
            }
        
        # General chat accepts almost any input
        # Only reject obviously malicious or inappropriate content
        inappropriate_keywords = [
            "hack", "crack", "illegal", "harmful", "dangerous"
        ]
        
        lower_input = user_input.lower()
        for keyword in inappropriate_keywords:
            if keyword in lower_input:
                return {
                    "is_valid": False,
                    "reason": f"Message appears to contain inappropriate content: '{keyword}'",
                    "suggestion": "Please ask about something else I can help with"
                }
        
        return {
            "is_valid": True,
            "reason": "Message is suitable for general conversation"
        } 