import csv
import os
import tempfile
from csv_writer import write_results


def test_write_results_creates_csv():
    """Test that CSV is created with correct headers and data."""
    results = [
        {
            "business_name": "Austin Dental",
            "address": "123 Main St",
            "phone": "(512) 555-0100",
            "website": "https://austindental.com",
            "rating": 4.5,
            "category": "Dentist",
            "google_maps_url": "https://maps.google.com/?cid=123",
            "emails": ["info@austindental.com"],
            "contacts": [{"name": "Dr. Smith", "role": "Owner", "email": "smith@austindental.com"}],
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = write_results(results, output_dir=tmpdir)
        assert os.path.exists(filepath)

        with open(filepath, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["business_name"] == "Austin Dental"
        assert "info@austindental.com" in rows[0]["emails"]
        assert "Dr. Smith" in rows[0]["contact_name"]


def test_write_results_handles_empty_contacts():
    """Test CSV output when no contact info was found."""
    results = [
        {
            "business_name": "Some Place",
            "address": "456 Oak Ave",
            "phone": "",
            "website": "",
            "rating": "",
            "category": "",
            "google_maps_url": "",
            "emails": [],
            "contacts": [],
        }
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = write_results(results, output_dir=tmpdir)

        with open(filepath, "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0]["emails"] == ""
        assert rows[0]["contact_name"] == ""
