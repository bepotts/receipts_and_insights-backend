"""
Unit tests for auth endpoints
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app

# String constants
AUTH_LOGIN_ENDPOINT = "/api/v1/auth/login"
AUTH_LOGOUT_ENDPOINT = "/api/v1/auth/logout"

TEST_USER_FIRST_NAME = "Test"
TEST_USER_LAST_NAME = "User"
TEST_USER_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"

MSG_INVALID_CREDENTIALS = "invalid email or password"


@pytest.fixture
def mock_db_session():
    """Fixture for mocked database session"""
    session = Mock()
    return session


@pytest.fixture
def override_get_db(mock_db_session):
    """Fixture to override get_db dependency"""

    def _get_db_override():
        try:
            yield mock_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def test_client(override_get_db):
    """Fixture for FastAPI TestClient with dependency override"""
    return TestClient(app)


@pytest.fixture
def existing_user():
    """Fixture for existing user model with hashed password"""
    from app.models.user import User

    user = User(
        id=1,
        first_name=TEST_USER_FIRST_NAME,
        last_name=TEST_USER_LAST_NAME,
        email=TEST_USER_EMAIL,
        password="hashed_password",
    )
    return user


@pytest.mark.testAuthEndpoints
class TestLogin:
    """Tests for POST /auth/login endpoint"""

    @patch("app.api.v1.endpoints.auth.UserSession")
    @patch("app.api.v1.endpoints.auth.secrets")
    @patch("app.api.v1.endpoints.auth.datetime")
    @patch("app.api.v1.endpoints.auth.verify_password")
    def test_login_success(
        self,
        mock_verify_password,
        mock_datetime,
        mock_secrets,
        mock_user_session_class,
        test_client,
        mock_db_session,
        existing_user,
    ):
        """Test successful login with valid credentials"""
        mock_verify_password.return_value = True

        # Mock session token
        MOCK_SESSION_TOKEN = "mock_session_token_12345"
        mock_secrets.token_urlsafe.return_value = MOCK_SESSION_TOKEN

        # Mock datetime.now(timezone.utc) for expires_at calculation
        from datetime import datetime as dt
        from datetime import timedelta, timezone

        mock_now = dt(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.timedelta = timedelta
        mock_datetime.timezone = timezone

        # Mock user lookup - return existing user
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = existing_user
        mock_db_session.query.return_value = mock_query

        # Create a mock user session instance
        mock_session_instance = MagicMock()
        mock_user_session_class.return_value = mock_session_instance

        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()

        credentials = {
            "email": TEST_USER_EMAIL,
            "password": TEST_PASSWORD,
        }
        response = test_client.post(AUTH_LOGIN_ENDPOINT, json=credentials)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == TEST_USER_FIRST_NAME
        assert data["last_name"] == TEST_USER_LAST_NAME
        assert data["email"] == TEST_USER_EMAIL
        assert data["id"] == 1
        assert data["session_token"] == MOCK_SESSION_TOKEN

        # Verify cookie was set in response headers
        assert "set-cookie" in response.headers
        cookie_header = response.headers["set-cookie"]
        assert "session_token=" in cookie_header
        assert MOCK_SESSION_TOKEN in cookie_header
        assert "HttpOnly" in cookie_header
        assert "Secure" in cookie_header
        assert "SameSite=lax" in cookie_header

        # Verify password was verified
        mock_verify_password.assert_called_once_with(
            TEST_PASSWORD, existing_user.password
        )

        # Verify UserSession was created
        mock_user_session_class.assert_called_once()
        call_kwargs = mock_user_session_class.call_args[1]
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["session_token"] == MOCK_SESSION_TOKEN
        assert call_kwargs["is_active"] is True

        # Verify only UserSession was added
        mock_db_session.add.assert_called_once_with(mock_session_instance)
        mock_db_session.commit.assert_called_once()

    def test_login_user_not_found(self, test_client, mock_db_session):
        """Test login when user does not exist"""
        # Mock that no user is found
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        credentials = {
            "email": "nonexistent@example.com",
            "password": TEST_PASSWORD,
        }

        response = test_client.post(AUTH_LOGIN_ENDPOINT, json=credentials)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert MSG_INVALID_CREDENTIALS in data["detail"].lower()

    @patch("app.api.v1.endpoints.auth.verify_password")
    def test_login_wrong_password(
        self, mock_verify_password, test_client, mock_db_session, existing_user
    ):
        """Test login with incorrect password"""
        mock_verify_password.return_value = False

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = existing_user
        mock_db_session.query.return_value = mock_query

        credentials = {
            "email": TEST_USER_EMAIL,
            "password": "wrongpassword",
        }

        response = test_client.post(AUTH_LOGIN_ENDPOINT, json=credentials)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert MSG_INVALID_CREDENTIALS in data["detail"].lower()

        # Verify no session was created
        mock_db_session.add.assert_not_called()


@pytest.mark.testAuthEndpoints
class TestLogout:
    """Tests for POST /auth/logout endpoint"""

    def test_logout_success(self, test_client, mock_db_session):
        """Test successful logout with valid session token"""
        MOCK_SESSION_TOKEN = "mock_session_token_12345"

        # Mock existing session in database
        mock_session = MagicMock()
        mock_session.session_token = MOCK_SESSION_TOKEN

        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_session
        mock_db_session.query.return_value = mock_query

        mock_db_session.delete = Mock()
        mock_db_session.commit = Mock()

        # Set cookie on client instance
        test_client.cookies["session_token"] = MOCK_SESSION_TOKEN
        response = test_client.post(AUTH_LOGOUT_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Logged out successfully"

        # Verify cookie was cleared (empty value)
        assert "set-cookie" in response.headers
        cookie_header = response.headers["set-cookie"]
        assert 'session_token=""' in cookie_header
        assert "Max-Age=0" in cookie_header
        assert "HttpOnly" in cookie_header
        assert "Secure" in cookie_header
        assert "SameSite=lax" in cookie_header

        # Verify session was deleted from database
        mock_db_session.delete.assert_called_once_with(mock_session)
        mock_db_session.commit.assert_called_once()

    def test_logout_session_not_found(self, test_client, mock_db_session):
        """Test logout when session token doesn't exist in database"""
        MOCK_SESSION_TOKEN = "non_existent_token"

        # Mock that session doesn't exist in database
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        mock_db_session.delete = Mock()
        mock_db_session.commit = Mock()

        # Set cookie on client instance
        test_client.cookies["session_token"] = MOCK_SESSION_TOKEN
        response = test_client.post(AUTH_LOGOUT_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Logged out successfully"

        # Verify cookie was still cleared even though session doesn't exist
        assert "set-cookie" in response.headers
        cookie_header = response.headers["set-cookie"]
        assert 'session_token=""' in cookie_header
        assert "Max-Age=0" in cookie_header

        # Verify no delete was attempted (session not found)
        mock_db_session.delete.assert_not_called()

    def test_logout_no_cookie(self, test_client, mock_db_session):
        """Test logout when no cookie is provided"""
        # Mock database query (shouldn't be called, but set up anyway)
        mock_query = Mock()
        mock_db_session.query.return_value = mock_query

        mock_db_session.delete = Mock()
        mock_db_session.commit = Mock()

        response = test_client.post(AUTH_LOGOUT_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Logged out successfully"

        # Verify cookie was still cleared
        assert "set-cookie" in response.headers
        cookie_header = response.headers["set-cookie"]
        assert 'session_token=""' in cookie_header
        assert "Max-Age=0" in cookie_header

        # Verify no database operations were attempted
        mock_db_session.query.assert_not_called()
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()
