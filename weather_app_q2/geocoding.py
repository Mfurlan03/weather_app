from typing import Optional, Tuple
import requests
import re

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
REVERSE_URL = "https://geocoding-api.open-meteo.com/v1/reverse"

# Set a user agent for API requests
HEADERS = {"User-Agent": "WeatherApp/1.0 (contact: demo@example.com)"}

# Simple pattern to detect "lat,lon" format
COORD_RE = re.compile(r"^\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*$")

# Checks if a string looks like coordinate input
def looks_like_coords(q: str) -> bool:
    return bool(COORD_RE.match(q or ""))

# Looks up a place name using OpenStreetMap 
def nominatim_search(q: str) -> Optional[Tuple[float, float, str]]:
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": q, "format": "json", "limit": 1},
            headers=HEADERS, timeout=10
        )
        if resp.status_code != 200:
            return None
        items = resp.json()
        if not items:
            return None
        it = items[0]
        lat, lon = float(it["lat"]), float(it["lon"])
        display = it.get("display_name") or q
        return (lat, lon, display)
    except Exception:
        return None

# Gets a readable location name from coordinates using OpenStreetMap
def nominatim_reverse(lat: float, lon: float) -> Optional[str]:
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "jsonv2"},
            headers=HEADERS, timeout=10
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data.get("display_name")
    except Exception:
        return None

# Validates that a string has valid latitude and longitude
def is_latlon(q: str) -> bool:
    try:
        lat_str, lon_str = q.split(",")
        lat, lon = float(lat_str), float(lon_str)
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return False
        return True
    except Exception:
        return False

# Finds coordinates for a place name using Open-Meteo, with a fallback to OpenStreetMap (had errors before adding the fallback)
def geocode_name(q: str, allow_fuzzy: bool = True) -> Optional[Tuple[float, float, str]]:
    resp = requests.get(GEOCODE_URL, params={"name": q, "count": 1, "language": "en"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        results = data.get("results") or []
        if results:
            r = results[0]
            name = r.get("name", "").lower().strip()
            admin1 = r.get("admin1")
            country = r.get("country")
            qn = q.lower().strip()
            if qn == name or (allow_fuzzy and qn in ", ".join(filter(None, [r.get("name",""), admin1 or "", country or ""])).lower()):
                display = ", ".join(filter(None, [r.get("name"), admin1, country]))
                return (r["latitude"], r["longitude"], display)
    return nominatim_search(q)

# Finds a readable place name for given coordinates
def reverse_geocode(lat: float, lon: float) -> Optional[str]:
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    resp = requests.get(REVERSE_URL, params={"latitude": lat, "longitude": lon, "language": "en"}, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        results = data.get("results") or []
        if results:
            r = results[0]
            name = ", ".join(filter(None, [r.get("name"), r.get("admin1"), r.get("country")]))
            if name:
                return name
    return nominatim_reverse(lat, lon)

# Determines coordinates (and name) from either a place name or direct coordinate input
def coordinates_from_query(q: Optional[str], allow_fuzzy: bool = True) -> Optional[Tuple[float, float, str]]:
    if not q:
        return None
    q = q.strip()

    if looks_like_coords(q):
        if not is_latlon(q):
            return None
        lat_str, lon_str = q.split(",")
        lat, lon = float(lat_str), float(lon_str)
        name = reverse_geocode(lat, lon)
        if not name:
            return None
        return lat, lon, name

    return geocode_name(q, allow_fuzzy=allow_fuzzy)
