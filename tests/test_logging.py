"""
Comprehensive tests for the logging system.
Tests structured logging, log formatting, and integration with application components.
"""

import json
import logging
import pytest
import io
from unittest.mock import patch, Mock
from app.logging_config import (
    StructuredFormatter, 
    SimpleFormatter, 
    setup_logging, 
    RequestLogger, 
    DatabaseLogger, 
    AILogger,
    get_logging_config
)


class TestStructuredFormatter:
    """Test the structured JSON formatter."""
    
    def test_basic_log_formatting(self):
        """Test basic log record formatting."""
        formatter = StructuredFormatter()
        
        # Create a test log record
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["level"] == "INFO"
        assert log_data["logger"] == "test.logger"
        assert log_data["message"] == "Test message"
        assert log_data["module"] == "test_module"
        assert log_data["function"] == "test_function"
        assert log_data["line"] == 42
        assert "timestamp" in log_data
    
    def test_request_context_formatting(self):
        """Test formatting with request context."""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Request processed",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.request_id = "req-123"
        record.user_id = "user-456"
        record.url = "/api/recipes"
        record.method = "GET"
        record.status_code = 200
        record.response_time = 150.5
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data["request_id"] == "req-123"
        assert log_data["user_id"] == "user-456"
        assert log_data["url"] == "/api/recipes"
        assert log_data["method"] == "GET"
        assert log_data["status_code"] == 200
        assert log_data["response_time_ms"] == 150.5
    
    def test_exception_formatting(self):
        """Test formatting with exception information."""
        formatter = StructuredFormatter()
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            record = logging.LogRecord(
                name="test.logger",
                level=logging.ERROR,
                pathname="/test/file.py",
                lineno=42,
                msg="Error occurred",
                args=(),
                exc_info=True
            )
            record.module = "test_module"
            record.funcName = "test_function"
            
            formatted = formatter.format(record)
            log_data = json.loads(formatted)
            
            assert "exception" in log_data
            assert log_data["exception"]["type"] == "ValueError"
            assert log_data["exception"]["message"] == "Test exception"
            assert "traceback" in log_data["exception"]
    
    def test_extra_data_formatting(self):
        """Test formatting with extra data."""
        formatter = StructuredFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Custom data",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.extra_data = {"custom": "value", "number": 42}
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert "extra" in log_data
        assert log_data["extra"]["custom"] == "value"
        assert log_data["extra"]["number"] == 42


class TestSimpleFormatter:
    """Test the simple human-readable formatter."""
    
    def test_basic_formatting(self):
        """Test basic log formatting."""
        formatter = SimpleFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        formatted = formatter.format(record)
        
        assert "INFO" in formatted
        assert "test.logger" in formatted
        assert "Test message" in formatted
        assert formatted.count(":") >= 3  # timestamp format
    
    def test_context_formatting(self):
        """Test formatting with context information."""
        formatter = SimpleFormatter()
        
        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Request processed",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        record.request_id = "req-123"
        record.url = "/api/recipes"
        record.method = "GET"
        record.status_code = 200
        
        formatted = formatter.format(record)
        
        assert "req_id=req-123" in formatted
        assert "url=/api/recipes" in formatted
        assert "method=GET" in formatted
        assert "status=200" in formatted


class TestLoggingConfiguration:
    """Test logging configuration and setup."""
    
    def test_get_logging_config_structured(self):
        """Test getting structured logging configuration."""
        config = get_logging_config(log_level="DEBUG", use_structured=True)
        
        assert config["version"] == 1
        assert config["disable_existing_loggers"] is False
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config
        
        # Check that structured formatter is used
        console_handler = config["handlers"]["console"]
        assert console_handler["formatter"] == "structured"
    
    def test_get_logging_config_simple(self):
        """Test getting simple logging configuration."""
        config = get_logging_config(log_level="WARNING", use_structured=False)
        
        # Check that simple formatter is used
        console_handler = config["handlers"]["console"]
        assert console_handler["formatter"] == "simple"
        
        # Check log level
        assert console_handler["level"] == "WARNING"
    
    @patch('logging.config.dictConfig')
    def test_setup_logging(self, mock_dict_config):
        """Test logging setup function."""
        setup_logging(log_level="INFO", use_structured=True)
        
        # Verify dictConfig was called
        mock_dict_config.assert_called_once()
        
        # Check the configuration passed
        config = mock_dict_config.call_args[0][0]
        assert config["handlers"]["console"]["level"] == "INFO"


