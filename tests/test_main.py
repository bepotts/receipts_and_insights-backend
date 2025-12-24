"""
Tests for main application
"""
import pytest
from app.main import main


def test_main_function(capsys):
    """Test main function output"""
    main()
    captured = capsys.readouterr()
    assert "Receipts and Insights Backend" in captured.out

