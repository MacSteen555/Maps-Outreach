import json
from unittest.mock import patch, MagicMock
from extractor import extract_contact_info


def test_extract_contact_info_parses_response():
    """Test that OpenAI's JSON response is correctly parsed."""
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "emails": ["info@dentist.com", "admin@dentist.com"],
        "contacts": [
            {"name": "Dr. Smith", "role": "Owner", "email": "smith@dentist.com"}
        ],
        "contact_page_path": None,
    })

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("extractor.OpenAI", return_value=mock_client):
        result = extract_contact_info("Some website text about dentistry")

    assert "info@dentist.com" in result["emails"]
    assert result["contacts"][0]["name"] == "Dr. Smith"
    assert result["contact_page_path"] is None


def test_extract_contact_info_returns_contact_page_path():
    """Test that contact page path is returned when no emails found."""
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "emails": [],
        "contacts": [],
        "contact_page_path": "/contact-us",
    })

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with patch("extractor.OpenAI", return_value=mock_client):
        result = extract_contact_info("Welcome to our site. Visit our contact page.")

    assert result["emails"] == []
    assert result["contact_page_path"] == "/contact-us"


def test_extract_contact_info_handles_api_error():
    """Test graceful handling of API errors."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    with patch("extractor.OpenAI", return_value=mock_client):
        result = extract_contact_info("Some text")

    assert result["emails"] == []
    assert result["contacts"] == []
    assert result["contact_page_path"] is None
    assert result["error"] is not None
