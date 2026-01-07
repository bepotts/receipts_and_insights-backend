"""
Unit tests for user endpoints
"""

from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.user import User

# String constants
USERS_ENDPOINT = "/api/v1/users/"
USERS_ENDPOINT_WITH_ID_1 = "/api/v1/users/1"
USERS_ENDPOINT_WITH_ID_999 = "/api/v1/users/999"

TEST_USER_FIRST_NAME = "Test"
TEST_USER_LAST_NAME = "User"
TEST_USER_EMAIL = "test@example.com"
TEST_PASSWORD = "testpassword123"
USER_ONE_FIRST_NAME = "User"
USER_ONE_LAST_NAME = "One"
USER_ONE_EMAIL = "user1@example.com"
USER_TWO_FIRST_NAME = "User"
USER_TWO_LAST_NAME = "Two"
USER_TWO_EMAIL = "user2@example.com"
NEW_USER_FIRST_NAME = "New"
NEW_USER_LAST_NAME = "User"
NEW_USER_EMAIL = "newuser@example.com"
UPDATED_FIRST_NAME = "Updated"
UPDATED_LAST_NAME = "Name"

MSG_NOT_FOUND = "not found"
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
def sample_user():
    """Fixture for sample user model"""
    user = User(
        id=1,
        first_name=TEST_USER_FIRST_NAME,
        last_name=TEST_USER_LAST_NAME,
        email=TEST_USER_EMAIL,
    )
    return user


@pytest.fixture
def sample_users_list():
    """Fixture for sample list of users"""
    return [
        User(
            id=1,
            first_name=USER_ONE_FIRST_NAME,
            last_name=USER_ONE_LAST_NAME,
            email=USER_ONE_EMAIL,
        ),
        User(
            id=2,
            first_name=USER_TWO_FIRST_NAME,
            last_name=USER_TWO_LAST_NAME,
            email=USER_TWO_EMAIL,
        ),
    ]


