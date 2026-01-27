"""
Unit tests for photo endpoints
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.database import get_db
from app.main import app
from app.models.photo import Photo
from app.models.user import User

# String constants
PHOTOS_ENDPOINT = "/api/v1/photos/"
PHOTOS_ENDPOINT_WITH_ID_1 = "/api/v1/photos/1"
PHOTOS_ENDPOINT_WITH_ID_999 = "/api/v1/photos/999"

TEST_USER_ID = 1
TEST_PHOTO_FILENAME = "test_photo.jpg"
TEST_PHOTO_TITLE = "Test Photo"
TEST_PHOTO_DESCRIPTION = "A test photo description"
TEST_PHOTO_MIME_TYPE = "image/jpeg"
TEST_PHOTO_FILE_SIZE = 1024
TEST_PHOTO_FILE_PATH = "uploads/test_uuid.jpg"

MSG_NOT_FOUND = "not found"
MSG_MUST_BE_IMAGE = "must be an image"


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
        id=TEST_USER_ID,
        first_name="Test",
        last_name="User",
        email="test@example.com",
    )
    return user


@pytest.fixture
def sample_photo():
    """Fixture for sample photo model"""
    photo = Photo(
        id=1,
        user_id=TEST_USER_ID,
        filename=TEST_PHOTO_FILENAME,
        file_path=TEST_PHOTO_FILE_PATH,
        file_size=TEST_PHOTO_FILE_SIZE,
        mime_type=TEST_PHOTO_MIME_TYPE,
        title=TEST_PHOTO_TITLE,
        description=TEST_PHOTO_DESCRIPTION,
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        updated_at=None,
    )
    return photo


@pytest.fixture
def sample_photos_list():
    """Fixture for sample list of photos"""
    return [
        Photo(
            id=1,
            user_id=TEST_USER_ID,
            filename="photo1.jpg",
            file_path="uploads/photo1.jpg",
            file_size=1024,
            mime_type="image/jpeg",
            title="Photo 1",
            description=None,
            created_at=datetime(2024, 1, 1, 12, 0, 0),
            updated_at=None,
        ),
        Photo(
            id=2,
            user_id=TEST_USER_ID,
            filename="photo2.jpg",
            file_path="uploads/photo2.jpg",
            file_size=2048,
            mime_type="image/png",
            title="Photo 2",
            description="Second photo",
            created_at=datetime(2024, 1, 2, 12, 0, 0),
            updated_at=None,
        ),
    ]


@pytest.mark.testPhotoEndpoints
class TestUploadPhoto:
    """Tests for POST /photos/ endpoint"""

    @patch("app.api.v1.endpoints.photos.Path")
    @patch("app.api.v1.endpoints.photos.uuid")
    @patch("app.api.v1.endpoints.photos.open")
    @patch("app.api.v1.endpoints.photos.Photo")
    def test_upload_photo_success(
        self,
        mock_photo_class,
        mock_open,
        mock_uuid,
        mock_path,
        test_client,
        mock_db_session,
        sample_user,
    ):
        """Test successful photo upload"""
        # Mock UUID generation
        MOCK_UUID = "test-uuid-12345"
        mock_uuid.uuid4.return_value = MOCK_UUID

        # Mock Path operations
        mock_path_instance = Mock()
        mock_path_instance.suffix = ".jpg"
        mock_path_instance.__truediv__ = Mock(return_value=Mock())
        mock_path.return_value = mock_path_instance

        # Mock file operations
        mock_file_content = b"fake image content"
        mock_file = MagicMock()
        mock_file.filename = TEST_PHOTO_FILENAME
        mock_file.content_type = TEST_PHOTO_MIME_TYPE
        mock_file.read = Mock(return_value=mock_file_content)

        # Mock user lookup
        mock_query_user = Mock()
        mock_query_user.filter.return_value.first.return_value = sample_user
        mock_db_session.query.return_value = mock_query_user

        # Mock photo instance
        mock_photo_instance = MagicMock()
        mock_photo_instance.id = 1
        mock_photo_instance.user_id = TEST_USER_ID
        mock_photo_instance.filename = TEST_PHOTO_FILENAME
        mock_photo_instance.file_path = TEST_PHOTO_FILE_PATH
        mock_photo_instance.file_size = len(mock_file_content)
        mock_photo_instance.mime_type = TEST_PHOTO_MIME_TYPE
        mock_photo_instance.title = TEST_PHOTO_TITLE
        mock_photo_instance.description = TEST_PHOTO_DESCRIPTION
        mock_photo_instance.created_at = datetime(2024, 1, 1, 12, 0, 0)
        mock_photo_instance.updated_at = None
        mock_photo_class.return_value = mock_photo_instance

        mock_db_session.add = Mock()
        mock_db_session.commit = Mock()
        mock_db_session.refresh = Mock()

        # Mock file path operations
        mock_file_path = Mock()
        mock_file_path.exists.return_value = False
        mock_open.return_value.__enter__.return_value = mock_file_path

        form_data = {
            "user_id": TEST_USER_ID,
            "title": TEST_PHOTO_TITLE,
            "description": TEST_PHOTO_DESCRIPTION,
        }
        files = {"file": (TEST_PHOTO_FILENAME, mock_file_content, TEST_PHOTO_MIME_TYPE)}

        response = test_client.post(PHOTOS_ENDPOINT, data=form_data, files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["user_id"] == TEST_USER_ID
        assert data["filename"] == TEST_PHOTO_FILENAME
        assert data["title"] == TEST_PHOTO_TITLE
        assert data["description"] == TEST_PHOTO_DESCRIPTION

        # Verify Photo was created
        mock_photo_class.assert_called_once()
        call_kwargs = mock_photo_class.call_args[1]
        assert call_kwargs["user_id"] == TEST_USER_ID
        assert call_kwargs["filename"] == TEST_PHOTO_FILENAME
        assert call_kwargs["mime_type"] == TEST_PHOTO_MIME_TYPE

        # Verify database operations
        mock_db_session.add.assert_called_once_with(mock_photo_instance)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(mock_photo_instance)

    def test_upload_photo_invalid_file_type(self, test_client, mock_db_session, sample_user):
        """Test uploading a non-image file"""
        # Mock user lookup
        mock_query_user = Mock()
        mock_query_user.filter.return_value.first.return_value = sample_user
        mock_db_session.query.return_value = mock_query_user

        form_data = {"user_id": TEST_USER_ID}
        files = {"file": ("document.pdf", b"fake pdf content", "application/pdf")}

        response = test_client.post(PHOTOS_ENDPOINT, data=form_data, files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert MSG_MUST_BE_IMAGE in data["detail"].lower()

    def test_upload_photo_user_not_found(self, test_client, mock_db_session):
        """Test uploading a photo for a non-existent user"""
        # Mock user lookup returning None
        mock_query_user = Mock()
        mock_query_user.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query_user

        form_data = {"user_id": 999}
        files = {"file": (TEST_PHOTO_FILENAME, b"fake image content", TEST_PHOTO_MIME_TYPE)}

        response = test_client.post(PHOTOS_ENDPOINT, data=form_data, files=files)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert MSG_NOT_FOUND in data["detail"].lower()
        assert "999" in data["detail"]

    @patch("app.api.v1.endpoints.photos.Path")
    @patch("app.api.v1.endpoints.photos.uuid")
    @patch("app.api.v1.endpoints.photos.open")
    def test_upload_photo_file_save_error(
        self,
        mock_open,
        mock_uuid,
        mock_path,
        test_client,
        mock_db_session,
        sample_user,
    ):
        """Test handling file save error"""
        # Mock UUID generation
        MOCK_UUID = "test-uuid-12345"
        mock_uuid.uuid4.return_value = MOCK_UUID

        # Mock Path operations
        mock_path_instance = Mock()
        mock_path_instance.suffix = ".jpg"
        mock_file_path = Mock()
        mock_file_path.exists.return_value = False
        mock_path_instance.__truediv__ = Mock(return_value=mock_file_path)
        mock_path.return_value = mock_path_instance

        # Mock file operations to raise an error
        mock_file = MagicMock()
        mock_file.filename = TEST_PHOTO_FILENAME
        mock_file.content_type = TEST_PHOTO_MIME_TYPE
        mock_file.read = Mock(return_value=b"fake image content")

        # Mock user lookup
        mock_query_user = Mock()
        mock_query_user.filter.return_value.first.return_value = sample_user
        mock_db_session.query.return_value = mock_query_user

        # Mock open to raise an error
        mock_open.side_effect = IOError("Disk full")

        form_data = {"user_id": TEST_USER_ID}
        files = {"file": (TEST_PHOTO_FILENAME, b"fake image content", TEST_PHOTO_MIME_TYPE)}

        response = test_client.post(PHOTOS_ENDPOINT, data=form_data, files=files)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data["detail"].lower()


@pytest.mark.testPhotoEndpoints
class TestGetPhotos:
    """Tests for GET /photos/ endpoint"""

    def test_get_photos_success(self, test_client, mock_db_session, sample_photos_list):
        """Test successful retrieval of all photos"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = (
            sample_photos_list
        )
        mock_db_session.query.return_value = mock_query

        response = test_client.get(PHOTOS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == 1
        assert data[0]["filename"] == "photo1.jpg"
        assert data[0]["title"] == "Photo 1"
        assert data[1]["id"] == 2
        assert data[1]["filename"] == "photo2.jpg"
        assert data[1]["title"] == "Photo 2"

    def test_get_photos_with_user_filter(
        self, test_client, mock_db_session, sample_photos_list
    ):
        """Test getting photos filtered by user_id"""
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = (
            sample_photos_list
        )
        mock_db_session.query.return_value = mock_query

        response = test_client.get(f"{PHOTOS_ENDPOINT}?user_id={TEST_USER_ID}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        # Verify filter was called (can't directly compare SQLAlchemy filter expressions)
        mock_query.filter.assert_called_once()

    def test_get_photos_with_pagination(
        self, test_client, mock_db_session, sample_photos_list
    ):
        """Test getting photos with pagination parameters"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = (
            sample_photos_list
        )
        mock_db_session.query.return_value = mock_query

        response = test_client.get(f"{PHOTOS_ENDPOINT}?skip=0&limit=10")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        mock_query.offset.assert_called_once_with(0)
        mock_query.offset.return_value.limit.assert_called_once_with(10)

    def test_get_photos_empty_list(self, test_client, mock_db_session):
        """Test getting photos when no photos exist"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        response = test_client.get(PHOTOS_ENDPOINT)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data == []


@pytest.mark.testPhotoEndpoints
class TestGetPhoto:
    """Tests for GET /photos/{photo_id} endpoint"""

    def test_get_photo_success(self, test_client, mock_db_session, sample_photo):
        """Test successful retrieval of a photo by ID"""
        # Mock get_photo_by_id utility function
        with patch("app.api.v1.endpoints.photos.get_photo_by_id") as mock_get_photo:
            mock_get_photo.return_value = sample_photo

            response = test_client.get(PHOTOS_ENDPOINT_WITH_ID_1)

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == 1
            assert data["user_id"] == TEST_USER_ID
            assert data["filename"] == TEST_PHOTO_FILENAME
            assert data["title"] == TEST_PHOTO_TITLE
            assert data["description"] == TEST_PHOTO_DESCRIPTION
            mock_get_photo.assert_called_once_with(1, mock_db_session)

    def test_get_photo_not_found(self, test_client, mock_db_session):
        """Test getting a photo that doesn't exist"""
        # Mock get_photo_by_id to raise HTTPException
        from fastapi import HTTPException

        with patch("app.api.v1.endpoints.photos.get_photo_by_id") as mock_get_photo:
            mock_get_photo.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Photo with id 999 not found",
            )

            response = test_client.get(PHOTOS_ENDPOINT_WITH_ID_999)

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert MSG_NOT_FOUND in data["detail"].lower()
            assert "999" in data["detail"]


@pytest.mark.testPhotoEndpoints
class TestDeletePhoto:
    """Tests for DELETE /photos/{photo_id} endpoint"""

    @patch("app.api.v1.endpoints.photos.Path")
    def test_delete_photo_success(
        self, mock_path, test_client, mock_db_session, sample_photo
    ):
        """Test successful deletion of a photo"""
        # Mock get_photo_by_id utility function
        with patch("app.api.v1.endpoints.photos.get_photo_by_id") as mock_get_photo:
            mock_get_photo.return_value = sample_photo

            # Mock file path operations
            mock_file_path = Mock()
            mock_file_path.exists.return_value = True
            mock_file_path.unlink = Mock()
            mock_path.return_value = mock_file_path

            mock_db_session.delete = Mock()
            mock_db_session.commit = Mock()

            response = test_client.delete(PHOTOS_ENDPOINT_WITH_ID_1)

            assert response.status_code == status.HTTP_204_NO_CONTENT
            mock_file_path.unlink.assert_called_once()
            mock_db_session.delete.assert_called_once_with(sample_photo)
            mock_db_session.commit.assert_called_once()

    @patch("app.api.v1.endpoints.photos.Path")
    def test_delete_photo_file_not_exists(
        self, mock_path, test_client, mock_db_session, sample_photo
    ):
        """Test deleting a photo when file doesn't exist on disk"""
        # Mock get_photo_by_id utility function
        with patch("app.api.v1.endpoints.photos.get_photo_by_id") as mock_get_photo:
            mock_get_photo.return_value = sample_photo

            # Mock file path operations - file doesn't exist
            mock_file_path = Mock()
            mock_file_path.exists.return_value = False
            mock_file_path.unlink = Mock()
            mock_path.return_value = mock_file_path

            mock_db_session.delete = Mock()
            mock_db_session.commit = Mock()

            response = test_client.delete(PHOTOS_ENDPOINT_WITH_ID_1)

            assert response.status_code == status.HTTP_204_NO_CONTENT
            # unlink should not be called if file doesn't exist
            mock_file_path.unlink.assert_not_called()
            mock_db_session.delete.assert_called_once_with(sample_photo)
            mock_db_session.commit.assert_called_once()

    def test_delete_photo_not_found(self, test_client, mock_db_session):
        """Test deleting a photo that doesn't exist"""
        # Mock get_photo_by_id to raise HTTPException
        from fastapi import HTTPException

        with patch("app.api.v1.endpoints.photos.get_photo_by_id") as mock_get_photo:
            mock_get_photo.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Photo with id 999 not found",
            )

            response = test_client.delete(PHOTOS_ENDPOINT_WITH_ID_999)

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert MSG_NOT_FOUND in data["detail"].lower()
            assert "999" in data["detail"]
