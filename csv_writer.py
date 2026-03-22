import csv
import os
from datetime import datetime

HEADERS = [
    "business_name",
    "address",
    "phone",
    "website",
    "rating",
    "category",
    "emails",
    "contact_name",
    "contact_role",
    "google_maps_url",
]


def write_results(results: list[dict], output_dir: str = "results") -> str:
    """Write results to a timestamped CSV file."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f"{timestamp}_results.csv")

    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()

        for result in results:
            emails = result.get("emails", [])
            contacts = result.get("contacts", [])

            writer.writerow({
                "business_name": result.get("business_name", ""),
                "address": result.get("address", ""),
                "phone": result.get("phone", ""),
                "website": result.get("website", ""),
                "rating": result.get("rating", ""),
                "category": result.get("category", ""),
                "emails": "; ".join(emails),
                "contact_name": "; ".join(c.get("name", "") for c in contacts),
                "contact_role": "; ".join(c.get("role", "") for c in contacts),
                "google_maps_url": result.get("google_maps_url", ""),
            })

    return filepath
