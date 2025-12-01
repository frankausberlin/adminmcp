import json
import pytest
import math
from unittest.mock import patch, mock_open
from datetime import datetime

# Import the functions from the server module
from adminmcp.server.acp_server import (
    add, subtract, multiply, divide,
    get_constant, is_even, current_datetime, wikipedia_article
)


class TestMathematicalOperations:
    """Test mathematical operation functions."""

    def test_add_positive_integers(self):
        """Test addition with positive integers."""
        assert add(5, 3) == 8
        assert add(0, 0) == 0
        assert add(100, 200) == 300

    def test_add_negative_integers(self):
        """Test addition with negative integers."""
        assert add(-5, 3) == -2
        assert add(-5, -3) == -8

    def test_subtract_positive_integers(self):
        """Test subtraction with positive integers."""
        assert subtract(10, 3) == 7
        assert subtract(5, 5) == 0
        assert subtract(3, 10) == -7

    def test_subtract_negative_integers(self):
        """Test subtraction with negative integers."""
        assert subtract(-5, 3) == -8
        assert subtract(-5, -3) == -2

    def test_multiply_positive_integers(self):
        """Test multiplication with positive integers."""
        assert multiply(4, 7) == 28
        assert multiply(0, 5) == 0
        assert multiply(1, 1) == 1

    def test_multiply_negative_integers(self):
        """Test multiplication with negative integers."""
        assert multiply(-4, 7) == -28
        assert multiply(-4, -7) == 28

    def test_divide_positive_integers(self):
        """Test division with positive integers."""
        assert divide(10, 2) == 5.0
        assert divide(7, 2) == 3.5

    def test_divide_by_zero(self):
        """Test division by zero returns None."""
        assert divide(10, 0) is None
        assert divide(0, 0) is None

    def test_divide_negative_integers(self):
        """Test division with negative integers."""
        assert divide(-10, 2) == -5.0
        assert divide(10, -2) == -5.0
        assert divide(-10, -2) == 5.0


class TestMathematicalConstants:
    """Test mathematical constants resource."""

    def test_get_constant_pi(self):
        """Test getting pi constant."""
        result = get_constant("pi")
        assert result == math.pi

    def test_get_constant_e(self):
        """Test getting e constant."""
        result = get_constant("e")
        assert result == math.e

    def test_get_constant_tau(self):
        """Test getting tau constant."""
        result = get_constant("tau")
        assert result == math.tau

    def test_get_constant_case_insensitive(self):
        """Test getting constants is case insensitive."""
        assert get_constant("PI") == math.pi
        assert get_constant("E") == math.e
        assert get_constant("Tau") == math.tau

    def test_get_constant_invalid(self):
        """Test getting invalid constant returns None."""
        assert get_constant("invalid") is None
        assert get_constant("") is None
        assert get_constant("xyz") is None


class TestNumberUtilities:
    """Test number utility functions."""

    def test_is_even_positive(self):
        """Test is_even with positive even numbers."""
        assert is_even(0) is True
        assert is_even(2) is True
        assert is_even(100) is True

    def test_is_even_positive_odd(self):
        """Test is_even with positive odd numbers."""
        assert is_even(1) is False
        assert is_even(3) is False
        assert is_even(99) is False

    def test_is_even_negative(self):
        """Test is_even with negative numbers."""
        assert is_even(-2) is True
        assert is_even(-1) is False
        assert is_even(-100) is True


class TestDateTimeResource:
    """Test datetime resource function."""

    @patch('adminmcp.server.acp_server._get_current_datetime')
    def test_current_datetime_structure(self, mock_get_datetime):
        """Test current_datetime returns correct structure."""
        # Mock datetime object with timezone
        from datetime import timezone
        mock_dt = datetime(2023, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
        mock_get_datetime.return_value = mock_dt

        result = current_datetime()

        assert isinstance(result, dict)
        assert 'datetime' in result
        assert 'timezone' in result
        assert 'unix_timestamp' in result

        # Check datetime format (should be ISO format)
        assert '2023-12-01T12:00:00' in result['datetime']
        assert isinstance(result['unix_timestamp'], float)


class TestWikipediaResource:
    """Test Wikipedia article resource function."""

    @patch('adminmcp.server.acp_server.request.urlopen')
    def test_wikipedia_article_success(self, mock_urlopen):
        """Test successful Wikipedia article fetch."""
        mock_response_data = {
            "title": "Python (programming language)",
            "extract": "Python is a programming language.",
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)"
        }

        # Mock the response
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = json.dumps(mock_response_data).encode('utf-8')
        mock_response.headers.get_content_charset.return_value = 'utf-8'

        result = wikipedia_article("Python (programming language)")

        assert result == mock_response_data
        mock_urlopen.assert_called_once()

    @patch('adminmcp.server.acp_server.request.urlopen')
    def test_wikipedia_article_not_found(self, mock_urlopen):
        """Test Wikipedia article not found."""
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(None, 404, "Not Found", None, None)

        result = wikipedia_article("NonExistentArticle12345")

        assert result == {"error": "Article not found", "title": "NonExistentArticle12345"}

    @patch('adminmcp.server.acp_server.request.urlopen')
    def test_wikipedia_article_other_error(self, mock_urlopen):
        """Test Wikipedia article with other HTTP error."""
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(None, 500, "Internal Server Error", None, None)

        with pytest.raises(HTTPError):
            wikipedia_article("Some Article")