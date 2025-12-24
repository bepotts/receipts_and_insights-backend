"""
Pytest configuration and fixtures
"""
import pytest


@pytest.fixture
def sample_fixture():
    """Sample pytest fixture"""
    return {"test": "data"}

