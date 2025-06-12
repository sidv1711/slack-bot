"""Code generation AI service."""
import json
from typing import Dict, Any, List, Optional
from loguru import logger
from .base_ai_service import BaseAIService

class CodeGenerationService(BaseAIService):
    """AI service for generating code from natural language descriptions."""
    
    def __init__(self):
        """Initialize the code generation service."""
        super().__init__(
            service_name="Code Generation",
            service_description="generating code from natural language descriptions"
        )
    
    async def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate code based on natural language description.
        
        Args:
            user_input: The user's code generation request
            context: Optional context (preferred language, framework, etc.)
            
        Returns:
            Dictionary with generated code and explanation
        """
        try:
            # Extract language preference from context or input
            language = self._extract_language(user_input, context)
            
            system_prompt = self._create_code_generation_prompt(language)
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            response = await self.call_openai(
                messages=messages,
                temperature=0.2,  # Low temperature for more consistent code
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response)
            
            return {
                "service": "code_generation",
                "success": True,
                "code": result.get("code", ""),
                "language": result.get("language", language),
                "explanation": result.get("explanation", ""),
                "usage_example": result.get("usage_example", ""),
                "user_request": user_input,
                "service_type": "code_generation"
            }
            
        except Exception as e:
            logger.error(f"Error in code generation: {str(e)}")
            return {
                "service": "code_generation",
                "success": False,
                "error": str(e),
                "user_request": user_input,
                "service_type": "code_generation"
            }
    
    def _extract_language(self, user_input: str, context: Optional[Dict[str, Any]]) -> str:
        """Extract programming language from input or context."""
        if context and "language" in context:
            return context["language"]
        
        # Common language keywords
        language_keywords = {
            "python": ["python", "py", "django", "flask", "pandas"],
            "javascript": ["javascript", "js", "node", "react", "vue", "angular"],
            "java": ["java", "spring", "maven"],
            "typescript": ["typescript", "ts"],
            "go": ["go", "golang"],
            "rust": ["rust"],
            "cpp": ["c++", "cpp"],
            "csharp": ["c#", "csharp", ".net"],
            "sql": ["sql", "database", "query"]
        }
        
        lower_input = user_input.lower()
        for language, keywords in language_keywords.items():
            if any(keyword in lower_input for keyword in keywords):
                return language
        
        return "python"  # Default to Python
    
    def _create_code_generation_prompt(self, language: str) -> str:
        """Create code generation prompt for specific language."""
        return self.create_system_prompt(f"""
You are an expert {language} programmer. Generate clean, efficient, and well-documented code based on user requests.

GUIDELINES:
1. Write production-ready code with proper error handling
2. Include helpful comments explaining complex logic
3. Follow language-specific best practices and conventions
4. Provide usage examples when appropriate
5. Focus on readability and maintainability

RESPONSE FORMAT:
Return a JSON object with this structure:
{{
    "code": "// The actual code here",
    "language": "{language}",
    "explanation": "Clear explanation of what the code does and how it works",
    "usage_example": "Example of how to use the code"
}}

EXAMPLE:
User: "Write a function to calculate fibonacci numbers"
Response: {{
    "code": "def fibonacci(n):\\n    if n <= 1:\\n        return n\\n    return fibonacci(n-1) + fibonacci(n-2)",
    "language": "python",
    "explanation": "Recursive function that calculates the nth Fibonacci number using the mathematical definition",
    "usage_example": "print(fibonacci(10))  # Output: 55"
}}
""")
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Return code generation capabilities."""
        return {
            "service": "Code Generation",
            "description": "Generate code from natural language descriptions",
            "supported_languages": [
                "Python", "JavaScript", "TypeScript", "Java", "Go", 
                "Rust", "C++", "C#", "SQL"
            ],
            "features": [
                "Function and class generation",
                "Algorithm implementation",
                "API client code",
                "Data processing scripts",
                "Test code generation",
                "Code documentation",
                "Usage examples"
            ],
            "code_quality": [
                "Error handling",
                "Best practices",
                "Code comments",
                "Production-ready",
                "Maintainable"
            ]
        }
    
    def get_examples(self) -> List[Dict[str, str]]:
        """Return example code generation requests."""
        return [
            {
                "input": "Write a Python function to sort a list of dictionaries by a key",
                "output": "Generates a sorting function with error handling"
            },
            {
                "input": "Create a JavaScript API client for REST endpoints",
                "output": "Generates a class with HTTP methods and error handling"
            },
            {
                "input": "Write a SQL query to find duplicate records",
                "output": "Generates SQL with proper grouping and having clauses"
            },
            {
                "input": "Generate a Python class for managing user sessions",
                "output": "Generates a session manager with authentication methods"
            }
        ]
    
    def validate_input(self, user_input: str) -> Dict[str, Any]:
        """Validate user input for code generation."""
        if not user_input or not user_input.strip():
            return {
                "is_valid": False,
                "reason": "Empty request cannot generate code",
                "suggestion": "Please describe what code you want me to generate"
            }
        
        # Check if it's actually a code generation request
        code_keywords = [
            "write", "create", "generate", "code", "function", "class", 
            "script", "program", "algorithm", "implement", "build"
        ]
        
        lower_input = user_input.lower()
        if not any(keyword in lower_input for keyword in code_keywords):
            return {
                "is_valid": False,
                "reason": "Request doesn't appear to be asking for code generation",
                "suggestion": "Try phrases like 'write a function', 'create a class', or 'generate code'"
            }
        
        return {
            "is_valid": True,
            "reason": "Request is suitable for code generation"
        } 