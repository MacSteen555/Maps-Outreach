import os
import httpx
from dotenv import load_dotenv

load_dotenv()

PLACES_API_URL = "https://places.googleapis.com/v1/places:searchText"


def search_places(query: str, max_results: int = 20) -> list[dict]:
    """Search Google Places API and return parsed business info."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not set in environment")

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.formattedAddress,"
            "places.nationalPhoneNumber,"
            "places.websiteUri,"
            "places.rating,"
            "places.userRatingCount,"
            "places.primaryTypeDisplayName,"
            "places.googleMapsUri"
        ),
    }

    body = {
        "textQuery": query,
        "maxResultCount": min(max_results, 20),
    }

    response = httpx.post(PLACES_API_URL, json=body, headers=headers)
    response.raise_for_status()
    data = response.json()

    results = []
    for place in data.get("places", []):
        results.append({
            "business_name": place.get("displayName", {}).get("text", ""),
            "address": place.get("formattedAddress", ""),
            "phone": place.get("nationalPhoneNumber", ""),
            "website": place.get("websiteUri", ""),
            "rating": place.get("rating", ""),
            "review_count": place.get("userRatingCount", ""),
            "category": place.get("primaryTypeDisplayName", {}).get("text", ""),
            "google_maps_url": place.get("googleMapsUri", ""),
        })

    return results
