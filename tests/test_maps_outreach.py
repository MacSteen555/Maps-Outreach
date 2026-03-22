from unittest.mock import patch, MagicMock
from maps_outreach import run_outreach


def test_run_outreach_finds_email_on_homepage():
    """Test the pipeline when emails are found on the homepage."""
    mock_places = [
        {
            "business_name": "Test Biz",
            "address": "123 Main St",
            "phone": "555-0100",
            "website": "https://testbiz.com",
            "rating": 4.0,
            "category": "Dentist",
            "google_maps_url": "https://maps.google.com/?cid=1",
        }
    ]

    mock_scrape = {
        "markdown": "# Test Biz\nEmail us at info@testbiz.com",
        "links": [],
        "error": None,
    }

    mock_contact = {
        "emails": ["info@testbiz.com"],
        "contacts": [{"name": "John", "role": "Manager", "email": "john@testbiz.com"}],
        "contact_page_path": None,
        "error": None,
    }

    with patch("maps_outreach.search_places", return_value=mock_places), \
         patch("maps_outreach.scrape_url", return_value=mock_scrape), \
         patch("maps_outreach.extract_contact_info", return_value=mock_contact), \
         patch("maps_outreach.write_results", return_value="results/test.csv") as mock_write:

        result = run_outreach("dentists near Austin TX", max_results=10)

    assert result["total"] == 1
    assert result["with_email"] == 1
    written_data = mock_write.call_args[0][0]
    assert written_data[0]["emails"] == ["info@testbiz.com"]


def test_run_outreach_follows_contact_page():
    """Test that contact page is scraped when homepage has no emails."""
    mock_places = [
        {
            "business_name": "Test Biz",
            "address": "123 Main St",
            "phone": "555-0100",
            "website": "https://testbiz.com",
            "rating": 4.0,
            "category": "Dentist",
            "google_maps_url": "https://maps.google.com/?cid=1",
        }
    ]

    homepage_scrape = {
        "markdown": "# Welcome to Test Biz",
        "links": ["https://testbiz.com/contact"],
        "error": None,
    }

    contact_scrape = {
        "markdown": "# Contact\nEmail: hello@testbiz.com",
        "links": [],
        "error": None,
    }

    homepage_extract = {
        "emails": [],
        "contacts": [],
        "contact_page_path": "/contact",
        "error": None,
    }

    contact_extract = {
        "emails": ["hello@testbiz.com"],
        "contacts": [],
        "contact_page_path": None,
        "error": None,
    }

    with patch("maps_outreach.search_places", return_value=mock_places), \
         patch("maps_outreach.scrape_url", side_effect=[homepage_scrape, contact_scrape]), \
         patch("maps_outreach.extract_contact_info", side_effect=[homepage_extract, contact_extract]), \
         patch("maps_outreach.write_results", return_value="results/test.csv") as mock_write:

        result = run_outreach("dentists", max_results=5)

    assert result["with_email"] == 1
    written_data = mock_write.call_args[0][0]
    assert written_data[0]["emails"] == ["hello@testbiz.com"]


def test_run_outreach_skips_no_website():
    """Test that businesses without websites are skipped for scraping."""
    mock_places = [
        {
            "business_name": "No Website Biz",
            "address": "456 Oak Ave",
            "phone": "555-0200",
            "website": "",
            "rating": 3.0,
            "category": "Cafe",
            "google_maps_url": "",
        }
    ]

    with patch("maps_outreach.search_places", return_value=mock_places), \
         patch("maps_outreach.scrape_url") as mock_scrape, \
         patch("maps_outreach.extract_contact_info") as mock_extract, \
         patch("maps_outreach.write_results", return_value="results/test.csv"):

        result = run_outreach("cafes", max_results=5)

    mock_scrape.assert_not_called()
    mock_extract.assert_not_called()
    assert result["total"] == 1
    assert result["with_email"] == 0
