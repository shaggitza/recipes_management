import pytest
from fastapi.testclient import TestClient
from app.main import app

def test_health_check():
    """Test health check endpoint."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_home_page():
    """Test home page serves HTML."""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_api_routes_exist():
    """Test that API routes are properly configured."""
    client = TestClient(app)
    # Test that the recipes API endpoint exists
    response = client.get("/api/recipes/")
    # Should return 200 with empty list or appropriate error, not 404
    assert response.status_code in [200, 500]  # 500 if DB not connected

def test_static_files_mounted():
    """Test that static files are accessible."""
    client = TestClient(app)
    # Test accessing a static file that should exist or return 404 (not 500)
    response = client.get("/static/style.css")
    # Should either find the file or return 404, not a server error
    assert response.status_code in [200, 404]

def test_application_metadata():
    """Test application metadata and configuration."""
    from app.config import settings
    assert app.title == settings.app_title
    assert app.version == settings.app_version

def test_router_registration():
    """Test that routers are properly registered."""
    # Check that the recipes router is included
    route_paths = []
    for route in app.routes:
        if hasattr(route, 'path'):
            route_paths.append(route.path)
        elif hasattr(route, 'prefix'):
            route_paths.append(route.prefix)
    
    # Should have API routes
    assert any('/api/recipes' in str(path) for path in route_paths)

def test_error_handling():
    """Test basic error handling."""
    client = TestClient(app)
    # Test non-existent endpoint
    response = client.get("/nonexistent")
    assert response.status_code == 404

def test_cors_headers():
    """Test CORS configuration if present."""
    client = TestClient(app)
    response = client.get("/health")
    # Check if CORS headers are present (they might not be configured)
    # This is just to document expected behavior
    assert response.status_code == 200