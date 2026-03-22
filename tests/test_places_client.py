import os
from unittest.mock import patch, MagicMock
from places_client import search_places


def test_search_places_parses_response():
    """Test that search_places correctly parses the Google Places API response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "places": [
            {
                "displayName": {"text": "Austin Dental"},
                "formattedAddress": "123 Main St, Austin, TX",
                "nationalPhoneNumber": "(512) 555-0100",
                "websiteUri": "https://austindental.com",
                "rating": 4.5,
                "primaryTypeDisplayName": {"text": "Dentist"},
                "googleMapsUri": "https://maps.google.com/?cid=123",
            }
        ]
    }

    with patch("places_client.httpx.post", return_value=mock_response), \
         patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"}):
        results = search_places("dentists near Austin TX", max_results=10)

    assert len(results) == 1
    assert results[0]["business_name"] == "Austin Dental"
    assert results[0]["address"] == "123 Main St, Austin, TX"
    assert results[0]["phone"] == "(512) 555-0100"
    assert results[0]["website"] == "https://austindental.com"
    assert results[0]["rating"] == 4.5
    assert results[0]["category"] == "Dentist"


def test_search_places_handles_missing_fields():
    """Test that missing optional fields default to empty strings."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "places": [
            {
                "displayName": {"text": "Some Place"},
                "formattedAddress": "456 Oak Ave",
            }
        ]
    }

    with patch("places_client.httpx.post", return_value=mock_response), \
         patch.dict(os.environ, {"GOOGLE_MAPS_API_KEY": "test-key"}):
        results = search_places("cafes", max_results=5)

    assert results[0]["phone"] == ""
    assert results[0]["website"] == ""
    assert results[0]["rating"] == ""
    assert results[0]["category"] == ""
