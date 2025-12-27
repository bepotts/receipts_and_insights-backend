"""
Tests for main application
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app, main


# Pytest fixtures
@pytest.fixture
def test_client():
    """Fixture for FastAPI TestClient"""
    return TestClient(app)


@pytest.fixture
def mock_init_db():
    """Fixture for mocked init_db function"""
    with patch("app.main.init_db") as mock:
        yield mock


@pytest.fixture
def mock_close_db():
    """Fixture for mocked close_db function"""
    with patch("app.main.close_db") as mock:
        yield mock


@pytest.fixture
def mock_uvicorn_run():
    """Fixture for mocked uvicorn.run function"""
    with patch("uvicorn.run") as mock:
        yield mock


@pytest.mark.testFastAPIApp
class TestFastAPIApp:
    """Tests for FastAPI application instance"""

    def test_api_router_included(self):
        """Test that API router is included in the app"""
        # Check if the router is included by looking at routes
        routes = [route.path for route in app.routes]
        # The API router should add routes with /api/v1 prefix
        assert any("/api/v1/users" in route for route in routes)

    def test_app_type(self):
        """Test that app is a FastAPI instance"""
        from fastapi import FastAPI

        assert isinstance(app, FastAPI)


@pytest.mark.testMainFunction
class TestMainFunction:
    """Tests for main() function"""

    def test_main_function_executes(self, mock_uvicorn_run):
        """Test that main function executes without error"""
        # Should not raise an exception
        main()

    def test_main_calls_uvicorn_run(self, mock_uvicorn_run):
        """Test that main() calls uvicorn.run with correct parameters"""
        # Call main function
        main()

        # Verify uvicorn.run was called
        mock_uvicorn_run.assert_called_once()

        # Check the arguments
        call_args = mock_uvicorn_run.call_args
        assert call_args[0][0] == "app.main:app"
        assert call_args[1]["host"] == "0.0.0.0"
        assert call_args[1]["port"] == 8000
        assert call_args[1]["reload"] is True

    @pytest.mark.parametrize(
        "expected_key,expected_value",
        [
            ("host", "0.0.0.0"),
            ("port", 8000),
            ("reload", True),
        ],
    )
    def test_main_uvicorn_parameters(self, mock_uvicorn_run, expected_key, expected_value):
        """Test individual uvicorn.run parameters"""
        main()
        call_args = mock_uvicorn_run.call_args
        assert call_args[1][expected_key] == expected_value


@pytest.mark.testAppEndpoints
class TestAppEndpoints:
    """Tests for app endpoints and routing"""

    def test_root_endpoint_not_configured(self, test_client):
        """Test that root endpoint is not explicitly configured"""
        response = test_client.get("/")
        # FastAPI typically returns 404 for unconfigured routes
        assert response.status_code == 404

    def test_openapi_schema_accessible(self, test_client):
        """Test that OpenAPI schema is accessible"""
        response = test_client.get("/openapi.json")
        assert response.status_code == 200

    @pytest.mark.parametrize(
        "endpoint,expected_status",
        [
            ("/docs", 200),
            ("/redoc", 200),
            ("/openapi.json", 200),
        ],
    )
    def test_documentation_endpoints_accessible(self, test_client, endpoint, expected_status):
        """Test that documentation endpoints are accessible"""
        response = test_client.get(endpoint)
        assert response.status_code == expected_status
