"""
Comprehensive logging configuration for the Recipe Management application.
Configured to work seamlessly with Docker containers and provide structured logging.
"""

import logging
import logging.config
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
import traceback

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs for better parsing and monitoring.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add request context if available
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
            
        if hasattr(record, 'url'):
            log_entry["url"] = record.url
            
        if hasattr(record, 'method'):
            log_entry["method"] = record.method
            
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = record.status_code
            
        if hasattr(record, 'response_time'):
            log_entry["response_time_ms"] = record.response_time
        
        # Add exception information if present
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_entry["extra"] = record.extra_data
        
        return json.dumps(log_entry, default=str)

class SimpleFormatter(logging.Formatter):
    """
    Simple formatter for human-readable logs in development.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        level = record.levelname.ljust(8)
        logger = record.name
        message = record.getMessage()
        
        base_msg = f"{timestamp} [{level}] {logger}: {message}"
        
        # Add context if available
        context_parts = []
        if hasattr(record, 'request_id'):
            context_parts.append(f"req_id={record.request_id}")
        if hasattr(record, 'url'):
            context_parts.append(f"url={record.url}")
        if hasattr(record, 'method'):
            context_parts.append(f"method={record.method}")
        if hasattr(record, 'status_code'):
            context_parts.append(f"status={record.status_code}")
        
        if context_parts:
            base_msg += f" [{', '.join(context_parts)}]"
        
        if record.exc_info:
            base_msg += f"\n{self.formatException(record.exc_info)}"
        
        return base_msg

def get_logging_config(log_level: str = "INFO", use_structured: bool = True) -> Dict[str, Any]:
    """
    Get logging configuration dictionary.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_structured: Whether to use structured JSON logging
    
    Returns:
        Logging configuration dictionary
    """
    formatter_class = "app.logging_config.StructuredFormatter" if use_structured else "app.logging_config.SimpleFormatter"
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structured": {
                "()": "app.logging_config.StructuredFormatter"
            },
            "simple": {
                "()": "app.logging_config.SimpleFormatter"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "structured" if use_structured else "simple",
                "stream": sys.stdout
            },
            "error_console": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "structured" if use_structured else "simple",
                "stream": sys.stderr
            }
        },
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": "INFO",
                "handlers": ["error_console"],
                "propagate": False
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False
            },
            "pymongo": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "motor": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "openai": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "httpx": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            },
            "requests": {
                "level": "WARNING",
                "handlers": ["console"],
                "propagate": False
            }
        }
    }

def setup_logging(log_level: str = "INFO", use_structured: bool = True):
    """
    Setup logging configuration for the application.
    
    Args:
        log_level: Logging level
        use_structured: Whether to use structured JSON logging
    """
    config = get_logging_config(log_level, use_structured)
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger("app.logging")
    logger.info("Logging system initialized", extra={
        "extra_data": {
            "log_level": log_level,
            "structured_logging": use_structured,
            "environment": "docker" if use_structured else "development"
        }
    })

class RequestLogger:
    """
    Utility class for logging HTTP requests and responses.
    """
    
    @staticmethod
    def log_request(logger: logging.Logger, method: str, url: str, request_id: Optional[str] = None, **kwargs):
        """Log incoming HTTP request."""
        logger.info("Incoming request", extra={
            "method": method,
            "url": url,
            "request_id": request_id,
            "extra_data": kwargs
        })
    
    @staticmethod
    def log_response(logger: logging.Logger, method: str, url: str, status_code: int, 
                    response_time: float, request_id: Optional[str] = None, **kwargs):
        """Log HTTP response."""
        level = logging.INFO if status_code < 400 else logging.WARNING if status_code < 500 else logging.ERROR
        
        logger.log(level, "Request completed", extra={
            "method": method,
            "url": url,
            "status_code": status_code,
            "response_time": response_time,
            "request_id": request_id,
            "extra_data": kwargs
        })

class DatabaseLogger:
    """
    Utility class for logging database operations.
    """
    
    @staticmethod
    def log_operation(logger: logging.Logger, operation: str, collection: Optional[str] = None, 
                     duration: Optional[float] = None, **kwargs):
        """Log database operation."""
        logger.info(f"Database {operation}", extra={
            "extra_data": {
                "operation": operation,
                "collection": collection,
                "duration_ms": duration,
                **kwargs
            }
        })
    
    @staticmethod
    def log_error(logger: logging.Logger, operation: str, error: Exception, 
                 collection: Optional[str] = None, **kwargs):
        """Log database error."""
        logger.error(f"Database {operation} failed", exc_info=error, extra={
            "extra_data": {
                "operation": operation,
                "collection": collection,
                "error_type": type(error).__name__,
                **kwargs
            }
        })

class AILogger:
    """
    Utility class for logging AI operations.
    """
    
    @staticmethod
    def log_extraction_start(logger: logging.Logger, url: str, method: str, **kwargs):
        """Log start of recipe extraction."""
        logger.info("Starting recipe extraction", extra={
            "extra_data": {
                "url": url,
                "extraction_method": method,
                **kwargs
            }
        })
    
    @staticmethod
    def log_extraction_success(logger: logging.Logger, url: str, method: str, 
                              duration: float, **kwargs):
        """Log successful recipe extraction."""
        logger.info("Recipe extraction completed", extra={
            "extra_data": {
                "url": url,
                "extraction_method": method,
                "duration_ms": duration,
                "success": True,
                **kwargs
            }
        })
    
    @staticmethod
    def log_extraction_error(logger: logging.Logger, url: str, method: str, 
                           error: Exception, **kwargs):
        """Log recipe extraction error."""
        logger.error("Recipe extraction failed", exc_info=error, extra={
            "extra_data": {
                "url": url,
                "extraction_method": method,
                "error_type": type(error).__name__,
                "success": False,
                **kwargs
            }
        })
    
    @staticmethod
    def log_ai_call(logger: logging.Logger, model: str, prompt_type: str, 
                   duration: Optional[float] = None, token_usage: Optional[dict] = None, **kwargs):
        """Log AI model call."""
        logger.info("AI model call", extra={
            "extra_data": {
                "model": model,
                "prompt_type": prompt_type,
                "duration_ms": duration,
                "token_usage": token_usage,
                **kwargs
            }
        })