class TestRequestLogger:
    """Test the RequestLogger utility class."""
    
    def test_log_request(self):
        """Test logging incoming requests."""
        logger = Mock()
        
        RequestLogger.log_request(
            logger, 
            method="POST", 
            url="/api/recipes", 
            request_id="req-123",
            client_ip="192.168.1.1",
            user_agent="TestClient/1.0"
        )
        
        logger.info.assert_called_once()
        call_args = logger.info.call_args
        
        assert call_args[0][0] == "Incoming request"
        extra = call_args[1]["extra"]
        assert extra["method"] == "POST"
        assert extra["url"] == "/api/recipes"
        assert extra["request_id"] == "req-123"
    
    def test_log_response_success(self):
        """Test logging successful responses."""
        logger = Mock()
        
        RequestLogger.log_response(
            logger,
            method="GET",
            url="/api/recipes",
            status_code=200,
            response_time=150.0,
            request_id="req-123"
        )
        
        # Should log at INFO level for 2xx status
        logger.log.assert_called_once()
        call_args = logger.log.call_args
        assert call_args[0][0] == logging.INFO
    
    def test_log_response_client_error(self):
        """Test logging client error responses."""
        logger = Mock()
        
        RequestLogger.log_response(
            logger,
            method="GET",
            url="/api/recipes/invalid",
            status_code=404,
            response_time=50.0,
            request_id="req-123"
        )
        
        # Should log at WARNING level for 4xx status
        logger.log.assert_called_once()
        call_args = logger.log.call_args
        assert call_args[0][0] == logging.WARNING
    
    def test_log_response_server_error(self):
        """Test logging server error responses."""
        logger = Mock()
        
        RequestLogger.log_response(
            logger,
            method="POST",
            url="/api/recipes",
            status_code=500,
            response_time=1000.0,
            request_id="req-123"
        )
        
        # Should log at ERROR level for 5xx status
        logger.log.assert_called_once()
        call_args = logger.log.call_args
        assert call_args[0][0] == logging.ERROR


class TestDatabaseLogger:
    """Test the DatabaseLogger utility class."""
    
    def test_log_operation(self):
        """Test logging database operations."""
        logger = Mock()
        
        DatabaseLogger.log_operation(
            logger,
            operation="insert",
            collection="recipes",
            duration=25.5,
            document_count=1
        )
        
        logger.info.assert_called_once()
        call_args = logger.info.call_args
        
        assert call_args[0][0] == "Database insert"
        extra = call_args[1]["extra"]["extra_data"]
        assert extra["operation"] == "insert"
        assert extra["collection"] == "recipes"
        assert extra["duration_ms"] == 25.5
        assert extra["document_count"] == 1
    
    def test_log_error(self):
        """Test logging database errors."""
        logger = Mock()
        error = ConnectionError("Database connection failed")
        
        DatabaseLogger.log_error(
            logger,
            operation="connect",
            error=error,
            collection="recipes",
            retry_count=3
        )
        
        logger.error.assert_called_once()
        call_args = logger.error.call_args
        
        assert call_args[0][0] == "Database connect failed"
        assert call_args[1]["exc_info"] == error
        extra = call_args[1]["extra"]["extra_data"]
        assert extra["operation"] == "connect"
        assert extra["error_type"] == "ConnectionError"


class TestAILogger:
    """Test the AILogger utility class."""
    
    def test_log_extraction_start(self):
        """Test logging extraction start."""
        logger = Mock()
        
        AILogger.log_extraction_start(
            logger,
            url="https://example.com/recipe",
            method="scrapegraphai",
            request_id="req-123"
        )
        
        logger.info.assert_called_once()
        call_args = logger.info.call_args
        
        assert call_args[0][0] == "Starting recipe extraction"
        extra = call_args[1]["extra"]["extra_data"]
        assert extra["url"] == "https://example.com/recipe"
        assert extra["extraction_method"] == "scrapegraphai"
        assert extra["request_id"] == "req-123"
    
    def test_log_extraction_success(self):
        """Test logging successful extraction."""
        logger = Mock()
        
        AILogger.log_extraction_success(
            logger,
            url="https://example.com/recipe",
            method="scrapegraphai",
            duration=1500.0,
            recipe_id="recipe-123",
            images_found=3
        )
        
        logger.info.assert_called_once()
        call_args = logger.info.call_args
        
        assert call_args[0][0] == "Recipe extraction completed"
        extra = call_args[1]["extra"]["extra_data"]
        assert extra["url"] == "https://example.com/recipe"
        assert extra["extraction_method"] == "scrapegraphai"
        assert extra["duration_ms"] == 1500.0
        assert extra["success"] is True
        assert extra["recipe_id"] == "recipe-123"
    
    def test_log_extraction_error(self):
        """Test logging extraction errors."""
        logger = Mock()
        error = ValueError("Invalid recipe data")
        
        AILogger.log_extraction_error(
            logger,
            url="https://example.com/recipe",
            method="rule_based",
            error=error,
            retry_count=2
        )
        
        logger.error.assert_called_once()
        call_args = logger.error.call_args
        
        assert call_args[0][0] == "Recipe extraction failed"
        assert call_args[1]["exc_info"] == error
        extra = call_args[1]["extra"]["extra_data"]
        assert extra["url"] == "https://example.com/recipe"
        assert extra["extraction_method"] == "rule_based"
        assert extra["error_type"] == "ValueError"
        assert extra["success"] is False
    
    def test_log_ai_call(self):
        """Test logging AI model calls."""
        logger = Mock()
        
        AILogger.log_ai_call(
            logger,
            model="gpt-4.1-mini",
            prompt_type="recipe_extraction",
            duration=2000.0,
            token_usage={"prompt_tokens": 150, "completion_tokens": 300},
            cost=0.001
        )
        
        logger.info.assert_called_once()
        call_args = logger.info.call_args
        
        assert call_args[0][0] == "AI model call"
        extra = call_args[1]["extra"]["extra_data"]
        assert extra["model"] == "gpt-4.1-mini"
        assert extra["prompt_type"] == "recipe_extraction"
        assert extra["duration_ms"] == 2000.0
        assert extra["token_usage"]["prompt_tokens"] == 150
        assert extra["cost"] == 0.001


