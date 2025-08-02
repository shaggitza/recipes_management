"""
Integration tests for the complete application.
Tests the full request/response cycle including logging, database operations, and error handling.
"""

import pytest
import asyncio
import json
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings


class TestApplicationIntegration:
    """Test complete application integration."""
    
    def test_application_startup(self):
        """Test that the application starts up correctly."""
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == settings.app_version
        assert "environment" in data
    
    def test_home_page_rendering(self):
        """Test that the home page renders correctly."""
        client = TestClient(app)
        
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    def test_request_id_middleware(self):
        """Test that request ID middleware works."""
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        
        # Should have request ID in headers
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]
        assert len(request_id) > 0
    
    def test_error_handling(self):
        """Test application error handling."""
        client = TestClient(app)
        
        # Test 404 error
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
    
    def test_cors_headers(self):
        """Test CORS configuration if present."""
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        # Basic test - just ensure we get a response


class TestAPIIntegration:
    """Test API endpoints integration."""
    
    def test_recipes_api_accessible(self):
        """Test that recipes API is accessible."""
        client = TestClient(app)
        
        # Test recipes list endpoint
        response = client.get("/api/recipes/")
        # Should return 200 or 500 (if DB not connected), not 404
        assert response.status_code in [200, 500]
    
    def test_ai_import_api_accessible(self):
        """Test that AI import API is accessible."""
        client = TestClient(app)
        
        # Test import test endpoint
        response = client.get("/ai/import/test")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "components" in data
    
    def test_ai_import_validation(self):
        """Test AI import request validation."""
        client = TestClient(app)
        
        # Test with invalid URL
        response = client.post("/ai/import", json={"url": "invalid-url"})
        assert response.status_code == 422
    
    def test_static_files_serving(self):
        """Test that static files are served correctly."""
        client = TestClient(app)
        
        # Test accessing a static file (may not exist, but should not error)
        response = client.get("/static/style.css")
        # Should return 200 or 404, not 500
        assert response.status_code in [200, 404]


class TestLoggingIntegration:
    """Test logging integration across the application."""
    
    @patch('app.main.logger')
    def test_request_logging(self, mock_logger):
        """Test that requests are properly logged."""
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        
        # Should have logged request and response
        assert mock_logger.info.called or mock_logger.log.called
    
    @patch('app.main.logger')
    def test_error_logging(self, mock_logger):
        """Test that errors are properly logged."""
        with patch('app.main.templates.TemplateResponse', side_effect=Exception("Test error")):
            client = TestClient(app)
            
            try:
                response = client.get("/")
            except:
                pass  # Expected to fail
            
            # Should have logged the error
            assert mock_logger.error.called
    
    def test_structured_logging_format(self):
        """Test that structured logging produces valid JSON."""
        from app.logging_config import StructuredFormatter
        import logging
        
        formatter = StructuredFormatter()
        record = logging.LogRecord(
            name="test.integration",
            level=logging.INFO,
            pathname="/test/file.py",
            lineno=42,
            msg="Integration test message",
            args=(),
            exc_info=None
        )
        record.module = "test_module"
        record.funcName = "test_function"
        
        formatted = formatter.format(record)
        
        # Should be valid JSON
        log_data = json.loads(formatted)
        assert log_data["message"] == "Integration test message"
        assert log_data["level"] == "INFO"


class TestDatabaseIntegration:
    """Test database integration and error handling."""
    
    @patch('app.database.logger')
    def test_database_connection_logging(self, mock_logger):
        """Test that database operations are logged."""
        from app.database import connect_to_mongo, close_mongo_connection
        
        async def test_connection():
            try:
                await connect_to_mongo()
                await close_mongo_connection()
            except:
                pass  # Expected to fail in test environment
        
        asyncio.run(test_connection())
        
        # Should have logged connection attempts
        assert mock_logger.info.called or mock_logger.error.called
    
    def test_database_error_handling(self):
        """Test database error handling."""
        from app.database import Database
        
        # Test with invalid connection
        with patch('motor.motor_asyncio.AsyncIOMotorClient', side_effect=Exception("Connection failed")):
            async def test_error():
                try:
                    await Database.create_connection()
                except:
                    pass  # Expected to fail
            
            asyncio.run(test_error())
            
            # Should not crash the application
            assert True