@pytest.mark.testUserEndpoints
class TestGetUsers:
    """Tests for GET /users/ endpoint"""

    def test_get_users_success(self, test_client, mock_db_session, sample_users_list):
        """Test successful retrieval of all users"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = (
            sample_users_list
        )
        mock_db_session.query.return_value = mock_query

        response = test_client.get(USERS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["first_name"] == USER_ONE_FIRST_NAME
        assert data[0]["last_name"] == USER_ONE_LAST_NAME
        assert data[0]["email"] == USER_ONE_EMAIL
        assert data[1]["id"] == 2
        assert data[1]["first_name"] == USER_TWO_FIRST_NAME
        assert data[1]["last_name"] == USER_TWO_LAST_NAME
        assert data[1]["email"] == USER_TWO_EMAIL

    def test_get_users_with_pagination(
        self, test_client, mock_db_session, sample_users_list
    ):
        """Test getting users with pagination parameters"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = (
            sample_users_list
        )
        mock_db_session.query.return_value = mock_query

        response = test_client.get(f"{USERS_ENDPOINT}?skip=0&limit=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        mock_query.offset.assert_called_once_with(0)
        mock_query.offset.return_value.limit.assert_called_once_with(10)

    def test_get_users_empty_list(self, test_client, mock_db_session):
        """Test getting users when no users exist"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        response = test_client.get(USERS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []


@pytest.mark.testUserEndpoints
class TestGetUser:
    """Tests for GET /users/{user_id} endpoint"""

    def test_get_user_success(self, test_client, mock_db_session, sample_user):
        """Test successful retrieval of a user by ID"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_user
        mock_db_session.query.return_value = mock_query

        response = test_client.get(USERS_ENDPOINT_WITH_ID_1)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == 1
        assert data["first_name"] == TEST_USER_FIRST_NAME
        assert data["last_name"] == TEST_USER_LAST_NAME
        assert data["email"] == TEST_USER_EMAIL

    def test_get_user_not_found(self, test_client, mock_db_session):
        """Test getting a user that doesn't exist"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        response = test_client.get(USERS_ENDPOINT_WITH_ID_999)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert MSG_NOT_FOUND in data["detail"].lower()
        assert "999" in data["detail"]


@pytest.mark.testUserEndpoints
class TestCreateUser:
    """Tests for POST /users/ endpoint"""

    @patch("app.api.v1.endpoints.users.UserSession")
    @patch("app.api.v1.endpoints.users.secrets")
    @patch("app.api.v1.endpoints.users.datetime")
    @patch("app.api.v1.endpoints.users.User")
    def test_create_user_success(
        self,
        mock_user_class,
        mock_datetime,
        mock_secrets,
        mock_user_session_class,
        test_client,
        mock_db_session,
    ):
        """Test successful creation of a new user"""
        # Mock session token
        MOCK_SESSION_TOKEN = "mock_session_token_12345"
        mock_secrets.token_urlsafe.return_value = MOCK_SESSION_TOKEN

        # Mock datetime.utcnow() for expires_at calculation
        from datetime import datetime as dt

        mock_now = dt(2024, 1, 1, 12, 0, 0)
        mock_datetime.utcnow.return_value = mock_now
        # Keep timedelta working normally by not mocking it
        from datetime import timedelta

        mock_datetime.timedelta = timedelta

        # Mock checking if user exists (should return None for new user)
        mock_query_email = Mock()
        mock_query_email.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query_email

        # Create a mock user instance that will be returned
        mock_user_instance = MagicMock()
        mock_user_instance.id = 1
        mock_user_instance.first_name = NEW_USER_FIRST_NAME
        mock_user_instance.last_name = NEW_USER_LAST_NAME
        mock_user_instance.email = NEW_USER_EMAIL
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
        response = test_client.post(USERS_ENDPOINT, json=user_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == NEW_USER_FIRST_NAME
        assert data["last_name"] == NEW_USER_LAST_NAME
        assert data["email"] == NEW_USER_EMAIL
        assert data["id"] == 1
        assert data["session_token"] == MOCK_SESSION_TOKEN

        # Verify User was created
        mock_user_class.assert_called_once_with(
            first_name=NEW_USER_FIRST_NAME,
            last_name=NEW_USER_LAST_NAME,
            email=NEW_USER_EMAIL,
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

    def test_create_user_duplicate_email(
        self, test_client, mock_db_session, sample_user
    ):
        """Test creating a user with an email that already exists"""
        DUPLICATE_USER_FIRST_NAME = "Duplicate"
        DUPLICATE_USER_LAST_NAME = "User"
        # Mock that user with email already exists
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_user
        mock_db_session.query.return_value = mock_query

        user_data = {
            "first_name": DUPLICATE_USER_FIRST_NAME,
            "last_name": DUPLICATE_USER_LAST_NAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_PASSWORD,
        }

        response = test_client.post(USERS_ENDPOINT, json=user_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert MSG_ALREADY_EXISTS in data["detail"].lower()
        assert MSG_EMAIL in data["detail"].lower()


@pytest.mark.testUserEndpoints
class TestUpdateUser:
    """Tests for PUT /users/{user_id} endpoint"""

    def test_update_user_success(self, test_client, mock_db_session, sample_user):
        """Test successful update of a user"""
        UPDATED_EMAIL = "updated@example.com"
        # Mock finding the user by ID
        mock_query_user = Mock()
        mock_query_user.filter.return_value.first.return_value = sample_user

        # Mock checking email uniqueness (should return None for unique email)
        mock_query_email = Mock()
        mock_query_email.filter.return_value.first.return_value = None

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: finding user by ID
                return mock_query_user
            else:
                # Subsequent calls: checking email uniqueness
                return mock_query_email

        mock_db_session.query.side_effect = query_side_effect
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        user_update_data = {
            "first_name": UPDATED_FIRST_NAME,
            "last_name": UPDATED_LAST_NAME,
            "email": UPDATED_EMAIL,
        }

        response = test_client.put(USERS_ENDPOINT_WITH_ID_1, json=user_update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == UPDATED_FIRST_NAME
        assert data["last_name"] == UPDATED_LAST_NAME
        assert data["email"] == UPDATED_EMAIL
        mock_db_session.commit.assert_called_once()

    def test_update_user_partial(self, test_client, mock_db_session, sample_user):
        """Test updating only some fields of a user"""
        UPDATED_FIRST_NAME_ONLY = "Updated"
        # Mock finding the user by ID
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_user
        mock_db_session.query.return_value = mock_query

        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        # Update only first_name
        user_update_data = {"first_name": UPDATED_FIRST_NAME_ONLY}

        response = test_client.put(USERS_ENDPOINT_WITH_ID_1, json=user_update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == UPDATED_FIRST_NAME_ONLY
        mock_db_session.commit.assert_called_once()

    def test_update_user_not_found(self, test_client, mock_db_session):
        """Test updating a user that doesn't exist"""
        # Mock that user is not found
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        user_update_data = {
            "first_name": UPDATED_FIRST_NAME,
            "last_name": UPDATED_LAST_NAME,
        }

        response = test_client.put(USERS_ENDPOINT_WITH_ID_999, json=user_update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert MSG_NOT_FOUND in data["detail"].lower()

    def test_update_user_duplicate_email(
        self, test_client, mock_db_session, sample_user
    ):
        """Test updating a user with an email that's already taken by another user"""
        EXISTING_USER_FIRST_NAME = "Existing"
        EXISTING_USER_LAST_NAME = "User"
        EXISTING_EMAIL = "existing@example.com"
        existing_user = User(
            id=2,
            first_name=EXISTING_USER_FIRST_NAME,
            last_name=EXISTING_USER_LAST_NAME,
            email=EXISTING_EMAIL,
        )

        # First query returns the user to update, second query returns another user with that email
        mock_query_user = Mock()
        mock_query_user.filter.return_value.first.return_value = sample_user

        mock_query_email = Mock()
        mock_query_email.filter.return_value.first.return_value = existing_user

        call_count = [0]

        def query_side_effect(model):
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_query_user
            else:
                return mock_query_email

        mock_db_session.query.side_effect = query_side_effect

        user_update_data = {"email": EXISTING_EMAIL}

        response = test_client.put(USERS_ENDPOINT_WITH_ID_1, json=user_update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert MSG_ALREADY_EXISTS in data["detail"].lower()
        assert MSG_EMAIL in data["detail"].lower()


@pytest.mark.testUserEndpoints
class TestDeleteUser:
    """Tests for DELETE /users/{user_id} endpoint"""

    def test_delete_user_success(self, test_client, mock_db_session, sample_user):
        """Test successful deletion of a user"""
        # Mock finding the user
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = sample_user
        mock_db_session.query.return_value = mock_query

        mock_db_session.delete = Mock()
        mock_db_session.commit = Mock()

        response = test_client.delete(USERS_ENDPOINT_WITH_ID_1)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        mock_db_session.delete.assert_called_once_with(sample_user)
        mock_db_session.commit.assert_called_once()

    def test_delete_user_not_found(self, test_client, mock_db_session):
        """Test deleting a user that doesn't exist"""
        # Mock that user is not found
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        response = test_client.delete(USERS_ENDPOINT_WITH_ID_999)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert MSG_NOT_FOUND in data["detail"].lower()
