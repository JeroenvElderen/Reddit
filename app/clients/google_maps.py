import requests
from app.config import GOOGLE_MAPS_API_KEY


def geocode(query: str):
    """Geocode a place name using Google Maps.

    Returns a tuple of (latitude, longitude) or None if not found.
    """
    if not GOOGLE_MAPS_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set")
    params = {"address": query, "key": GOOGLE_MAPS_API_KEY}
    res = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=params, timeout=10)
    data = res.json()
    results = data.get("results")
    if results:
        loc = results[0]["geometry"]["location"]
        return loc["lat"], loc["lng"]
    return None