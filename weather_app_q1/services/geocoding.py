# Converts user input into valid geographic coordinates (lat/lon).
from typing import Optional, Tuple
import requests

# Open-Meteo endpoints for forward and reverse geocoding
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
REVERSE_URL = "https://geocoding-api.open-meteo.com/v1/reverse"

# Provides a User-Agent for external geocoding services
HEADERS = {"User-Agent": "WeatherApp/1.0 (contact: your-email@example.com)"}


# Checks if a string is in 'lat,lon' form and within valid bounds
def is_latlon(q: str) -> bool:
    try:
        lat_str, lon_str = q.split(",")
        lat, lon = float(lat_str), float(lon_str)
        return -90 <= lat <= 90 and -180 <= lon <= 180
    except Exception:
        return False


# Looks up landmarks/POIs using OpenStreetMap Nominatim 
def nominatim_search(q: str) -> Optional[Tuple[float, float, str]]:
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1},
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        items = resp.json() or []
        if not items:
            return None
        it = items[0]
        lat, lon = float(it.get("lat")), float(it.get("lon"))
        display = it.get("display_name") or q
        return (lat, lon, display)
    except Exception:
        return None


# Reverse-geocodes coordinates using Nominatim 
def nominatim_reverse(lat: float, lon: float) -> Optional[str]:
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "jsonv2"},
            headers=HEADERS,
            timeout=10,
        )
        if resp.status_code != 200:
            return None
        data = resp.json() or {}
        return data.get("display_name")
    except Exception:
        return None


# Converts a place name into coordinates, then matches, then uses the landmark as a fallback
def geocode_name(q: str) -> Optional[Tuple[float, float, str]]:
    resp = requests.get(GEOCODE_URL, params={"name": q, "count": 1, "language": "en"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json() or {}
        results = data.get("results") or []
        if results:
            r = results[0]
            name = (r.get("name") or "").lower().strip()
            admin1 = r.get("admin1")
            country = r.get("country")
            if q.lower().strip() == name:
                display = ", ".join(filter(None, [r.get("name"), admin1, country]))
                return (r["latitude"], r["longitude"], display)

    # If strict city match failed, try landmark fallback
    return nominatim_search(q)


# Converts coordinates into a display name
def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None

    # Try Open-Meteo reverse first
    resp = requests.get(REVERSE_URL, params={"latitude": lat, "longitude": lon, "language": "en"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json() or {}
        results = data.get("results") or []
        if results:
            r = results[0]
            name = ", ".join(filter(None, [r.get("name"), r.get("admin1"), r.get("country")]))
            if name:
                return name

    # Fallback to Nominatim reverse for place names
    return nominatim_reverse(lat, lon)


# Decides whether a query is coordinates or a place name and returns (lat, lon, display)
def coordinates_from_query(q: Optional[str]) -> Optional[Tuple[float, float, str]]:
    if not q:
        return None

    # Numeric coordinates path
    if is_latlon(q):
        lat_str, lon_str = q.split(",")
        lat, lon = float(lat_str), float(lon_str)
        name = reverse_geocode(lat, lon)
        if not name:
            return None
        return lat, lon, name

    # Landmark path
    return geocode_name(q)
