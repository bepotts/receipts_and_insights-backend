"""
Unit tests for auth endpoints
"""

from unittest.mock import ANY, MagicMock, Mock, patch

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
NEW_USER_FIRST_NAME = "New"
NEW_USER_LAST_NAME = "User"
NEW_USER_EMAIL = "newuser@example.com"

MSG_ALREADY_EXISTS = "already exists"
MSG_EMAIL = "email"


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
    """Fixture for existing user model"""
    from app.models.user import User

    user = User(
        id=1,
        first_name=TEST_USER_FIRST_NAME,
        last_name=TEST_USER_LAST_NAME,
        email=TEST_USER_EMAIL,
    )
    return user


@pytest.mark.testAuthEndpoints
class TestLogin:
    """Tests for POST /auth/login endpoint"""

    @patch("app.api.v1.endpoints.auth.UserSession")
    @patch("app.api.v1.endpoints.auth.secrets")
    @patch("app.api.v1.endpoints.auth.datetime")
    @patch("app.api.v1.endpoints.auth.User")
    def test_login_success(
        self,
        mock_user_class,
        mock_datetime,
        mock_secrets,
        mock_user_session_class,
        test_client,
        mock_db_session,
    ):
        """Test successful login (user creation)"""
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

        # Mock checking if user exists (should return None for new user)
        mock_query_email = Mock()
        mock_query_email.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query_email

        # Create a mock user instance that will be returned
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user_instance.first_name = NEW_USER_FIRST_NAME
        mock_user_instance.last_name = NEW_USER_LAST_NAME
        mock_user_instance.email = NEW_USER_EMAIL.lower()
        mock_user_class.return_value = mock_user_instance

        # Create a mock user session instance
        mock_session_instance = MagicMock()
        mock_user_session_class.return_value = mock_session_instance

        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        user_data = {
            "first_name": NEW_USER_FIRST_NAME,
            "last_name": NEW_USER_LAST_NAME,
            "email": NEW_USER_EMAIL,
            "password": TEST_PASSWORD,
        }
        response = test_client.post(AUTH_LOGIN_ENDPOINT, json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == NEW_USER_FIRST_NAME
        assert data["last_name"] == NEW_USER_LAST_NAME
        assert data["email"] == NEW_USER_EMAIL.lower()
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

        # Verify User was created
        mock_user_class.assert_called_once_with(
            first_name=NEW_USER_FIRST_NAME,
            last_name=NEW_USER_LAST_NAME,
            email=NEW_USER_EMAIL.lower(),
            password=ANY,
        )
        # Verify UserSession was created
        mock_user_session_class.assert_called_once()
        call_kwargs = mock_user_session_class.call_args[1]
        assert call_kwargs["user_id"] == 1
        assert call_kwargs["session_token"] == MOCK_SESSION_TOKEN
        assert call_kwargs["is_active"] is True

        # Verify both User and UserSession were added
        assert mock_db_session.add.call_count == 2
        mock_db_session.add.assert_any_call(mock_user_instance)
        mock_db_session.add.assert_any_call(mock_session_instance)

        # Verify commit was called twice (once for user, once for session)
        assert mock_db_session.commit.call_count == 2
        mock_db_session.refresh.assert_called_once_with(mock_user_instance)

    def test_login_duplicate_email(self, test_client, mock_db_session, existing_user):
        """Test login with an email that already exists"""
        # Mock that user with email already exists
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = existing_user
        mock_db_session.query.return_value = mock_query

        user_data = {
            "first_name": TEST_USER_FIRST_NAME,
            "last_name": TEST_USER_LAST_NAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_PASSWORD,
        }

        response = test_client.post(AUTH_LOGIN_ENDPOINT, json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert MSG_ALREADY_EXISTS in data["detail"].lower()
        assert MSG_EMAIL in data["detail"].lower()


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
