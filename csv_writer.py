import csv
import os
from datetime import datetime

HEADERS = [
    "business_name",
    "address",
    "phone",
    "website",
    "rating",
    "review_count",
    "category",
    "emails",
    "contact_name",
    "contact_role",
    "google_maps_url",
]


def write_results(results: list[dict], query: str = "", output_dir: str = "results") -> str:
    """Write results to a CSV file named after the search query."""
    import re
    os.makedirs(output_dir, exist_ok=True)
    # Sanitize query for use as filename
    safe_name = re.sub(r'[^\w\s-]', '', query).strip().replace(' ', '_')[:100]
    if not safe_name:
        safe_name = "results"
    filepath = os.path.join(output_dir, f"{safe_name}.csv")

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
                "review_count": result.get("review_count", ""),
                "category": result.get("category", ""),
                "emails": "; ".join(emails),
                "contact_name": "; ".join(c.get("name", "") for c in contacts),
                "contact_role": "; ".join(c.get("role", "") for c in contacts),
                "google_maps_url": result.get("google_maps_url", ""),
            })

    return filepath