class TestLoggingIntegration:
    """Test logging integration with application components."""
    
    @patch('sys.stdout', new_callable=io.StringIO)
    def test_structured_logging_output(self, mock_stdout):
        """Test that structured logging produces valid JSON."""
        # Setup structured logging
        setup_logging(log_level="INFO", use_structured=True)
        
        logger = logging.getLogger("test.integration")
        logger.info("Test message", extra={
            "extra_data": {"test": "value"}
        })
        
        # Check that output contains valid JSON
        output = mock_stdout.getvalue()
        if output.strip():
            log_data = json.loads(output.strip())
            assert log_data["message"] == "Test message"
            assert log_data["logger"] == "test.integration"
    
    def test_logger_hierarchy(self):
        """Test that logger hierarchy works correctly."""
        # Setup logging
        setup_logging(log_level="DEBUG", use_structured=False)
        
        # Test different loggers
        app_logger = logging.getLogger("app.test")
        uvicorn_logger = logging.getLogger("uvicorn.test")
        
        assert app_logger.level <= logging.DEBUG
        assert uvicorn_logger.level <= logging.INFO
    
    def test_error_logger_separation(self):
        """Test that error logs go to stderr."""
        config = get_logging_config(log_level="INFO", use_structured=True)
        
        error_handler = config["handlers"]["error_console"]
        assert error_handler["level"] == "ERROR"
        assert error_handler["stream"] == "ext://sys.stderr"


class TestLoggingPerformance:
    """Test logging performance and efficiency."""
    
    def test_log_message_performance(self):
        """Test that logging doesn't significantly impact performance."""
        import time
        
        logger = logging.getLogger("test.performance")
        logger.setLevel(logging.INFO)
        
        # Test logging performance
        start_time = time.time()
        for i in range(1000):
            logger.info("Performance test message", extra={
                "extra_data": {"iteration": i}
            })
        end_time = time.time()
        
        # Logging 1000 messages should be fast (< 1 second in most cases)
        duration = end_time - start_time
        assert duration < 5.0  # Very generous limit for CI environments
    
    def test_disabled_logger_performance(self):
        """Test that disabled loggers have minimal overhead."""
        import time
        
        logger = logging.getLogger("test.disabled")
        logger.setLevel(logging.CRITICAL)  # Disable lower levels
        
        start_time = time.time()
        for i in range(10000):
            logger.debug("This should be ignored")  # Below threshold
        end_time = time.time()
        
        # Disabled logging should be very fast
        duration = end_time - start_time
        assert duration < 1.0


@pytest.mark.integration
class TestLoggingWithApplication:
    """Integration tests for logging with the full application."""
    
    def test_application_startup_logging(self):
        """Test that application startup is properly logged."""
        with patch('app.main.logger') as mock_logger:
            # Import should trigger logging setup
            from app.main import app
            
            # Should have logged startup messages
            assert mock_logger.info.called
    
    def test_request_logging_middleware(self):
        """Test that request logging middleware works."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        with patch('app.main.logger') as mock_logger:
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            # Should have logged the request and response
            assert mock_logger.info.called or mock_logger.log.called
            
            # Response should include request ID header
            assert "X-Request-ID" in response.headers
    
    def test_database_operation_logging(self):
        """Test that database operations are logged."""
        with patch('app.database.logger') as mock_logger:
            from app.database import connect_to_mongo
            
            # This will likely fail in test environment, but should log the attempt
            try:
                import asyncio
                asyncio.run(connect_to_mongo())
            except:
                pass  # Expected to fail in test environment
            
            # Should have logged the connection attempt
            assert mock_logger.info.called or mock_logger.error.called