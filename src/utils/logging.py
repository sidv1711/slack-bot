"""Logging utilities to reduce code duplication."""
from typing import Any, Optional, Dict
from loguru import logger
from functools import wraps

def log_operation(operation_name: str, log_level: str = "info"):
    """Decorator to log function operations with consistent formatting."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger_func = getattr(logger, log_level)
            logger_func(f"=== Starting {operation_name} ===")
            try:
                result = await func(*args, **kwargs)
                logger_func(f"=== Completed {operation_name} successfully ===")
                return result
            except Exception as e:
                logger.error(f"=== {operation_name} failed: {e} ===")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger_func = getattr(logger, log_level)
            logger_func(f"=== Starting {operation_name} ===")
            try:
                result = func(*args, **kwargs)
                logger_func(f"=== Completed {operation_name} successfully ===")
                return result
            except Exception as e:
                logger.error(f"=== {operation_name} failed: {e} ===")
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def log_database_operation(table_name: str, operation: str, params: Optional[Dict[str, Any]] = None):
    """Log database operations with consistent formatting."""
    param_str = f" with params: {params}" if params else ""
    logger.debug(f"Database {operation} on {table_name}{param_str}")

def log_api_call(service: str, endpoint: str, status: Optional[int] = None):
    """Log external API calls with consistent formatting."""
    status_str = f" (status: {status})" if status else ""
    logger.debug(f"API call to {service} {endpoint}{status_str}")

def log_user_action(user_id: str, action: str, details: Optional[str] = None):
    """Log user actions with consistent formatting."""
    detail_str = f" - {details}" if details else ""
    logger.info(f"User {user_id}: {action}{detail_str}")

def log_error_with_context(error: Exception, context: Dict[str, Any]):
    """Log errors with additional context information."""
    logger.error(f"Error: {error}")
    for key, value in context.items():
        logger.error(f"Context {key}: {value}")

def mask_sensitive_data(data: Dict[str, Any], sensitive_keys: list = None) -> Dict[str, Any]:
    """Mask sensitive data in dictionaries for safe logging."""
    if sensitive_keys is None:
        sensitive_keys = ["token", "secret", "key", "password", "auth"]
    
    masked_data = {}
    for key, value in data.items():
        if any(sensitive in key.lower() for sensitive in sensitive_keys):
            masked_data[key] = "***MASKED***"
        else:
            masked_data[key] = value
    
    return masked_data 