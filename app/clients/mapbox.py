"""Mapbox Geocoding API client."""

from typing import Optional, Tuple
import os
import requests
from dotenv import load_dotenv

load_dotenv()
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")


def geocode(query: str) -> Optional[Tuple[float, float]]:
    """Return (latitude, longitude) for a free-form location query.

    If the lookup fails or MAPBOX_TOKEN is missing, returns ``None``.
    """
    if not MAPBOX_TOKEN:
        return None
    url = (
        "https://api.mapbox.com/geocoding/v5/mapbox.places/"
        f"{requests.utils.quote(query)}.json"
    )
    params = {"access_token": MAPBOX_TOKEN, "limit": 1}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features")
        if not features:
            return None
        lon, lat = features[0].get("center", [None, None])
        if lat is None or lon is None:
            return None
        return float(lat), float(lon)
    except Exception:
        return None