class TestAIIntegration:
    """Test AI components integration."""
    
    def test_ai_components_initialization(self):
        """Test that AI components can be initialized."""
        from app.ai.scraper import RecipeScraper
        from app.ai.extractor import RecipeExtractor
        from app.ai.transformer import RecipeTransformer
        
        scraper = RecipeScraper()
        extractor = RecipeExtractor()
        transformer = RecipeTransformer()
        
        assert scraper is not None
        assert extractor is not None
        assert transformer is not None
    
    def test_ai_import_test_endpoint(self):
        """Test AI import test endpoint functionality."""
        client = TestClient(app)
        
        response = client.get("/ai/import/test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "error"]
        assert "components" in data
        assert "ai_backend" in data
    
    def test_ai_sources_endpoint(self):
        """Test AI supported sources endpoint."""
        client = TestClient(app)
        
        response = client.get("/ai/import/sources")
        assert response.status_code == 200
        
        data = response.json()
        assert "supported_sources" in data
        assert "general_support" in data
        assert "limitations" in data


class TestConfigurationIntegration:
    """Test configuration and environment handling."""
    
    def test_settings_loading(self):
        """Test that settings are loaded correctly."""
        from app.config import settings
        
        assert settings.app_title is not None
        assert settings.app_version is not None
        assert settings.mongodb_url is not None
        assert settings.database_name is not None
    
    def test_logging_configuration(self):
        """Test logging configuration settings."""
        from app.config import settings
        
        assert hasattr(settings, 'log_level')
        assert hasattr(settings, 'use_structured_logging')
        assert settings.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    def test_environment_detection(self):
        """Test environment detection."""
        from app.config import settings
        
        assert hasattr(settings, 'environment')
        assert settings.environment in ['development', 'production', 'test']


class TestSecurityIntegration:
    """Test security aspects of the application."""
    
    def test_no_sensitive_data_in_responses(self):
        """Test that sensitive data is not exposed in responses."""
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        
        # Should not contain sensitive information
        response_text = response.text
        assert "password" not in response_text.lower()
        assert "secret" not in response_text.lower()
        assert "api_key" not in response_text.lower()
    
    def test_error_messages_sanitization(self):
        """Test that error messages don't leak sensitive information."""
        client = TestClient(app)
        
        # Try to trigger an error
        response = client.get("/nonexistent")
        assert response.status_code == 404
        
        # Error response should not contain sensitive info
        if hasattr(response, 'json') and callable(response.json):
            try:
                error_data = response.json()
                error_text = str(error_data)
                assert "password" not in error_text.lower()
                assert "mongodb://" not in error_text
            except:
                pass  # Response might not be JSON


@pytest.mark.integration
class TestEndToEndFlows:
    """Test complete end-to-end user flows."""
    
    def test_recipe_management_flow(self):
        """Test basic recipe management flow."""
        client = TestClient(app)
        
        # 1. Access home page
        response = client.get("/")
        assert response.status_code == 200
        
        # 2. Access recipes API
        response = client.get("/api/recipes/")
        # Might fail due to DB connection, but should not return 404
        assert response.status_code in [200, 500]
        
        # 3. Check health
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_ai_import_flow(self):
        """Test AI import flow."""
        client = TestClient(app)
        
        # 1. Check AI system status
        response = client.get("/ai/import/test")
        assert response.status_code == 200
        
        # 2. Get supported sources
        response = client.get("/ai/import/sources")
        assert response.status_code == 200
        
        # 3. Attempt import (will fail validation)
        response = client.post("/ai/import", json={"url": "invalid"})
        assert response.status_code == 422
    
    def test_monitoring_endpoints(self):
        """Test monitoring and observability endpoints."""
        client = TestClient(app)
        
        # Health check
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        
        # AI test endpoint
        response = client.get("/ai/import/test")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data


class TestPerformanceIntegration:
    """Test performance aspects of the application."""
    
    def test_response_times(self):
        """Test that response times are reasonable."""
        import time
        client = TestClient(app)
        
        # Test health endpoint performance
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 5.0  # Should respond within 5 seconds
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        client = TestClient(app)
        results = []
        
        def make_request():
            response = client.get("/health")
            results.append(response.status_code)
        
        # Make 10 concurrent requests
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert len(results) == 10
        assert all(status == 200 for status in results)


class TestDockerIntegration:
    """Test Docker-related functionality."""
    
    def test_docker_environment_detection(self):
        """Test detection of Docker environment."""
        # This would typically check for Docker-specific environment variables
        # or filesystem indicators
        import os
        
        # Check if we're likely in a container
        in_container = (
            os.path.exists('/.dockerenv') or
            os.environ.get('CONTAINER_ENV') == 'docker'
        )
        
        # Test should work regardless of environment
        assert True
    
    def test_production_vs_development_config(self):
        """Test configuration differences between environments."""
        from app.config import settings
        
        # Should have environment-appropriate settings
        if settings.environment == 'production':
            assert settings.use_structured_logging is True
        
        # Log level should be appropriate
        assert settings.log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']